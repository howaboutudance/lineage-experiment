# PLANNING.md — lineage-experiment

## Goal

Validate whether the 2026 data tooling stack can express a layered data quality +
lineage architecture cleanly — one that was built ad-hoc and painfully at BMS (2018-2021)
with the tools available then. This is an experiment, not a product. Success means
learnings, not a publishable library (yet).

## Guiding principles

- **Experiments over abstractions**: understand the tools before abstracting over them
- **Failure modes are first-class**: every phase includes injecting known real failures
  and confirming the architecture catches them
- **Reproducibility as a primitive**: every datacut must be re-queryable at a specific
  version and return the same answer
- **Lineage must be resolvable**: "where did this number come from" must be answerable
  from metadata alone, without re-running the pipeline

---

## Phase 1: Synthetic data generation + pytest ingestion contracts

**Goal**: Build synthetic data generators that model the BMS CRO transfer topology and
confirm that pytest ingestion contracts catch all 6 known failure modes.

**Deliverables**:
- `src/lineage_experiment/synthetic/` — deterministic (seeded) generators for:
  - FCS-equivalent binary payloads (numpy arrays as acquisition data, dict as metadata)
  - MSD/Luminex-equivalent Excel exports (openpyxl)
  - Transfer manifests (JSON, mix of S3 and FTP-style source URIs)
- `test/test_ingestion/` — pytest tests confirming detection of:
  1. Duplicate payload (same data array, different metadata)
  2. Missing timepoint in patient/timepoint matrix
  3. Partial transfer (manifest count != actual file count)
  4. Sample ID format inconsistency across CRO sources
  5. MSD plate layout mismatch
  6. Derived endpoint outside plausibility range (sanity check — this one bleeds
     into Phase 3 but seed it here)

**Key questions**:
- Does fcsparser's data segment extraction work cleanly enough for payload hashing?
- Can hypothesis generate realistic enough patient/timepoint matrices for property-based
  ingestion tests?
- Where does the pytest fixture boundary naturally fall — per-file or per-manifest?

**Done when**: `pytest test/test_ingestion/ -v` shows all 6 failure modes detected with
clear, readable failure messages. A human reading the output should understand what went
wrong without reading the test code.

---

## Phase 2: Delta Lake snapshot isolation + reproducible datacuts

**Goal**: Confirm that Delta Lake's commit log provides snapshot isolation strong enough
to use as a reproducibility primitive. A datacut at version N should always return the
same result regardless of subsequent writes.

**Deliverables**:
- `src/lineage_experiment/ingestion/` — ingestion layer that writes validated data into
  a local Delta table (using `deltalake` Python bindings)
- Snapshot/version metadata carried forward in the Delta commit log
- pytest tests confirming:
  - Write at version N → query at version N → same result after version N+1 writes
  - Time-travel query by timestamp works
  - Schema evolution (new column added) doesn't break version N reads

**Key questions**:
- Does `deltalake` (rust-backed) vs `delta-spark` matter for local experimentation?
  (Hypothesis: rust-backed is fine for this scale, no Spark needed)
- What's the right granularity for a "datacut" — per study? per CRO batch? per timepoint?
- How does the Delta commit log interact with OpenLineage events? (Phase 4 question but
  note observations here)

**Done when**: Can write two sequential batches, query each by version, and get
deterministically different results confirming snapshot isolation.

---

## Phase 3: GE handoff contracts on derived endpoints

**Goal**: GE 1.0+ API (August 2024 breaking changes) expressing derived endpoint
contracts that are stakeholder-readable and auditable. Confirm the GE/pytest boundary
holds — GE is for derived handoff, pytest is for source/intermediate.

**Deliverables**:
- `src/lineage_experiment/derived/` — simple aggregation pipeline: FCS payload →
  per-patient/per-timepoint derived metrics (% positive, MFI equivalent)
- `config/gx/` — GE expectation suites for derived endpoint tables:
  - Completeness (all expected patient/timepoint combinations present)
  - Plausibility ranges (% positive 0-100, MFI within instrument range)
  - No nulls in primary key columns
  - Row count within expected bounds per cohort
