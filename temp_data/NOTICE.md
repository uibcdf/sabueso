# Test fixtures: sources, versions and licences

The files in this directory are **frozen public database responses**, redistributed with
Sabueso so that its offline tests are reproducible. They are not Sabueso's own work.

Sabueso's code is MIT licensed (`LICENSE`). That licence does **not** apply to these
files: each keeps the licence of the source it came from, listed below. A repository
holding both is a collection of separately licensed works.

These fixtures are not included in the Python distribution (the wheel and sdist ship only
the `sabueso` package). They are distributed only with the git repository.

Where a fixture was trimmed to the fields the tests need, or wrapped in a small envelope
recording the release and retrieval time, it is a modified copy. It is redistributed
under the source's licence, and the modification is stated here and in the client that
wrote it (`sabueso/tools/db/`, `sabueso/resolver/`).

## Contents

| Files | Source | Version / release | Retrieved | Licence |
| --- | --- | --- | --- | --- |
| `P00938.json`, `P35372.json`, `P52270.json`, `P52789.json`, `P60174.json`, `P60175.json`, `Q6FHP9.json`, `V9HWK1.json`, `A0A140VJM9.json` | UniProtKB (UniProt Consortium) | release 2026_03 | 2026-09-23 | CC BY 4.0 |
| `uniprot_search/*.json` | UniProtKB search responses; refreshed with lineage and gene-locus cross-references, and the Trichomonas vaginalis search added, on 2026-09-25 (same release, same results) | release 2026_03 | 2026-09-23 | CC BY 4.0 |
| `alphafold/*.json` | AlphaFold DB (Google DeepMind and EMBL-EBI), prediction API responses | model version 6 | 2026-09-25 | CC BY 4.0 |
| `ncbi_taxonomy/*.json` | NCBI Taxonomy (NCBI/NLM), Datasets API taxon records, trimmed to id, name, rank, lineage and BLAST name | Datasets API 18.37.0 | 2026-09-25 | US public domain (NLM policy) |
| `bindingdb/*.json` | BindingDB, REST `getLigandsByUniprots` responses for P52270 and P60174 | — | 2026-09-25 | **CC BY-SA 3.0** (treated as such: BindingDB curation is CC BY 3.0, ChEMBL imports CC BY-SA 3.0, and records state no origin) |
| `pubchem_bioassay/*.json` | PubChem BioAssay (NCBI/NLM): assays linked to P52270 and P60174, their summaries, concise tables and the InChIKeys of their compounds | — | 2026-09-25 | US public domain (NLM policy); deposited data keeps its depositor's terms: these assays were deposited by ChEMBL (**CC BY-SA 3.0**) and BindingDB |
| `rcsb/*.json` | RCSB PDB (wwPDB archive), GraphQL entry data; assemblies added and 3Q37 retrieved 2026-09-24; all refetched with mutations, tags, unobserved residues, refinement and dates, and 2OMA, 2VOM, 4HHP and 4UNK added, 2026-09-25 | — | 2026-09-23 | CC0 1.0 |
| `pdb_ccd/*.json` | wwPDB Chemical Component Dictionary, served by RCSB PDB | — | 2026-09-23 | CC0 1.0 |
| `pdbe_kb/*.json` | PDBe-KB (EMBL-EBI), ligand binding sites (2026-09-23) and interface residues (2026-09-24) | — | 2026-09-23 | CC BY 4.0 |
| `interpro/*.json` | InterPro (EMBL-EBI), site residues from the CDD member database | InterPro 110.0 | 2026-09-23 | see note below |
| `string/*.json` | STRING | 12.0 | 2026-09-23 | CC BY 4.0 |
| `chembl/*.json`, `CHEMBL90555.json` | ChEMBL (EMBL-EBI); CHEMBL90555 added to `chembl/molecules.json` 2026-09-24 | ChEMBL_37 (released 2026-05-01) | 2026-09-23 | **CC BY-SA 3.0** |
| `unichem/*.json` | UniChem (EMBL-EBI); vincristine added 2026-09-24; lookups of the BindingDB monomers of the TIM fixtures by source id (`source31__<monomer>.json`) added 2026-09-25 | — | 2026-09-23 | see note below |
| `5978.json`, `66414.json` | PubChem (NCBI/NLM) | — | earlier | US public domain (NLM policy) |
| `2NZT.json` | RCSB PDB entry | — | earlier | CC0 1.0 |
| `frozen_cards/*.json` | Sabueso cards built from the fixtures above by a published release, kept to test that later versions still read them (#42). `schema_0.3.0__P52270.json`: the published conda package `sabueso=0.1.1` (uibcdf channel; card schema 0.3.0). `schema_0.3.1__P52270.json`: the release 0.2.0 candidate, built as its conda package and installed in a clean environment (card schema 0.3.1). Both were run on the UniProt, RCSB PDB and ChEMBL fixtures. `schema_0.3.2__P52270.json`: the release 0.3.0 candidate, built and installed the same way (card schema 0.3.2), run on the UniProt, RCSB PDB, ChEMBL, PDBe-KB and AlphaFold DB fixtures, with curated statements under a placeholder DOI (`doi:10.0000/frozen-card`) that claim nothing about the literature. `schema_0.3.3__P60174.json`: the release 0.3.1 candidate, built and installed the same way (card schema 0.3.3), run on the HsTIM UniProt, RCSB PDB, ChEMBL, PDBe-KB and AlphaFold DB fixtures, so that it holds AlphaFold models of isoforms. `schema_0.3.4__P52270.json`: the release 0.4.0 candidate, built and installed the same way (card schema 0.3.4), run on the TcTIM UniProt, RCSB PDB (every entry UniProt lists, with mutations, constructs and observed residues), ChEMBL (first 25 records), PDBe-KB, InterPro, AlphaFold DB, NCBI Taxonomy, BindingDB and UniChem fixtures. PubChem BioAssay is left out to keep the card small: its copies pull in every ChEMBL record they point to | — | 2026-09-24 | each part keeps its source's licence; the ChEMBL part is **CC BY-SA 3.0** |

Modifications: the ChEMBL activity and molecule fixtures keep only the fields the clients
request and drop the `molfile` block; the UniChem fixtures keep the compound's InChIKey,
UCI and source list. The RCSB entries hold the fields the structure query requests, including per-instance
ligand neighbours. The rest are verbatim responses, re-serialised as indented, key-sorted
JSON.

## Attribution

- **UniProtKB** — © UniProt Consortium, https://www.uniprot.org/terms, distributed under
  CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
- **RCSB PDB / wwPDB** — data files of the PDB archive are released under CC0 1.0
  (https://creativecommons.org/publicdomain/zero/1.0/). No attribution is required;
  crediting the depositors of each structure is good practice.
- **PDBe-KB** — PDBe-KB consortium, https://www.ebi.ac.uk/pdbe/pdbe-kb, CC BY 4.0, free for
  academic and commercial use. PDBe-KB asks users to cite the PDBe-KB consortium paper.
- **InterPro** — EMBL-EBI, https://www.ebi.ac.uk/interpro/. InterPro data is CC0 1.0, but
  InterPro notes that member-database signature collections may carry their own terms.
  The site residues in these fixtures come from **CDD** (NCBI), a U.S. government work
  under NLM policy, like PubChem.
- **STRING** — https://string-db.org, CC BY 4.0.
- **AlphaFold DB** — Google DeepMind and EMBL-EBI, https://alphafold.ebi.ac.uk, CC BY 4.0.
  Cite Jumper et al., Nature 2021 (AlphaFold) and the AlphaFold DB paper (Varadi et al.).
- **ChEMBL** — EMBL-EBI, https://www.ebi.ac.uk/chembl/, CC BY-SA 3.0 Unported
  (https://creativecommons.org/licenses/by-sa/3.0/).
- **UniChem** — EMBL-EBI, https://www.ebi.ac.uk/unichem/. EMBL-EBI adds no restrictions
  of its own beyond those of the original data owners, so the rights of the resources a
  UniChem record points to still apply. The fixtures hold cross-reference identifiers
  (for example a DrugBank accession), not the content of those resources.
- **PubChem** — NCBI/NLM. Works produced by the U.S. government are not subject to
  copyright in the United States; individual depositor contributions may have their own
  terms.

## ChEMBL share-alike

ChEMBL is the only source here with a share-alike clause. What it means in practice:

- The ChEMBL fixtures, including the trimmed copies, are redistributed **under CC BY-SA
  3.0**, with the attribution above. They are not relicensed as MIT.
- Sabueso's code is an independent work that reads these files. It is not an adaptation of
  ChEMBL data, so it stays MIT. The repository is a collection of separately licensed
  works, which CC BY-SA 3.0 allows.
- Anything that *is* an adaptation of ChEMBL data, such as a derived dataset built from
  these records, would have to be shared under CC BY-SA 3.0.
- Isolated factual values quoted in tests and reports (an IC50, a ChEMBL id, a compound
  name) are used to document measured behaviour.

This is a good-faith reading, not legal advice. Before a release that redistributes
larger ChEMBL extracts, or a dataset derived from them, confirm the scope with ChEMBL's
current licence statement.

## Adding a fixture

Add a row above with the source, its version or release, the retrieval date and the
licence. If the source is not already listed, check its licence and attribution first,
and record any restriction in `devguide/LICENSING_AND_COMPLIANCE.md`. Keep fixtures
trimmed to what the tests need.
