# Source access (uibcdf/sabueso#49)

Sabueso has three public layers:

1. **Source access** (`sabueso.tools.db.<source>`): raw records in a provenance envelope.
2. **Mappings** (`sabueso.mappings`): records become SourceAssertions and relationships.
3. **Cards and decks** (`sabueso.resolve`, `Card`, `Deck`): resolved knowledge.

## One module per source

Each module holds the source's clients and its public `get_*` functions: `uniprot`,
`rcsb`, `chembl`, `pubchem`, `interpro`, `pdbe_kb`, `pdb_ccd`, `unichem`, `stringdb`. Card
building uses the same clients, so there is one way to query each source.
`sabueso.resolver.uniprot_client` and `rcsb_client` are aliases until 1.0.

## Client protocol

- Two interchangeable clients per source:
  - `Online<Source>Client(timeout=30.0)` queries the service;
  - `Fixture<Source>Client(directory="temp_data", retrieved_at="fixture", failing=None)`
    reads saved responses from `<directory>/<source>/...`.
  - `failing` simulates a failing source for the given ids.
- Methods are named after what they return (`fetch_entry`, `bioactivities`, `molecules`,
  `components`, `compound`, `site_residues`, `ligand_sites`, `interface_residues`,
  `partners`, `search`). Each returns the record together with `retrieved_at`, and with
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