- GE Data Docs output to `docs/gx_reports/` for "stakeholder-readable" validation

**Key questions**:
- Does GE 1.0+ API feel materially better than 0.x for this use case?
- Can GE express cross-dataset checks (derived count matches source count)?
  (This is where GE historically got awkward — test the limit)
- What does GE Data Docs output actually look like for a non-technical audience?
  Would a scientist or biostatistician trust it?

**Done when**: GE suite runs against a derived endpoint table with 2 injected anomalies
(plausibility violation, missing timepoint) and produces a Data Docs report that clearly
identifies both failures in plain language.

---

## Phase 4: OpenLineage spine

**Goal**: Wire OpenLineage event emission into both the pytest ingestion layer and the GE
handoff layer so that "which source file contributed to this derived endpoint value" is
answerable from metadata alone.

**Deliverables**:
- `src/lineage_experiment/lineage/` — OpenLineage client helpers:
  - Emit `RunEvent` on ingestion (input: manifest URI, output: Delta table + version)
  - Emit `RunEvent` on GE validation (input: derived table + version, output: GE suite
    result + Data Docs URI)
  - Content hash as a dataset facet (the key insight from BMS)
- Local Marquez instance (Docker) as the lineage backend, OR just emit to file for
  initial experiments
- pytest test: given a derived endpoint row, trace back to source manifest entry via
  OpenLineage events

**Key questions**:
- Is Marquez still the right local backend in 2026 or has something better emerged?
- Does OpenLineage's Airflow integration (if Airflow is added later) subsume manual
  emission, or is explicit emission still valuable for non-Airflow transforms?
- What's the right OpenLineage dataset identifier for a Delta table version?
  (`delta://path/to/table@v3`?)

**Done when**: Can answer "what was the payload hash of the FCS file that contributed to
patient 007 day 15 MFI value" by querying OpenLineage events alone, without re-running
the pipeline.

---

## Phase 5: Portable query layer (DuckDB / DataFusion)

**Goal**: Confirm that the datacut is portable — a Delta table + DuckDB is queryable
on a laptop with no server, no Spark, no infrastructure. Bonus: expose via pg_wire for
Postgres-compatible client access.

**Deliverables**:
- DuckDB queries over Delta tables (using `duckdb` + `deltalake` together)
- Confirm time-travel queries work through DuckDB
- Optional stretch: DataFusion + pg_wire layer exposing the datacut as a Postgres
  endpoint that psql / SQLAlchemy can connect to

**Key questions**:
- Does DuckDB's Delta Lake support (via `delta` extension) handle version/time-travel
  queries natively or does it need Python-layer mediation?
- What's the actual developer experience of DataFusion + pg_wire for a non-Rust developer?
  Is it worth it for the "looks like Postgres" benefit?
- Could this stack replace the "biostat gets a CSV" handoff with "biostat gets a
  connection string"?

**Done when**: Analyst-facing query (`SELECT * FROM endpoints WHERE patient_id = '007'
AND timepoint = 'D15'`) works via DuckDB against a versioned Delta table on local disk,
and the same query returns the same result at the pinned version after new data is written.

---

## Stretch / future phases

- **Airflow integration**: replace synthetic pipeline runner with Airflow DAG + native
  OpenLineage Airflow integration; compare to manual emission
- **SAS boundary**: can `haven` (R) or `pyreadstat` read the derived endpoint Delta table
  and emit a valid XPT file? Close the loop on the original BMS submission chain.
- **Multi-CRO simulation**: two synthetic CROs with different ID formats, unified by
  ingestion normalization layer, full lineage through both
- **Publish the pattern**: if the experiments validate the hypothesis, write it up as a
  named architecture pattern with reference implementation

---

## Non-goals (for now)

- Production-grade infrastructure (no real S3, no real Airflow, no cloud)
- Real biomedical data (synthetic only — no PHI, no HIPAA surface)
- Generalizing to non-biomedical domains (that comes after validation)
- Performance optimization (correctness first, scale later)
- A user-facing API or library (experiments, not products)
