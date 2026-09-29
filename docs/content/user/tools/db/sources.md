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
| `alphafold` | `get_prediction(accession)` |
| `bindingdb` | `get_affinities(accession)` |
| `pubchem_bioassay` | `get_assays(accession)` |
| `ncbi_taxonomy` | `get_taxon(tax_id)` |
| `skempi` | `get_mutations(pdb_ids)` |
| `ncbi_gene` | `get_gene(gene_id)` |

Every function accepts `client=`. The default is the source's online client. Each module
also has a fixture client that reads saved responses, for offline work and tests, for
example `uniprot.FixtureUniProtClient("temp_data")`. Card building uses these same
clients, so there is one way to query each source.

- **Errors.** `RecordNotFoundError` means the source answered and holds no such record.
  `ConnectorError` means it could not answer. The two are never confused.
- **Network.** Every request names Sabueso in its user agent. A source that is briefly
  overloaded (HTTP 429, 502, 503, 504) or drops the connection is asked again, twice at
  most, waiting a little longer each time. A timeout is not retried.
- **Personal keys.** A source that asks for a key gets yours, never Sabueso's: pass
  `api_key=` to its online client, or set `SABUESO_<SERVICE>_KEY`. Sabueso sends the
  key only to its own service, and never writes it into a card, a record, a cache or a
  message. NCBI's key is optional (`SABUESO_NCBI_KEY`, for NCBI Gene, NCBI Taxonomy
  and ClinVar): it raises NCBI's rate limit and changes nothing in the answers. A source that needs a key it was not given is not
  asked; the card records it as not queried, with the reason.
- **Boundaries.**
  - Sabueso retrieves knowledge records: entries, annotations and metadata. It does not
    download coordinate files; loading structures belongs to MolSysMT.
  - Returning a record to you is fine. Storing or redistributing it depends on each
    source's terms (see *Licensing*).
