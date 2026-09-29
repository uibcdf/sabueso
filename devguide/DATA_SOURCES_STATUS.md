# Data Sources Status (Implemented)

The index of every resource, with its status and the reason for it, is `devguide/sources/registry.yaml` (`devguide/sources/README.md`). This file keeps the technical detail of the sources in use.

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
  - positional features: binding and active sites, modified residues, disulfide bonds, glycosylation, natural variants and mutagenesis (substitution, verbatim description, `VAR_` id and cross-references; uibcdf/sabueso#33). A deletion ("Missing") is `substitution.missing` (#80);
  - isoforms (ALTERNATIVE PRODUCTS: ids, names, synonyms, sequence status, `VSP_` ids; events and note) and alternative sequences, linked to the isoforms the entry lists for them (#80);
  - secondary structure (helix, strand, turn), each segment with the PDB entries it was read from (#80);
  - PDB cross-references as `has_structure` relationships (method, resolution, chains, UniProt-numbered ranges, coverage), shown through `Card.structures()`;
  - GO cross-references as `annotated_with` relationships (aspect, term, GO code, assigned by; ECO in `source_metadata`);
  - InterPro, Pfam, Gene3D (CATH), SUPFAM, PANTHER, PROSITE and CDD cross-references as `classified_in` relationships;
  - curated INTERACTION comments (IntAct binary interactions) as `interacts_with` relationships;
  - UniProt evidence qualifiers kept per SourceAssertion as `source_metadata.eco`.
- **Known limits**:
  - other comment types (similarity, miscellaneous, …) and feature types (sequence conflict, cross-link, chain, region, motif, …) are not mapped;
  - isoform sequences are not fetched, and never built by applying alternative sequences;
  - UniProt's secondary structure comes from the PDB entries each segment cites, often several; it describes those structures, not the protein in every state or construct;
  - the stated effect of a variant or mutagenesis is free text, kept verbatim: "thermolabile" or "abolishes ligand binding" is not turned into a category;
  - isoform restrictions (`molecule`) are part of the value for catalytic activity and subcellular location. For free-text comments they are on the SourceAssertion (`source_metadata.molecule`, since 0.3.6), since the value is the stated text;
  - identical repeated values in one record share one SourceAssertion id.
  - INTERACTION comments are UniProt's curated subset of binary interactions: 3 for human TIM, while its IntAct cross-reference reports 75. Full interaction data would need IntAct, STRING or BioGRID directly.
- **Notes**: stable online tests

### RCSB PDB — polymer-entity mapping (GraphQL)
- **Status**: implemented (uibcdf/sabueso#6, step 4b)
- **Access**: online GraphQL (`OnlineRCSBClient`), saved entries (`FixtureRCSBClient`, `temp_data/rcsb/`)
- **Quality**: green for the listed coverage. Verified on 1HTI, 1KLG, 1TCD, 1SUX, 2OMA, 2VOM, 3Q37, 4HHP and 4UNK, and live on every entry of TcTIM and HsTIM (2026-09-25).
- **Coverage**:
  - `has_structure` relationships per UniProt accession aligned to polymer entities: chains, UniProt-numbered ranges, method, resolution;
  - since schema 0.3.4, what choosing a structure needs:
    - R-free and R-work, deposit and release dates;
    - the construct: length, expression host and tags;
    - mutations as RCSB marks them, placed in UniProt numbering;
    - sequence differences against the UniProt sequence;
    - per chain, the UniProt ranges with coordinates (`SCHEMA.md`);
  - since schema 0.3.6, per chain, helices and strands (`HELIX_P`, `SHEET`) in UniProt
    numbering, with the assigning program (`provenance_source`, e.g. PROMOTIF; #80);
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
- **Structure lookup** (#93): `smiles:` and `inchi:` queries are matched by PubChem (POST `compound/<notation>/cids/JSON`; `tools.db.pubchem.get_structure_match`). CID 0 means PubChem holds no such compound, and HTTP 400 that it cannot read the structure.
- **Notes**: PubChem's `SMILES` (formerly `IsomericSMILES`) keeps stereochemistry and `ConnectivitySMILES` (formerly `CanonicalSMILES`) does not; the isomeric one used to be dropped (uibcdf/sabueso#10). XLogP3 and rotatable bonds carry their method. Stable online tests.

### ChEMBL
- **Status**: implemented
- **Access**: online API, local JSON
- **Quality**: green
- **Coverage**: identifiers, preferred name, molecule type, formula, physchem (ALogP, HBD/HBA, TPSA, rotatable bonds, aromatic rings, molecular weight as `full_mwt`), `max_phase`, InChI/InChIKey, isomeric SMILES
- **Notes**: numbers ChEMBL serialises as strings are normalized; logP and rotatable bonds carry their method (`ALogP`, `chembl:rtb`) and are compared only within it (uibcdf/sabueso#10). Stable online tests.

### gnomAD — population frequencies
- **Status**: implemented as an enricher of `resolve_protein_card(..., gnomad={})` (uibcdf/sabueso#83)
- **Access**: GraphQL API, dataset gnomad_r4, no key (`OnlineGnomADClient`); saved variants in `temp_data/gnomad/`; `tools.db.gnomad.get_variants`
- **Quality**: green for the listed coverage. Verified live on TPI1 (ENSG00000111669, 2026-09-29): 1,668 variants, of which 729 have a protein change. E105D, on the canonical transcript ENST00000396705, is placed at UniProt 105 with its exome and genome frequencies.
  - Placement: 540 placed, 2 of them through isoform P60174-3's map. 184 fall in that isoform's own N-terminal segment, and 2 are on transcripts UniProt does not state. 3 are not placed: two stop-codon changes and one unparsed notation.
- **Coverage**: `annotations.population_variants`, with consequence, transcript, HGVS, flags, and exome and genome allele count, number and frequency as stated
- **Notes**:
  - Found by the Ensembl gene UniProt cross-references.
  - Variants without a protein change are left out and counted.
  - At most 1000 per gene by default, with the cut reported.
  - The API states no release finer than the dataset.
  - Human genes only.
  - Licence: CC0 1.0 (core).

### ClinVar — variants and their clinical classification
- **Status**: implemented as an enricher of `resolve_protein_card(..., clinvar={})` (uibcdf/sabueso#83)
- **Access**: E-utilities (einfo for the build, esearch by NCBI Gene id, esummary), no key (`OnlineClinVarClient`); saved summaries in `temp_data/clinvar/`; `tools.db.clinvar.get_variants`
- **Quality**: green for the listed coverage. Verified live on TPI1 (GeneID 7167, Build260924-0125.1): 249 records in about 8 s. 110 have a protein change on the canonical transcript NM_000365.6, and those placed include UniProt's natural variants at 42, 105, 171 and 241.
- **Coverage**: `annotations.clinical_variants`, with the classification, review status, conditions and consequences as stated. Positions are in UniProt numbering only through a canonical transcript UniProt states and a matching residue.
- **Notes**: found by the NCBI Gene id UniProt cross-references, never by gene symbol. Every record of the gene by default, up to 5000; a cut is reported. Human genes only. Not for diagnostic use without review by a genetics professional.

### Reactome — pathways and reactions
- **Status**: implemented as an enricher of `resolve_protein_card(..., reactome=True)` (uibcdf/sabueso#83)
- **Access**: Content Service, UniProt mapping and event ancestors, no key (`OnlineReactomeClient`, which names Sabueso: the service refuses Python's default user agent); saved answers in `temp_data/reactome/`; `tools.db.reactome.get_pathways`
- **Quality**: green for the listed coverage. Verified live on HsTIM (release 97): glycolysis and gluconeogenesis, two reactions, and their ancestors up to Metabolism. TcTIM: not mapped.
- **Coverage**: `participates_in` relationships, with kind, name, species, the orthology-inference flag and pathway ancestors
- **Notes**: one request per pathway for its ancestors. Licence: CC0 1.0 (data).

### Orphadata (Orphanet) — rare disorders and their genes
- **Status**: implemented as an enricher of `resolve_protein_card(..., orphadata=True)` (uibcdf/sabueso#82)
- **Access**: `en_product6.xml` (about 22 MB, dated in its header), downloaded and indexed once per process in memory (`OnlineOrphadataClient`); saved disorders in `temp_data/orphadata/`; `tools.db.orphadata.get_associations`
- **Quality**: green for the listed coverage. Verified live on HsTIM (file of 2026-06-23, about 5 s): ORPHA:868, triose phosphate-isomerase deficiency, "Disease-causing germline mutation(s) in", Assessed.
- **Coverage**: `associated_with` relationships to `orphanet:ORPHA:<code>`, with the association type and status, the disorder's type and group, and the validating publications
- **Notes**: joined through the Swiss-Prot accession Orphanet states for each gene; genes without one are not attached. Human genes only. Licence: CC BY 4.0 (cite Orphanet and the data version).

### Open Targets Platform — target–disease associations
- **Status**: implemented as an enricher of `resolve_protein_card(..., open_targets={})` (uibcdf/sabueso#82)
- **Access**:
  - GraphQL API v4, no key (`OnlineOpenTargetsClient`);
  - saved answers in `temp_data/open_targets/`;
  - `tools.db.open_targets.get_associations`.
- **Quality**: green for the listed coverage. Verified live on TPI1 (ENSG00000111669, data 26.09): 483 associations, the first being TIM deficiency (MONDO_0014221, score 0.78). A missing gene is not found.
- **Coverage**: `associated_with` relationships, with the overall score, the per-datatype scores and the rank, as stated.
- **Notes**:
  - Joined through the Ensembl gene UniProt cross-references, only when Open Targets also lists the entry among the gene's products.
  - Every association of the gene by default, up to 5000, in Open Targets' order; a cut
    is reported.
  - Human genes only.
  - Tractability, safety and evidence strings are not mapped yet.
  - Licence: CC0 1.0.

### DISEASES (Jensen lab) — gene–disease associations
- **Status**: implemented as an enricher of `resolve_protein_card(..., diseases={})` (uibcdf/sabueso#82)
- **Access**:
  - the filtered channel files from download.jensenlab.org (`OnlineDISEASESClient`), versioned by their publication date and kept in memory, or in a cache directory when one is given;
  - saved rows in `temp_data/diseases/`;
  - `tools.db.diseases.get_associations`.
- **Quality**: green for the listed coverage. Verified live on HsTIM (ENSP00000229270): 2 curated associations (TIM deficiency, congenital hemolytic anemia) and 42 text-mined ones.
- **Coverage**: `associated_with` relationships, one per disease, channel and Ensembl protein, with DISEASES's scores as stated.
- **Notes**:
  - Joined only through the Ensembl proteins UniProt cross-references.
  - Text mining links names, not molecules, and is added only when asked for.
  - Human genes only: a non-human protein is `not_queried`, with the reason.
  - Licence: CC BY 4.0.

### ChEMBL indications and ClinicalTrials.gov — the clinical layer
- **Status**: implemented as enrichers of `resolve_molecule_card(..., indications=True)` and `trials={}` (uibcdf/sabueso#81)
- **Access**:
  - ChEMBL `drug_indication` (`OnlineChEMBLClient.indications`, `tools.db.chembl.get_indications`);
  - ClinicalTrials.gov API v2 studies by NCT id, in batches, no key (`OnlineClinicalTrialsClient`, `tools.db.clinicaltrials.get_studies`);
  - saved responses in `temp_data/chembl/indications.json` and `temp_data/clinicaltrials/studies.json`.
- **Quality**: green for the listed coverage.
  - Verified live on benznidazole (CHEMBL110): 4 indications, all phase 4 (ChEMBL_37), and the 16 trials they cite (API v2, data of 2026-09-25).
  - An NCT id ClinicalTrials.gov does not hold is returned as missing.
- **Coverage**:
  - `investigated_for`: disease term, MeSH heading, maximum phase and cited references;
  - `tested_in`: title, status, phases, study type, enrolment, dates, conditions, interventions as written, lead sponsor, and whether results are posted;
  - `Card.clinical()`.
- **Notes**:
  - Trials come only through the NCT ids ChEMBL cites, never by matching intervention names.
  - Adverse events (openFDA/FAERS) are not covered.
  - Licences: ChEMBL CC BY-SA 3.0; ClinicalTrials.gov is a US government work (credit NLM).

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

### BindingDB — affinities
- **Status**: implemented as an enricher of `resolve_protein_card(..., bindingdb={})` (uibcdf/sabueso#66)
- **Access**: REST `getLigandsByUniprots` (`OnlineBindingDBClient`), saved responses (`FixtureBindingDBClient`, `temp_data/bindingdb/`), `tools.db.bindingdb.get_affinities`; monomers anchored at their InChIKey through UniChem (source 31)
- **Quality**: verified on TcTIM (17 records: 16 grouped with ChEMBL, one attributed by ChEMBL to another molecule) and HsTIM (23 records: 13 grouped, 3 from a paper ChEMBL lacks for the target, 5 monomers UniChem does not hold, one with another stereochemistry than ChEMBL's)
- **Coverage**: `has_bioactivity` relationships with the ChEMBL layout (`source: BindingDB`, `stated_value` keeps the written precision); measurements shared with ChEMBL are grouped by `measurement_identity@1`
- **Notes**: the REST records carry no origin (BindingDB curation or ChEMBL import) and no record id; licence treated as CC BY-SA 3.0.

### PubChem BioAssay — results linked to a protein
- **Status**: implemented as an enricher of `resolve_protein_card(..., pubchem_bioassay=True)` (uibcdf/sabueso#68)
- **Access**: PUG REST: assays by protein accession, summaries (depositor and its assay id), concise tables, compound InChIKeys (`OnlinePubChemBioAssayClient`); saved responses (`FixturePubChemBioAssayClient`, `temp_data/pubchem_bioassay/`); `tools.db.pubchem_bioassay.get_assays`
- **Quality**: verified on TcTIM (13 assays, all deposited by ChEMBL, 492 results) and HsTIM (11 assays: 10 by ChEMBL, 1 by BindingDB)
- **Coverage**: `has_bioactivity` relationships with `source: PubChem BioAssay`; copies carry `copy_of` (depositor and its assay id) and are grouped with their originals by provenance; ChEMBL assays a copy names but the card lacks are fetched from ChEMBL (`retrieved_via`)
- **Notes**: the concise table does not state the relation of a value (`>`), so copies never vote for a group's class when the original is present; PubChem's CID can carry another stereochemistry or salt form than the depositor's compound, reported as `stereo_differs`.

### NCBI Taxonomy — ranks and ancestors
- **Status**: implemented as an enricher of `resolve_protein_card(..., taxonomy=True)` (uibcdf/sabueso#67)
- **Access**: NCBI Datasets API `taxonomy/taxon/<ids>` in batches (`OnlineNCBITaxonomyClient`), saved records (`FixtureNCBITaxonomyClient`, `temp_data/ncbi_taxonomy/`), and `tools.db.ncbi_taxonomy.get_taxon`
- **Quality**: green for the listed coverage, verified on T. cruzi (species 5693), its strain CL Brener (353153, whose ancestors include 5693) and Homo sapiens
- **Coverage**: `annotations.taxonomy`, the organism's taxon with its rank and every ancestor with name and rank; two requests per card (the taxon, then its ancestors)
- **Notes**: no data release is stated (only the API version); licence: US public domain (NLM policy).

### NCBI Gene — gene products (identity across gene databases)
- **Status**: implemented, consulted by the resolver's identity audit with `resolve(..., ncbi_gene=True)` (uibcdf/sabueso#69)
- **Access**: Entrez E-utilities `efetch` (XML), no key (`OnlineNCBIGeneClient`); saved records (`FixtureNCBIGeneClient`, `temp_data/ncbi_gene/`); `tools.db.ncbi_gene.get_gene`
- **Quality**: green for its one use, verified on GeneID 3550449, whose record lists both a Swiss-Prot and a TrEMBL entry of one *T. cruzi* gene
- **Coverage**: gene id, symbol, locus tag, taxon, update date, and the UniProtKB accessions (Swiss-Prot and TrEMBL) of the gene's products. NCBI's lists can include secondary accessions; only the entries compared are matched.
- **Notes**: asked only for candidate pairs whose loci are in databases that do not overlap; NCBI's rate limit (3 requests per second without a key) is not approached. Licence: US public domain (NLM policy).

### PHI-base — phenotypes of pathogen mutants
- **Status**: implemented as an enricher of `resolve_protein_card(..., phi_base=True)` (uibcdf/sabueso#83)
- **Access**:
  - `OnlinePHIBaseClient`: versioned PHI-base 5 releases on Zenodo (concept record 10722192), downloaded once and checked against their MD5, then indexed by UniProt accession. The index is kept in memory for the process, or written to a cache directory only when one is given (`cache_dir=`, `$SABUESO_CACHE_DIR`; `CACHE_POLICY.md`);
  - `FixturePHIBaseClient` reads saved sessions from `temp_data/phi_base/`;
  - `tools.db.phi_base.get_phenotypes`.
- **Quality**: green for the listed coverage.
  - Verified live on release 5.6 (2026-09-27): about 11,300 genes, 339 pathogen species and 5,747 curation sessions.
  - First load about 30 s, with a peak of about 750 MB while parsing. The cache on disk is 76 MB; later reads take about 1 s.
- **Coverage**: `annotations.pathogen_phenotypes`, one item per pathogen-host interaction, pathogen or gene-for-gene phenotype whose pathogen genotype includes the gene. Each item holds:
  - PHIPO term, extensions and high-level terms;
  - the whole genotype;
  - pathogen and host (taxon, strain);
  - diseases, conditions and method (PHI-base's `evidence_code`);
  - PHI ids, publication and the curator's comment.

  GO, interaction and expression annotations are not mapped.
- **Notes**:
  - PHIPO terms keep their ids; their labels are not fetched, and `high_level_terms` gives PHI-base's readable summary.
  - Coverage of trypanosomatids is small (11 *T. cruzi* genes in 5.6), and TcTIM is not in it. That absence is `not_stated`, never evidence.
  - Licence: CC BY 4.0 (cite PHI-base and the release).

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
- **Quality**: green for the listed coverage, verified on human TIM (STRING 12.0: 78 partners at score ≥ 700; the fixture keeps the 50 most confident, marked `truncated`)
- **Coverage**: `functionally_associated_with` relationships with the combined score, the seven evidence channels, the query parameters and the STRING version (`source.version`)
- **Notes**:
  - STRING edges are functional associations, not physical interactions. The channels show whether an association rests on experiments or on pathways, fusion or text mining.
  - Partners are STRING proteins (`string:<taxon>.<id>`). They are not yet linked to UniProt entities.
  - The species comes from the UniProt anchor. STRING has no *T. cruzi* species-level entry for P52270: it covers the strain CL Brener (e.g. Q4DV43). The enricher records `not_found` and does not attach the strain network silently.

### SKEMPI 2.0 — interface mutations and binding changes
- **Status**: implemented as an enricher (`skempi=True`, #83), card schema 0.3.7
- **Access**: the whole CSV file (1.6 MB), downloaded once per process and indexed by PDB entry; saved subset `temp_data/skempi/skempi_v2.csv` (barnase–barstar)
- **Quality**: green, verified on barnase (P00648). Of its 89 mutations in SKEMPI, the 83 in 1BRS are placed through RCSB's author numbering when 1BRS is loaded, each with a matching residue; K27A has ΔΔG 5.38 kcal/mol under `binding_ddg@1`, as published.
- **Coverage**: `annotations.interface_mutations`, 7085 rows over 345 PDB entries.
- **Notes**:
  - Rows are joined only through the PDB chains UniProt states are the protein. The protein names SKEMPI writes are never used to join.
  - Mutations are in the entry's author numbering. They are placed only through the author numbering RCSB states for the chain (`rcsb_author_numbering@1`) of a structure the card holds.
  - The file states no finer version than the database's (2.0), and the site reports corrections after 2018. The file's SHA-256 is recorded in the enrichment record, so a changed file is told apart.
  - Licence CC BY 4.0 (the site's terms of download and use).

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
- **Selection rules:** resolved by #10. The packaged rules (0.2.0) no longer list CATH,
  SCOPe or TED. The rule for `annotations.domains` remains for a reserved field that no
  mapping produces, since domains are `classified_in` relationships; it is harmless. The
  copy published in the user guide had stayed at 0.1.0 until 2026-09-26, and a test
  now keeps the two identical.
