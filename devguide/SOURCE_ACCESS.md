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
(unreleased, #92); the accession search keeps bibliography. Each located occurrence
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
in development covers the built-in online and fixture clients for UniProt entry
and search, Europe PMC mentions and explicit article annotations, and RCSB
single/batch structure lookup. Other sources and custom clients are explicitly `not_observed`; this is incomplete pipeline
coverage. New sources must declare their observation coverage and test its gaps.

These five public envelopes add `acquisition_trace` outside the unchanged raw
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
`per_entry_revision`, `not_stated`).
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

Regression tests are in `tests/core/test_source_acquisition_offline.py` and
`tests/core/test_rcsb_acquisition_offline.py`; the public
installed-consumer workflow is `examples/ackredit_pilot/`.

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
