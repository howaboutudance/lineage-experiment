# Synthetic Data Generators

## User Story

As the experiment author, I want deterministic, seeded synthetic data generators for
FCS-equivalent payloads, MSD/Luminex-equivalent exports, and CRO transfer manifests
so that ingestion contract tests are reproducible and failure modes can be injected
precisely without relying on real patient data.

## Acceptance Criteria

- [ ] `src/lineage_experiment/synthetic/fcs.py` — generates `SyntheticFCSFile` instances
  with a numpy data array (hashable payload) and a metadata dict (TEXT segment equivalent);
  seeded via `numpy.random.default_rng(seed)`
- [ ] `src/lineage_experiment/synthetic/msd.py` — generates `SyntheticMSDExport` instances
  with plate layout, analyte data as a DataFrame, and an LXB provenance URI
- [ ] `src/lineage_experiment/synthetic/manifest.py` — generates transfer manifests as
  dicts (JSON-serializable) for both CRO-A (S3-style) and CRO-B (FTP-style) sources
- [ ] Each generator accepts a `seed: int` parameter; same seed → same output always
- [ ] Failure mode variants are first-class generator outputs, not test-side monkey patches:
  - `fcs.duplicate_payload(seed)` — two files with identical data arrays, different metadata
  - `manifest.partial_transfer(seed, drop_n=1)` — manifest declares N, only N-1 files present
  - `manifest.bad_sample_id(seed, cro="B")` — CRO-B file with CRO-A format ID
  - `msd.plate_layout_mismatch(seed)` — analyte positions don't match template
- [ ] `test/fixtures/conftest.py` exposes generators as pytest fixtures
- [ ] All generators are importable from `lineage_experiment.synthetic`

## Key Questions

- Does `fcsparser` data segment extraction suit payload hashing, or do we hash the raw
  numpy array directly and treat fcsparser as read-path only?
- What's the right numpy dtype for synthetic event matrices — float32 to match real FCS
  instrument output, or float64 for simplicity?
- Where does the `SyntheticFCSFile` dataclass live — in `synthetic/fcs.py` or in a shared
  `synthetic/models.py`? Decide based on how much the MSD generator needs to share.

---

## Project Plan

### File changes

| File | Change |
|------|--------|
| `src/lineage_experiment/synthetic/fcs.py` | New — FCS generator + failure mode variants |
| `src/lineage_experiment/synthetic/msd.py` | New — MSD generator + plate mismatch variant |
| `src/lineage_experiment/synthetic/manifest.py` | New — manifest generator + failure variants |
| `src/lineage_experiment/synthetic/__init__.py` | Update to re-export public generators |
| `test/fixtures/conftest.py` | New — pytest fixtures wrapping generators |

### Dependencies

- `numpy` (already in core deps via pyarrow transitive, add explicitly)
- `openpyxl` — needed for MSD Excel export generation; add to core deps
- `pandas` — already declared

### Env vars

None.

### Merge notes

- This story is a dependency of [Ingestion Contracts for All 6 Failure Modes](./ingestion-contracts.md)
- Merge this first; ingestion contracts story branches from the merged state
