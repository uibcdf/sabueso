---
summary: Adopt the MOLI Ruff formatting baseline in Sabueso.
issue: uibcdf/sabueso#11
status: resolved
opened: 2026-09-23
closed: 2026-09-23
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

A local measurement with Ruff 0.16.5 on 2026-09-23 also found 42 `ruff check .` findings
(37 `I001`, 4 `F401`, 1 `E741`), 41 of them auto-fixable, so the Ruff job failed on both
gates.

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

Resolved on 2026-09-23 by uibcdf/sabueso#12, in two commits kept separate from any
scientific or API change:

- `style: apply the MOLI Ruff baseline mechanically` (`21b73a0`): `ruff format .` and
  `ruff check --fix .`. 52 files were reformatted, including Python code blocks in 11
  Markdown files. Imports were sorted, and four unused imports were removed
  (`typing.Iterable`, `typing.List`, `typing.Dict`, and `sys` in `docs/conf.py`).
- `fix(scope): resolve Ruff E741 in the SCOPe dump reader`: the only finding Ruff could
  not fix automatically. The dump lines are now passed directly instead of through a
  generator that used the name `l`.

Verification:

- All 57 modified Python modules are AST-equivalent to their previous versions, ignoring
  import order and the four removed imports.
- A snapshot of the outputs of all mappings and resolver-integrated cards is
  byte-identical before and after the migration.
- `ruff format --check .` reports 218 files already formatted, and `ruff check .` passes.
- The offline suite passes locally, 37 tests, on clean venvs with CPython 3.11.10,
  3.12.12, 3.13.14 and 3.14.7.
- Hosted CI run 35852905826 on the PR passed the Ruff job and the offline jobs on Python
  3.11 to 3.14 (37 passed, 12 deselected each), and the MOLI governance run passed.

No local Ruff exception was needed.
