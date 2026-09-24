# Sabueso — Diagnostics (SMonitor)

Sabueso reports through SMonitor, the UIBCDF diagnostics layer, as required by MOLI's
support-library policy (uibcdf/sabueso#31).

## Principle: outcomes are data first

Every source outcome is recorded on the result: `card.quality["enrichments"]`,
`deck.meta["sources"]` and `deck.meta["unanchored"]`. Diagnostics are **derived from
those same records** (`sabueso/_private/smonitor/outcomes.py`), so what a user is told
and what a card stores cannot diverge. SMonitor is the user-facing channel; it never
replaces the recorded outcome.

- **Reported:** a source that could not be consulted (`status: "error"`), a truncated
  result (`truncated: true`), and records left out of a deck because they have no
  standard InChIKey.
- **Not reported:** `not_found`. "The source holds no record" is an answer, not a
  failure, and it stays data only.

## Codes

| Code | Class | When |
|---|---|---|
| `SABUESO-W-ENRICH-001` | `EnrichmentFailedWarning` | a source failed; the result was built without it |
| `SABUESO-W-ENRICH-002` | `EnrichmentTruncatedWarning` | a source returned fewer records than it holds |
| `SABUESO-W-IDENTITY-001` | `UnanchoredRecordsWarning` | records without a standard InChIKey were left out of a deck |
| `SABUESO-E-GENERIC-001` | `SabuesoError` | base error |
| `SABUESO-E-RESOLVE-001` | `ResolverError` | |
| `SABUESO-E-SCHEMA-001` | `SchemaError` | |
| `SABUESO-E-STORAGE-001` | `StorageError` | |
| `SABUESO-E-SOURCE-001` | `ConnectorError` | a source could not answer |
| `SABUESO-E-SOURCE-002` | `RecordNotFoundError` | a source answered that it holds no such record |

The warnings are catalog warnings: they emit a structured SMonitor event and raise an
ordinary Python warning, so `warnings.filterwarnings` and `pytest.warns` work as usual.
Tests that simulate a source failure assert the warning (`pytest.warns`).

The exceptions keep the message written where they are raised (template `{message}`)
and gain `exc.code` and `exc.extra`. Catching code should read `exc.code`, not parse the
message.

## Layout

- `sabueso/_smonitor.py`: configuration and profiles. It must stay inside the package,
  so that it is installed with it.
- `sabueso/_private/smonitor/`: `catalog.py` (the single source of message templates),
  `warnings.py`, `emitter.py`, `outcomes.py` and `meta.py`.
- `sabueso/__init__.py` calls `ensure_configured(PACKAGE_ROOT)` on import.
- `@signal` decorates `resolve_protein_card`, `resolve_molecule_card` and `ligand_deck`.
- `tests/core/test_smonitor_integration_offline.py` holds the five mandatory checks of
  the SMonitor guide. The first one runs `smonitor --validate-config` against the
  package.

## Known issues

- With pytest-receptor 1.1.0, every receptor run ends with
  `ResourceWarning: unclosed file ... '/dev/null'`. The receptor never closes a discard
  stream, and SMonitor's warning capture makes the normally hidden warning visible. It is
  cosmetic: exit status and verdict are unaffected. Tracked upstream in
  uibcdf/pytest-receptor#4.
- A development environment with an older SMonitor (before 0.16.0) is not supported;
  `devtools/conda-envs/development_env.yaml` requires `>=0.16.0`.
