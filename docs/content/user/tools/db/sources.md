# Source access

Each database has a module in `sabueso.tools.db` whose `get_*` functions return the record
**as the source gives it**, inside a provenance envelope. You don't need to build a card:

```python
from sabueso.tools.db import uniprot, rcsb, chembl

entry = uniprot.get_entry("P60174")
print(entry["source"], entry["kind"], entry["version"], entry["retrieved_at"])
print(entry["record"]["primaryAccession"])  # the raw UniProt JSON

structure = rcsb.get_entry("1SUX")  # the entry data Sabueso maps (not coordinates)
activities = chembl.get_bioactivities("CHEMBL4880", limit=100)
```

Every function returns `{source, kind, query, retrieved_at, version, record}`:

- `query` is what was asked;
- `retrieved_at` is when;
- `version` is the source release, when the source states one (UniProt entry version,
  ChEMBL release, InterPro and STRING versions);
- `record` is the raw record. Turning it into knowledge (SourceAssertions, cards) is the
  job of the mappings and of `sabueso.resolve`.

| Module | Functions |
|---|---|
| `uniprot` | `get_entry(accession)`, `search(name, organism, include_subtaxa=False)` |
| `rcsb` | `get_entry(pdb_id)` |
| `chembl` | `get_bioactivities(target, limit)`, `get_molecules(chembl_ids)` |
| `pubchem` | `get_compound(cid)` |
| `interpro` | `get_site_residues(accession)` |
| `pdbe_kb` | `get_ligand_sites(accession)`, `get_interface_residues(accession)` |
| `pdb_ccd` | `get_components(codes)` |
| `unichem` | `get_compound(inchikey)` |
| `stringdb` | `get_partners(identifier, species, required_score, limit)` |

Every function accepts `client=`. The default is the source's online client. Each module
also has a fixture client that reads saved responses, for offline work and tests, for
example `uniprot.FixtureUniProtClient("temp_data")`. Card building uses these same
clients, so there is one way to query each source.

- **Errors.** `RecordNotFoundError` means the source answered and holds no such record.
  `ConnectorError` means it could not answer. The two are never confused.
- **Boundaries.**
  - Sabueso retrieves knowledge records: entries, annotations and metadata. It does not
    download coordinate files; loading structures belongs to MolSysMT.
  - Returning a record to you is fine. Storing or redistributing it depends on each
    source's terms (see *Licensing*).
