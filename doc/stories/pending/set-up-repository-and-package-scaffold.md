# Set Up Repository and Package Scaffold

## User Story

As the experiment author, I want the repository to have a correct, standards-compliant
Python package scaffold so that I can begin implementing synthetic data generators and
ingestion contracts on a stable foundation without fighting tooling setup mid-experiment.

## Acceptance Criteria

- [ ] `pyproject.toml` uses `lineage-experiment` as the project name with hatchling as
  build backend and all core experiment dependencies declared
- [ ] Package source lives at `src/lineage_experiment/` (src layout, hatchling `sources = ["src"]`)
- [ ] Four subpackages exist as importable modules: `synthetic`, `ingestion`, `derived`, `lineage`
- [ ] pytest runs with `--import-mode=importlib`; no `__init__.py` required in test directories
- [ ] tox environments cover `py313`, `py312`, `lint`, `format`, `type_check` with correct
  coverage target (`lineage_experiment`)
- [ ] Planning docs (`PLANNING.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`) are in place and
  consistently use "milestone" (not "phase") throughout
- [ ] `CLAUDE.md` documents the story system and project conventions for future sessions

---

## Project Plan

### What was done

**Python version and build**
- `.python-version` set to Python 3.14 (pyenv)
- `pyproject.toml` renamed project from generic `app` to `lineage-experiment`, updated
  description, bumped `requires-python` to `>=3.14`
- Added all core dependencies: `deltalake`, `duckdb`, `great-expectations`, `fcsparser`,
  `pandas`, `pyarrow`, `openlineage-python`
- Added `hypothesis` to `[dependency-groups.testing]` for property-based test generation
- Fixed tox `--cov` target from `app` to `lineage_experiment`

**Package structure**
- Renamed `src/app/` → `src/lineage_experiment/`
- Updated `src/lineage_experiment/config.py` docstring (was "Pomo" boilerplate)
- Created four subpackage `__init__.py` stubs with intent-level docstrings:
  - `synthetic/` — deterministic seeded data generators
  - `ingestion/` — custody-transfer boundary checks + OpenLineage emission
  - `derived/` — aggregation pipeline + GE handoff contracts
  - `lineage/` — OpenLineage client helpers

**Test layout**
- Updated `test/test_config.py` import: `app.config` → `lineage_experiment.config`
- Created `test/test_ingestion/`, `test/test_derived/`, `test/fixtures/` directories
- No `__init__.py` in test directories — project uses `--import-mode=importlib`
- Added `addopts = ["--import-mode=importlib"]` to `[tool.pytest.ini_options]`

**Planning docs**
- Created `doc/PLANNING.md`, `doc/ARCHITECTURE.md`, `doc/DATA_MODEL.md`
- Global replace of "Phase" → "Milestone" across all docs and `CLAUDE.md`
- Added story system documentation section to `CLAUDE.md`

### File changes

| File | Change |
|------|--------|
| `.python-version` | Set to Python 3.14 |
| `pyproject.toml` | Project name, deps, pytest importlib, tox coverage target |
| `src/lineage_experiment/__init__.py` | Renamed from `src/app/` |
| `src/lineage_experiment/config.py` | Renamed + docstring update |
| `src/lineage_experiment/synthetic/__init__.py` | New |
| `src/lineage_experiment/ingestion/__init__.py` | New |
| `src/lineage_experiment/derived/__init__.py` | New |
| `src/lineage_experiment/lineage/__init__.py` | New |
| `test/test_config.py` | Import updated to `lineage_experiment.config` |
| `test/test_ingestion/` | New directory (no `__init__.py`) |
| `test/test_derived/` | New directory (no `__init__.py`) |
| `test/fixtures/` | New directory (no `__init__.py`) |
| `doc/PLANNING.md` | New |
| `doc/ARCHITECTURE.md` | New |
| `doc/DATA_MODEL.md` | New |
| `CLAUDE.md` | Phase → Milestone, story system section |

### Env vars

None introduced in this story. `ENV` in `config.py` defaults to `dev` via `os.getenv`.

### Merge notes

- Branch: `feature/1-setup-repo`
- No migrations, no schema changes, no external service dependencies
- After merge: `uv pip install -e ".[dev,testing]"` to pick up new dependencies
- `requirements-dev.txt` should be regenerated from `pyproject.toml` after merge if
  it is kept in sync manually
