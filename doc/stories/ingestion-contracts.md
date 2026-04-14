# Ingestion Contracts for All 6 Failure Modes

## User Story

As the experiment author, I want pytest ingestion contracts that catch all 6 known CRO
transfer failure modes so that I can confirm the architecture detects real-world data
custody problems at the ingestion boundary with clear, human-readable failure output.

## Acceptance Criteria

- [ ] `pytest test/test_ingestion/ -v` passes for all clean inputs
- [ ] Each of the 6 failure modes causes a named test to fail with a readable message —
  a human should understand what went wrong without reading the test code:
  - [ ] FM-1: Duplicate FCS payload detected via content hash
  - [ ] FM-2: Missing timepoint in patient/timepoint matrix
  - [ ] FM-3: Partial transfer — manifest declared count != actual file count
  - [ ] FM-4: Sample ID format inconsistency across CRO sources
  - [ ] FM-5: MSD plate layout mismatch against expected template
  - [ ] FM-6: Derived endpoint outside plausibility range (sanity check at ingestion)
- [ ] Tests use synthetic generators from `lineage_experiment.synthetic` via pytest
  fixtures — no inline data construction in test bodies
- [ ] OpenLineage `RunEvent` is emitted on successful ingestion batch; event is
  asserted in at least one test (can use a file transport for local testing)

## Key Questions

- Does the fixture boundary fall at the file level (one fixture per synthetic file) or
  manifest level (one fixture per batch)? Start at manifest level and split if needed.
- For FM-6: does the plausibility check belong in the ingestion contract or purely in GE
  (Milestone 3)? Seed it here as a pytest assert on raw values; GE picks it up formally
  in Milestone 3.
- What's the right assertion for OpenLineage emission in tests — mock the client, use a
  file transport, or use an in-process collector? Prefer file transport to avoid mocking
  the lineage layer.

---

## Project Plan

### File changes

| File | Change |
|------|--------|
| `src/lineage_experiment/ingestion/contracts.py` | New — ingestion contract functions (hash check, matrix completeness, manifest count, ID format, plate layout, plausibility) |
| `src/lineage_experiment/ingestion/hashing.py` | New — SHA-256 payload hashing utilities |
| `src/lineage_experiment/ingestion/__init__.py` | Update to re-export public API |
| `test/test_ingestion/test_fm1_duplicate_payload.py` | New |
| `test/test_ingestion/test_fm2_missing_timepoint.py` | New |
| `test/test_ingestion/test_fm3_partial_transfer.py` | New |
| `test/test_ingestion/test_fm4_sample_id_format.py` | New |
| `test/test_ingestion/test_fm5_plate_layout.py` | New |
| `test/test_ingestion/test_fm6_plausibility.py` | New |

### Dependencies

- Synthetic data generators (see [Synthetic Data Generators](./synthetic-data-generators.md)) — merge that story first
- `openlineage-python` — already declared in core deps

### Env vars

- `LINEAGE_TRANSPORT` — `file` (default for tests) or `http` for Marquez; configure via
  dynaconf so tests don't need environment surgery

### Merge notes

- Depends on Synthetic Data Generators being merged first
- Done when: `pytest test/test_ingestion/ -v` shows all 6 FM tests failing on injected
  inputs and passing on clean inputs, with readable output throughout
- Move to `completed/` after merge and manual review of pytest output readability
