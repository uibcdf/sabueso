# Source access (uibcdf/sabueso#49)

Sabueso has three public layers:

1. **Source access** (`sabueso.tools.db.<source>`): raw records in a provenance envelope.
2. **Mappings** (`sabueso.mappings`): records become SourceAssertions and relationships.
3. **Cards and decks** (`sabueso.resolve`, `Card`, `Deck`): resolved knowledge.

## One module per source

Each module holds the source's clients and its public `get_*` functions:
- `uniprot`, `rcsb`, `pdb_ccd`, `pdbe_kb`, `interpro`, `alphafold`;
- `chembl`, `bindingdb`, `pubchem`, `pubchem_bioassay`, `unichem`;
- `stringdb`, `ncbi_taxonomy`, `ncbi_gene`;
- `phi_base`, whose online client works on versioned releases rather than an API
  (`CACHE_POLICY.md`);
- `clinicaltrials`, asked only for the NCT ids another source states (#81);
- `diseases` (DISEASES), whose channel files are versioned downloads, like `phi_base`;
- `open_targets`, GraphQL;
- `orphadata`, one dated XML file indexed in memory;
- `reactome`, the Content Service;
- `clinvar`, NCBI's E-utilities;
- `gnomad`, GraphQL.
Europe PMC additionally exposes `get_annotations(article_ids)` for explicit MED/PMC
articles. It keeps accession-number annotations with source-native locations and
quote fragments. Explicit card intake uses `europepmc={"article_ids": ...}`
(since 0.12.0, #92); the accession search keeps bibliography. Each located occurrence
has its own SourceAssertion, and its fragments remain governed by article terms.
Clients added since #82 name Sabueso over HTTP through `tools/db/_http.py`.
Card building uses the same clients, so there is one way to query each source. The
registry (`sources/registry.yaml`) must list each module as `in_use`, and a test checks
it.
`sabueso.resolver.uniprot_client` and `rcsb_client` are aliases until 1.0.

## Client protocol

- Two interchangeable clients per source:
  - `Online<Source>Client(timeout=30.0)` queries the service;
  - `Fixture<Source>Client(directory="temp_data", retrieved_at="fixture", failing=None)`
    reads saved responses from `<directory>/<source>/...`.
  - `failing` simulates a failing source for the given ids.
- Methods are named after what they return:
  - `fetch_entry`, `fetch_structure`, `search`;
  - `bioactivities`, `assay_activities`, `molecules`, `ligands`, `assays`;
  - `components`, `compound`, `compound_by_source`;
  - `site_residues`, `ligand_sites`, `interface_residues`;
  - `partners`, `prediction`, `taxa`, `gene`, and `version` where a source states its
    release. Each returns the record together with `retrieved_at`, and with
  the source release when the source states one.
- Errors:
  - `RecordNotFoundError`: the source answered and holds no such record;
  - `ConnectorError`: it could not answer (HTTP error, timeout, malformed response).

  Never a bare `urllib` exception, and never "not found" for a failure.
- Every request has a timeout.

## Public functions

`get_*(identifier | identifiers, ..., client=None)` returns
`{source, kind, query, retrieved_at, version, record}` (`tools/db/_record.py`):

- `record` is raw, as the source gave it;
- `version` is the original source-record version, or None when unstated; an entry
  version or service version is not a database release;
- arguments go through ArgDigest: `identifier`, `identifiers`, `client`, `limit`,
  `name`, `organism`, `include_subtaxa`, `species`, `required_score`;
- the functions are listed in `tests/core/test_argument_contracts_offline.py`, and
  their envelopes are tested in `tests/core/test_source_access_offline.py`.

## Required acquisition traceability (#108, moli#36)

Traceability is mandatory and automatic for supported boundaries. The first slice
released in 0.12.0 covers the built-in online and fixture clients for UniProt entry
and search, Europe PMC mentions and explicit article annotations, and RCSB
single/batch structure lookup. Since 0.13.0, Sabueso also observes ChEMBL
bioactivities, assay activities, molecules, indications and disease indications.
It also observes PubChem compound properties, structure matches and BioAssay target
rows with their summary/compound batches.
BindingDB REST, fixture and installed-mirror affinity queries are also observed.
PDB CCD component batches and UniChem InChIKey/source-id lookups are observed too.
PDBe-KB ligand-site and interface-residue aggregates are also observed.
AlphaFold DB model-list queries are observed with native per-model versions.
InterPro family-site residue queries are observed with native header/fixture releases.
`resolve_molecule_card` retains card/resolution traces; `ligand_deck` exposes detached
`Deck.acquisition_trace`, with its native snapshot, result card pins and input protein
pin. Ordinary deck operations and payload-only readers create no runtime trace.
Other sources and custom clients are explicitly `not_observed`; this is incomplete pipeline
coverage. New sources must declare their observation coverage and test its gaps.

The corresponding public envelopes add `acquisition_trace` outside the unchanged raw
`record`. `resolve`, `resolve_protein_card`, `EntityResolver.resolve` and
`refresh_card` attach independent runtime copies to `Card.acquisition_trace` and
`EntityResolution.acquisition_trace`, including resolutions returning no card.
`knowledge_packet` retains its observed intake in `KnowledgePacket.acquisition_trace`,
with the packet snapshot and card pins. Composition from existing cards does not
claim new intake. Exceptions escaping these wrappers retain `acquisition_trace`.
Direct client methods keep their original returns; a `sabueso.attribution()`
collector exposes their events in `run.acquisitions`, separately from completed
packet `run.records`.

The provisional local formats are `sabueso.acquisition_trace@1` and
`sabueso.source_acquisition@1`. A trace has an operation identity independent of
the scientific object, declared coverage, result status and original source events.
Successful card returns name the final card pin, including refresh history. Each
source event records source, operation, query, original executing package version,
start/finish times, original retrieval time and a source version with an explicit
basis (`entry_version`, `database_release`, `service_version`, `entry_revision`,
`per_entry_revision`, `model_version`, `per_model_version`, `response_header_release`,
`fixture_declared_release`, `not_stated`).
Decoded response identity uses canonical JSON (`response_identity.hash`); observed
HTTP bodies additionally retain their raw `response_sha256` and archive reference
where available. These are different identities. No whole raw response is copied
into the runtime trace. RCSB entries retain their
source-stated revision and primary-citation metadata.

Observed access is `network`, `fixture`, `reuse`, `replay`, `mixed` or explicitly
unobserved/not reached. Request records retain method, URL, request-body hash,
HTTP status, retry reasons and actual network-attempt counts. Archive reuse/replay
keeps original retrieval identities and times with zero new network attempts.
Outcomes distinguish `received`, `empty`, `not_found`, `unavailable`, `not_queried`,
`failed`, `partial` and `unobserved`. A missing fixture cannot establish source absence.
An unasked source has no event or usage credit. A partial failed annotation batch
retains completed transport records without claiming completed source access.

Completed access, including evaluated-empty/not-found answers and local replay,
contributes contextual resource use and bibliography to the enclosing application's
Ackredit capture. Failed/unqueried/unavailable access stays in the host trace with
`provider.status: not_attempted`. Provider or pin-recording failures emit SMonitor
diagnostics and explicit gaps, preserving the original scientific return/exception.
They never establish complete provenance. References do not establish reuse rights.

Applications save original JSON traces beside scientific objects. Card/packet
serialization, hashes, schemas and knowledge-store formats remain unchanged;
payload-only saved readers have `acquisition_trace is None` and add no credit.
There is no implicit journal, project destination or Recorda integration. MOLI
owns future ProjectRecord routing/correlation and recording reliability policy.
RCSB logical batches own all chunks and fallback requests. Their `entries` preserve
per-entry outcomes, native revision metadata and primary citations; `completed_ids`
bounds successful-access credit, including empty and partial received entries.
Unknown entry revisions remain unstated, not an invented database release.
Identical primary metadata reuses a reference; different stated forms retain
separate identities without overwriting earlier citations. Missing citation fields
are explicit gaps. See `docs/content/user/attribution.md` for verified metadata sources.

InterPro observes `site_residues`, the existing protein-scoped family-site query,
not the complete domain/family catalog. `InterPro-Version` is a response-header
release; fixture `version` is a fixture-declared release. Missing releases remain
unknown, and no member/signature version or independently consulted UniProt release
is inferred. Archive reuse/replay preserves the original header, retrieval time
and decoded/wire identities, with no network attempts.

Returned signature keys, native accession/name/member-database forms, location
records and declared fragments retain source scope. Counts measure signature
records, not mapped family sites or validated protein identity. Invalid signature
records remain unobserved or partial, with actual received-subset credit. Signature
receipt does not validate downstream mapping. Source-provided sequence positions
do not imply a local alignment, InterProScan execution or member-database access.

Empty objects/bodies and HTTP 204 preserve the existing evaluated-empty contract;
HTTP 404 remains not-found. Neither proves whether the source knows the accession
or simply states no sites. Missing fixtures are unavailable, offline access is
unqueried, and failures keep their original exceptions. Unexpected decoded envelopes
do not establish completed annotation credit. Resource-description bibliography is
verified separately; member/signature/site citations and rights are not supplied
by this operation. Scientific mapping, payloads, schema and inert saved readers
remain unchanged. `test_interpro_acquisition_offline.py` runs unchanged in installed
public-provider and future staged gates.

Chemical identity access remains source-scoped: CCD's `components` event materializes
its normalized identifier batch once, including generator inputs, and retains each
requested component's `received`, `empty`, `unavailable` or failed/unqueried outcome.
Successful network omissions are evaluated-empty; missing fixture files are local
unavailability. `completed_ids` bounds completed access, including evaluated-empty
network entries but never unavailable/failed ones. Received subsets survive later
GraphQL/fixture processing failures as partial while the original exception escapes.

UniChem's `compound` and `compound_by_source` events retain POST/query identities,
native compound/source-record forms and the existing first-returned-compound
selection basis. Linked source ids/names/records do not establish direct access to
those providers. A decoded empty answer or declared empty source fixture is distinct
from a missing file. Both resources keep source versions explicitly unstated; CCD
release status/dates and UniChem compound ids do not become database release versions.
CCD/RCSB-distribution and UniChem resource descriptions are verified separately.
Original identity policies, mappings, raw returns/exceptions and card/deck schemas
are unchanged. `test_chemical_identity_acquisition_offline.py` covers this slice,
also copied unchanged into public-provider and future staged receiving gates.

PDBe-KB observes `ligand_sites` and `interface_residues` as separate protein-scoped
aggregate queries. Native response/wire/archive identities, original retrieval times,
retries, evaluated-empty/HTTP-not-found answers, fixture unavailability and failures
remain distinct. Decoded unexpected envelopes retain their receipt and original
processing failure without completed-data credit. Versions remain `not_stated`;
neither a PDB identifier nor the query's UniProt accession is a release version.

Each returned group keeps its zero-based original response index, native accession,
name/type, numbering kinds, residue-record count and decoded identity. Listed PDB ids,
all mapped PDB ids and interacting PDB/entity/chain forms remain separate. The count
is returned aggregate groups, not mapped relationships or validated identities.
An omitted/null aggregate `data` field has an explicitly unknown count; a returned
empty record/list remains empty under the existing source-client contract.
These are PDBe-KB statements, not additional access to UniProt, PDB entries, PISA
or annotation providers. The verified PDBe-KB resource description does not replace
underlying structure/method/provider citations; their missing metadata is explicit.
No runtime bibliography lookup is added. Existing maps, raw returns/exceptions,
card/refresh pins and saved-reader behavior remain unchanged. See
`tests/core/test_pdbe_kb_acquisition_offline.py`, also copied unchanged into installed
public-provider and future staged gates.

AlphaFold DB's `prediction` event retains each native model-list index and both
`entryId`/`modelEntityId` forms; its reference choice names the existing mapping's
basis, without inventing equivalence between different identifiers. Native
`latestVersion`, including zero when stated, is retained per record. Missing latest
versions remain unknown even when `allVersions` lists historical versions; those
older models were not queried. Repeated ids keep separate indexed versions. Model,
sequence and creation dates are not global database versions or experimental revisions.

The trace retains native tool/provider, accession/range/checksum and artifact URL
metadata without copying sequences or downloading coordinates, confidence files or
MSAs. Listed providers/UniProt were not separately consulted, and a declared
generation tool does not claim a local prediction execution. The three verified
resource/background citations follow the database's recommendation; they do not
prove each returned model's method or replace missing provider/model-specific citations.

Requests, original response/wire/archive identities and times, retries, evaluated
empty lists, HTTP absence, fixture unavailability, offline unqueried access and
original failures stay distinct. Unexpected non-list envelopes are unobserved,
preserving original client returns/exceptions without completed-model credit.
Partially invalid lists retain received subsets and incomplete context; original
public processing failures still escape with their trace. Counts measure returned
records, not mapped relationships or validated identities. Card maps/schemas,
experimental/predicted separation, refresh pins and inert saved reads remain fixed.
`tests/core/test_alphafold_acquisition_offline.py` exercises the slice unchanged
in installed public-provider CI and future staged gates.

Regression tests are in `tests/core/test_source_acquisition_offline.py` and
`tests/core/test_rcsb_acquisition_offline.py`; the public
installed-consumer workflow is `examples/ackredit_pilot/`.

ChEMBL's adapter (since 0.13.0) retains normalized logical queries, all transport
requests, pagination/chunks, caps, decoded page identities and original document
citation forms. A failure after received content pages is `partial`, with those
pages in `completed_pages`; the original exception still escapes. Completed subsets
receive contextual credit without claiming the whole operation succeeded. Missing
fixture datasets are `unavailable`, even where the original fixture API returns an
empty mapping. An empty logical identifier batch is `not_queried`.
The database release is the client's reported ChEMBL version. Its origin distinguishes
status responses, fixtures and the existing client cache; it is explicitly not
verified independently for each page. Cached release metadata must not be read as
proof that every reused page belongs to that release. Native document metadata is
preserved without DOI enrichment; missing authors and indication bibliography stay
explicit gaps. `tests/core/test_chembl_acquisition_offline.py` covers this boundary.

PubChem's adapter (since 0.13.0) observes built-in online and fixture `compound`,
`structure` and BioAssay `assays` operations. Compound properties and structure
matches declare `source_version: {value: null, basis: not_stated}`. BioAssay retains
native `Version`, `Revision` (including zero) and `LastDataChange` per received assay
summary; these are assay revisions, never a global database release or proof of the
version of every CSV row/compound property. Incomplete revision pairs remain unknown.

Decoded response identities and transport records preserve POST-body identities,
CSV rows for the requested target, summary/property chunks, row-order rules and
caps. A later batch failure retains received pages and their PubMed pointers as
`partial`, with the terminal outcome and original exception; its count explicitly
means received target rows before completion. Received empty rows, HTTP absence,
rejected structure input, unavailable fixtures and unqueried offline access remain
distinct. Rejected input is not credited as completed source-data access. No raw
scientific return or exception is changed.

PubChem's verified resource description is separate from measurement PubMed pointers.
Missing pointer metadata and depositor bibliography remain explicit.
Pointer citations use content-based identities, so an incomplete source pointer
cannot replace a fuller host citation under the same PubMed publication identifier.
Its original publication id remains in the trace and bibliography-gap record.
`SourceName` and `SourceID` do not imply direct access to that depositor. Full native summary
forms remain on observed response pages. Stored readers add no credit. Coverage is
tested by `tests/core/test_pubchem_acquisition_offline.py`, also copied unchanged
into installed-provider and future staged-artifact gates. Cards and schema are unchanged.

BindingDB's adapter (since 0.13.0) retains accession/cutoff/limit, the applied
`bindingdb_record_order@1`, totals/caps, native response identities, retries and
original DOI/PubMed pointer forms. Successful REST and fixture responses state no
global version. The cutoff is recorded as `{value, unit}` in `cutoff_scope`, with
its application basis: submitted to REST, applied to the mirror index, or not
reapplied by the existing fixture client. Fixture selection behavior is unchanged.

`MirrorBindingDBClient.ligands` is observed as `access: mirror` without HTTP
requests or network attempts. Its release comes from the installed manifest, which
is retained with its original URL, checksum, installation time and a content hash.
This is client-manifest metadata, not live REST/version proof or independent index
integrity verification. `retrieved_at` retains the client's installation-time basis;
`started_at`/`finished_at` identify the current query. Mirror installation/update and
client-constructor failures remain outside this query boundary.

Decoded empty answers, absent fixtures, offline-unqueried queries and failures
remain distinct. HTTP errors preserve BindingDB's native `ConnectorError`; a 404
is not reinterpreted as record absence. Received data that fails local processing
is `partial`, retaining the response identity and count basis before completion.
Corrupt mirror reads retain known manifest metadata but get no completed-access
credit. Saved readers add no credit. Card payloads, source mappings and schema are
unchanged.

Publication pointers use content-based citation identities, preserving differing
source forms and fuller host references. Missing title/authors/year remain explicit;
no DOI enrichment is performed. The verified BindingDB resource description is a
separate citation. REST measurement origins remain unknown; the mirror's declared
`data_source` is preserved without claiming that imported providers were consulted.
The source-local parser fix (#114) treats an exactly empty HTTP 200 body, a JSON
empty string and decoded empty affinity lists as evaluated-empty access. Only this
client opts into an empty body in the shared JSON transport; other clients keep
their unreadable-body retries. Whitespace-only bodies, malformed JSON, unexpected
nonempty payloads and HTTP errors remain failures. Original wire hashes, archive
identities and retrieval times are retained, including replay and saved fixtures.
The official REST documentation declares an empty string; a public no-match probe
on 2026-10-04 returned HTTP 200 with the native empty affinities array. Compatibility
tests exercise the documented string forms synthetically, not as a claimed live outage.
See `tests/core/test_bindingdb_acquisition_offline.py`, also run unchanged in
installed-provider CI and future staged gates.

## Deprecated (removed before 1.0)

Each warns with `DeprecatedUsageWarning` (`SABUESO-W-DEPRECATED-001`, also a
`FutureWarning`) and still works:

- `fetch_uniprot_json`, `fetch_chembl_json`, `fetch_pubchem_json` and
  `tools.db.pdb.fetch_pdb_json`: use `get_*`;
- `create_protein_card_online`, `create_molecule_card_online` and
  `create_compound_card_online`: use `sabueso.resolve`, which takes `pubchem:<cid>`
  since #50.

`create_*_card_from_json` and `create_*_card_from_file` stay, for offline work and tests.

## Enriching cards (#86)

A source that adds knowledge to cards declares an enricher in `sabueso/enrichers/`
(`devguide/SOURCE_ARCHITECTURE.md`). The declaration has:
- the option and source name;
- the registry id;
- the knowledge areas it answers;
- the organisms it covers;
- `requests`, `fetch` and `map`.

The runner applies what every source needs: coverage (`not_applicable`), `not_found`
and `error` per request, and a fixed order. The knowledge-state rows and the migration
map are derived from the declarations.

To add one:
1. Write the client, the `get_*` function and the mapping, as above.
2. Write the enricher, and register it in `ENRICHERS` in the order it runs.
   `stage` places it among the bespoke enrichments; new sources use the default,
   `after_bioactivity`.
3. Add the option and its client to `resolve_protein_card`, with their digesters.
4. Add fixtures, and a card in the card-shape builder.

`tests/core/test_enrichers_offline.py` checks the wiring: the parameters, the
digesters, the registry entry `in_use`, and the derived rows.

RCSB structures, the ChEMBL/BindingDB/PubChem BioAssay group and NCBI Gene stay
bespoke, for the reasons in the architecture document.

Before designing a client, survey the server's own programmatic access: batch queries
(RCSB GraphQL `entries`), per-target queries (PubChem `assay/target/accession`), bulk
release files, usage policies and throttling headers. Test them live, and check that a
faster route keeps a stated identity (#98).

Every client uses the shared services in `sabueso/tools/db/`:
- `_http.urlopen`, never `urllib.request.urlopen`, for the user agent and the retries
  (a test checks it). A request that reads JSON passes `expect_json=True`, so that an
  unreadable 200 answer is asked again (#97). Leave it out where an empty or non-JSON
  body is an answer (InterPro's empty body, Reactome's plain-text version);
- `_http.gather`, for a service answered one record per request, with the pace its
  online client states (`workers`, `per_second`); saved answers need none (#98);
- `_release`, for a source published as whole releases;
- `_keys`, for a source that takes a personal key. A client that needs one calls
  `_keys.required(...)` when asked, and the runner records `not_queried` if the key is
  missing. A key never goes into a record, a message or a cache.

## Boundaries

- **MolSysMT.** Sabueso retrieves knowledge records, not coordinate files.
- **Licensing (#29).** Returning a record to the caller is fine. Storing or
  redistributing it depends on each source's terms.

## Possible future problems

- **Caching.** Sources have rate limits, and no client caches on its own. Reuse goes
  through the retrieval archive the user asks for (`reusing(max_age)`, #100), which
  records what it served and when; what may be kept follows each source's terms (#29).
- **Envelope drift.** The `record` of a source changes when the source changes its API.
  Mappings absorb that; direct users of `get_*` see it. The envelope is stable, the
  record is not.

## Explicit article metadata acquisition (since 0.13.0, #92/#108)

Europe PMC `get_article(identifier)` explicitly queries REST search with `resultType=core`
using EXT_ID + SRC:MED, PMCID or DOI. The returned projection includes native identifiers,
title, full returned author records, journal/date/pages, licence/open-access declarations
and native URL/reference forms. It excludes `abstractText` and never follows a full-text
URL. Official endpoint semantics: <https://europepmc.org/RestfulWebService>.
Multiple matching records and a capped/incomplete answer remain visible; fragment
binding refuses absence, ambiguity and missing source-stated publication identity.

Queries retain service-version basis (not article revision), wire/decoded/archive
identities, original times, retries, explicit empty/HTTP-absence/failed/unavailable/
unqueried outcomes, received subsets and original per-result/portable references.
The bibliographic projection's exact field set is `core.article_metadata.FIELDS`.
Unknown native author/year/journal/page fields remain citation gaps; no secondary
lookup or inferred alias fills them. Saved raw core answers may contain abstracts;
existing `PUBLICATION-TERMS` raw retention stays unchanged. Metadata is explicit
support for supplied-fragment intake, not an automatic card enrichment or new article
coverage claim. No enricher/bulk/knowledge-packet request is added.
