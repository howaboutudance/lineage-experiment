# ARCHITECTURE.md — lineage-experiment

## Overview

A layered data quality and lineage architecture for regulated-style data pipelines.
The key insight is that `pytest` and `great_expectations` are **not alternatives** —
they are complementary tools operating at different pipeline boundaries with different
audiences and different contract semantics.

```
┌─────────────────────────────────────────────────────────────────┐
│  CRO / External Source                                          │
│  (FCS files, MSD Excel, transfer manifests)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │  custody transfer boundary
                ┌───────────▼───────────┐
                │   pytest contracts    │  ← INGESTION LAYER
                │   (structural,        │
                │    programmatic,      │
                │    conditional)       │
                └───────────┬───────────┘
                            │  emit OpenLineage RunEvent
                            │  (input: manifest URI + content hash)
                            │  (output: Delta table + version)
                ┌───────────▼───────────┐
                │   Delta Lake          │  ← INTERMEDIATE LAYER
                │   (snapshot isolation,│
                │    commit log,        │
                │    time travel)       │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   derived transforms  │  ← TRANSFORM LAYER
                │   (aggregation,       │
                │    normalization,     │
                │    endpoint calc)     │
                └───────────┬───────────┘
                            │  emit OpenLineage RunEvent
                            │  (input: Delta version)
                            │  (output: derived table + version)
                ┌───────────▼───────────┐
                │   GE contracts        │  ← HANDOFF LAYER
                │   (declarative,       │
                │    auditable,         │
                │    stakeholder-       │
                │    readable)          │
                └───────────┬───────────┘
                            │  emit OpenLineage RunEvent
                            │  (input: derived table version)
                            │  (output: GE suite result + Data Docs)
                ┌───────────▼───────────┐
                │   DuckDB query layer  │  ← DELIVERY LAYER
                │   (portable,          │
                │    no server,         │
                │    time-travel)       │
                └─────────────────────────┘
```

---

## Layer 1: pytest ingestion contracts

**What it owns**: everything between external custody transfer and internal storage.

**Why pytest, not GE**: ingestion contracts are **engineering contracts** — they verify
that data arriving from an external source conforms to structural and logical expectations
before it enters the system. These checks are:

- **Conditional**: "if this is CRO-A format, then sample IDs must match `PT\d{3}-D\d+`"
- **Programmatic**: "compute SHA-256 of data payload (not metadata), check for
  duplicates against known hashes"
- **Fixture-heavy**: "given this manifest, these files, and this known-good hash registry"
- **Infrastructure-aware**: "does file count match manifest count"

GE's declarative model is awkward for all of these. pytest fixtures + parametrize handle
them naturally.

**Key contracts to implement**:
```python
# Structural
test_manifest_completeness          # all declared files present
test_fcs_channel_presence           # expected channels in acquisition
test_sample_id_format_per_source    # per-CRO format validation

# Integrity
test_no_duplicate_fcs_payloads      # content hash uniqueness
test_transfer_hash_matches_manifest # end-to-end integrity

# Logical
test_patient_timepoint_matrix       # no unexpected gaps
test_msd_plate_layout               # analyte positions match template
```

**OpenLineage emission pattern**:
```python
# emit after successful ingestion batch
client.emit(RunEvent(
    eventType=RunState.COMPLETE,
    run=Run(runId=str(uuid4())),
    job=Job(namespace="lineage-experiment", name="fcs_ingestion"),
    inputs=[Dataset(
        namespace="cro-transfer",
        name=manifest_uri,
        facets={"contentHash": ContentHashFacet(hash=payload_hash)}
    )],
    outputs=[Dataset(
        namespace="delta",
        name=f"intermediate/fcs_derived@v{delta_version}"
    )]
))
```

---

## Layer 2: Delta Lake intermediate storage

**What it owns**: snapshot isolation, schema evolution, time travel, commit log as
implicit lineage.

**Why Delta Lake, not plain Parquet**: the "custom piles of Parquet" approach (BMS
2019-2020) required reinventing:
- Snapshot isolation ("which files constitute this cut")
- The manifest problem
- Schema evolution
- Concurrent write safety

Delta's commit log solves all of these. The commit log is also an **append-only audit
trail** — tamper-evident by construction, which maps naturally to regulated environment
requirements.

**Datacut semantics**: a "datacut" is a specific Delta table version. Version numbers
are stable, monotonically increasing, and resolvable. The lineage spine carries the
version as the dataset identifier.

**Local usage** (no Spark required):
```python
from deltalake import DeltaTable, write_deltalake

# write
write_deltalake("data/intermediate/fcs_derived", df, mode="append")

# read at specific version
dt = DeltaTable("data/intermediate/fcs_derived", version=3)
df = dt.to_pandas()

# time travel
dt = DeltaTable("data/intermediate/fcs_derived",
                as_of_version=3)
```

