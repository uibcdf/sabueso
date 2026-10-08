# Follow-up 35: final historical review and current HK2 test system

On **2026-10-08**, close the final **11 individual file reviews**, then inspect
**two cards, one ligand list and six historical notebooks**. The useful ready
runtime behavior in those files is already covered by current qualified routes.
Historical wrappers or schema placeholders need no further wholesale restoration.
Generic individual-review labels now fall **11 to 0**; this closes the historical
audit, not all future source capabilities or delivery work.

At the maintainer's direction, HK2 becomes a **current public test system** alongside
TcTIM/HsTIM. Rebuilding expected documents from qualified source responses is the
maintained route; the old exports are temporary local reference material.

## Remaining original files

| Original | Final disposition |
|---|---|
| `sabueso/__init__.py` | Current public SDK exports supersede legacy grouped constructors, query records and generic Evidence objects. |
| `sabueso/core/__init__.py` | Current quantity/relationship/derived-composition APIs supersede six generic prototype exports. |
| `sabueso/tools/db/go.py` | UniProt GO cross-reference support replaces ready protein annotation access; independent native ontology-term intake requires a correctly scoped subject, transport, release and rights. |
| `schemas/card_schema.yaml` | Conceptual field requirements reconciled with current schema and native-source acceptance; peptide/supplier/clinical/patent scopes retain owning work. |
| `schemas/card_schema_0.1.0.yaml` | Prototype shape and Evidence terminology superseded; published current schemas remain immutable, development schema is 0.3.13. |
| `sabueso/tools/protein.py` | Current resolver, bounded source routes, source acquisition and named knowledge views replace generic orchestration, maturity defaults and caller identity; remote calculations remain outside Sabueso. |
| `sabueso/tools/protein_sources.py` | Current native clients, retrieval archive and transport qualify scope and replay; first-page search, implicit gene/protein joins and generic payload permissions are not restored. |
| `tests/tools/test_online_protein_priority_sources.py` | Three historical nonempty/retired-route tests superseded by current offline native qualification and separate online-health scope; not executed. |
| `tests/tools/test_protein_annotation_sources_offline.py` | Fourteen synthetic tests reconciled with current source-specific access/support, partial-success/error, rights, quantities and identity guards; undeclared native scopes remain future requirements. |
| `tests/tools/test_protein_priority_sources_offline.py` | Four synthetic tests superseded by current native LIGYSIS/AlphaFill/gnomAD, source catalog and query-bound snapshot tests; no retired-source reactivation. |
| `tests/tools/test_protein_translational_sources_offline.py` | Three synthetic tests superseded by qualified variant/proteomic/drug/orphan/native-snapshot coverage and preserved future peptide/PTM/clinical requirements. |

The four historical test files contain **24 test functions** (3 online and 21
synthetic offline). Their requirements are reconciled, not executed under obsolete
APIs. Consent to a DoGSite job does not make calculation part of Sabueso's knowledge
role. Prototype `consulted`/`not_found` counts, first-page limits, unconditional
curated/experimental classes and cache timestamps cannot establish complete native
query coverage, experimental Evidence, protein identity or original retrieval time.

## Artifact findings and useful remaining material

- `PTGS2_human.card.json` actually declares **P52789/HK2**. Its 253 UniProt
  field/value occurrences equal those in the HK2 export; complete record identities
  and metadata are not identical. Preserve the mismatch in the audit; do not create
  a PTGS2 fixture or silently rename the scientific subject.
- `notebooks/HK2_human.card.json` contains **21,555 historical Evidence-shaped
  records** across 43 reported consulted sources. Its support pointers are internally
  complete, but a mapped historical export is not an original native response or a
  licensed fixture. Counts, coverage labels and predictions cannot be promoted into
  current SourceAssertions by changing vocabulary. Native scope requirements are
  already retained in follow-ups 32–34 and the provider reactivation matrix.
- The ligand list has **188 occurrences / 313 observations**. Every observation
  matches its parent-card value and original support record exactly. Standalone
  ligand cards have no card id or support store. Preserve each original occurrence
  and its parent support candidates in an inert query-hint manifest: **52 BindingDB
  plus SMILES, 62 ChEMBL, 62 PubChem and 12 CCD** identifier occurrences. No compound
  merge, binding classification or numeric measurement is admitted. Three historical
  measurement values are blank; none supplies a numeric value without a unit.
