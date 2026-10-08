# Follow-up 30: source configuration, transport and persistence review

Review **two blocks of five original files** on **2026-10-08**. Their useful
implemented behavior has current equivalents or earlier qualified recovery.
No additional runtime code is copied from this slice. Close these ten individual
reviews and retain explicit acceptance for future unified source configuration.
An obsolete constructor, Evidence store or indefinite raw cache is not reintroduced.

## Block A: card entry points and source configuration

| Original file | Current equivalent and reviewed disposition |
|---|---|
| `sabueso/tools/card/__init__.py` | Current public exports already include notebook and JSON/SQLite card storage. No missing export; original ordering has no scientific/API effect. |
| `sabueso/tools/source_options.py` | Original-file/gzip/byte-hash/format requirements are recovered in `load_source_snapshot`, explicit native `Snapshot*Client` adapters and `BoundSourceSnapshot` (follow-ups 22/26). Current loaders validate before decoding, reject malformed native documents and keep declared retrieval separate from local reading. Generic payload/client/snapshot routing remains a future input-contract requirement below, rather than a ready source integration. |
| `tests/tools/test_protein_card_multisource_offline.py` | Current `resolve_protein_card`, `EntityResolver`, enrichment runner and ambiguity decks replace the old shared client/constructor/Evidence expectations. Independent source support, partial failure and ambiguous identity are already regression-tested. Native InterPro residue access is its current bounded scope; the test's fabricated InterPro domain bundle is not native provider qualification. |
| `tests/tools/test_protein_source_catalog_offline.py` | The registry-generated detached catalog and versioned `resolve(profile=...)` options cover source metadata, separate adoption states, valid profiles, copies and recorded overrides. Do not recover unjustified `production_ready`/`verified`/`mapped` labels or activate an entire historical comprehensive profile. Registry adoption does not establish current health or scientific completeness. |
| `tests/tools/test_protein_source_http_offline.py` | Current `_http`, `Pace`/`gather` and explicit RetrievalArchive replace the old transport. Bounded transient retries, Retry-After, observable retry summaries, connector-visible nonretryable errors, paced requests and explicit archive freshness/replay already have tests. The old indefinite per-client cache lacks the current retention/freshness/source context; no hidden default cache or old timeout policy is restored. |

The public resolution dispatcher refuses unknown/foreign options, applies named
versioned profiles and records explicit overrides. Per-source native readers still
own format, identity, units, revision, terms and coordinate scope. Reading registry
metadata neither queries a provider nor enriches a card. The supplied-file reader
records caller declarations as declarations; a correct byte hash is not scientific
qualification or permission to admit an arbitrary payload into a card.

### Future unified source configuration, retained without the stash

