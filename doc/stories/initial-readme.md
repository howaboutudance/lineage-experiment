# Write an Initial README

## User Story

As a developer encountering this repository for the first time, I want a README that
explains what the experiment is and how to get a local development environment running
so that I can understand the purpose of the project and start working without hunting
through multiple docs files.

## Acceptance Criteria

- [ ] `README.md` exists at the repository root
- [ ] Project purpose is explained in plain language — what the experiment is testing,
  why it exists, and what "success" looks like (reference to PLANNING.md for detail)
- [ ] Local development setup is covered end-to-end:
  - [ ] Prerequisites (Python 3.14, pyenv, uv)
  - [ ] Clone and install steps (`uv pip install -e ".[dev,testing]"`)
  - [ ] How to run the test suite (`pytest -v test/` and `tox`)
  - [ ] How to run linting and formatting (`tox -e lint`, `tox -e format`)
- [ ] Project structure section gives a one-line description of each top-level directory
- [ ] Links to `doc/PLANNING.md`, `doc/ARCHITECTURE.md`, and `doc/DATA_MODEL.md` for
  readers who want to go deeper
- [ ] No installation of real biomedical data required — README makes clear everything
  runs on synthetic data generated at test time

## Key Questions

- Should the README mention the BMS origin story or keep that detail in CLAUDE.md /
  PLANNING.md? Lean toward a one-sentence reference with a link to PLANNING.md.
- Does the setup section need a `config/` bootstrapping step (default.yaml, dev.yaml),
  or does dynaconf handle missing config files gracefully enough to skip that for now?

---

## Project Plan

### File changes

| File | Change |
|------|--------|
| `README.md` | New — project overview + local dev setup |

### Sections

1. **What this is** — one paragraph on the experiment hypothesis, BMS origin in one
   sentence, pointer to PLANNING.md
2. **Project structure** — annotated directory tree (top-level only)
3. **Prerequisites** — Python 3.14 via pyenv, uv
4. **Install** — clone, `uv pip install -e ".[dev,testing]"`
5. **Run tests** — `pytest -v test/`, tox commands
6. **Docs** — links to PLANNING.md, ARCHITECTURE.md, DATA_MODEL.md

### Env vars

None introduced. Note in README that `ENV` defaults to `dev` if unset.

### Merge notes

- No code dependencies — can be written and merged independently of other Milestone 1 stories
- Keep it honest: if setup has rough edges at merge time, document them rather than
  papering over them