- Four notebook reports preserve legacy rendering/refresh examples; current snapshot
  regeneration replaces them. `Sandbox/test.ipynb` preserves exploratory resolver
  cases, already reconciled in follow-up 33. `Sandbox/test2.ipynb` is a four-cell
  molecule inspection with an indentation error, not an additional scientific
  workflow. Saved outputs remain historical, and no notebook code was executed.
- Of the three excluded automatic notebook checkpoints, one duplicates its notebook,
  one has the same rendered cell content with different JSON source representation,
  and one is empty. They add no scientific content. The excluded CLI session state
  remains outside scientific recovery.

## Current HK2 baseline

`tools/build_hk2_test_system.py` rebuilds HK2 with `sabueso.resolve` and the unchanged
qualified public UniProt fixture. It generates a current card, pinned receipt and
regenerable notebook; **239 SourceAssertions**, development schema **0.3.13**,
original acquisition **2026-09-23**. Generated artifacts are at
`recovered_work/current_HK2/`, outside published-schema frozen cards.

Five integrated regression cases check native subject/sequence/quantity support,
the two independent ATP-site groups, explicit unqueried source scope, exact
KnowledgeStore persistence, card/report rebuilding without acquisition and actual
CLI relative-path output from another directory.
Existing HK2 domain/residue/mutagenesis/mapping tests remain in place.

This first baseline covers **UniProt**, not the old multi-source export's 43 labels
or 188 candidate compounds. Extend it with qualified native RCSB/PDBe-KB/InterPro/
ChEMBL/other responses and their declared rights, identity, units, numbering,
completeness and revisions. [HK2_TEST_SYSTEM.md](../../HK2_TEST_SYSTEM.md) is the
maintained recipe and expansion boundary. No historical fixture promotion, new
provider, public API, packaging or schema change occurs.

## Stash-independent retention and closure

All **87 original exports** retain their original bytes/hash/length. The local
backup `recovered_work/local_work_2026-07_verified_originals.tar.gz` contains those
87 files plus the independent hash manifest, artifact audit, query hints and local
README. Every archive member was read back and checked against its original bytes.
The archive is a temporary local safeguard, not a maintained scientific baseline
or a remotely stored backup. Details are in `closure.json`.

The ignored `recovered_work/audit_2026-10-08/ligand_query_candidates.json` retains
unverified identifiers and old parent support pointers without admitting knowledge.
Future requirements remain in the tracked reports, current source registry,
[reactivation matrix](../../pending_proposals/historical_provider_reactivation.md)
and [owning issue update](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6062691987). The seven access-dependent providers remain
conditional, as requested; their future evaluation no longer requires the stash.

The historical scientific/file review is complete. After this review, the
maintainer explicitly authorized stash deletion on **2026-10-08**. The exact
reviewed stash was dropped after rechecking the archive and all 87 originals;
381 recovered working files, HEAD and index remained unchanged. The stash list
is empty. The temporary backup remains available. `closure.json` records the
completed deletion. Accumulated implementation is still local/uncommitted;
review, commit/delivery and exact-SHA CI remain separate from audit closure.

## Validation

Full offline code checkpoint: **5554 passed in 173.00 seconds**, with **10 expected
fixture warnings**, pytest-receptor (`--receptor=llm`), **12 workers**, Python
**3.14.7** and the existing editable `molsyssuite@uibcdf_3.14` environment.
Focused HK2 gate: **5 passed in 4.53 seconds**. Selected current schema/migration,
native snapshot, registry, saved-report, ligand-context and knowledge-baseline gate:
**260 passed in 9.67 seconds**. Each gate was run separately and its result read.

Ruff, source registry, current card shape, strict Sphinx, maintained links and
original/backup integrity are qualified in `validation.md` and the local receipts.
The existing public UniProt responses, all published schemas/frozen cards and
unpublished 0.3.13 shape remain unchanged. No new environment, staged changes,
commit or push during the code review. The later authorized stash deletion
is recorded above. No remote checkpoint was requested;
`gh-run-receptor` is therefore not applicable to this local checkpoint.


HK2 acceptance update: [issue #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6062813640).
