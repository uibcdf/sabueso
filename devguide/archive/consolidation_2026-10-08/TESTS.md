> Historical snapshot preserved on 2026-10-08 during consolidation (#112).
> Current guidance: [devguide/TESTS.md](../../TESTS.md). Statements below retain their original receipt dates and qualification scopes.

# Sabueso — Tests and Quality Gates

The public HK2 integrated gate is `tests/core/test_hk2_test_system_offline.py`.
It rebuilds the current card from the qualified UniProt response, retains its
two ATP-site groups, verifies quantities/support and unknown scope, and checks
exact store/report round trips without acquisition. Run with pytest-receptor,
12 workers and the existing Python 3.14 environment. See
[HK2_TEST_SYSTEM.md](../../HK2_TEST_SYSTEM.md) for generation and expansion limits.

Development FDA OOPD guards in `tests/tools/test_fda_orphan_offline.py` preserve
the two unchanged native detailed pages, separate designation/approval occurrences,
blank/N/A/date/name/status/sponsor literals, native nested-table quirks and explicit
URL/caller identity basis. Returned search forms and missing/failed/malformed late
tables never become no-designation results. Invalid arguments, foreign/cut/revision
binding, gzip/hash/time/caller terms and one-GET/zero-network archive replay are
covered. Run pytest-receptor with 12 workers in the existing editable Python 3.14
environment. Actual live transport failure is retained separately from fixture
and imported-original replay qualification.

Development TTD/iPTMnet guards in `test_ttd_offline.py` and
`test_iptmnet_offline.py` qualify all native tag-value blocks and HTML substrate
groups before selection/mapping. Original releases/key semantics, placeholders,
blank sites/fields, hidden PMID/source support, opaque score0/future labels,
repeated/conflicting occurrences and missing/failed/empty states remain distinct.
Wrong titles/dates/late rows, identity/group/table/header mismatch, malformed HTML,
unsafe queries, bound gzip/hash/time/terms and original-response replay are covered.
Run with pytest-receptor and 12 workers in the existing editable Python 3.14 environment.

Development BRENDA guards in `tests/tools/test_brenda_offline.py` qualify native
EC identity, systematic names/descriptions, RDF language/datatype fidelity, empty
literals versus unbound OPTIONALs, duplicate/conflicting solution occurrences,
malformed late rows, no-match versus failed acquisition, exact query/revision/cut
binding, JSON/gzip/hash/time snapshots and one-GET original-time archive replay.
Run with pytest-receptor and 12 workers in the existing shared Python 3.14 environment.

Development ChEBI description guards in
`tests/core/test_chebi_descriptive_recovery_offline.py` exercise all seven existing
native entries, independently supported original name/formula, missing versus
malformed fields, retained identity gating and explicit formula-conflict support.
These 26 cases add no fixture or schema change. Run pytest-receptor with 12 workers
in the existing editable Python 3.14 environment.

Development PubChem description guards in
`tests/core/test_pubchem_title_recovery_offline.py` qualify three original public
titles, independent CID/source support, optional missing versus malformed text,
literal spelling, retained standard-key admission, equal-name distinct structures,
conflicting supported titles and the existing online property request. Eighteen
cases add no schema change. Run pytest-receptor with 12 workers in the existing
editable Python 3.14 environment.

Development UniProt source-annotation guards in
`tests/core/test_uniprot_additional_annotations_offline.py` and
`tests/core/test_uniprot_domain_recovery_offline.py` qualify all 57 newly retained
assertions from five unchanged native fixtures: five comment types and eight feature
types. Fifty-four new cases exercise native support/revisions, exact boundaries,
unknown/fuzzy/malformed endpoints, molecule scope, detached metadata, missing versus
not stated, different sequence versions and exact storage. Schema policy and migration
guards verify additive unpublished 0.3.13 and keep published 0.3.12 frozen. Run
pytest-receptor with 12 workers in the existing editable Python 3.14 environment.

## Running the tests

Development Pharos/DepMap guards in `test_pharos_offline.py` and
`test_depmap_offline.py` check unchanged native fixtures, exact target/model identity,
provider TDL and model context, null/blank/future literals, complete CSV validation,
malformed/error versus no-match, unsupported query/release/revision/cuts, bound
JSON/CSV/gzip/hash/time/terms and one-GET archive replay. DepMap's fixed online
release digest fails if bytes change. Gene effects and aggregate associations are
not claimed. Use pytest-receptor and 12 workers in the existing Python 3.14 environment.


Development Interactome3D guards in `tests/tools/test_interactome3d_offline.py`
qualify all 18000 original fourteen-column rows, one P60174 structure and thirty
Q8WZ42 representative occurrences. Native blank/whitespace chain labels, case,
model/template distinction, duplicate rows, zero percent quantities under a host
unit context and opaque negative/future scores survive. Late malformed rows,
wrong source/query/organism/set/revision/cuts, strict archive/accession contracts,
bound TSV/gzip/hash/time/terms, missing/error versus not-listed and one-GET replay
are checked through pytest-receptor with 12 workers in the existing environment.

Development ProBiS guards in `tests/tools/test_probis_offline.py` qualify the
complete unchanged 42270-row native catalog, its first data row, padded unknown
columns, gaps and duplicate selectors. Three `5a2q.h` and five `2ww9.L` occurrences
remain independent; documented `1ytb.B` differs from listed `1ytb.A`. Native chain
case, future opaque columns, malformed late rows, invalid source/query/revision/
cuts, bound TSV/gzip/hash/time/terms, missing/error versus not-listed and one-GET
replay are checked through pytest-receptor with 12 workers in the existing environment.

Development PDBTM guards in `tests/tools/test_pdbtm_offline.py` qualify the
unchanged 6866-byte XML, three independent chains/45 regions, nonuniform native
sequence/PDB endpoints, repeated/generated chains, zero counts and future type
codes. Original copyright/declared encoding/non-ASCII bytes, XML character data,
late malformed chains, changed source/query/revision/terms/cuts/hashes, unavailable
versus unsupported representation, bound XML/gzip/time and one-GET replay are
checked through pytest-receptor with 12 workers in the existing environment.

Development 3did guards in `tests/tools/test_threedid_offline.py` qualify the
complete native 1657-pair/17478-instance DMI export, six independent 7m5l instances,
block parent/order/terminator integrity, opaque patterns/dates, repeated lowercase
chain tokens, insertion/negative PDB endpoints and zero/conflicting counts.
Malformed late rows, invalid query/source/kind/revision/cuts, bound text/gzip/hash/
time/terms, failure versus not-listed and one-GET replay are exercised through
pytest-receptor with 12 workers in the existing Python 3.14 environment.


Development HPO guards in `tests/tools/test_hpo_offline.py` qualify the complete
unchanged 333983-row release, independent TPI1 disease/frequency occurrences,
duplicate/conflicting/future literals, exact Gene/release scope and malformed
late rows. Bound TSV/gzip/hash/time/terms, missing/error versus not-listed,
one-GET replay and conservative custom-licence retention are exercised through
pytest-receptor with 12 workers in the existing Python 3.14 environment.


Development MEROPS guards in `tests/tools/test_merops_offline.py` qualify the
complete original export, all four representation issues, exact namespace/case/
quoted/versioned literals, blank/whitespace taxonomy, conflicting/duplicate rows
and support hashes. Late errors and unbound/malformed representations do not
become complete not-found results. Bound TSV/gzip/hash/time/source/query/revision,
missing files, one-GET replay and unversioned licence unknown-use/internal-retention
semantics are exercised. Use pytest-receptor and 12 workers in the existing environment.


Development MetalPDB guards in `tests/tools/test_metalpdb_offline.py` qualify
independent API-versus-HTML donor identities, explicit angstrom header/rounding,
quantity units under a nanometer host context, native parent occurrences, false
flags, unknown labels, zero distances and original chain/residue numbers.
Wrong identity, documented-versus-native type mismatches, new unit-labelled shapes,
nonfinite/error bodies, malformed late rows, missing fixtures, bound JSON/gzip/
hash/time and one-GET replay are exercised. Use pytest-receptor with 12 workers
in the existing shared Python 3.14 development environment.


Development ECOD guards in `tests/tools/test_ecod_offline.py` qualify numeric UID
padding, exact source domain/PDB/chain, id/name hierarchy, false flags and opaque
ranges. Null pointers, unassigned family 0, discontinuous/other-chain/inserted
literals, extra fields, wrong identity/origin/revision, nonfinite/error bodies,
unsafe queries, bound JSON/gzip/hash/time and one-GET replay are exercised. Run
through pytest-receptor with 12 workers in the existing Python 3.14 environment.


Development TCDB guards in `tests/tools/test_tcdb_offline.py` qualify the full
native headerless table, first-row retention, unbound blank accessions, versioned
and case-sensitive identifiers, multiple/six-component assignments and duplicate
pair occurrences. Late malformed rows, empty/error/header bodies, unsafe queries,
bound TSV/gzip/hash/time/terms and one-GET replay remain distinct from not-listed.
No sequence/family acquisition or function/identity transfer is added. Run through
pytest-receptor with 12 workers in the existing shared Python 3.14 environment.

Development ChannelsDB guards in `tests/tools/test_channelsdb_offline.py` cover
native entry/reaction and independent residue groups, literal HTML text/reference
and numbering gaps, duplicates/conflicts, malformed late rows and unknown groups.
Unsafe identifiers, unavailable/error bodies, explicit empty arrays, query-bound
JSON/gzip/hash/time/terms and one-GET replay are exercised. Geometry/assembly and
linked references are not acquired. Use pytest-receptor with 12 workers in the
existing shared Python 3.14 environment.

Development GWAS guards in `tests/tools/test_gwas_catalog_offline.py` qualify
native HBB/TPI1 HAL pages, independent study/association occurrences, explicit
partial/empty coverage and original mantissa/exponent/numeric/text statistics.
Repeated/conflicting IDs/alleles/traits, zero versus null/missing, query symbols,
unsafe/changed/cyclic page links, contradictory totals/row shapes, page argument
types, bound JSON/gzip/hash/time/terms and failed/unavailable access are exercised.
One-GET archive replay retains original support without following pages or studies.
Use pytest-receptor and 12 workers in the existing shared Python 3.14 environment.

Development Monarch/PRIDE guards in `tests/tools/test_monarch_offline.py` and
`tests/tools/test_pride_offline.py` cover native relationship/project identities,
opposing negation, qualifiers, gene-level support, explicit page counts/offsets/cuts,
all original project CV/protocol/licence context and representation differences.
Missing/null/future/duplicate declarations, exact scope, malformed JSON/counts,
bound JSON/gzip hashes/time, failed access and one-GET archive replay pass through
pytest-receptor with 12 workers in the shared Python 3.14 environment.

Development OmniPath guards in `tests/tools/test_omnipath_offline.py` cover native
human aggregate interactions, opposing signs/consensus, duplicate occurrences,
resource-prefixed support, exact participant/query scope, native empty arrays versus
HTTP-200 application errors, malformed rows/bytes, bound JSON/gzip snapshots and
one-GET archive replay. Resource-specific rights remain separate from access filters.
Use pytest-receptor with 12 workers in the shared editable Python 3.14 environment.

Development `tests/tools/test_wikipathways_offline.py` qualifies the unchanged
2218-row native export, nine exact TPI1 pathways and misplaced native prefixes
without column repair. Guards retain alias positions, repeated/conflicting pathways,
species, version digits, unknown finite fields and raw shortened descriptions.
Substring/name/case joins, malformed unrelated rows, invented release/cuts, wrong
snapshot binding, invalid JSON/gzip/hash, unavailable files and failed HTTP fail
explicitly. One-GET replay retains original time/identity and CC0 terms without
fetching links. Run with pytest-receptor and 12 workers in the shared Python 3.14
editable environment.


Development EMA orphan guards in `tests/tools/test_ema_orphan_offline.py` exercise
the full unchanged 3310-row JSON, declared count/generation time, repeated EU numbers
on independent page subjects, differing dates, withdrawn status and literal product
references. Unknown-number placeholders, repeated/conflicting/future labels and
fields survive. Exact query/envelope scope, all-row type/URL/finite validation,
malformed count/timestamp, generation-versus-revision, bound JSON/gzip SHA/time/terms,
unavailable/failed/not-listed outcomes and one-GET archive replay are covered.
Use pytest-receptor with 12 workers in the existing editable Python 3.14 environment.

Development CIViC guards in `tests/tools/test_civic_offline.py` exercise the full
4940-row monthly native export, independent BRAF Supports/Does Not Support items,
accepted flagged DNMT3A, atomic ALK/fusion profile scope, duplicate/conflicting/future
labels and quoted TSV. Exact profile/monthly-release checks, all-row validation,
malformed scope/cuts, bound TSV/gzip hashes/time/CC0, missing/failed/not-listed
outcomes and one-GET archive replay are covered. Use pytest-receptor with 12
workers in the existing editable Python 3.14 development environment.

Development DrugCentral guards in `tests/tools/test_drugcentral_offline.py`
exercise the unchanged full native export, independent EGFR rows, composite-target
scope, repeated/conflicting observations, native activity/units/MOA and quoted TSV.
Complete-export shape/identity validation precedes selection. Guards cover exact
queries/envelopes, unknown revisions/cuts, bound TSV/gzip/SHA/time/terms, failure
versus unavailable/not-listed, and one-GET archive replay. Use pytest-receptor and
12 workers in the existing editable Python 3.14 environment.


Development ClinGen guards in `tests/tools/test_clingen_offline.py` exercise the
unchanged complete 3702-curation export, independent BRCA1 diseases/inheritance,
legacy report namespaces and unknown classification timezone, and TPI1 not-listed
versus explicit No Known Disease Relationship. Guards cover repeated/conflicting
occurrences, future native labels/CSV quoting, unrelated malformed rows, complete
preamble/shape/identity validation, unsupported cuts/revisions, source-bound CSV/
gzip/SHA, unavailable/failed access, one-GET replay and CC0 retention. Use the shared
editable Python 3.14 environment, pytest-receptor and 12 workers.


Development HPA guards in `tests/tools/test_hpa_offline.py` use the unchanged
native public TPI1 object and exercise RNA/protein scope, native null versus
missing categories, complete raw quantitative context without normalized projection,
exact gene identity, malformed/finite JSON, unsupported cuts/revisions, bound
JSON/gzip and original-byte SHA, access failure versus missing fixture, one-GET
archive replay and CC BY/third-party terms. Use the shared editable Python 3.14
environment, pytest-receptor and 12 workers.


Development SIGNOR guards in `tests/tools/test_signor_offline.py` qualify original
headerless HsTIM and AKT1 tables plus a native no-result response. They retain the
first row, independent occurrences, original regulator/target support, mixed
native taxa and quote/trailer literals. Cases cover exact query namespaces,
complete-row validation, no-result versus failed/unavailable access, malformed
wrappers/headers, unsafe IDs/organisms, cuts/invented revisions, bound TSV/gzip SHA
and one-GET archive replay without linked acquisition. Source CC BY terms remain
separate from underlying publication rights. Use pytest-receptor and 12 workers
in the shared editable Python 3.14 development environment.

Development APPRIS guards in `tests/tools/test_appris_offline.py` exercise the full
unchanged native TPI1 exporter, repeated/conflicting principal declarations and
independent row occurrences. They cover all-row identity/text/range validation,
unknown native labels, empty-received versus failed/missing access, unsafe IDs,
unsupported cuts/revisions, query-bound JSON/gzip and original-byte SHA, one-GET
archive replay without linked acquisition, and noncommercial/share-alike terms.
Use the shared editable Python 3.14 environment, pytest-receptor and 12 workers.

Development `test_complex_portal_offline.py` guards three unchanged native complex
records, non-protein participants, HsTIM prediction/ECO/star context, null versus zero
stoichiometry and partial feature references. Independent equal occurrences and changed
support retain distinct IDs. Exact primary/internal/query identity, complete array/
feature/reference types, finite JSON, dates and all unselected rows fail closed.
Snapshots check exact source/query and original-byte SHA-256; missing files, malformed
objects and HTTP failures remain distinct. Single-GET archive replay keeps original
times without following support links or expanding binary interactions.

Development `test_cath_offline.py` guards four full native domain summaries,
independent ATOM/COMBS sequences, unresolved PDB locations, discontinuous segments,
chain case, literal insertions and original GO/EC alternatives. Fixed request release
and unknown response revisions stay separate. Complete identity/hierarchy/sequence/
correspondence checks fail closed; native unknown context survives. Bound supplied
JSON/gzip intake checks exact source/query and original-byte digest. Missing fixtures,
malformed files and failed HTTP remain distinct, and single-GET archive replay keeps
original times without acquiring linked resources. All pytest uses the shared
Python 3.14 environment, 12 workers and pytest-receptor.

Agents run pytest through pytest-receptor, as MOLI's developer-tools policy asks
(`MOLI_GUIDE.md`):

Use the Python 3.14 development environment for routine local tests. The
supported 3.11–3.13 interpreters remain in CI and release compatibility gates.

```bash
python -m pytest -n 12 -m "not online" --receptor=llm   # local offline suite
python -m pytest -m online --receptor=llm         # online tests, on demand
```

Use the shared development environment's `pytest-xdist` for 12 local worker
processes, as requested by the maintainer. `pytest-receptor` controls reporting;
`-n 12` controls parallel execution. Inspect Actions runs with the published
`gh-run-receptor` first, keeping GitHub conclusions authoritative and native
`gh run view` as fallback, as `MOLI_GUIDE.md` requires.

CI runs the offline suite with `--receptor=ci`. Read the receptor's summary line (`PASS`
or `FAIL`, with the exit code) before doing anything that depends on the result.

