# Sabueso — Developer Guide

The developer guide is the repository's memory: what Sabueso is, how it is built, what
was decided and why, and what comes next. Start with `CHECKPOINT.md` and `ROADMAP.md`.
Contributors and agents also read `../AGENTS.md`.

To resume after a pause, read [CHECKPOINT.md, Resume here](CHECKPOINT.md#resume-here),
then [ROADMAP.md, Immediate resumption sequence](ROADMAP.md#immediate-resumption-sequence).
These separate published behavior, accumulated local work, latest qualification
and the next implementation/design steps. Detailed receipts remain linked; neither
a previous test count nor a diagnostic local wheel establishes a public release.

Every document is one of four kinds:
- **normative**: rules and contracts that code must follow;
- **living**: the current state, kept true;
- **design**: vision and architecture;
- **historical**: kept, not maintained.

## Where to start

| Document | Kind | What it holds |
|---|---|---|
| `CHECKPOINT.md` | living | The current state: release, schema, layout, quality baseline, open work |
| `ROADMAP.md` | living | Both routes, objective status, and the approved next roadmap after 0.13.0: user journeys, query/traceability guarantees, peptides and parallel consumer contracts |
| `DECISIONS.md` | living (log) | Every design decision, dated, with its reason |
| `RISKS_AND_OPEN_QUESTIONS.md` | living | Risks for the future, and decisions to re-evaluate |

Release preparation and receipts live in `../devtools/conda-build/`: the committed
plan, route checklist, `release_notes_0.13.0.md` and exact-artifact publication receipt (#121), plus the
immutable 0.12.0 notes/publication receipt (#110). Published state stays in `CHECKPOINT.md`; a preparation plan is
not a release receipt.

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
| `SOURCE_ACCESS.md` | normative | Source clients, `get_*` functions and required acquisition traceability |
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
| `SOURCE_COVERAGE.md` | living | Knowledge areas, the source rubric, and evaluations by wave (#83) |
| `SOURCE_ARCHITECTURE.md` | living | Declared enrichers, the runner and shared services for many sources (#86) |
| `STORAGE_LAYOUT.md` | living | Knowledge store, files, recommended project layout |
| `CACHE_POLICY.md` | living | What is stored and what is not, and open questions |
| `CARD_SIZE_RISKS.md` | living | Card growth, measurements, mitigations |
| `DOCS_GAPS.md` | living | What the user guide lacks |

## Working folders

- `pending_bugs/`, `pending_proposals/`: analyses of active issues, each tied to its
  issue.
  `pending_proposals/design_implementation_review.md` compares original design,
  scientific capabilities and current implementation, with concrete gaps and owning
  acceptance criteria (#112).
  `pending_proposals/independent_user_journeys.md` scopes the three standalone SDK
  journeys, the implemented protein comparison, molecule/target and bounded disease
  examples, exact disease membership support, conservative whole-context admission
  and remaining filtering by terms of use, clinical, query and observation gaps
  (#112, #29/#91/#71/#108). The source-state
  correction is implemented locally under versioned rules (#122); delivery is pending.
  `pending_proposals/ackredit_knowledge_pipeline_attribution.md` records the required
  pipeline attribution plan (#108, moli#36), its automatic composition and bounded
  acquisition adapters (including development ClinicalTrials.gov native references
  and explicit Europe PMC bibliography), and remaining coverage/publication gates.
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
