# MOLI component coordination

This repository is directly governed by the MOLI platform for shared cross-component contracts.

Before cross-component or architectural work, read `MOLI_GUIDE.md`. Its canonical source is `uibcdf/moli/MOLI_GUIDE.md`; do not intentionally diverge the local copy.

This repository remains authoritative for its own implementation, tests, local API, scientific behavior, releases, and component-specific development decisions.

Use `uibcdf/moli` when a change affects a shared MOLI contract, terminology, architecture boundary, or coordination policy. Report provider-specific limitations to the provider repository and cross-link consumer work.

Do not expose confidential vertical-pilot content in public issues or documentation.

# Working in Sabueso

Sabueso is the Knowledge component of MOLI's Scientific Context. **Sabueso knows; it does
not discover.** Start with `devguide/README.md`, then `devguide/CHECKPOINT.md` and
`devguide/ROADMAP.md`.

## Language

Everything written into the repository is in English: code, comments, docstrings,
commit messages, issues, pull requests, release notes and documentation.

## Knowledge principles (see `devguide/ARCHITECTURE.md`)

- `SourceAssertion ≠ Evidence ≠ Provenance`. Sabueso records what sources assert; it
  never creates Evidence (Nextia's) and never imports project conclusions as knowledge.
- Every value is linked to the SourceAssertions that support it. Selection never
  discards them. Conflicts and ambiguity are reported, never resolved silently.
- Derived knowledge (a class, group, state or finding) carries a named, versioned rule
  (`name@N`) and is never stored as a SourceAssertion.
- Identity is never merged by similarity: not by sequence, not by a shared name, not by
  an equal residue number. Two entries are one entity only when a source states it.
  Every identity finding states its basis.
- Absence is not evidence. Tell apart what a source does not state, what was not asked,
  and what failed.
- Physical quantities are PyUnitWizard quantities, stored as `{value, unit}`. A unit
  never lives in a field name, and units are never lost across MOLI boundaries.

## Code conventions

- The UIBCDF tools:
  - public arguments are checked through ArgDigest, one digester per argument name, in
    `sabueso/_private/argdigest/argument/` (`devguide/ARGUMENT_CONTRACTS.md`);
  - diagnostics go through SMonitor (`devguide/DIAGNOSTICS.md`);
  - optional dependencies go through DepDigest.
- A new source follows `devguide/SOURCE_ACCESS.md`:
  - a client with online and fixture implementations;
  - public `get_*` functions;
  - a mapping in `sabueso/mappings/`;
  - an `in_use` entry in `devguide/sources/registry.yaml` (then
    `python tools/source_registry.py --write`).
- Python 3.11–3.14 are supported.
- Report bugs of UIBCDF tools, such as ArgDigest, PyUnitWizard, SMonitor, DepDigest or
  the receptors, upstream in their repositories, and cross-link them.

## Card schema

- Card schema changes follow the versioning policy in `devguide/SCHEMA.md`:
  - an additive change goes to the unpublished version;
  - a published version (it has a frozen card in `temp_data/frozen_cards/`) is never
    changed;
  - every change is described in the schema file, and listed in
    `sabueso/core/migration.py` (`SCHEMA_CHANGES`).
- After an intended change, record the shape (`python tools/card_shape.py --write`), and
  update `devguide/FIELD_PATHS.md` and `devguide/SCHEMA.md`.

## Tests and fixtures

- Run pytest through the receptor, as `MOLI_GUIDE.md` asks:
  `python -m pytest -m "not online" --receptor=llm`.
- Fixtures in `temp_data/` are frozen **public** responses, each declared in
  `temp_data/NOTICE.md` with its source, date and licence. No private or pilot data, ever.
  TcTIM and HsTIM may be used as public test systems.
- Local gates before every commit are listed in `devguide/TESTS.md`.
  - Run each gate on its own and read its result.
  - Never pipe a gate through `tail` or `grep`, and never chain a commit after a command
    whose exit code does not reflect the gate.

## Commits, CI and releases

- Maintainers commit directly to `main` once the local gates pass, then verify CI by the
  commit SHA.
- Releases follow the staged route in `devtools/conda-build/README.md`:
  - the candidate's CI, a staging build, and the installed-package gates on Linux,
    macOS and Windows;
  - then the GitHub release, promotion to the public channel, a clean public install,
    and the Zenodo archive.
- Never document an installation route before a clean install from the public channel
  has been verified.
- Releases are few and substantial. Propose one for a substantial set of changes, for an
  integrity fix that affects users of a published version, or when the maintainers ask.

## Recording work

- A decision goes to `devguide/DECISIONS.md`, and a possible future problem to
  `devguide/RISKS_AND_OPEN_QUESTIONS.md`.
- A decision to re-evaluate later gets a GitHub issue.
- A change that makes a devguide line false updates it in the same commit
  (`devguide/README.md`, "Keeping the guide true").
- Work is planned along two integrated routes, the foundational plan and the
  pilot-driven route (`devguide/ROADMAP.md`). Neither replaces the other.
- Vertical pilots are private:
  - read them only;
  - phrase their needs generically in public issues, commits and docs;
  - never copy their hypotheses, strategies, campaigns or candidate regions.