`recovered_work/` is a local historical export, explicitly excluded from pytest
discovery. Its original tests describe obsolete APIs and are not active regressions.
Recovery guards live in `test_residue_knowledge_offline.py`,
`test_residue_composition_offline.py`,
`test_card_notebook_offline.py` and `test_aaindex_offline.py`: exact item support,
explicit sequence/numbering, disulfide endpoints, detached saved readers, inert
deterministic notebooks/sealed sidecars, escaping, native paired scales/NA,
complete-document integrity, online transport, acquisition and missing fixtures.
Generated notebook-cell replay guards additionally execute full/minimal reports
in English/Spanish after moving the saved pair, preserving title/options, metadata,
markdown cells and sealed-card bytes with no acquisition. A different valid snapshot
is refused before regenerated files are written. These five regressions qualify
normal Python/Jupyter execution of the existing assertion-based snapshot guard.

Equal values asserted about another protein cannot support a residue item.

Development `test_residue_composition_offline.py` guards unique selected positions,
original selection/duplicate locators, concrete versus ambiguous letters, explicit
full denominators and empty versus missing sequence. Source subject/hash/content,
independent revisions, conflicting declarations and canonical support gaps are
checked. Native MobiDB sequence declarations and the frozen public 0.3.12 HsTIM
card qualify source-axis counts and inert round trips with no acquisition/credit.
Legacy row names and structural numbers are never coerced into sequence positions.

