# CLAUDE.md — lineage-experiment

## What this project is

An experimental Python package exploring a layered data quality + lineage architecture
using synthetic biomedical data modeled on real translational medicine pipelines (BMS
2018-2021 vintage). The goal is to validate whether the 2026 tooling stack (Delta Lake,
OpenLineage, DuckDB, DataFusion, Great Expectations) actually delivers on what was
impossible to build cleanly in 2019-2020.

This is **experiments first** — no library, no product, no framework yet. The output is
learnings, not software. Code quality matters but premature abstraction does not.

## The core hypothesis being tested

A layered testing topology where:
- `pytest` owns **ingestion contracts** (source → intermediate): structural, programmatic,
  conditional checks that run at custody transfer boundaries
- `great_expectations` owns **handoff contracts** (intermediate → derived): declarative,
  auditable, stakeholder-readable checks that run at delivery boundaries
- `OpenLineage` emits structured lineage events from both layers, carried forward as a
  provenance spine
- `Delta Lake` / `DuckDB` provides snapshot isolation + time travel as the reproducibility
  primitive for transportable datacuts

This pattern was built ad-hoc at BMS (2019-2021) using Airflow DAGs + S3 log uploads +
contractors parsing logs. The hypothesis is that it can now be expressed cleanly as a
first-class architecture.

## Synthetic data topology (BMS-modeled)

The synthetic data mimics a translational immunology study with:

- **FCS-equivalent files**: synthetic flow cytometry acquisition payloads with injected
  anomalies (duplicate payloads with different metadata, missing timepoints, partial
  transfers)
- **MSD/Luminex-equivalent exports**: synthetic Excel-style tabular cytokine data with
  plate layout issues and provenance pointers to raw "LXB" files
- **CRO transfer layer**: simulated custody transfer with manifest files (mix of S3-style
  and legacy FTP-style sources)
- **Derived endpoint tables**: aggregated per-patient/per-timepoint summary metrics
  (the actual analysis inputs)

Known failure modes to inject (drawn from real incidents):
1. Duplicate acquisition payload (different metadata, identical data — the original
   detection problem that motivated payload hashing)
2. Missing timepoint (patient X has day 8 and day 22, no day 15)
3. Partial transfer (manifest declares 12 files, 11 arrived)
4. Sample ID format inconsistency across CROs (CRO-A uses `PT007-D15`, CRO-B uses
   `007_15d`)
5. MSD plate layout mismatch (wrong analyte in well position)
6. Derived endpoint outside biological plausibility range

## Project structure (hatchling template conventions)

```
lineage-experiment/
    src/lineage_experiment/     # package source (src layout)
        synthetic/              # synthetic data generators
        ingestion/              # ingestion layer + pytest contracts
        derived/                # derived endpoint transforms
        lineage/                # OpenLineage emission helpers
    test/
        test_ingestion/         # pytest ingestion contract tests
        test_derived/           # GE-driven derived endpoint tests
        fixtures/               # shared pytest fixtures, synthetic data factories
    config/                     # dynaconf config (environments, paths)
    docs/
        PLANNING.md             # experiment phases and goals
        ARCHITECTURE.md         # layered testing topology spec
        DATA_MODEL.md           # synthetic data topology spec
    CLAUDE.md                   # this file
    pyproject.toml
```

## Build system and conventions

- **Build backend**: hatchling
- **Package manager**: uv (preferred) or pip with requirements-dev.txt
- **Test runner**: tox (py313, py312, lint, format envs) / pytest directly for dev
- **Linting**: ruff (line length 120, google docstring convention)
- **Config**: dynaconf
- **Python**: >= 3.12
- **License**: Apache-2.0

Install for development:
```bash
uv pip install -e ".[dev,testing]"
# or
pip install -r requirements-dev.txt
```

Run tests:
```bash
pytest -v test/
# or via tox
tox run -e py313
```

## Key dependencies (to be added to pyproject.toml)

```toml
dependencies = [
    "dynaconf",
    "deltalake",          # Delta Lake Python bindings (rust-backed)
    "duckdb",             # local query engine
    "great-expectations", # GX 1.0+ API
    "fcsparser",          # FCS file payload extraction
    "pandas",
    "pyarrow",
    "openlineage-python", # OpenLineage client
]

[dependency-groups]
testing = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "hypothesis",         # property-based testing for synthetic data generation
]
```

## How to work with Claude on this project

- **Always read this file at the start of a session** before writing any code
- This project uses **src layout** — imports are `from lineage_experiment.X import Y`
- pytest tests live in `test/` not `src/`
- Synthetic data generators should be **deterministic** (seeded) so tests are reproducible
- Prefer **explicit lineage emission** over implicit — if a function transforms data,
  it should emit an OpenLineage event
- GE suites live in `config/gx/` (dynaconf will handle paths)
- Do not abstract prematurely — duplicate code in experiments is fine, premature
  abstraction is not
- When in doubt about whether something is "working" vs "working correctly", write a
  pytest test that injects the known failure mode and confirm it catches it

## What success looks like per experiment phase

See `docs/PLANNING.md` for full phase breakdown. Short version:

- **Phase 1**: Synthetic data generation + pytest ingestion contracts catch all 6 known
  failure modes
- **Phase 2**: Delta Lake snapshot isolation gives reproducible datacuts (same version =
  same query result, always)
- **Phase 3**: GE handoff contracts on derived endpoints are stakeholder-readable and
  auditable
- **Phase 4**: OpenLineage spine connects ingestion events to derived endpoint versions —
  "which FCS file contributed to this endpoint value" is answerable from metadata alone
- **Phase 5**: DuckDB/DataFusion query layer makes the datacut portable — analyst on a
  laptop, no server required

## Documentation — story system

All feature work is tracked as stories in `doc/stories/` using a hybrid user story / project plan
format. Read the relevant story before starting any feature work.

### Story format

Each story opens with a user story and acceptance criteria, followed by a project plan with
architecture, file changes, env vars, and merge notes. When starting new feature work, create a
story in `doc/stories/` first (or `pending/` if a branch already exists). Title of the story is always in
MLA-style title case (so no capital "a", "the", etc.)

### Story lifecycle

- Planned, no branch yet → `doc/stories/<story-name>.md`
- Branch created, unmerged → move to `doc/stories/pending/<story-name>.md`
- Merged to main → move to `doc/stories/completed/<story-name>.md`

## Context for Claude

The author (Mike) has direct lived experience with the problem this project is
investigating. He built a version of this at Bristol Myers Squibb (2018-2021) using
Airflow, containerized DAGs, S3, pins (R), Great Expectations, and pytest — before Delta
Lake, OpenLineage, and DuckDB existed in usable form. The synthetic data is modeled on
real translational immunology workflows including flow cytometry (FCS files), cytokine
multiplex (Luminex/MSD), and CRO data custody transfer chains.

Do not suggest simplifying the problem domain — the complexity is intentional and
reflects the real failure modes the architecture needs to handle. Do suggest simplifying
the code when the experiments would be clearer with less abstraction.
