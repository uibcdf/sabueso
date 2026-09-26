# PDB DB Tools

Experimental structures are not Cards in Sabueso. They are `has_structure` relationships of
protein entities: use `sabueso.resolve(..., structures="all")` and `card.structures()`
({doc}`/content/user/structures`). The raw RCSB entry is `sabueso.tools.db.rcsb.get_entry`
({doc}`../sources`).

```{toctree}
:maxdepth: 1

fetch_pdb_json
```
