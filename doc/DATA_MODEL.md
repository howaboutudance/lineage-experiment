# DATA_MODEL.md — lineage-experiment

## Overview

Synthetic data modeled on a translational immunology clinical study. All data is
generated programmatically — no real patient data, no PHI, no HIPAA surface. The
synthetic topology is designed to reproduce the **structural complexity and known failure
modes** of real CRO data transfer pipelines, not to simulate real biology.

---

## Study topology

```
Study: SYNTH-001
    2 CRO sources (different ID formats, different transfer methods)
    20 synthetic patients
    4 timepoints: Baseline (D0), Day 8 (D8), Day 15 (D15), Day 22 (D22)
    2 assay types: FCS (flow cytometry), MSD (cytokine multiplex)
    Expected: 20 patients × 4 timepoints × 2 assays = 160 source files
```

---

## Patient / sample ID schemes

**CRO-A** (S3-style transfer, newer):
```
Format: PT{NNN}-D{NN}
Examples: PT001-D00, PT007-D15, PT020-D22
```

**CRO-B** (FTP-style transfer, legacy):
```
Format: {NNN}_{DD}d
Examples: 001_00d, 007_15d, 020_22d
```

Normalization to canonical form (`patient_id`, `timepoint`) happens at ingestion.
The ID format inconsistency is a known failure mode — the ingestion contract must
detect and flag non-conforming IDs before normalization.

---

## FCS-equivalent synthetic data

### Structure

FCS files have two logical segments:
- **TEXT segment** (metadata): acquisition date, operator, instrument serial, sample ID,
  channel names — this varies between CROs and even between runs from the same CRO
- **DATA segment** (acquisition payload): the actual cytometry event matrix — this is
  what we hash for duplicate detection

Synthetic equivalent:
```python
@dataclass
class SyntheticFCSFile:
    metadata: dict          # TEXT segment equivalent — variable, not hashed
    data: np.ndarray        # DATA segment equivalent — shape (n_events, n_channels)
                            # this is the payload hash input

# typical dimensions
n_events: int = 10_000      # events per acquisition
n_channels: int = 12        # CD3, CD4, CD8, CD14, CD19, CD25, CD45,
                            # FSC-A, FSC-H, SSC-A, SSC-H, viability
```

### Channels (synthetic)
```
FSC-A, FSC-H    # forward scatter
SSC-A, SSC-H    # side scatter
viability       # live/dead
CD3             # T cell marker
CD4             # helper T cell
CD8             # cytotoxic T cell
CD14            # monocyte marker
CD19            # B cell marker
CD25            # activation marker
CD45            # leukocyte marker
```

### Derived endpoints from FCS
```
pct_cd4_of_cd3      # % CD4+ of CD3+ (helper T cells)
pct_cd8_of_cd3      # % CD8+ of CD3+ (cytotoxic T cells)
pct_cd25_of_cd4     # % CD25+ of CD4+ (activated helper T)
mfi_cd25_cd4        # MFI of CD25 in CD4+ gate
```

### Plausibility ranges (for GE contracts)
```
pct_cd4_of_cd3:   0 – 80    (typically 40-60 in healthy donors)
pct_cd8_of_cd3:   0 – 70    (typically 20-40 in healthy donors)
pct_cd25_of_cd4:  0 – 50    (typically 5-20 at baseline)
mfi_cd25_cd4:     0 – 50000 (instrument-dependent, rough upper bound)
```

---

## MSD/Luminex-equivalent synthetic data

### Structure

MSD exports are tabular: one row per sample per analyte, with plate metadata.
The raw instrument format is proprietary (`.lxb`), but the export is effectively an
Excel file with a structured layout.

Synthetic equivalent:
```python
@dataclass
class SyntheticMSDExport:
    plate_id: str
    plate_layout: dict[str, str]    # well_position → sample_id mapping
    analyte_data: pd.DataFrame      # columns: sample_id, analyte, concentration_pgml
    lxb_uri: str                    # provenance pointer to "raw" file
```

