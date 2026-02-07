# Sabueso — Sources and Verified Fields

## Minimum Sources (Agreed)
- UniProt
- PDB (RCSB)
- ChEMBL
- PubChem
- eMolecules
- ChemSpider
- DrugBank

## Priority Classification (Current)
High priority:
- UniProt
- PDB (RCSB)
- ChEMBL
- PubChem
- DrugBank
- GO Consortium
- InterPro
- STRING
- BioGRID

Medium priority:
- CATH
- SCOPe
- TED
- PhosphoSitePlus

Low priority:
- eMolecules
- ChemSpider
- iPPI-DB
- PiSITE
- IUPAC
- CPPsite

Note:
- CPPsite is a specialized source relevant for **cell‑penetrating peptides (CPPs)** and should be mapped to PeptideCard when included.

## Verified UniProt Examples
- UniProt IDs used for JSON verification:
  - P52789
  - P35372
  - A0A140VJM9

Local JSON files (used for verification in this repo):
- `temp_data/P52789.json`
- `temp_data/P35372.json`
- `temp_data/A0A140VJM9.json`

From these JSONs we confirmed:
- `commentType` values (FUNCTION, CATALYTIC ACTIVITY, PATHWAY, etc.)
- positional features (Active site, Binding site, Modified residue, etc.)
- extensive cross‑reference lists (PDB, ChEMBL, DrugBank, IntAct, BioGRID, etc.)

Verified enumerations are recorded here:
- `devguide/UNIPROT_ENUMS.md`

## Verified PDB Examples
- PDB IDs:
  - 1TCD
  - 2BQV

Confirmed presence of:
- entry metadata (classification, method, resolution, deposit/release dates)
- primary citation
- entity metadata (chains, sequence lengths)

## Clinical Data Sources (DrugBank)
Clinical data is planned as a dedicated layer:
- pharmacology
- ADMET
- clinical trials
- pharmacovigilance
- indications
- contraindications
- interactions

## Notes
- The schema must preserve all values and attach them to evidence objects.
- Cross‑references to external databases are expected and should be stored in `identifiers` and/or `annotations` sections.
