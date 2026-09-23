# Sabueso — Licensing and Compliance

## Sabueso's own licence
Sabueso's code is MIT (`LICENSE`). That licence covers the code, not the external data
Sabueso retrieves, caches or redistributes.

## External Data Sources
Some sources have license or access restrictions. These must be respected in:
- caching strategy
- redistribution of data
- packaging and distribution

## Sources in use
Verified on 2026-09-23 against each source's own statement. The retrieved records
themselves are not Sabueso's work and keep their source's licence.

| Source | Licence | Attribution | Notes |
| --- | --- | --- | --- |
| UniProtKB | CC BY 4.0 | UniProt Consortium | Stated in the entry's own `CC` lines |
| RCSB PDB / wwPDB (entries and Chemical Component Dictionary) | CC0 1.0 | not required | Crediting structure depositors is good practice |
| STRING | CC BY 4.0 | STRING (string-db.org) | |
| ChEMBL | **CC BY-SA 3.0 Unported** | EMBL-EBI / ChEMBL | Share-alike: see below |
| UniChem | EMBL-EBI adds no restrictions of its own | EMBL-EBI / UniChem | The rights of the resources it points to still apply |
| PubChem | US public domain (NLM policy) | NCBI / NLM | Depositor contributions may carry their own terms |

## Known Sensitive Sources
- **DrugBank**: data downloads are license‑controlled. Clinical datasets may be restricted.
  Sabueso currently holds DrugBank **identifiers only**, as UniChem cross-references. It
  does not retrieve or redistribute DrugBank content.
- **eMolecules**: data downloads may require license agreements.
- **ChemSpider**: API access requires a key and has usage conditions.
- **BioGRID** (uibcdf/sabueso#22): requires an access key; terms to be checked before use.

## Share-alike (ChEMBL)
ChEMBL is the only source in use with a share-alike clause, so it is the one to watch.

- ChEMBL records that Sabueso redistributes, including trimmed copies, are redistributed
  under CC BY-SA 3.0 with attribution. They are not relicensed as MIT.
- Sabueso's code is an independent work that reads those records, not an adaptation of
  them, so it stays MIT. A repository holding both is a collection of separately licensed
  works.
- A dataset **derived** from ChEMBL data would be an adaptation and would have to be
  shared under CC BY-SA 3.0. This matters if Sabueso ever ships precomputed cards, decks
  or a bundled store built from ChEMBL.
- This is a good-faith reading, not legal advice. Confirm the scope against ChEMBL's
  current statement before any release that redistributes larger extracts.

## Test fixtures
`temp_data/` holds frozen public responses used by the offline tests. They are
redistributed with the git repository, and each keeps its source's licence.

- `temp_data/NOTICE.md` lists, per fixture group: the source, its version or release, the
  retrieval date, the licence, the attribution, and any trimming applied. It must be
  updated whenever a fixture is added.
- Fixtures are kept trimmed to what the tests need: it limits both the size and the
  amount of redistributed data.
- They are **not** shipped in the Python distribution: packaging includes only the
  `sabueso` package (`pyproject.toml`, `[tool.setuptools.packages.find]`), and the sdist
  was checked to contain no `temp_data` file. Adding a `MANIFEST.in` or package data must
  not change that without revisiting this section.

## Compliance Principles
- Do not redistribute restricted datasets without permission.
- Store only what is required for reproducibility when licenses allow.
- Ensure any caching respects source terms.
- Record the licence and attribution of every source before adding a client for it, and
  the same for every fixture before committing it.
- Keep each source's version or release with the data (`source.version`,
  `temp_data/NOTICE.md`): attribution is only meaningful if it says which release.