### Analytes (synthetic cytokine panel)
```
IL-2, IL-4, IL-6, IL-10, IL-17A, IFN-γ, TNF-α
```

### Plausibility ranges (pg/mL)
```
IL-2:    0 – 5000
IL-4:    0 – 1000
IL-6:    0 – 50000   (acute phase, wide range)
IL-10:   0 – 5000
IL-17A:  0 – 2000
IFN-γ:   0 – 20000
TNF-α:   0 – 10000
```

---

## Transfer manifest structure

```json
{
    "manifest_id": "batch-007",
    "source_cro": "CRO-A",
    "transfer_method": "s3",
    "transfer_timestamp": "2024-03-15T14:22:00Z",
    "study_id": "SYNTH-001",
    "declared_count": 12,
    "files": [
        {
            "sample_id": "PT001-D00",
            "assay_type": "fcs",
            "source_uri": "s3://synth-cro-a/SYNTH-001/run-001/PT001-D00.fcs",
            "expected_hash": "sha256:abc123..."
        },
        ...
    ]
}
```

CRO-B (FTP-style) manifest is structurally identical but `transfer_method: "ftp"` and
`source_uri` uses `ftp://` scheme. Ingestion layer normalizes both.

---

## Injected failure modes

### FM-1: Duplicate FCS payload
```python
# same data array, different metadata (date, operator)
# represents CRO copying a file and changing only the header
fcs_day8 = SyntheticFCSFile(
    metadata={"date": "2024-03-08", "operator": "JSmith", "sample_id": "PT007-D08"},
    data=acquisition_array_42     # seeded array, deterministic
)
fcs_day15_duplicate = SyntheticFCSFile(
    metadata={"date": "2024-03-15", "operator": "JSmith", "sample_id": "PT007-D15"},
    data=acquisition_array_42     # SAME array — duplicate payload
)
```
Detection: payload hash of `data` field matches known hash in registry.

### FM-2: Missing timepoint
```python
# patient 012 has D0, D8, D22 — missing D15
# manifest declares 4 timepoints, only 3 arrive for PT012
```
Detection: patient/timepoint matrix completeness check in pytest.

### FM-3: Partial transfer
```python
# manifest declares 12 files, 11 FCS files actually present on disk
# one file listed in manifest has no corresponding file
```
Detection: `len(actual_files) != manifest.declared_count`.

### FM-4: Sample ID format inconsistency
```python
# CRO-B sends a file with CRO-A format by mistake
# file is named PT007-D15.fcs but CRO-B convention is 007_15d
```
Detection: per-source regex validation in pytest ingestion contracts.

### FM-5: MSD plate layout mismatch
```python
# analyte mapping in export doesn't match expected plate template
# IL-2 is in position B2 but template says IL-6 should be in B2
```
Detection: plate layout validation against expected template in pytest.

### FM-6: Derived endpoint outside plausibility range
```python
# pct_cd4_of_cd3 = 105.3  (impossible — over 100%)
# or mfi_cd25_cd4 = -200  (impossible — negative MFI)
```
Detection: GE plausibility range expectations on derived endpoint table.
(Also detectable at ingestion as a sanity check — see Phase 1 notes.)

---

## Derived endpoint table schema

Final output table written to Delta Lake:

```
patient_id          STRING      NOT NULL    canonical ID (PT{NNN})
timepoint           STRING      NOT NULL    canonical (D0, D8, D15, D22)
assay_type          STRING      NOT NULL    "fcs" | "msd"
analyte             STRING      NOT NULL    endpoint name
value               DOUBLE      NOT NULL    derived value
unit                STRING                  "pct" | "mfi" | "pgml"
source_batch        STRING                  manifest batch_id
source_hash         STRING                  payload hash of source file
delta_version       LONG                    Delta table version at write
ingestion_run_id    STRING                  OpenLineage run ID
```

The `source_hash` and `ingestion_run_id` columns are the lineage anchors — they connect
each derived value back to its source file and ingestion event without needing to
re-query the OpenLineage backend.
