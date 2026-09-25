# Data Sources Status (Implemented)

This document is a living checkpoint of the data sources (DBs) currently integrated in Sabueso. It summarizes the quality of each source integration, known issues, and operational notes (online/offline behavior).

## Legend
- **Status**: implemented / partial / paused
- **Access**: online API / dump (remote) / local file
- **Quality**: green (stable), yellow (works with caveats), red (broken)
- **Notes**: incidents, timeouts, missing fields, or skipped tests

---

## Protein / Structure / Chemistry

### UniProt
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green for the listed coverage. Offline tests on five fixtures, including HsTIM (P60174) and TcTIM (P52270), compare mapped counts against the raw records (uibcdf/sabueso#13).
- **Coverage**:
  - identifiers, canonical name, organism;
  - free-text comments: function, pathway, subunit, tissue specificity, PTM, polymorphism;
  - catalytic activity as `{reaction, ec_number, rhea_id, molecule?}`;
  - subcellular location as `{location, topology?, orientation?, molecule?}`;
  - sequence: primary, length, molecular weight in Da, CRC64/MD5 checksums;
  - positional features: binding and active sites, modified residues, disulfide bonds, glycosylation, natural variants and mutagenesis (substitution, verbatim description, `VAR_` id and cross-references; uibcdf/sabueso#33);
  - PDB cross-references as `has_structure` relationships (method, resolution, chains, UniProt-numbered ranges, coverage), shown through `Card.structures()`;
  - GO cross-references as `annotated_with` relationships (aspect, term, GO code, assigned by; ECO in `source_metadata`);
  - InterPro, Pfam, Gene3D (CATH), SUPFAM, PANTHER, PROSITE and CDD cross-references as `classified_in` relationships;
  - curated INTERACTION comments (IntAct binary interactions) as `interacts_with` relationships;
  - UniProt evidence qualifiers kept per SourceAssertion as `source_metadata.eco`.
- **Known limits**:
  - other comment types (disease, alternative products, similarity, …) and feature types (sequence conflict, cross-link, chain, secondary structure) are not mapped;
  - the stated effect of a variant or mutagenesis is free text, kept verbatim: "thermolabile" or "abolishes ligand binding" is not turned into a category;
  - isoform restrictions (`molecule`) are recorded for catalytic activity and subcellular location, but not for free-text comments;
  - identical repeated values in one record share one SourceAssertion id.
  - INTERACTION comments are UniProt's curated subset of binary interactions: 3 for human TIM, while its IntAct cross-reference reports 75. Full interaction data would need IntAct, STRING or BioGRID directly.
- **Notes**: stable online tests

### RCSB PDB — polymer-entity mapping (GraphQL)
- **Status**: implemented (uibcdf/sabueso#6, step 4b)
- **Access**: online GraphQL (`OnlineRCSBClient`), saved entries (`FixtureRCSBClient`, `temp_data/rcsb/`)
- **Quality**: green for the listed coverage, verified on 1HTI, 1KLG and 1TCD
- **Coverage**:
  - `has_structure` relationships per UniProt accession aligned to polymer entities: chains, UniProt-numbered ranges, method, resolution;
  - polymer entities, the other entities present, and bound ligands;
  - structure facts keep `pdb:<id>` as SourceAssertion subject;
  - `EntityResolver` resolves `pdb:<id>` to the structure record and its proteins.
- **Notes**: one request per entry. Each ligand carries its per-instance neighbour residues (`rcsb_ligand_neighbors`), mapped to UniProt numbering through the entity alignment. Ligand lists include every non-polymer entity (buffers and solvents too). Each ligand carries the PDB "subject of investigation" flag and its provenance (`Author`, or `RCSB` for older entries), which `ligand_deck` uses by default (uibcdf/sabueso#25, item 3). RCSB returns entities in no fixed order, so the mapping sorts them.

### PDB (RCSB) — entry metadata cards (removed)
- **Status**: removed 2026-09-23 (uibcdf/sabueso#21)
- **Notes**:
  - `create_structure_card_*` and `mappings/pdb.py::map_structure` built one card per PDB entry, typed as a protein, with scalar `structure.entry_metadata.*` fields. That was a structure card in all but name, contrary to the decision "no StructureCard" (#6, #20).
  - Structures are now `has_structure` relationships (see *RCSB PDB — polymer-entity mapping* above and the UniProt coverage).
  - Entry title, dates and primary citation are not mapped at the moment. They can return as structure-subject SourceAssertions shown in `Card.structures()` when a real need appears.
  - `tools/db/pdb.py::fetch_pdb_json` (raw REST entry) remains.

### PubChem
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: formula, MW, isomeric SMILES (`identifiers.smiles`) and connectivity SMILES (`identifiers.smiles_connectivity`), InChI/InChIKey, XLogP3, TPSA, HBD/HBA, rotatable bonds; PubChem compounds are InChIKey-anchored like any small molecule (uibcdf/sabueso#25)
- **Notes**: PubChem's `SMILES` (formerly `IsomericSMILES`) keeps stereochemistry and `ConnectivitySMILES` (formerly `CanonicalSMILES`) does not; the isomeric one used to be dropped (uibcdf/sabueso#10). XLogP3 and rotatable bonds carry their method. Stable online tests.

### ChEMBL
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: identifiers, preferred name, molecule type, formula, physchem (ALogP, HBD/HBA, TPSA, rotatable bonds, aromatic rings, molecular weight as `full_mwt`), `max_phase`, InChI/InChIKey, isomeric SMILES
- **Notes**: numbers ChEMBL serialises as strings are normalized; logP and rotatable bonds carry their method (`ALogP`, `chembl:rtb`) and are compared only within it (uibcdf/sabueso#10). Stable online tests.

### ChEMBL bioactivities
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#23)
- **Access**: online API (`OnlineChEMBLClient`), saved responses (`FixtureChEMBLClient`, `temp_data/chembl/`)
- **Quality**: green for the listed coverage, verified on TcTIM (CHEMBL5834) and HsTIM (CHEMBL4880), ChEMBL_37
- **Coverage**: `has_bioactivity` relationships, one per activity record. They carry the measurement, the assay (with target-assignment confidence and assay organism), the document, the tested and parent molecule, and the ChEMBL release (`source.version`). `Card.bioactivities()` gives derived activity classes.
- **Notes**:
  - The target comes from the ChEMBL cross-reference of the UniProt entry. Complex or family targets are not included.
  - Homology-assigned assays (relationship type `H`) are excluded from the default view and reported. Every HsTIM Ki in ChEMBL was measured on rabbit TIM or on TIM of unknown organism.
  - The test concentration of single-point measurements is extracted from the assay description (derived).
  - About 2 KB per measurement. `limit` (default 5000) and truncation are recorded (card size: uibcdf/sabueso#19).
  - Report: `devguide/archive/chembl_bioactivities.md`.
- **Molecules** (`molecules(ids)`, batched): identity (standard InChIKey, hierarchy), `max_phase` and the ChEMBL-asserted properties, for SmallMoleculeCards anchored at the InChIKey (uibcdf/sabueso#25). Fixture: `temp_data/chembl/molecules.json` (275 parent molecules measured on TcTIM or HsTIM).

---

## Interaction Sources

### PDB Chemical Component Dictionary (CCD)
- **Status**: implemented for small-molecule identity (uibcdf/sabueso#25)
- **Access**: RCSB GraphQL `chem_comps` (`OnlineCCDClient`), saved records (`FixtureCCDClient`, `temp_data/pdb_ccd/`)
- **Quality**: green for the listed coverage, verified on BTS, PGA and SO4
- **Coverage**: name, formula (normalized), type, standard InChI/InChIKey (`identifiers.inchi`, `identifiers.inchikey`), and a `same_as` link of `pdb.ligand:<code>` to the InChIKey anchor
- **Notes**:
  - RCSB omits unknown codes from a batch without an error. The client reports them as `missing`.
  - CCD SMILES are kept in the assertion, not in `identifiers.smiles` (a different representation from ChEMBL's; uibcdf/sabueso#10).
  - `ligand_deck` keeps, by default, only the structure ligands the PDB declares subject of investigation (item 3 of #25).

### UniChem
- **Status**: implemented for small-molecule identity (uibcdf/sabueso#25)
- **Access**: REST `compounds` by InChIKey (`OnlineUniChemClient`), saved compounds (`FixtureUniChemClient`, `temp_data/unichem/`)
- **Quality**: green for the listed coverage, verified on BTS (UCI 336651) and 2-phosphoglycolate (UCI 118810)
- **Coverage**: `same_as` links to the InChIKey anchor for ChEMBL, PDB (RCSB and PDBe), PubChem, DrugBank, ChEBI and BindingDB records. The full source list stays in the assertion.
- **Notes**: an unknown key returns HTTP 200 with `"Not found"`, which the client maps to not found. One call per molecule, so it is opt-in for decks.

### AlphaFold DB — predicted structures
- **Status**: implemented as an enricher of `resolve_protein_card(..., predicted_structures=True)` (uibcdf/sabueso#57)
- **Access**: AlphaFold DB API `prediction/<accession>` (`OnlineAlphaFoldClient`), saved responses (`FixtureAlphaFoldClient`, `temp_data/alphafold/`), and `tools.db.alphafold.get_prediction`
- **Quality**: green for the listed coverage, verified on TcTIM and HsTIM (model v6, mean pLDDT 97.3 and 96.7) and on an unreviewed entry with no experimental structure (A0A6A5BWU3, v6, mean pLDDT 96.2)
- **Coverage**: `has_predicted_structure` relationships, one per model, with the model version, tool, mean pLDDT and its bands, the UniProt range, and whether the modelled sequence is the entry's current one (MD5)
- **Notes**:
  - Models are never experimental structures: `Card.structures()` does not count them.
  - A missing accession answers 404, mapped to not found.
  - Licence: CC BY 4.0; cite AlphaFold and AlphaFold DB.

### PDBe-KB — ligand binding sites
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#28)
- **Access**: PDBe graph API `uniprot/ligand_sites/<accession>` (`OnlinePDBeKBClient`), saved responses (`FixturePDBeKBClient`, `temp_data/pdbe_kb/`)
- **Quality**: green for the listed coverage, verified on TcTIM (6 ligands) and HsTIM (10 ligands)
- **Coverage**: `has_ligand_site` relationships: residues each ligand contacts, in UniProt numbering, over all structures of the protein, with PDBe-KB's descriptors
- **Notes**:
  - Ligand copies are aggregated. The per-residue chain is one representative, so it cannot tell one ligand contacting two chains from two copies (in 1HTI, Asn12 is attributed to chain B and His96 to chain A, while the only PGA instance contacts chain B). Chain spanning is read from RCSB per-instance contacts instead.
  - `is_solvent` and `significance` do not separate crystallisation additives on TIM: glycerol, PEG, sulfate and hexane are not flagged as solvents, and glycerol has the same significance as BTS. Both are kept as PDBe-KB states them.
  - `chembl_id` is empty for every TIM ligand.
  - An accession without data answers 404, mapped to not found.
  - Licence: CC BY 4.0, academic and commercial use; cite the PDBe-KB consortium paper.

### PDBe-KB — interface residues
- **Status**: implemented as an enricher of `resolve_protein_card(..., interfaces=True)` (uibcdf/sabueso#40)
- **Access**: PDBe graph API `uniprot/interface_residues/<accession>` (same clients as ligand sites)
- **Quality**: green for the listed coverage. Verified on TcTIM (2 partners) and HsTIM (7 partners).
- **Coverage**: `has_interface_with` relationships, one per partner chain: the interface residues of this protein in UniProt numbering, and the entries and chains where each is observed
- **Notes**:
  - A "partner" is any chain PDBe-KB finds at an interface, so it is not necessarily a biological partner:
    - TcTIM lists TbTIM (P04789), only because 3Q37 is a TcTIM/TbTIM chimera whose entity maps to both;
    - HsTIM lists HLA-DR and T-cell receptor chains, from complexes with a TIM peptide.
    `Card.oligomer()` classifies each partner, per structure, and says so.
  - Partners without a UniProt entry (`type` other than `UNP`) keep PDBe-KB's label.
  - Licence: CC BY 4.0, as for ligand sites.

### InterPro — site residues
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#28)
- **Access**: InterPro API `protein/uniprot/<accession>/?residues` (`OnlineInterProClient`), saved responses (`FixtureInterProClient`, `temp_data/interpro/`)
- **Quality**: green for the listed coverage, verified on TcTIM and HsTIM (InterPro 110.0, CDD `cd00311`)
- **Coverage**: `features_positional.family_site`: sites a member database places on the protein's sequence, with description and signature
- **Notes**:
  - Positions are placed by the source's family model, so Sabueso never aligns sequences. The same CDD model places TcTIM's catalytic glutamate at 168 and HsTIM's at 166.
  - An empty answer is the same for "no site residues" and "unknown accession"; both are recorded as not_found with that caveat.
  - The release is read from the `InterPro-Version` response header.
  - Licence: InterPro CC0 1.0; member-database content may carry its own terms. The CDD sites are NCBI work (US public domain, NLM policy).

### M-CSA — evaluated, not implemented (uibcdf/sabueso#28)
- M-CSA links HsTIM and TcTIM to entry 324 (triosephosphate isomerase), but it states catalytic residues and roles only in the numbering of its reference protein (chicken TIM, P00940, PDB 1TPH).
- Placing them on another sequence needs an alignment, which Sabueso does not compute (`devguide/DECISIONS.md`; boundary evaluated in uibcdf/sabueso#30). The InterPro family sites cover the positional part; M-CSA would add mechanistic roles once a source-stated mapping or a MolSysSuite/Praxis result is available.

### STRING
- **Status**: implemented as an enricher of `resolve_protein_card` (uibcdf/sabueso#21, part 2c)
- **Access**: online API (`OnlineStringClient`), saved responses (`FixtureStringClient`, `temp_data/string/`)
- **Quality**: green for the listed coverage, verified on human TIM (STRING 12.0: 50 partners at score ≥ 700)
- **Coverage**: `functionally_associated_with` relationships with the combined score, the seven evidence channels, the query parameters and the STRING version (`source.version`)
- **Notes**:
  - STRING edges are functional associations, not physical interactions. The channels show whether an association rests on experiments or on pathways, fusion or text mining.
  - Partners are STRING proteins (`string:<taxon>.<id>`). They are not yet linked to UniProt entities.
  - The species comes from the UniProt anchor. STRING has no *T. cruzi* species-level entry for P52270: it covers the strain CL Brener (e.g. Q4DV43). The enricher records `not_found` and does not attach the strain network silently.

---

## Removed per-concept card tools (2026-09-23, uibcdf/sabueso#21 part 2b)
- **What was removed:** the GO, InterPro, CATH, SCOPe, TED, PhosphoSitePlus and BioGRID
  tools and their mappings.
- **Why:**
  - GO, InterPro, CATH, SCOPe and TED fetched *one term, family or domain* by its own id
    and built a card of it typed as a protein, e.g. `sabueso:protein:go:GO:0005524`.
  - PhosphoSitePlus read a synthetic format (record id "PTM") with no real access
    behind it.
  - BioGRID produced a protein-typed card holding a list of partner names.
- **Where that knowledge comes from now:** the protein itself. GO annotations
  (`annotated_with`), InterPro, Pfam, Gene3D/CATH, SUPFAM, PANTHER, PROSITE and CDD
  classifications (`classified_in`) and curated interactions (`interacts_with`) are
  typed relationships stated by UniProt (see *UniProt*).
- **Not replaced yet:**
  - TED domain assignments, SCOPe domain classification, and positional domain
    boundaries from InterPro;
  - PTM sites from PhosphoSitePlus;
  - the BioGRID interaction enricher, which needs an access key to be verified against
    live data.

## Summary of Open Incidents
- **Selection rules:** the default `priority_sources` still lists InterPro, CATH, SCOPe and
  TED for `annotations.domains`, a field no mapping produces now. It is harmless, since
  no source matches and resolution falls back to frequency, but stale. Revisit with the
  selection-rule work in uibcdf/sabueso#10.
