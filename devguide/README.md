# Sabueso — Developer Guide

The developer guide is the repository's memory: what Sabueso is, how it is built, what
was decided and why, and what comes next. Start with `CHECKPOINT.md` and `ROADMAP.md`.
Contributors and agents also read `../AGENTS.md`.

Every document is one of four kinds:
- **normative**: rules and contracts that code must follow;
- **living**: the current state, kept true;
- **design**: vision and architecture;
- **historical**: kept, not maintained.

## Where to start

| Document | Kind | What it holds |
|---|---|---|
| `CHECKPOINT.md` | living | The current state: release, schema, layout, quality baseline, open work |
| `ROADMAP.md` | living | Both routes (foundational plan and pilot-driven), and the status of every objective |
| `DECISIONS.md` | living (log) | Every design decision, dated, with its reason |
| `RISKS_AND_OPEN_QUESTIONS.md` | living | Risks for the future, and decisions to re-evaluate |

## Design

| Document | Kind | What it holds |
|---|---|---|
| `VISION.md` | design | Definition, mission, scope, platform context, non-goals |
| `ARCHITECTURE.md` | design | Layers, core objects, principles, what is planned but not built |
| `DATA_FLOW.md` | design | One resolution, end to end, and its invariants |
| `USE_CASES.md` | design | Use cases of both routes (status in `ROADMAP.md`) |
| `SCIENTIFIC_POTENTIAL.md` | design | Long-term scientific direction (non-binding) |
| `GLOSSARY.md` | design | Terms |

## Contracts and conventions

| Document | Kind | What it holds |
|---|---|---|
| `SCHEMA.md` | normative | Card schema, SourceAssertion and relationship contracts, versioning policy |
| `FIELD_PATHS.md` | normative | Canonical field paths (checked against the schema) |
| `PUBLIC_API.md` | normative | The public surface |
| `API_CONVENTIONS.md` | normative | Naming, inputs, view conventions |
| `INTERFACES_MINIMAL.md` | normative | Core interfaces: Card, Deck, stores, resolvers |
| `RESOLVER.md` | normative | FieldResolver contract and selection rules |
| `SELECTION_RULES_EXAMPLES.md` | normative | Selection rules, field by field |
| `SOURCE_ACCESS.md` | normative | Source clients and `get_*` functions |
| `ARGUMENT_CONTRACTS.md` | normative | ArgDigest: one digester per argument |
| `DIAGNOSTICS.md` | normative | SMonitor codes and outcomes |
| `LICENSING_AND_COMPLIANCE.md` | normative | Source licences and obligations |
| `TESTS.md` | normative | Test kinds, fixtures, local gates |
| `LOCATION_EXAMPLES.md`, `UNIPROT_ENUMS.md` | reference | Verified examples and source enumerations |

## Sources, storage and size

| Document | Kind | What it holds |
|---|---|---|
| `sources/registry.yaml` | living (source of truth) | Every resource: in use, evaluating, queued, deferred, rejected, retired, out of scope |
| `sources/README.md` | normative | How sources are proposed, triaged and decided |
| `DATA_SOURCES_STATUS.md` | living | Technical detail of each source in use |
| `STORAGE_LAYOUT.md` | living | Knowledge store, files, recommended project layout |
| `CACHE_POLICY.md` | living | What is stored and what is not, and open questions |
| `CARD_SIZE_RISKS.md` | living | Card growth, measurements, mitigations |
| `DOCS_GAPS.md` | living | What the user guide lacks |

## Working folders

- `pending_bugs/`, `pending_proposals/`: analyses of active issues, each tied to its
  issue.
- `templates/report.md`: the report template (MOLI reporting protocol).
- `archive/`: resolved reports and superseded documents, indexed in
  `archive/README.md`. The original plans are there, and `ROADMAP.md` still tracks them.

## Keeping the guide true

- A change that makes a line false updates it in the same commit. This applies to
  `CHECKPOINT.md`, `PUBLIC_API.md`, `FIELD_PATHS.md`, `SCHEMA.md`, `TESTS.md` and the
  registry.
- A decision goes to `DECISIONS.md`. A possible future problem goes to
  `RISKS_AND_OPEN_QUESTIONS.md`, with an issue when it needs a decision later.
- Each release reviews `ROADMAP.md` against both routes, and updates `CHECKPOINT.md`.
- A superseded document is archived with a note that says what replaced it, never
  deleted.
- Public documents never carry confidential pilot content; pilot needs are phrased
  generically.
