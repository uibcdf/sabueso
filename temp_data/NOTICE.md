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
| `P00648.json` | UniProtKB (UniProt Consortium), barnase of *Bacillus amyloliquefaciens*, a public test system for interface mutations | release 2026_03 (entry version 146) | 2026-09-29 | CC BY 4.0 |
| `Q9Y2T5.json` | UniProtKB (UniProt Consortium), human GPR52, a public test system for GPCR numbering (GPCRdb) | entry version 170 | 2026-09-30 | CC BY 4.0 |
| `Q4DV43.json` | UniProtKB (UniProt Consortium), the TIM of *T. cruzi* strain CL Brener (TrEMBL), TcTIM's genome-strain entry, a public test system (#103) | entry version 97 | 2026-10-01 | CC BY 4.0 |
| `O75716.json` | UniProtKB (UniProt Consortium), human STK16, a public test system for kinase pockets (KLIFS) | entry version 221 | 2026-09-30 | CC BY 4.0 |
| `mondo/mondo.obo` | MONDO (Monarch Initiative), release v2026-09-01: the file's header and the whole stanzas of 63 terms: those equivalent to the diseases on the HsTIM and benznidazole fixtures, plus type 2 diabetes mellitus and its parent, and an obsolete term and its replacement; unchanged | v2026-09-01 | 2026-09-29 | CC BY 4.0 |
| `medgen/concepts.json` | MedGen (NCBI), the record UID of each MedGen concept id naming a condition in the ClinVar fixture (esearch by concept id, then esummary), and the database's last update; only the ids are kept | last update 2026/09/28 23:56 | 2026-09-29 | US public domain (NLM policy) |
| `skempi/skempi_v2.csv` | SKEMPI 2.0 (Jankauskaitė et al. 2019), the 105 rows of the barnase–barstar complexes (1BRS, 1B2S, 1B2U, 1B3S, 1X1W, 1X1X), header kept; a subset of the whole file, rows unchanged | 2.0 (CSV of 2018-06-06) | 2026-09-29 | CC BY 4.0 |
| `Q4D3W2.json`, `Q4QGX0.json` | UniProtKB (UniProt Consortium), a *T. cruzi* and an *L. major* entry with PHI-base records | release 2026_03 | 2026-09-27 | CC BY 4.0 |
| `phi_base/*.json` | PHI-base 5 (Zenodo record 21196331), the curation sessions naming Q4D3W2, H2DQH1 and Q4QGX0, as split by `sabueso.tools.db.phi_base.split_release` | 5.6 | 2026-09-27 | CC BY 4.0 (cite PHI-base; Urban et al., Nucleic Acids Res. 2025) |
| `uniprot_search/*.json` | UniProtKB search responses; refreshed with lineage and gene-locus cross-references, and the Trichomonas vaginalis search added, on 2026-09-25 (same release, same results) | release 2026_03 | 2026-09-23 | CC BY 4.0 |
| `alphafold/*.json` | AlphaFold DB (Google DeepMind and EMBL-EBI), prediction API responses | model version 6 | 2026-09-25 | CC BY 4.0 |
| `ncbi_taxonomy/*.json` | NCBI Taxonomy (NCBI/NLM), Datasets API taxon records, trimmed to id, name, rank, lineage and BLAST name | Datasets API 18.37.0 | 2026-09-25 | US public domain (NLM policy) |
| `ncbi_gene/*.xml` | NCBI Gene (NCBI/NLM), Entrez E-utilities `efetch` gene records (XML), as returned | E-utilities | 2026-09-26 | US public domain (NLM policy) |
| `bindingdb/*.json` | BindingDB, REST `getLigandsByUniprots` responses for P52270 and P60174 | — | 2026-09-25 | **CC BY-SA 3.0** (treated as such: BindingDB curation is CC BY 3.0, ChEMBL imports CC BY-SA 3.0, and records state no origin) |
| `pubchem_bioassay/*.json` | PubChem BioAssay (NCBI/NLM): assays linked to P52270 and P60174, their summaries, concise tables and the InChIKeys of their compounds | — | 2026-09-25 | US public domain (NLM policy); deposited data keeps its depositor's terms: these assays were deposited by ChEMBL (**CC BY-SA 3.0**) and BindingDB |
| `rcsb/*.json` | RCSB PDB (wwPDB archive), GraphQL entry data; assemblies added and 3Q37 retrieved 2026-09-24; all refetched with mutations, tags, unobserved residues, refinement and dates, and 2OMA, 2VOM, 4HHP and 4UNK added, 2026-09-25; refetched with author numbering, and 2V5B and 1WYI added, 2026-09-26 (1KLG kept from 2026-09-25: RCSB answered it only partially that day); all refetched with the program that assigned each instance feature (`provenance_source`), 2026-09-27, each answered completely, 1KLG included; 1BRS (barnase–barstar) added 2026-09-29; 2BUJ (STK16) and 6LI0 (GPR52, with OPM's and PDBTM's membrane segments) added 2026-09-30 | — | 2026-09-23 | CC0 1.0 |
| `pdb_ccd/*.json` | wwPDB Chemical Component Dictionary, served by RCSB PDB | — | 2026-09-23 | CC0 1.0 |
| `pdbe_kb/*.json` | PDBe-KB (EMBL-EBI), ligand binding sites (2026-09-23) and interface residues (2026-09-24) | — | 2026-09-23 | CC BY 4.0 |
| `interpro/*.json` | InterPro (EMBL-EBI), site residues from the CDD member database | InterPro 110.0 | 2026-09-23 | see note below |
| `string/*.json` | STRING; HsTIM's 50 most confident partners at score ≥ 700, of 78, marked `truncated` 2026-09-29 (refetched: same rows) | 12.0 | 2026-09-23 | CC BY 4.0 |
| `chembl/*.json`, `CHEMBL90555.json` | ChEMBL (EMBL-EBI); CHEMBL90555 added to `chembl/molecules.json` 2026-09-24; `chembl/indications.json` (benznidazole, CHEMBL110) added 2026-09-28 | ChEMBL_37 (released 2026-05-01) | 2026-09-23 | **CC BY-SA 3.0** |
| `diseases/*.tsv`, `diseases/versions.json` | DISEASES (Jensen lab), the filtered rows of HsTIM's Ensembl protein ENSP00000229270 per channel | files of 2026-09-18 (knowledge, experiments) and 2026-09-20 (text mining) | 2026-09-28 | CC BY 4.0 |
| `open_targets/ENSG00000111669.json` | Open Targets Platform, HsTIM's gene (TPI1): its target record and first 20 of 483 associated diseases | data 26.09 | 2026-09-28 | CC0 1.0 |
| `open_targets/diseases/MONDO_0014221.json` | Open Targets Platform, triosephosphate isomerase deficiency: its first 20 of 252 associated targets, in Open Targets' order | data 26.09 | 2026-09-29 | CC0 1.0 |
| `orphadata/en_product6.xml` | Orphadata Science (Orphanet, INSERM), the disorders naming HsTIM (P60174); "Orphadata Science: Free access data from Orphanet. © INSERM 1999." | file of 2026-06-23 | 2026-09-28 | CC BY 4.0 |
| `reactome/P60174.json` | Reactome, HsTIM's pathways, reactions and pathway ancestors | release 97 | 2026-09-28 | CC0 1.0 |
| `clinvar/7167.json` | ClinVar (NCBI), 21 of the 249 variation summaries of TPI1 (GeneID 7167), chosen to cover each kind of record | Build260924-0125.1 | 2026-09-29 | Freely available; credit ClinVar |
| `gnomad/ENSG00000111669.json` | gnomAD (Broad Institute), 18 of the 1,668 variants of TPI1: protein changes on the canonical transcript, on isoform P60174-3's (inside and outside its own segment) and on a transcript UniProt does not state (12-6869106-A-G, added 2026-09-30), and non-coding ones; the gene's transcripts gnomAD annotates (added 2026-09-30) | dataset gnomad_r4 | 2026-09-29, 2026-09-30 | CC0 1.0 |
| `uniref/*.json` | UniProt's UniRef: the clusters of P52270 and the 7 members of UniRef90_P52270 | release 2026_03 | 2026-10-01 | CC BY 4.0 |
| `oma/*.json` | OMA (Dessimoz lab): the cross-references OMA states for P60174 and P52270, 7 of P60174's 3,090 orthologs, and UniProt's accessions for their Swiss-Prot entry names (`entry_names.json`, UniProt search); the OMA protein P52270 is mapped to (`protein_TRYCC03899.json`, added 2026-10-01) | OMA REST API 1.11 | 2026-10-01 | CC BY 4.0 (OMA; UniProt) |
| `sabdab/rcsb_pdb_annotations.json` | SAbDab (Oxford Protein Informatics Group), SAbDab2's annotations of the PDB (`api/rcsb-pdb-annotations`), the 9 antibody instances of 1YY9, 10BT, 9IJR, 9IJS and 9MQI | API 2.1.4 | 2026-09-30 | CC BY 4.0 |
| `gpcrdb/*.json` | GPCRdb, GPR52 (gpr52_human): its receptor entry, its residues with segments and generic numbers, and its seven structures | REST services | 2026-09-30 | CC BY 4.0 |
| `klifs/*.json` | KLIFS (Kooistra lab), STK16 (MPSK1, kinase 280): five entries of the kinase list (AKT1, EGFR, JAK1, JAK1-b, MPSK1), its information, its two structures (2BUJ chains A and B) and chain B's pocket residues | api_v2 | 2026-09-30 | no formal licence; the FAQ states the data is free and open for academia and industry |
| `gnomad/consequences.json` | gnomAD (Broad Institute), the consequence on every transcript of the six TPI1 fixture changes the isoform map would place (variant query) | dataset gnomad_r4 | 2026-10-01 | CC0 1.0 |
| `gnomad/pext_ENSG00000111669.json` | gnomAD (Broad Institute), the pext of TPI1 (GRCh38): 12 coding regions, each with its mean and its value in 49 GTEx v10 tissues, and the gene's transcripts with their exons | gnomad_r4 pext (GTEx v10) | 2026-10-01 | CC0 1.0 (gnomAD; computed from GTEx) |
| `gtex/tissue_site_detail_gtex_v10.json` | GTEx Portal API v2 (`dataset/tissueSiteDetail`, gtex_v10): the 54 tissues of GTEx v10, each with its id, name, tissue site and the ontology term GTEx states (UBERON, or EFO for a cell line); only those fields kept | gtex_v10 | 2026-10-01 | GTEx open-access data, free to use with acknowledgement of the GTEx Portal |
| `gnomad/ENST00000396705.json` | gnomAD (Broad Institute), the same variants as stated on TPI1's canonical transcript (version 10), 9 of its 1,404 | dataset gnomad_r4 | 2026-09-30 | CC0 1.0 |
| `clinicaltrials/studies.json` | ClinicalTrials.gov (NLM), the 16 studies ChEMBL's benznidazole indications cite | API v2 data of 2026-09-25 | 2026-09-28 | US government work; Source: National Library of Medicine |
| `unichem/*.json` | UniChem (EMBL-EBI); vincristine added 2026-09-24; lookups of the BindingDB monomers of the TIM fixtures by source id (`source31__<monomer>.json`) added 2026-09-25 | — | 2026-09-23 | see note below |
| `5978.json`, `66414.json` | PubChem (NCBI/NLM) | — | earlier | US public domain (NLM policy) |
| `europepmc/P60174.json` | Europe PMC (EMBL-EBI) REST search `ACCESSION_ID:P60174 AND ACCESSION_TYPE:uniprot`: 25 of the 354 articles whose text states HsTIM's accession (the 24 newest and a preprint), ids and bibliographic data only (#92) | service 6.9 | 2026-09-29 | EMBL-EBI terms of use (no restrictions of its own; attribution); no article text is kept |
| `chebi/compounds.json` | ChEBI 2.0 (EMBL-EBI) API, 7 entries: vincristine and ligands of the TIM fixtures, with the fields Sabueso reads (structure, classes, roles, definition, stars) (#83) | — | 2026-09-30 | CC BY 4.0 |
| `pubchem/structures.json`, `pubchem/3717450.json` | PubChem (NCBI/NLM) PUG REST: structure lookups (vincristine's SMILES, its SMILES without stereocentres, its InChI, a structure PubChem does not hold, an unreadable SMILES), and the property table of CID 3717450 (vincristine with undefined stereochemistry) (#93) | — | 2026-09-29 | US public domain (NLM policy) |
| `2NZT.json` | RCSB PDB entry | — | earlier | CC0 1.0 |
| `frozen_cards/*.json` | Sabueso cards built from the fixtures above by a published release, kept to test that later versions still read them (#42). `schema_0.3.0__P52270.json`: the published conda package `sabueso=0.1.1` (uibcdf channel; card schema 0.3.0). `schema_0.3.1__P52270.json`: the release 0.2.0 candidate, built as its conda package and installed in a clean environment (card schema 0.3.1). Both were run on the UniProt, RCSB PDB and ChEMBL fixtures. `schema_0.3.2__P52270.json`: the release 0.3.0 candidate, built and installed the same way (card schema 0.3.2), run on the UniProt, RCSB PDB, ChEMBL, PDBe-KB and AlphaFold DB fixtures, with curated statements under a placeholder DOI (`doi:10.0000/frozen-card`) that claim nothing about the literature. `schema_0.3.3__P60174.json`: the release 0.3.1 candidate, built and installed the same way (card schema 0.3.3), run on the HsTIM UniProt, RCSB PDB, ChEMBL, PDBe-KB and AlphaFold DB fixtures, so that it holds AlphaFold models of isoforms. `schema_0.3.4__P52270.json`: the release 0.4.0 candidate, built and installed the same way (card schema 0.3.4), run on the TcTIM UniProt, RCSB PDB (every entry UniProt lists, with mutations, constructs and observed residues), ChEMBL (first 25 records), PDBe-KB, InterPro, AlphaFold DB, NCBI Taxonomy, BindingDB and UniChem fixtures. PubChem BioAssay is left out to keep the card small: its copies pull in every ChEMBL record they point to. `schema_0.3.5__P60174.json`: the release 0.5.0 candidate, built and installed the same way (card schema 0.3.5), run on the HsTIM UniProt, RCSB PDB (1HTI, 1WYI, 2VOM, 4UNK: author numbering, an author-defined tetramer, two mutants), ChEMBL (first 25 records), PDBe-KB, InterPro, AlphaFold DB, NCBI Taxonomy, BindingDB and UniChem fixtures. `schema_0.3.6__P60174.json`: the release 0.6.0 candidate, built and installed the same way (card schema 0.3.6), run on the same fixtures plus STRING, DISEASES (three channels), Open Targets, Orphadata, Reactome, ClinVar and gnomAD: isoforms, secondary structure, disease associations, pathways, and clinical and population variants placed in UniProt numbering. `schema_0.3.7__P60174.json`: the release 0.7.0 candidate, built and installed the same way (card schema 0.3.7), run on the same fixtures plus MedGen, MONDO (disease identity and hierarchy) and Europe PMC (text-mined accession mentions): every SourceAssertion states how it entered. `schema_0.3.8__P60174.json`: the release 0.8.0 candidate, built and installed the same way (card schema 0.3.8), run on the same fixtures plus gnomAD's pext and canonical-transcript answers, OMA's orthologs, and KLIFS, GPCRdb and SAbDab (not found for TPI1). `schema_0.3.9__P52270.json`: the release 0.9.0 candidate, built and installed the same way (card schema 0.3.9), run on the TcTIM fixtures of `schema_0.3.4__P52270.json` plus UniRef (its clusters, and the members of UniRef90_P52270, among them CL Brener's Q4DV43) and OMA (which maps P52270 to CL Brener's entry, so its orthologs are not joined). `schema_0.3.10__P60174.json`: the release 0.10.0 candidate, built and installed the same way (card schema 0.3.10), run on the fixtures of `schema_0.3.8__P60174.json` plus GTEx's tissue terms for the pext's 49 tissues; it also holds UniProt's Ensembl transcripts per isoform | — | 2026-09-24 | each part keeps its source's licence; the ChEMBL part is **CC BY-SA 3.0** |

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
- **MONDO** — Mondo Disease Ontology, Monarch Initiative, https://mondo.monarchinitiative.org/,
  CC BY 4.0. Cite Mondo and the release (v2026-09-01).
- **SKEMPI 2.0** — https://life.bsc.es/pid/skempi2/, CC BY 4.0 (its terms of download and
  use). Cite: Jankauskaitė J, Jiménez-García B, Dapkūnas J, Fernández-Recio J, Moal IH
  (2019) SKEMPI 2.0: an updated benchmark of changes in protein–protein binding energy,
  kinetics and thermodynamics upon mutation. Bioinformatics 35, 462–469.
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