Development `test_uniprot_isoforms_offline.py` guards the original full P60174 parent
and its three native FASTA sequences, distinct name/ID correspondence, source-native
lengths, unknown isoform revision and separate parent/canonical/release context.
Supplied assertions feed the existing residue reader without canonical annotation
projection or card mutation. Equal sequences/changed parent support stay distinct.
Missing/partial scope, explicit not-listed/empty declarations and unknown/external/
not-described status do not trigger speculative FASTA queries. Malformed unselected
declarations, unsafe IDs, truncated client components, malformed JSON and wrong/
multiple FASTA records fail closed. Unavailable files and failed HTTP remain distinct;
two-GET archive replay retains original component times and successful parent access
survives a later sequence failure. Existing canonical candidate tests retain their scope.

Development `test_swissmodel_offline.py` guards the native 30-occurrence response
and 57 alignment pairs, all providers, target MD5 versus model identity, native
QMEAN dictionaries, independent duplicate rows and changed source sequences.
Identity/scope/version mismatches, malformed unselected rows, missing collections,
unsafe identifiers and inconsistent peptides/columns fail closed. Zero/null/missing
values and extra context survive; empty arrays, missing files and failed HTTP stay
distinct. Single-GET archive replay keeps original times without following linked
resources. Data terms retain CC BY-SA 4.0 attribution and share-alike obligations.

