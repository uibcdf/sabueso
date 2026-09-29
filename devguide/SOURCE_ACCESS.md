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
- `version` is None when the source states no release;
- arguments go through ArgDigest: `identifier`, `identifiers`, `client`, `limit`,
  `name`, `organism`, `include_subtaxa`, `species`, `required_score`;
- the functions are listed in `tests/core/test_argument_contracts_offline.py`, and
  their envelopes are tested in `tests/core/test_source_access_offline.py`.

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
3. Add the option and its client to `resolve_protein_card`, with their digesters.
4. Add fixtures, and a card in the card-shape builder.

`tests/core/test_enrichers_offline.py` checks the wiring: the parameters, the
digesters, the registry entry `in_use`, and the derived rows.

RCSB structures, the ChEMBL/BindingDB/PubChem BioAssay group and NCBI Gene stay
bespoke, for the reasons in the architecture document.

## Boundaries

- **MolSysMT.** Sabueso retrieves knowledge records, not coordinate files.
- **Licensing (#29).** Returning a record to the caller is fine. Storing or
  redistributing it depends on each source's terms.

## Possible future problems

- **Caching.** Sources have rate limits, and none of the clients caches. A cache must
  respect each source's terms (#29) and record what it served, and when.
- **Envelope drift.** The `record` of a source changes when the source changes its API.
  Mappings absorb that; direct users of `get_*` see it. The envelope is stable, the
  record is not.
