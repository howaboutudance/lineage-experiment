# Scoping Milestones + Milestone 1

## User Story

As the experiment author, I want to review and scope the experiment milestones into
actionable stories so that Milestone 1 work can begin with a clear plan, well-defined
acceptance criteria per story, and a shared milestone tracker that future sessions can
use to orient quickly.

## Acceptance Criteria

- [ ] `doc/stories/milestones.md` exists as a milestone tracker — status, description,
  and story links for all 5 milestones
- [ ] Milestone 1 is broken into individual stories in `doc/stories/`:
  - [ ] Synthetic data generators story (FCS, MSD, manifest generators)
  - [ ] Ingestion contracts story (all 6 failure modes)
- [ ] Each Milestone 1 story has a full user story, acceptance criteria, and project plan
- [ ] PLANNING.md milestones are reviewed for accuracy and adjusted if anything has
  shifted since initial drafting

---

## Project Plan

### What this story covers

This is a scoping and planning story — no production code is written. Output is:
1. `doc/stories/milestones.md` — a durable milestone tracker
2. Two Milestone 1 child stories in `doc/stories/`
3. A reviewed and confirmed PLANNING.md

### Milestone tracker (`doc/stories/milestones.md`)

A single file tracking all 5 milestones with status and story links. Format:

| Milestone | Description | Status | Stories |
|-----------|-------------|--------|---------|
| 1 | Synthetic data + pytest ingestion contracts | planned | links |
| 2 | Delta Lake snapshot isolation | planned | — |
| 3 | GE handoff contracts on derived endpoints | planned | — |
| 4 | OpenLineage spine | planned | — |
| 5 | Portable query layer (DuckDB / DataFusion) | planned | — |

### Milestone 1 story breakdown

**Story: Synthetic Data Generators**
- Deterministic (seeded) generators for FCS-equivalent payloads, MSD/Luminex-equivalent
  exports, and CRO transfer manifests
- Lives in `src/lineage_experiment/synthetic/`
- Key open question: does `fcsparser` data segment extraction suit payload hashing, or
  do we hash the raw numpy array directly?

**Story: Ingestion Contracts for All 6 Failure Modes**
- pytest contracts in `test/test_ingestion/` catching FM-1 through FM-6
- Depends on synthetic generators being available as pytest fixtures
- Key open question: does the fixture boundary fall at the file level or manifest level?

### File changes

| File | Change |
|------|--------|
| `doc/stories/milestones.md` | New — milestone tracker |
| `doc/stories/synthetic-data-generators.md` | New — Milestone 1 child story |
| `doc/stories/ingestion-contracts.md` | New — Milestone 1 child story |
| `doc/PLANNING.md` | Review pass — adjust if needed |

### Env vars

None.

### Merge notes

- No branch needed — planning story, merged as part of repo setup or standalone commit
- Move this file to `doc/stories/completed/` once milestones.md and both child stories
  are written and reviewed