Development `test_amypro_offline.py` guards the native 125-entry export, exact
AmyPro selection, investigated-sequence regions, parent-bound inconsistencies,
mutation/category literals, repeated equal regions and independent source identities.
Unselected entries are validated before selection. Changed native sequence support
has distinct assertion IDs even when region values match. Empty region dictionaries,
not-listed entries, unavailable files, malformed JSON and HTTP failures remain
distinct. Shared single-GET archive replay keeps original time/hash and queries no
parent sequence or publication; individual Python-literal downloads are not evaluated.

Development `test_intact_offline.py` guards the native HsTIM MITAB 2.7 page,
all 42 columns, A/B/alternative/self-interaction matches, namespaces, quoting,
publications/scores, negation and complex expansion. Synthetic boundary cases
retain feature/parameter/role literals without guessed biological classes.
Counts and exact query/format/page scope are checked before caps; duplicate
occurrences survive independently. Unavailable fixtures, failed HTTP and known
zero differ. Count/service headers and original times survive archive replay
without publication/continuation requests.

Development `test_mobidb_offline.py` guards complete native v1 exports, canonical
identity/sequence/release, separate annotation bases, literal modification labels,
unknown PTM experimental support, conversion issues, zero versus missing intervals,
export/header counts, unavailable/not-found/failed access and original-time replay.
Its source-axis residue case does not manufacture an ontology ID or canonical
coordinate equivalence. `test_sifts_offline.py` guards exact structure identity,
distinct protein/isoform references, author versus label chains, interval/endpoint
numbering, negative author numbers/insertion codes, missing releases and replay.
The registry gate also checks the packaged source metadata catalog, status-separated
category profiles, declared limits and detached offline access with no source query.
AAindex parser data in these tests is synthetic, not redistributed native data.

Development `test_structural_context_recovery_offline.py` guards native EPPIC 1HTI
interfaces/assemblies, area units under a non-default session policy, explicit
component identities/hashes/times, alternatives, method sentinels and unit-cell scope;
native PDB-REDO 1CBS refinement stages, original arrays and input/software versions;
invalid identities/types/domains, null/zero/absence, later failure receipts, missing
fixtures, original-time archive replay and unknown versus explicitly stated reuse.

Development `test_eppic_residues_offline.py` guards the full native 1HTI interface-1
table, 496 per-side records, original context/hashes, square-angstrom ASA/BSA under
a nanometre session, zero and quoted-NaN distinctions, region/entropy literals and
independent repeated occurrences. Boundary cases keep negative/unknown serials,
null labels and same-chain sides, reject malformed scope/values, private jobs and
invalid IDs before access, and distinguish empty arrays from missing/failed tables.
Two-GET archive replay preserves original component times; later failures retain
successful context acquisition. No biological class or coordinate projection is added.

Development `test_ligand_context_recovery_offline.py` guards native HsTIM AlphaFill
metadata and LIGYSIS segment 1, model/transplant subjects, all alternatives, original
HTML, zero/null/missing distinctions, source run versus record revision, distinct
compound labels and donor numbering. Explicit angstrom/percent quantities remain
stable under a nanometre session. Adversarial cases reject malformed identities,
metrics, incomplete tables/membership, unsafe query arguments, changed layouts,
JavaScript expressions, duplicate JSON keys and non-finite JSON. Shared two-GET
archive replay retains original times and no assets/jobs are acquired. Missing
fixtures and HTTP failures are distinct from empty source results; software and
publication licences are not substituted for data terms.

Development `test_ligysis_residues_offline.py` qualifies all 20 original initial
residue-panel rows and their independent column/row/hash/receipt support. It guards
percent RSA under a host unit context, zero versus NaN, repeated/conflicting
positions, unknown declared columns, empty display versus segment absence, late
malformed rows, wrong identity/revision/cuts, changed column contracts and literal
expressions/duplicates/non-finite JSON. Generic site-only parsing does not acquire
the new detail requirement. Run receptor with 12 workers in the shared environment.

Development `test_ligysis_correspondences_offline.py` qualifies four original directed
chain dictionaries (491 entries in each direction), detached support and explicit
unknown chain-to-protein identity/numbering. It guards signed/zero/leading-zero
labels, case, empty dictionaries versus missing input, unmatched opposite parents,
conflicting/non-bijective mappings, malformed late parents/values, executable or
duplicate/non-finite literals and exact query/revision/cut scope. The site-only
contract remains independent. Use receptor and 12 workers in the shared environment.

Development `test_glygen_offline.py` guards native HsTIM glycosylation/phosphorylation
rows, declared sequence identity, provider isoform comments, peptide versus residue,
original support pointers and independent alternatives; literal predicted/text-mined
categories, ranges and unlocated numbering, exact table counts, invalid identity/
shape/scope, empty versus missing/failed access and original-time archive replay.

The knowledge-baseline curation and storage cases prepare detached cards independently.
The storage test proves pinned original/curated snapshots without relying on another
test running first; it passes alone and under 12-worker scheduling.

## Test kinds

Development `test_pdbe_validation_offline.py` guards native public 1HTI/1CBS metrics,
exact structure subjects, raw versus percentile values, optional relative ranks,
zero versus unstated metrics, unknown provider metrics, detached mapping, malformed
wire responses, invalid identity/numeric domains, unavailable fixtures, HTTP failures
and archive replay with original support/times. Synthetic adversarial changes exercise
boundaries rather than establish source fidelity. No quality class is inferred.

- **Offline tests** (`tests/core`, `tests/ops`, `tests/resolver`, `tests/tools`). They
  need no network, and read frozen public responses from `temp_data/`.
- **Acceptance tests.** Flows on real test systems, TcTIM (P52270) and HsTIM (P60174),
  from public data. Examples: the knowledge baseline (`test_knowledge_baseline_offline`),
  identity hygiene, measurement identity, the structural inventory.
- **Online tests** (`@pytest.mark.online`). Smoke tests against live services. Any test
  that reaches a remote endpoint must carry the mark. Some skip when a service is slow
  or needs a key (BioGRID: `BIOGRID_ACCESS_KEY`).
- **Schema guards.**
  - Frozen cards (`temp_data/frozen_cards/`) of every published card schema must stay
    readable, and must migrate.
  - The recorded card shape (`schemas/card_shape_<version>.json`) must match the cards
    built from the fixtures (`tools/card_shape.py`). An unannounced change fails.
  - `tools/validate_schema.py` keeps `FIELD_PATHS.md` and the schema aligned.
- **Registry guard.** Every source module is an `in_use` entry of
  `sources/registry.yaml`, and the generated page matches it
  (`tools/source_registry.py --check`).
- **Argument contracts.** Every public signature has its digesters
  (`ARGUMENT_CONTRACTS.md`).
