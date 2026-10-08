# Follow-up 33: protein query and retired constructor review

Individually reconcile **five preserved originals** on **2026-10-08**. Current
native resolver, exact-sequence candidate and explicit isoform workflows replace
their useful ready implementation. Retain missing convenience/query requirements
with scientific acceptance criteria independently of the stash. No old resolver
ranking, generic Evidence layer, blanket coverage claim or retired source is restored.

## Five-file disposition

| Original | Current replacement / disposition | Residual value |
|---|---|---|
| `sabueso/resolver/__init__.py` | Current exports expose `EntityQuery`, `EntityResolution`, `EntityResolver` and field selection/source clients. Legacy `ProteinQuery`, `ProteinCandidate`, `TaxonRef` and `resolve_protein` wrappers are obsolete API, not additional knowledge. | A future convenience facade must preserve current named decisions, source assertions, detached acquisition and alternatives; the old class names are not a compatibility requirement. |
| `sabueso/resolver/protein.py` | Current resolution handles source-stated primary/merged/demerged/isoform accessions, explicit protein-name plus organism queries and PDB structure context. Separate `exact_sequence_candidates@1` verifies archive and current sequences without identity resolution; explicit native isoform access remains independent. | Native taxonomy/common-name normalization, gene/entry-name queries and explicit PDB chain/polymer selection remain bounded future contracts below. Automatic score-based uniqueness, silent source-error exclusion, concatenation of several FASTA records and sequence-based PDB identity fallback are not retained. |
| `tests/resolver/test_protein_resolution_offline.py` | Current native resolver/identity/organism/acquisition/sequence/isoform tests cover current contracts more thoroughly. The old fake mouse record rewrites a human HK2 fixture; it does not qualify native mouse data, taxonomy or the current query wire response. | Preserve ambiguous taxa/identities, string/numeric organism input, candidate choice, exact sequence checks and source chain selection as acceptance scenarios with real native source support; do not restore old ranking or synthetic source qualification. |
| `sabueso/tools/db/uniprot.py` | Current source record access, offline card creation, acquisition receipts, audit revisions, source knowledge state and native isoform readers replace legacy direct fetch and prototype metadata. Current cards use actual schema versions and support. | The prototype's `consulted` coverage and current-date defaults do not establish successful access, complete coverage or original retrieval time. Unqueried layers remain distinct through maintained query/knowledge state; no new schema or top-level metadata is needed from this helper. |
| `sabueso/tools/db/scope.py` | SCOPe remains retired under #21. The old SUNID dump fetch/per-database protein-card helper does not establish source-stated protein identity or native domain coordinates. No current client is claimed for this retired route. | If a concrete need reopens SCOPe, require a complete qualified native classification/hierarchy/description and domain/chain/coordinate contract with exact release, original retrieval/hash/rights and explicit protein correspondence; silently skipping malformed lines and lossy UTF-8 are not acceptable native validation. |

## Useful future query requirements, independent of old code

1. **Taxonomy names and aliases:** a native resolver must retain the original user
   value, exact scientific/common/alias occurrence, source taxon identifier, source
   revision and support. Several taxa sharing a name remain ambiguous; complete
   requested/returned-query scope is explicit. Invalid taxon ids fail before access.
   A FASTA header, arbitrary name or candidate's first taxon never resolves taxonomy.
   Current protein name queries support taxonomy ids/scientific names, not a separately
   qualified taxonomy alias lookup.
2. **Gene and entry-name lookup:** distinguish explicit protein-name, gene-symbol,
   stable locus, transcript and UniProt entry-name inputs. Require actual native
   query/response/page scope, gene/taxon/revision and independently source-stated
   gene-product or identifier correspondence. A gene symbol/search hit is a candidate,
   not protein identity; products/paralogues/isoforms remain separate. Current name
   searches use `protein_name`, not the legacy `gene_exact` union. Source-stated
   accession transitions continue through the existing resolver. Any selection
   preserves alternatives and records a named/versioned preference or explicit
   caller choice; the old unnamed 100/50/40 score is not restored.