---

## Layer 3: GE handoff contracts

**What it owns**: everything at the derived endpoint delivery boundary.

**Why GE, not pytest**: handoff contracts are **data contracts** — they verify that
derived data conforms to expectations that scientists, biostatisticians, and auditors
can read and understand without reading Python code. These checks are:

- **Declarative**: "MFI values must be between 0 and 500,000"
- **Auditable**: GE Data Docs produce HTML reports a regulator could review
- **Stakeholder-readable**: expectation names and failure messages are plain English
- **Suite-based**: a named, versioned collection of expectations maps to a protocol
  endpoint definition

**Key expectation suites**:
```python
# completeness
expect_table_row_count_to_be_between(min_value=n_patients * n_timepoints * 0.9, ...)
expect_compound_columns_to_be_unique(["patient_id", "timepoint", "analyte"])

# plausibility
expect_column_values_to_be_between("pct_positive", min_value=0, max_value=100)
expect_column_values_to_be_between("mfi", min_value=0, max_value=500_000)

# completeness per cohort
expect_column_value_z_scores_to_be_less_than("cohort_n", threshold=3)

# no nulls in keys
expect_column_values_to_not_be_null("patient_id")
expect_column_values_to_not_be_null("timepoint")
```

**The GE/pytest boundary test**: if you find yourself writing a GE custom expectation
that needs a fixture, a database lookup, or conditional logic — stop. That check belongs
in pytest at the ingestion layer, not in GE at the handoff layer.

---

## Layer 4: OpenLineage spine

**What it owns**: connecting ingestion events to derived endpoint versions so that
provenance is resolvable from metadata alone.

**The core insight from BMS**: the information was all there in Airflow logs. It just
had no structured extraction layer. Contractors parsed logs manually. OpenLineage is
the structured extraction layer that was missing.

**Event model**:
```
RunEvent (ingestion)
    job: fcs_ingestion
    input: cro-transfer://manifest/batch-007
           facets: { contentHash: "sha256:abc123..." }
    output: delta://intermediate/fcs_derived@v3

RunEvent (transform)
    job: derive_endpoints
    input: delta://intermediate/fcs_derived@v3
    output: delta://derived/endpoints@v5

RunEvent (validation)
    job: ge_handoff_validation
    input: delta://derived/endpoints@v5
    output: ge://suites/endpoint_suite/results/run-xyz
```

**Answering the provenance question**:
```
"Which FCS file contributed to patient 007 day 15 MFI value?"

1. Query: derived/endpoints WHERE patient_id='007' AND timepoint='D15'
   → comes from delta://derived/endpoints@v5

2. OpenLineage: what produced delta://derived/endpoints@v5?
   → RunEvent: derive_endpoints, input was delta://intermediate/fcs_derived@v3

3. OpenLineage: what produced delta://intermediate/fcs_derived@v3?
   → RunEvent: fcs_ingestion, input was cro-transfer://manifest/batch-007
     contentHash: sha256:abc123...

4. Manifest batch-007 entry for patient 007 day 15:
   → s3://bms-cro-data/cro-b/study-123/run-4/PT007-D15.fcs
     contentHash: sha256:abc123...  ✓
```

---

## Layer 5: DuckDB query layer

**What it owns**: portable, server-free query access to versioned datacuts.

**The portability test**: the datacut is just files. DuckDB reads them anywhere. No
server to spin up, no environment to reconstruct, no database to restore. Analyst on a
laptop, validation environment, regulatory submission package — same files, same answer.

```python
import duckdb

conn = duckdb.connect()
conn.execute("INSTALL delta; LOAD delta;")

# query latest
result = conn.execute("""
    SELECT * FROM delta_scan('data/derived/endpoints')
    WHERE patient_id = '007' AND timepoint = 'D15'
""").df()

# query at version (time travel)
result = conn.execute("""
    SELECT * FROM delta_scan('data/derived/endpoints', version=5)
    WHERE patient_id = '007' AND timepoint = 'D15'
""").df()
```

**Stretch: pg_wire layer**: DataFusion as query engine + pg_wire as Postgres-compatible
frontend — makes the datacut queryable by psql, SQLAlchemy, dbt, Tableau without any
custom client. This is the "looks like Postgres to legacy tooling" layer. Useful if
the biostat handoff is "here's a connection string" rather than "here's a CSV."

---

## What this is NOT

- A Lakehouse platform (no Databricks, no Snowflake, no cloud required)
- A data catalog (no DataHub, no Amundsen — OpenLineage events are the catalog)
- An orchestration framework (no Airflow in Phase 1-5, possible stretch goal)
- Production infrastructure (local files, local DuckDB, local Marquez)
- A generalizable framework (yet — validate first, abstract later)