- **Installed-package gates.** Release candidates are tested from the exact conda
  artifact, on Linux, macOS and Windows × Python 3.11–3.14, before publication
  (`devtools/conda-build/README.md`). The 0.12.0 gate additionally rejects
  source-shadowed/inconsistent or incomplete Ackredit imports, then runs unchanged
  acquisition/attribution tests and the public saved-reader workflow outside both
  checkouts. Public Pytest/Receptor tooling is installed with Conda; no runtime
  source/pip overlay substitutes for the artifact. Ackredit is pinned to public
  0.9.0/py_0 with its qualified SHA-256; a different digest or staging import fails.
  The preliminary 0.12.0/py_0 file passed all 12 installed lanes, 36 integration tests
  and the public workflow per lane. The producer/archive/matrix and independent
  clean Linux pip-check receipt is
  `devtools/conda-build/receipts/sabueso_0.12.0_staged_2026-10-03.json` (#110).
- **Required Ackredit integration.** `tests/core/test_attribution_offline.py` exercises
  automatic per-result attachment without a collector,
  per-result/workflow reuse, exact support scope, real provider failure, saved readers,
  context isolation and genuine fresh-process absence. All runtime CI lanes
  obtain the required provider from public Conda; dedicated receiving lanes pin
  Ackredit 0.9.0/py_0 on Python 3.11–3.14. No source overlay or Requires-Python
  override remains. The generic preflight's unpublished-provider safeguards are
  retained through synthetic negative rehearsals, independently of current delivery.
  Dedicated lanes run unchanged integration tests and the public workflow outside
  the checkout using installed code and public fixtures. The delivered portable
  minimum is `ackredit>=0.9.0` (ackredit#22/#75/#80).
  Fresh Linux receiving environments at Python 3.11–3.14 run the 36 unchanged
  attribution/acquisition cases, public workflow and pip check with the planned
  exact public core builds. Their artifact/source/installed-byte and origin receipt
  is `devtools/conda-build/receipts/ackredit_0.9.0_public_2026-10-03.json`.
  The consumer is a local wheel with all source modules/resources checked against
  its commit; these are not Sabueso's staged Conda installed-package gates.
  `test_source_acquisition_offline.py` checks automatic card/resolution/one-call
  packet traces, final refresh pins, original versions/hashes, fixtures, archive
  replay/reuse, evaluated-empty access, HTTP absence, missing fixtures, timeouts,
  partial batches, retries, provider/pin-recording failure, separate nested collectors,
  custom-client coverage and saved readers without new credit. Dedicated lanes copy
  these unchanged tests alongside packet-attribution tests outside both checkouts.
  `test_rcsb_acquisition_offline.py` adds native entry revisions (including zero
  minor versions), source citations, differing citation forms, single/batch archive
  reuse, empty/unavailable/unqueried/failure outcomes, chunking, fallbacks, partial
  completed credit, retries and saved readers. CI and the installed matrix copy and
  run it against the public Ackredit floor. The RCSB extension supersedes `py_0`
  with the qualified `7739317`/`py_1` archive: all 12 installed lanes and clean
  public installation pass 56 cases and the three-packet workflow. Publication,
  unchanged promotion, public origins/bytes/API and identical-tag Zenodo are recorded
  in `devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.
  `dependency_preflight.py --release` now passes the adopted public closure;
  stale floors, omitted public pins and future unpublished providers still fail.
  Ackredit #81 tracks the earlier editable Git-version mismatch. The current
  editable satisfies the published minimum; all workspace packages remain editable.
  The latest primary-environment check reports unrelated external dependency
  conflicts, recorded in `CHECKPOINT.md`; installed-candidate pip check passes.

## Clinical registry and bibliography guards in development

`test_clinicaltrials_acquisition_offline.py` checks both registry operations,
version/page/entry scope, continuation after empty pages, chunks, invalid envelopes,
conflicting duplicates, repeated tokens, reuse and partial completed credit.
Unavailable fixtures never become biological negatives. Explicit native reference
lookup and three separately queried Europe PMC articles preserve native PMID,
pointer forms, host citations, full personal/collective authors, saved CSL-JSON and
BibTeX readers, concurrent context and provider failure. Existing clinical assertions
and frozen card shape remain unchanged. `test_article_metadata_offline.py` adds
mixed and collective-only author regressions (#128). Both test modules are copied
and executed unchanged outside the checkout by installed-provider CI and the
future staged package matrix; this local slice is not yet publicly delivered.

## Traceability and extraction guards delivered in 0.13.0

`test_indication_bibliography_offline.py` guards the development ChEMBL reference
projection: both indication queries, exact native grouped identifiers and row/page
bases, overlapping disease queries, duplicate/alternative reference forms, later
failures, original archive versions/times and empty/unavailable/unqueried outcomes.
Malformed and identifier-only forms keep explicit gaps and unchanged raw returns.
Host citation preservation, per-reference roles, concurrent queries and inert
CSL-JSON/BibTeX exports are checked. The file runs unchanged outside the checkout
in installed public-provider CI and future staged installed-package gates.

`test_chembl_acquisition_offline.py` verifies paginated/chunked access, native releases,
original document citations, archive reuse/replay, retries, partial received-page credit,
fixtures, empty answers and failures. `test_rule_literature_extraction_offline.py`
verifies exact namespaces/token boundaries, Unicode offsets, repeated occurrence
support, original rule acquisition, input identity, saved attribution and provider
failure. Both run unchanged outside the checkout in installed-provider CI lanes.

`test_literature_intake_offline.py` adds original support/receipt replay, inert
store and card readers, saved historical pins, refresh without rerunning extraction,
explicit missing-sidecar gaps, alternative fragments, empty fragment scope, provider
failure, exact subject/refused inconsistent closure and terms-profile boundaries.
It also runs unchanged in installed-provider lanes and future staged artifact gates.

`test_pubchem_acquisition_offline.py` covers compound/structure/BioAssay traces,
native per-assay revisions (including zero), caps/chunks, original PubMed pointers,
depositor context, POST-body identity, archive reuse/replay, retries, evaluated-empty
access, rejected inputs, missing fixtures, offline unqueried access and partial
received-row credit after later failures. Public fixture cards, refresh, saved
readers, nested collectors, custom-client gaps and provider failure are exercised.
These tests also run unchanged outside the checkout with public Ackredit 0.9.0.

`test_bindingdb_acquisition_offline.py` covers REST/fixture/mirror queries, native
response/manifest identities, version and cutoff bases, caps/order, DOI/PubMed
forms and host citation preservation, archive reuse/replay, retries, decoded-empty
responses, missing fixtures, offline-unqueried access, original failures and partial
received-data credit. Mirror corruption, public card storage/refresh, nested
collectors, inert readers, provider failure and custom-client gaps are exercised.
The #114 regressions distinguish source-declared empty strings, unexpected status,
malformed/unexpected payloads, default shared-transport retries, archived empty
replay, fixture absence and card-level not-found outcomes without failure warnings.
These tests run unchanged in installed-provider and future staged gates.

`test_disease_explanation_offline.py` checks the five-source public disease group,
selected annotation members, multi-hop MedGen/MONDO support, hierarchy steps,
exact historical card/item pins, missing support, selection/qualifier alternatives,
ungrouped/conflicting identity and unqueried context, inert attribution and argument
validation. Versioned grouping guards (#115) reverse relationship insertion order,
retain converging/conflicting/unfinished MedGen branches, direct naming conflicts,
source/version differences, qualifier alternatives and all hierarchy paths. Explicit
`@1` reproduces the historical lookup/partial explanation at the unchanged card pin;
default `@2` never chooses an ambiguous target. These tests also run unchanged
outside the checkout in installed-provider CI and future staged gates.

`test_knowledge_state_explanation_offline.py` checks exact row/classification
parity, selected and competing support, conflicts, UniProt absence/relationship
coverage, unqueried curation, empty/failure/cut/partial reports, area-specific
Europe PMC counts, original report locators and historical item pins. Missing
field/relationship/conflict support stays partial rather than hiding behind a
derived absence. Original UniProt versions survive reversed support order (#116).
Selectors are digested; readers stay inert. The tests run unchanged outside the
checkout with the public provider and in future staged installed-package gates.

`test_bioactivity_explanation_offline.py` checks public TcTIM/HsTIM group/class
parity, exact source versions, coarser stated precision with units, declared copies,
assay/precision/connectivity selectors, copy-only voters, group disagreement,
cross-group discordance, direct-assay filtering and non-default quantity thresholds.
Ranges, single-point concentrations, unknown units, not-determined measurements,
ambiguity/candidate support, consistency flags, stored identity locators, missing
lineage, historical pins, ArgDigest and inert detached readers have regressions.
The #117 guards cover missing activity-only originals, successful exact pointers,
assay fallback and later statement resolution, both current and historical.
Diagnostic completeness changes neither groups/classes nor original copy support;
readers remain inert, and later acquisition cannot resolve an older pinned card.
The file runs unchanged with public Ackredit outside the checkout in installed
CI and future staged gates. No new source fixture or stored card field is introduced.

`test_ligand_explanation_offline.py` checks public TcTIM/HsTIM native site/crossing
parity, distinct protein/molecule pins, source-stated identity and actual class/name
choices, quantity thresholds, numbering/absent-annotation distinctions and
instance-level spanning. Relevance statements, selected/competing field support,
missing assertions/conflict support, duplicate deck members, historical card/deck
reads, exact selectors and detached inert readers have regressions. The existing
ligand count correction (#118) checks distinct groups across matched molecule/parent
items, declared copies, statement restatements, same-source independence, ambiguity,
discordance, copy-only fallback and assay filtering. Versioned current/legacy counts,
comparisons, exact counted ids, historical source support and ArgDigest have guards.
The file runs unchanged
outside the checkout with public Ackredit and in future staged installed gates.

`test_chemical_identity_acquisition_offline.py` covers CCD batches and both UniChem
lookup methods: normalized iterable queries, POST/wire/decoded identities, original
times and archive references, retries, empty/missing-fixture/offline/failure outcomes,
received subsets before later failures, native source forms and citation roles.
Threaded capture context, molecular resolution, ligand-deck input/result pins,
detached readers, unknown versions, provider/pin failures and custom gaps have guards.
The file runs unchanged in public-provider CI and future staged installed gates.

`test_pdbe_kb_acquisition_offline.py` covers both aggregate queries, native structural
scope and record/count bases, raw return parity, citation roles, original archive
times/wire identities, retries, empty/HTTP-not-found outcomes, unavailable and malformed
fixtures, unqueried offline access, processing failures and concurrent capture.
Card/refresh pins, stored-reader inactivity, provider failure and custom-client gaps
have guards. The file runs unchanged in public-provider CI and future staged gates.

`test_alphafold_acquisition_offline.py` covers model-list queries, native per-record
versions/identifiers, unknown latest versions, historical-version/URL/provider
declarations and citation roles. Original archive times/wire identities, retries,
empty/absent/unavailable/unqueried outcomes, unexpected envelopes, partial lists,
raw return parity, card/refresh pins, saved-reader inactivity, provider failure,
custom gaps and concurrent capture have guards. The file runs unchanged with the
public Ackredit floor in installed-provider CI and future staged gates.

`test_interpro_acquisition_offline.py` covers native family-site residue queries,
signature/member/position context, header/fixture releases (including zero/unknown),
resource-description roles, original archive time/wire/header reuse, transport retries,
empty bodies/objects/HTTP 204, ambiguous absence, HTTP 404 and original failures.
Missing/malformed fixtures, unexpected/partial signature shapes, raw parity,
card/refresh pins, inert saved readers, provider failure, custom-client gaps and
concurrent capture have guards. The file runs unchanged with the public Ackredit
floor in installed-provider CI and future staged gates.

Local diagnostic wheels additionally pass
`devtools/conda-build/check_local_wheel.py <exact-wheel>` before installation (#113):
module/resource bytes and membership must match the source, excluding generated
`_version.py`. The negative regression rejects stale, missing and ghost modules.
Clean local wheel receiving tests are diagnostic evidence, not public Conda delivery.

`test_persisted_pipeline_offline.py` launches independent producer, guarded reader
and reuse processes over `examples/persisted_pipeline/`. Historical full/index pins,
exact item support, native author/page citations, original versions, unavailable
fixture outcomes and reused credit survive reacquisition. A different reader
version and forbidden credit/source calls leave original records unchanged.
Missing/altered files, result/scope/item misbinding, workflow bibliography/context
loss and overwrite attempts are refused. Installed-provider and future staged lanes
copy the unchanged script and tests outside both checkouts; libraries are installed.

`test_oligomer_explanation_offline.py` checks public TcTIM/HsTIM view parity,
source assembly alternatives/methods, actual partner-class branches, exact family
members and agreement inputs, original versions (including zero/unknown), native
identity bases, selected/competing/conflicting support and qualifier alternatives.
Missing inputs, empty/failure/unqueried reports, unconfirmed numbering (#120),
historical card/item pins and detached inert readers have guards. The file runs
unchanged outside the checkout with public Ackredit in CI and future staged gates.
The #120 guards cover default confirmed-numbering agreement `@2`, incompatible
and missing sequence/indexing, qualifier conflicts, absent versus explicit empty
contacts, partial family scope, missing comparison inputs and exact ArgDigest
selectors. Explicit `@1` retains the legacy view/explanation at historical pins;
new full/index packets declare `@2` and saved packet payloads remain unchanged.
Stored card shape is unchanged.

## Independent-user journey acceptance (#112, after 0.13.0)

`tests/core/test_molecule_knowledge_state_offline.py` guards the #122 correction:
native molecular record/compound counts, unusable/unknown counts, true empty versus
missing/partial/failed/unqueried outcomes, separate identity/indication/study areas,
exact counting-report indexes, original version/support and inert pinned readers
after a new head. `knowledge_state@5` and `knowledge_state_explanation@2` change
derived output only; published cards and frozen packets keep their bytes/rules.
The file runs unchanged outside the checkout in installed-provider/staged gates.

`tests/core/test_user_journeys_offline.py` starts genuinely separate producer,
reader and reacquisition processes for `examples/user_journeys/protein_comparison.py`.
The reader has no fixture directory, uses a different reported Sabueso version,
and refuses new acquisition/composition/credit. Tests verify exact historical
card/deck/packet support, original reports, physical units, identity alternatives,
unmapped positions, partial RCSB fixture access and bibliography after reacquisition.
Missing/changed sidecars, mismatched comparison roles/report inputs/item pins and
overwrite attempts are refused. These are local example/SDK acceptance gates,
separate from installed-artifact and actual Nextia consumer qualification.

`tests/core/test_molecule_target_journey_offline.py` independently produces, reads
and reacquires `examples/user_journeys/molecule_target.py`. It verifies source-stated
ChEMBL/CCD identity, exact molecular/target/deck pins, assay context, IC50 and
single-point quantities, undetermined values, clinical indication support and
unfetched trials, source versions, unavailable fixture scope and original citations.
The reader refuses new acquisition, credit and scientific derivation. Missing
workflow files, mismatched trace/packet/molecular/item bindings and altered assay
statements are refused before export. Copy both example scripts when running
outside the checkout; this is local application bookkeeping, not a shared format.
`tests/core/test_disease_entities_journey_offline.py` starts separate producer,
reader and reacquisition processes for `examples/user_journeys/disease_entities.py`.
It preserves MONDO equivalence/unresolved EFO identity, target/drug metadata,
scores/phases, exclusions/caps, exact card/group support and original partial
runtime credit. Readers forbid acquisition, current-rule explanation and new
credit, and need no fixtures. Missing workflow files, changed membership/support,
wrong trace/member/item pins and overstated coverage fail before export.
Copy all three example scripts together outside the checkout. Its development `@2`
format checks native membership/input pins; `@3` adds MONDO observations and `@4`
adds Open Targets/Orphanet observations and pinned disease-build traces. Readers
keep original `@1`/`@2`/`@3`/`@4` reports and gaps readable. `@5` adds
DISEASES/ClinVar/MedGen observation; underlying study bibliography remains partial. Misbound deck traces fail before export.

`tests/core/test_disease_source_acquisition_offline.py` guards native Open Targets
pagination/order/counts/versions, partial later-page failure, invalid/null answers,
mixed-version/count refusal, full resource bibliography and host capture. Orphadata
cases guard original XML identity/time across memory/archive reuse, unknown origins,
SwissProt-index scope, validation pointers, fixture subsets and failed/unavailable/
unqueried access. Both sources keep portable credit and provider failures preserve
science. Disease-build cases verify exact input/support/deck/member pins, detached
copies, saved readers without acquisition/credit, failed resolution and custom-client
gaps. The unchanged file runs in installed-provider/staged lanes.

`tests/core/test_disease_lookup_acquisition_offline.py` adds 64 regressions for
DISEASES channel/file/index dates and unknown disk origins, native channel order
and scores, single-pass iterable inputs, fixture subsets and partial channel failure.
NCBI cases guard raw/normalized queries, build/update/accession version bases,
per-gene counts and caps, overlapping UIDs, complete native summaries, malformed
classification shapes, ambiguous/capped MedGen identity, missing/mixed fixtures,
partial later failures, archive reuse/replay and credential-free recorded metadata.
Original resource bibliography, host captures, provider failure and inert portable
readers are covered. The unchanged file runs outside the checkout in installed
provider lanes and future staged artifact gates.

`tests/core/test_disease_deck_support_offline.py` guards development disease rules
`@2`: complete native rows/order/counts/indication references, original MONDO and
member identity pins, kept/unbuilt/capped support, inert saved readers after new
heads, save-deck-only persistence and self-contained JSONL/SQLite reimport. Missing
or wrong support, rank/score disagreement and rewritten embedded input are reported
partial or refused atomically. Empty/failed source scopes and legacy metadata-only
decks remain readable without fabricated statements. Terms include embedded
sources; unsupported member-only admission is refused. The file runs unchanged
in installed-provider and staged gates.

`test_mondo_acquisition_offline.py` covers normalized term/equivalence queries,
native OBO versions and byte identities, checksum verification, index-memory and
archive reuse/replay, original scientific/runtime response times and unknown-origin
client-clock fallback,
fixture subset/absence scopes, retries and unavailable/unqueried/failed/unobserved
outcomes. Unknown versions/origins remain explicit. Complete resource bibliography,
concurrent host attribution, provider failure, original card/resolution pins and inert
saved reads have guards. The unchanged file runs in installed-provider/staged gates.

All three journey files and unchanged example scripts are copied into the installed
public-provider CI lane and the staged installed-package gate. Their local installed
SDK acceptance does not replace future remote matrix results for these workflow changes.

## Fixtures

`test_alphamissense_offline.py` qualifies the declared native HsTIM host discovery
and complete substitution CSV, independent prediction source assertions, original
score/class literals, missing versus zero values, unrecognized classes and unknown
score revisions. Negative cases guard discovery/accession/URL/sequence/version,
variant positions/reference/alternative, score bounds, duplicate rows and malformed
headers/widths before output caps. Artifact grid completeness stays separate from
returned-row truncation. Native empty/unavailable/failed/unstated access, separate
host/artifact acquisition and original-time archive replay are covered. Synthetic
negative rows qualify validation, not additional scientific source content.

`test_uniparc_offline.py` and `test_sequence_candidates_offline.py` guard single
raw/FASTA pre-access validation, native checksum/sequence/reference binding,
counts/caps, trusted continuation URLs, pagination drift/loops/partial failures,
page receipts, missing versus failed access and archive replay. Candidate tests
retain distinct equal-sequence entries, compare current full sequences, reject
redirected primary accessions, preserve historical associations and explicitly
leave isoforms unqueried. Exact taxonomy, independent check limits, original
assertion snapshots and detached raw records are covered. Pagination duplicates
use fictitious UniParc ids solely as adversarial synthetic parser scenarios;
the HsTIM public fixture is an unchanged native search body in a declared wrapper.

`tests/core/test_residue_tracks_offline.py` recovers the richer residue acceptance
scenarios: several providers/state definitions, type statistics versus position
tracks, dense/sparse zero and missing samples, units and original revision pins,
wrong subject/sequence/hash/numbering, explicit source/isoform sequence selection
and contradictory declarations. Native DisProt input stays on its original axis
even when strings match UniProt; AAindex literals remain type references. Detached
saved readers and Ackredit captures verify no mutation/acquisition/new credit.
Synthetic track inputs are parser/view scenarios, not qualified external responses.

Local development recovery additionally guards `load_source_snapshot` with all
supported formats/compression, original-byte digests, literal zero/empty values,
strict malformed-data rejection, detached metadata and no reader acquisition
credit. Literal HTML/TXT keep BOM/CRLF/whitespace, gzip failures are explicit
connector failures, and invalid UTF-8 is never repaired. Native FDA/iPTMnet
artifacts compare mapped fields/support with direct native input after shared
loading, while generic envelopes fail the native completeness gate.
`test_disprot_offline.py` uses a declared native public subset to guard
source/query binding, distinct DisProt sequence scope, bounds/counts/revisions,
unknown ontology terms, default subset scope, empty versus unavailable/failure,
original archive replay time and source acquisition. A 404 API route is failed
access, never biological absence. These are shared-environment local tests, not
new installed-package or automatic card-enrichment qualification.

- Fixtures are frozen public responses, saved as the source returns them (trimmed only
  when stated).
- Each set is declared in `temp_data/NOTICE.md`: source, what it holds, retrieval date
  and licence. A test checks the declaration.
- No private or pilot data, ever.
- Refetching a fixture can change counts in other tests. Update them as findings, not
  silently.

## Local checks and CI checkpoints

Select checks by the actual changed surface. Run every selected command on its
own and read its exit status. A short documentation or research-evidence commit
does not require the entire offline scientific suite. A change to public or
numerical behavior needs targeted regressions; run the full offline suite at
the next unskipped code checkpoint and inspect the CI run for that exact head.
If a changed area is not covered by a targeted test, add or identify a
meaningful guard before claiming it validated.

Use the relevant commands below:

```bash
ruff format --check .
ruff check .
python -m pytest -n 12 -m "not online" --receptor=llm
python tools/card_shape.py
python tools/source_registry.py --check
python tools/validate_schema.py
python devtools/moli_governance.py
python devtools/dependency_preflight.py
```

- Python code or tests: Ruff format/check and the affected pytest selectors;
  run the full offline suite before an ordinary code checkpoint is declared
  complete. Source, schema and quantity changes also need their specific
  guards and scientific regression cases.
- Source registry or generated source terms: `tools/source_registry.py --check`.
  Card-shape and schema changes: `tools/card_shape.py` and
  `tools/validate_schema.py`, plus the relevant tests.
- `AGENTS.md`, `MOLI_GUIDE.md` or governance files: `devtools/moli_governance.py`.
  Dependency metadata, Conda environments, recipes or CI acquisition:
  `devtools/dependency_preflight.py` and the relevant package/CI checks.
- Documentation and recorded evidence: validate changed links, examples and
  generated content as applicable; use the docs build below for `docs/` or
  docstring changes. Do not claim a scientific equivalence or package result
  merely because a document check passed.

Keep several exploratory commits local when remote visibility is unnecessary.
For now, `[skip ci]` is limited to authorized direct documentation/evidence
pushes whose applicable local checks pass and whose changes cannot affect
runtime behavior, test inputs, package contents or publication. Code changes
use an ordinary push; Sabueso has no accepted recovery route for skipped code
pushes. Do not use the marker on a PR head with required checks, release
candidate or publication route. A skipped run is not passing evidence.

When `docs/` or a docstring changes, also build the documentation, failing on any
warning. Use the environment of `devtools/conda-envs/docs_env.yaml`, with the checkout
installed:

```bash
sphinx-build -W --keep-going -b html docs <output directory>
```

The API reference renders module docstrings, so a malformed RST list in a docstring
fails this build.

- Run each selected gate on its own and read its result.
- Never pipe a gate through `tail` or `grep`, and never chain a commit after a command
  whose own exit code does not reflect the gate. Both have let a failure through before.
- After an unskipped push, verify CI by the exact commit SHA. Preserve local
  check results and mark deferred remote checks as pending until they run.

## Quality rules for knowledge

- Every selected field has at least one entry in `source_assertion_ids`, and every
  referenced id exists in the card's `source_assertion_store`.
- Relationships cite SourceAssertions present on the card.
- Quantities are stored as `{value, unit}` and sealed. The seal is verified on load.
- Derived knowledge carries its rule. A test fixes each rule's observable behaviour.

`test_disease_deck_admission_offline.py` checks all five use contexts, whole embedded
support, unused/unknown/per-record raw statements, non-commercial restrictions,
broken membership bindings (including another candidate's valid basis and a changed
resolved identifier with unrelated original support, #126), historical exclusions, empty/repeated admission and
current-registry changes. JSONL/SQLite exports and advanced-head store reads retain
exact original support and admission decisions without source access or new credit.
The unchanged file runs with its support fixture module outside the checkout in
public-provider CI and future staged installed-package gates. Finer filtering by terms of use
is deliberately refused rather than treated as completed admission.

`test_article_metadata_offline.py` guards explicit PMID/PMCID/DOI identity, core
bibliographic projection, full native authors, service-version/unknown article-revision
bases, original wire/archive reuse, raw publication-term retention, empty/failure/
unavailable/unqueried/partial outcomes and rejected ambiguity. Separate binding support,
alias/metadata alternatives, original receipt consistency, incomplete bibliography,
unknown fragment rights, original store/card refresh, exact full/index packet support,
inert readers, source-scoped citations, custom gaps, provider failure and concurrent
queries are covered. The file runs unchanged outside the checkout in public-provider
CI and future staged installed-package gates.

Development `test_ligysis_structure_mapping_offline.py` qualifies the unchanged
9185-byte native POST response and 14 separate directed/identity/remapping assertions.
Explicit heteromer/isoform/case declarations, signed labels, orphan/missing opposite
parents, non-bijective/conflicting maps, empty-versus-missing tables and detached
support survive. Late malformed/nonfinite tables, foreign identity/query/revision/
cuts, public argument rejection before access, unavailable/duplicate-key fixtures,
one read-only POST and zero-network archive replay with original time are guarded.
Use pytest-receptor with 12 workers in the existing editable Python 3.14 environment.

Development `test_channelsdb_membership_offline.py` qualifies original 26 channels,
910 layers and seven independent annotation references, all twelve source categories,
opaque/repeated tokens and IDs, MOLE/CAVER native bool/string and HetResidues quirks,
unequal residue/index arrays and empty versus missing groups. Late malformed/nonfinite
items, foreign source/query/kind/revision/cuts, public and skipped argument checks,
bound gzip/hash/time/terms, unavailable/duplicate-key files, one-GET acquisition and
zero-network archive replay with original support are covered. Use pytest-receptor
with 12 workers in the existing editable Python 3.14 development environment.

Development `tests/tools/test_bound_native_snapshots_offline.py` qualifies five
native-file pathways in plain/gzip form against their existing public fixtures and
mappers. It checks original compressed-byte SHA, receipt propagation/detachment,
caller metadata copying, declared versus unknown retrieval times, no remote access,
foreign source/kind/query/revision rejection before I/O, missing versus malformed
inputs, hash mismatch before decoding, duplicate JSON keys and native echoed
identity failures despite valid binding/hash. Run pytest-receptor with 12 workers
in the existing editable Python 3.14 development environment. Native source suites
and shared snapshot-loader tests remain applicable gates.
