---
summary: Adopt the MOLI Ruff formatting baseline in Sabueso.
issue: uibcdf/sabueso#11
status: active
opened: 2026-09-23
closed:
verification: measured
area: [engineering, quality]
blocked_by: []
supersedes: []
---

# Adopt MOLI Ruff formatting baseline

## What

Sabueso now carries the MOLI `python-package` capability and has adopted the shared Ruff/pytest engineering policy.

The new formatting gate exposes pre-existing formatting debt.

## How / evidence

The GitHub Actions Ruff job reports:

- `ruff format --check .` fails;
- 52 files would be reformatted;
- 165 files are already formatted;
- the offline test jobs pass on Python 3.11, 3.12, 3.13, and 3.14.

The local MOLI governance-surface gate was separately repaired after discovering an incorrect repository-root calculation.

## Why

A common formatter/linter baseline prevents repository-specific style drift and makes future MOLI components easier for humans and agents to maintain consistently.

The migration should remain mechanical and must not be mixed with scientific/API changes.

## Alternatives

- Disable the formatter gate: rejected because it would claim adoption without enforcement.
- Exclude legacy source/tests broadly: rejected because it would preserve avoidable debt.
- Format the repository mechanically, review, then rerun tests: selected.

## Acceptance criteria

- `ruff format --check .` passes.
- `ruff check .` passes or any genuine lint findings are separately resolved/tracked.
- Offline tests pass on Python 3.11–3.14.
- No intentional scientific/API behavior changes are introduced by the formatting migration.

## Resolution

Pending.