3. **PDB chain and polymer selectors:** preserve PDB entry/model/polymer entity,
   author versus label chain namespaces and source revisions/construct scope.
   Fragments, chimeras, repeated copies and several UniProt references remain explicit.
   An equal chain label/sequence or numbering is not a correspondence; source mapping
   supplies support. No mapping, unqueried mapping and failed access remain distinct.
   Sequence lookup may offer separate candidates but cannot create a missing identity
   link. Current PDB resolution returns a structure with its related polymer/protein
   declarations; it does not implement the old protein-only chain selector facade.
4. **Retired structural classification:** reopening SCOPe requires a demonstrable
   use beyond existing UniProt/InterPro/CATH/ECOD context and an explicit source
   adoption decision. Distinguish SUNID/SID/classification hierarchy, PDB domain/chain,
   insertion/discontinuous numbering and full-chain correspondence. A description
   dump row alone neither locates a domain nor identifies a current protein.
   Original native validation, permissions and online/fixture/supplied-file parity
   remain prerequisites; no environment override supplies scientific qualification.

Public implementation acceptance is recorded in
[issue #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6061946457),
with native-source scope under #83. The existing SCOPe retirement remains under #21.
These future requirements do not need an obsolete package tree to be revisited.

## Qualification

Selected resolver/identity/organism/acquisition/sequence/isoform gates:
**171 passed in 3.99 seconds**, pytest-receptor (`--receptor=llm`) with **12 workers**,
Python **3.14.7** in the existing editable `molsyssuite@uibcdf_3.14` environment.
This slice changes documentation and review dispositions only; it adds no executable
code, fixture, provider grant, card field, schema or packaging change. The full code
checkpoint remains follow-up 32's **5549 passed in 176.40 seconds**; no new full run
is claimed or required for this metadata review.

Outside-checkout replay verifies editable metadata/imports, seven resolution
records with exact detached acquisition traces, **18 preference alternatives /
19 unpreferred candidates**, two demerged candidates, four related protein entities
in the native 1KLG complex, three distinct exact-sequence candidates and three
explicit native isoforms (lengths **249 / 286 / 167**). Scientific documents,
assertions, trace and document digests survive exact JSON round trips. Sequence
lookup remains partial in the checked native fixture scope, without selection or
identity resolution. **Zero source requests** occur. The replay script initially
passed a dictionary to the string-only snapshot digest helper; fixing the external
script to hash canonical JSON requires no repository code change.
Receipt: `/tmp/sabueso-followup33-replay.json`; artifacts:
`/tmp/sabueso-followup33-replay`.

Registry, strict Sphinx HTML at `/tmp/sabueso-followup33-docs-build` and diff gates
pass. Original integrity verifies all **87 original byte lengths/SHA-256 hashes**,
91 accounted paths, unchanged stash, empty index, all published schemas/frozen
cards, published 0.3.12 shape and unchanged native UniProt/scientific fixtures.
Unpublished 0.3.13 remains unchanged by this slice. Receipts:
`/tmp/sabueso-followup33-integrity.json` and `/tmp/sabueso-followup33-gates.json`.
No remote code checkpoint or `gh-run-receptor` inspection occurs.

## Remaining audit

Generic individual file-review labels fall **21 to 16**. This is a count of original
files awaiting reconciliation, not sixteen ready features/providers. Remaining
core/schema entry points, knowledge/other grouped mappers, large protein/source
wrappers and their tests need review. Historical HK2 cards, ligand lists and
exploratory notebooks remain scientific artifacts, not current qualified knowledge.
Stash and all 87 exact exports remain intact. No stash deletion, staging, commit,
push, separate environment or additional source activation occurs. Deletion is not
yet recommended.

### Remaining individual file queue

- `sabueso/__init__.py`
- `sabueso/core/__init__.py`
- `sabueso/tools/db/go.py`
- `schemas/card_schema.yaml`
- `schemas/card_schema_0.1.0.yaml`
- `sabueso/mappings/knowledge.py`
- `sabueso/mappings/protein_priority_sources.py`
- `sabueso/mappings/protein_structural_context.py`
- `sabueso/mappings/protein_translational_sources.py`
- `sabueso/tools/protein.py`
- `sabueso/tools/protein_sources.py`
- `tests/tools/test_knowledge_enrichment_offline.py`
- `tests/tools/test_online_protein_priority_sources.py`
- `tests/tools/test_protein_annotation_sources_offline.py`
- `tests/tools/test_protein_priority_sources_offline.py`
- `tests/tools/test_protein_translational_sources_offline.py`