This requirement is owned by [#112](https://github.com/uibcdf/sabueso/issues/112),
with supplied-file access under [#131](https://github.com/uibcdf/sabueso/issues/131)
and source constraints under [#83](https://github.com/uibcdf/sabueso/issues/83).
The remaining requirement is convenience at a public input boundary, not a missing
native loader or an authorized automatic adoption of the whole historical catalog.

1. Specify an accepted public configuration contract and one ArgDigest digester per
   public argument. Reject unknown source/options, conflicting client/payload/file
   choices, duplicate normalized names and unsupported formats before any I/O.
2. Dispatch only through declared supported source adapters. A raw supplied payload
   needs that source's native validator and exact query/record identity contract,
   just as an original file does. Do not dynamically select old mappers or admit
   already-derived card fields/Evidence-shaped objects as original source assertions.
3. Preserve exact original bytes/hash when available, original retrieval separately
   from reading, unknown revisions/units, source terms and actual failure/absence/
   unsupported/unqueried outcomes. Caller licences/releases cannot overwrite source
   grants or manufacture scientific revisions.
4. Exercise online/fixture/supplied-file equivalence for each supported route with
   no optional-source I/O until requested. Bind chemical structures, protein/source
   sequences and numbering explicitly before card intake or positional placement.
5. Keep registry category groups distinct from named, versioned execution profiles.
   Profile expansion, explicit overrides, terms filtering and outcomes need stored
   traces. Status/maturity convenience filters must not pretend that adoption is a
   live access, native-format or scientific validation receipt.
6. Use the explicit retrieval archive for response reuse/replay under a declared
   freshness and retention policy. Preserve original HTTP/source/timing/retry context
   and sanitize sensitive query/credential fields in diagnostics. Do not recover the
   prototype's implicit indefinite raw cache or unqualified global host pacing.

These acceptance conditions replace the incomplete old generic validation helper;
the helper itself is not needed to implement or re-evaluate this future feature.

## Block B: decks, assertions, selection and persistence

| Original file | Current equivalent and reviewed disposition |
|---|---|
| `sabueso/core/deck.py` | Current decks implement add/extend/filter/sort/map/compare/summarize and JSONL/SQLite hydration, with membership basis, exclusions, operation traces and exact snapshots. Sorting unwraps resolved values and places missing values last. Persisted metadata and duplicate occurrences are already supported; no old minimal container needs restoration. |
| `sabueso/core/evidence_store.py` | SourceAssertionStore, source support and immutable card/KnowledgeStore snapshots replace the old Evidence registry. Deterministic IDs and field reads already exist. The old store overwrites equal IDs and makes no independent revision guarantee; it is not a version-preservation feature to recover. Historical Evidence terms/classes never enter the current scientific schema. |
| `sabueso/core/errors.py` | Current SMonitor catalog errors and resolver/source outcomes replace old raw exception aliases. Source absence, access failure, unavailable input/key and unsupported/ambiguous resolution remain distinct. Observed acquisition routes carry request/retry context; an old `.attempts` attribute is not restored as a universal observation guarantee. |
| `sabueso/resolver/field_resolver.py` | Current field resolver already has priority/recency/frequency/tolerant grouping plus scientific precision, comparable partitions, original assertion support and explicit alternatives/conflicts. SourceAssertions stay independent of selected values. Generic value normalization is never chemical/protein/sequence identity. |
| `tests/core/test_storage_offline.py` | Current storage regressions replace Evidence/raw-payload expectations with verified cards/decks. Expanded membership/meta/sealing/KnowledgeStore tests preserve pinned historical states, independent source retrieval dates, repeated members and source support through JSON/JSONL/SQLite. No old test copy or persistence implementation adds useful behavior. |

The old JSONL format has no deck header and its reader does not preserve metadata.
Current readers keep a header where present and still accept current-format sealed
cards in headerless decks with empty metadata. That compatibility does not admit
an arbitrary extended historical card or make obsolete Evidence fields valid.
KnowledgeStore's separate immutable snapshots preserve changed retrieval contexts
across saved revisions; assertion IDs alone are not exact historical state pins.
No in-card multi-revision support claim is added by this review.

## Qualification

Source/configuration/transport/resolution gate: **209 passed in 4.89 seconds**.
Deck/assertion/selection/storage gate: **64 passed in 9.28 seconds**. Each runs
through pytest-receptor with **12 workers** in the existing editable Python
**3.14.7** environment. The test files in the two gates are distinct; 273 selected
cases pass in total. No new regression or runtime implementation is introduced.

Outside-checkout replay confirms editable import/metadata and three native fixture
source groups (UniProt, RCSB PDB, InterPro): **203 SourceAssertions** retain exact
scientific support through card JSON/SQLite and KnowledgeStore, deck JSONL/SQLite,
repeated card occurrences, exact snapshots and metadata. Two native demerged
identity candidates survive an ambiguity-deck round trip. A detached registry
catalog cannot activate sources or affect the next read. Transport is forbidden;
**zero source requests** occur. `/tmp/sabueso-followup30-replay.json` and artifacts
under `/tmp/sabueso-followup30-replay`.

Ruff lint/format (**937 files**), generated registry, schema alignment, strict Sphinx
HTML at `/tmp/sabueso-followup30-docs-build` and diff pass. Integrity confirms all
87 original lengths/SHA-256 hashes, 91 accounted paths, the unchanged stash, empty
index, published frozen card and previous scientific fixtures. Receipts:
`/tmp/sabueso-followup30-integrity.json` and `/tmp/sabueso-followup30-gates.json`.
The public input/profile/persistence acceptance is recorded in
[issue #112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6060762515).


## Remaining broader recovery

These ten original files now have concrete final review dispositions in
`inventory.json`; there is no additional ready runtime change identified in these
two blocks. Convenience/profile/diagnostic requirements above are independently
preserved with conditions; they are not active implementation promises or reasons
to import the obsolete package tree.

Remaining assessment still includes canonical/source-sequence and residue views,
older core/schema entry points, specialist metadata/support parsers for already-used
sources, and the historical scientific data artifacts. Consumer projection
requirements are already self-contained in
[the reviewed consumer matrix](consumer_projection_requirements.md); source/input
conditions remain in [the provider reactivation matrix](../../pending_proposals/historical_provider_reactivation.md).
Check any residual implementation gaps and reconcile remaining inventory dispositions
before recommending stash deletion. Deferred requirements can survive that decision
without their old code. The original stash and 87 exported originals remain intact.

This slice changes review documentation/inventory only. There is no new source
adoption, scientific fixture, runtime/schema change, separate environment, stage,
commit, push, remote code checkpoint or stash deletion. The last full code result
remains follow-up 29: **5477 passed in 172.18 seconds**, receptor with 12 workers and
10 expected fixture warnings. Selected gates below are separate current results,
not another full-suite checkpoint.

## Remaining inventory labels at this checkpoint

**31 original file entries** still carry the generic
`requires_individual_review` label. Many already have partial provider/batch reviews;
this is a finite list for whole-file residual-gap reconciliation, not 31 known new
integrations or 31 providers. Scientific artifact admission and previously retained
requirements must also be reconciled; a label count alone is not stash-deletion
readiness. Twenty originals now have explicit final review records in follow-ups
28/29/30; earlier recoveries use their own records.

- `sabueso/__init__.py`
- `sabueso/core/__init__.py`
- `sabueso/mappings/interpro.py`
- `sabueso/mappings/pdb.py`
- `sabueso/mappings/pubchem.py`
- `sabueso/mappings/ted.py`
- `sabueso/mappings/uniprot.py`
- `sabueso/resolver/__init__.py`
- `sabueso/tools/db/go.py`
- `sabueso/tools/db/scope.py`
- `sabueso/tools/db/uniprot.py`
- `schemas/card_schema.yaml`
- `schemas/card_schema_0.1.0.yaml`
- `sabueso/mappings/knowledge.py`
- `sabueso/mappings/protein_annotations.py`
- `sabueso/mappings/protein_context.py`
- `sabueso/mappings/protein_drug_discovery.py`
- `sabueso/mappings/protein_expansion.py`
- `sabueso/mappings/protein_priority_sources.py`
- `sabueso/mappings/protein_specialist.py`
- `sabueso/mappings/protein_structural_context.py`
- `sabueso/mappings/protein_translational_sources.py`
- `sabueso/resolver/protein.py`
- `sabueso/tools/protein.py`
- `sabueso/tools/protein_sources.py`
- `tests/resolver/test_protein_resolution_offline.py`
- `tests/tools/test_knowledge_enrichment_offline.py`
- `tests/tools/test_online_protein_priority_sources.py`
- `tests/tools/test_protein_annotation_sources_offline.py`
- `tests/tools/test_protein_priority_sources_offline.py`
- `tests/tools/test_protein_translational_sources_offline.py`
