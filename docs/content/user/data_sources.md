# Data sources

<!-- Generated from devguide/sources/registry.yaml by
     `python tools/source_registry.py --write`. Do not edit by hand. -->

The online resources Sabueso uses, has set aside, or has yet to review. To
propose one, open a discussion in the **Data sources** category of the
repository's GitHub Discussions; triage adds it here as *queued*.

Summary: in use 31, evaluating 23, deferred 24, retired 3, out of scope 13.

## In use

| Resource | Category | Access | Licence | Since |
| --- | --- | --- | --- | --- |
| [UniProtKB](https://www.uniprot.org/) | Targets, sequence and basic pharmacology | REST API (entries and search) | CC BY 4.0 | 2026-02-06 |
| [RCSB PDB](https://www.rcsb.org/) | Macromolecular structures, models and dynamics | GraphQL and REST APIs | CC0 1.0 | 2026-02-07 |
| [wwPDB Chemical Component Dictionary](https://www.wwpdb.org/data/ccd) | Chemical space, synthesis, ADMET and safety | RCSB REST API | CC0 1.0 | 2026-09-23 |
| [PDBe-KB](https://www.ebi.ac.uk/pdbe/pdbe-kb) | Binding sites, cavities and specialised families | PDBe graph API | CC BY 4.0 | 2026-09-23 |
| [InterPro and member databases (Pfam, CDD, PANTHER, PROSITE, SUPFAM, Gene3D/CATH)](https://www.ebi.ac.uk/interpro/) | Targets, sequence and basic pharmacology | InterPro REST API; UniProt cross-references | CC0 1.0 (member databases may carry their own terms) | 2026-02-07 |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Binding affinity and experimental bioactivity | REST API | CC BY-SA 3.0 (share-alike) | 2026-02-07 |
| [PubChem (compounds)](https://pubchem.ncbi.nlm.nih.gov/) | Chemical space, synthesis, ADMET and safety | PUG REST | US public domain (NLM policy); depositor terms may apply | 2026-02-07 |
| [UniChem](https://www.ebi.ac.uk/unichem/) | Chemical space, synthesis, ADMET and safety | REST API | No restrictions of its own; the linked resources' rights apply | 2026-09-23 |
| [STRING](https://string-db.org/) | Protein–protein interactions and structural modulation | REST API | CC BY 4.0 | 2026-02-07 |
| [AlphaFold DB](https://alphafold.ebi.ac.uk/) | Macromolecular structures, models and dynamics | REST API | CC BY 4.0 | 2026-09-25 |
| [Gene Ontology annotations](https://geneontology.org/) | Targets, sequence and basic pharmacology | via UniProt cross-references | CC BY 4.0 | 2026-09-23 |
| [IntAct](https://www.ebi.ac.uk/intact/) | Protein–protein interactions and structural modulation | via UniProt | CC BY 4.0 | 2026-09-23 |
| [Rhea](https://www.rhea-db.org/) | Targets, sequence and basic pharmacology | via UniProt | CC BY 4.0 | 2026-09-23 |
| [OrthoDB](https://www.orthodb.org/) | Organism, orthology and biological context | via UniProt cross-references | Identifiers only, through UniProt (CC BY 4.0) | 2026-09-25 |
| [eggNOG](http://eggnog5.embl.de/) | Organism, orthology and biological context | via UniProt cross-references | Identifiers only, through UniProt (CC BY 4.0) | 2026-09-25 |
| [NCBI Gene / RefSeq](https://www.ncbi.nlm.nih.gov/gene/) | Targets, sequence and basic pharmacology | via UniProt cross-references; Entrez E-utilities efetch (XML), optional NCBI key, when resolve(..., ncbi_gene=True) | US public domain (NLM policy) | 2026-09-25 |
| [VEuPathDB gene identifiers](https://veupathdb.org/) | Organism, orthology and biological context | via UniProt cross-references | Identifiers only | 2026-09-25 |
| [Open Targets Platform](https://platform.opentargets.org/) | Target validation, genetics and functional networks | GraphQL API v4 (pages of 3000), no key, when resolve(..., open_targets={}), in Open Targets' order | CC0 1.0 (cite the latest Open Targets publication; third-party sources inside keep their terms, agreed for unrestricted use by its users) | 2026-09-25 |
| [DISEASES (Jensen lab)](https://diseases.jensenlab.org/) | Target validation, genetics and functional networks | Filtered channel files (TSV) from download.jensenlab.org, versioned by publication date, kept in memory or in a cache directory, when resolve(..., diseases={}) | CC BY 4.0 | 2026-09-27 |
| [Orphadata (Orphanet)](https://www.orphadata.com/) | Target validation, genetics and functional networks | The en_product6.xml file (about 22 MB), dated in its header, downloaded and indexed once per process in memory, when resolve(..., orphadata=True) | CC BY 4.0 (Orphadata Science; cite Orphanet and the data version) | 2026-09-27 |
| [PHI-base](https://phi-base.org/) | Organism, orthology and biological context | Versioned releases of PHI-base 5 on Zenodo (JSON), downloaded once, checked against their MD5 and split per UniProt accession in the local cache, when resolve(..., phi_base=True) | CC BY 4.0 (cite PHI-base and the release) | 2026-09-27 |
| [Reactome](https://reactome.org/) | Target validation, genetics and functional networks | Content Service (UniProt mapping, event ancestors), no key, when resolve(..., reactome=True) | CC0 1.0 (data); CC BY 4.0 (illustrations, not used) | 2026-09-25 |
| [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) | Target validation, genetics and functional networks | E-utilities (einfo, esearch by gene id, esummary), optional NCBI key, when resolve(..., clinvar={}) | Freely available; ClinVar asks to be credited as the source. Not for diagnostic use without review by a genetics professional. | 2026-09-25 |
| [gnomAD](https://gnomad.broadinstitute.org/) | Target validation, genetics and functional networks | GraphQL API (dataset gnomad_r4; the API states no finer release), no key, when resolve(..., gnomad={}) | CC0 1.0 (core data; some annotations, not read, carry other terms) | 2026-09-25 |
| [SKEMPI 2.0](https://life.bsc.es/pid/skempi2/) | Protein–protein interactions and structural modulation | The whole CSV file (1.6 MB, database version 2.0, its SHA-256 recorded), downloaded once per process and indexed by PDB entry, when resolve(..., skempi=True) | CC BY 4.0 (the site's terms of download and use; cite Jankauskaitė et al. 2019) | 2026-09-25 |
| [BindingDB](https://www.bindingdb.org/) | Binding affinity and experimental bioactivity | REST getLigandsByUniprots, no key; monomers anchored through UniChem | CC BY 3.0 (BindingDB curation) and CC BY-SA 3.0 (imported from ChEMBL); treated as CC BY-SA 3.0, since the REST records state no origin | 2026-09-25 |
| [PubChem BioAssay](https://pubchem.ncbi.nlm.nih.gov/) | Binding affinity and experimental bioactivity | PUG REST (assays by protein, summaries, concise tables, compound InChIKeys) | US public domain (NLM policy); deposited data keeps its depositor terms (ChEMBL copies: CC BY-SA 3.0) | 2026-09-25 |
| [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy) | Organism, orthology and biological context | NCBI Datasets REST API, optional NCBI key | US public domain (NLM policy) | 2026-09-25 |
| [ClinicalTrials.gov](https://clinicaltrials.gov/) | Target validation, genetics and functional networks | API v2 (studies by NCT id, in batches), no key, when resolve(..., trials={}) | US government work (not under copyright in the US); NLM asks credit (Source: National Library of Medicine) | 2026-01-31 |
| [MedGen (NCBI)](https://www.ncbi.nlm.nih.gov/medgen/) | Target validation, genetics and functional networks | E-utilities (esearch by [ConceptId], esummary), in batches, optional NCBI key, when resolve(..., medgen=True) | US public domain (NLM policy) for NCBI's records; names from integrated vocabularies may carry their own terms and are not kept | 2026-09-29 |
| [MONDO (Mondo Disease Ontology)](https://mondo.monarchinitiative.org/) | Target validation, genetics and functional networks | Dated GitHub releases; mondo.obo (about 53 MB) downloaded once per process, checked against the SHA-256 GitHub states, and indexed; resolve('mondo:...'), or any id of a terminology MONDO maps | CC BY 4.0 (cite Mondo and the release) | 2026-09-29 |

### How much Sabueso asks for

By default Sabueso asks each source for everything it states about an entry.
Where an answer can be very large, a safety ceiling applies; an option such as
`open_targets={"limit": n}` asks for fewer. A cut is never silent: the card
records it as `truncated`, with the source's total when the source states one,
and Sabueso warns. The other sources in use are read whole.

| Resource | Default ceiling | Counts |
| --- | --- | --- |
| UniProtKB | 500 | candidates of a name or gene search (kept low on purpose; more than this is ambiguous, and the resolution records search_truncated) |
| ChEMBL | 5000 | bioactivities per target |
| STRING | 5000 | partners at the required score (700 by default); STRING states no total, so a cut is detected by asking for one more |
| Open Targets Platform | 5000 | associations per gene |
| ClinVar | 5000 | records per gene |
| gnomAD | 5000 | protein-level variants per gene |
| ClinicalTrials.gov | 5000 | trials per molecule, among those ChEMBL's indications cite |

## Being evaluated

| Resource | Category | What it would bring | State | Since |
| --- | --- | --- | --- | --- |
| [Target 2035 / SGC](https://www.thesgc.org/) | Benchmarks, open challenges and open-science consortia | Selective chemical probes and negative controls for understudied targets. | under review | 2026-09-25 |
| [ChEBI](https://www.ebi.ac.uk/chebi/) | Chemical space, synthesis, ADMET and safety | Ontology of chemical entities, endogenous metabolites and cofactors. | under review | 2026-09-25 |
| [SureChEMBL](https://surechembl.org/) | Chemical space, synthesis, ADMET and safety | Chemical structures text-mined from patents. | under review | 2026-09-25 |
| [Tox21 / ToxCast](https://www.epa.gov/chemical-research/toxicity-forecasting) | Chemical space, synthesis, ADMET and safety | In vitro toxicity screening profiles, cellular stress and assay-interference flags. | under review | 2026-09-25 |
| [PROTAC-DB](http://cadd.zju.edu.cn/protacdb/) | Emerging modalities (targeted degradation) | Targeted-degradation chimeras: E3 ligases, warheads, linkers, ternary complexes and DC50/Dmax. | under review | 2026-09-25 |
| [iPPI-DB](https://ippidb.pasteur.fr/) | Protein–protein interactions and structural modulation | Non-peptide inhibitors and modulators of protein–protein interactions, with pharmacological, chemical and structural data. | Blocked (2026-09-29): the compounds' targets, activities and InChIKeys are only in HTML pages (the CSV export has SMILES only, and the REST API covers structures, cavities and hotspots), and no data licence was found. Waiting for its maintainers (#84). | 2026-09-25 |
| [TDR Targets](https://tdrtargets.org/) | Organism, orthology and biological context | Target prioritisation for pathogens of neglected tropical diseases: essentiality, druggability, similarity to the host. | Blocked: its site did not answer from our network (2026-09-27/28), and no terms or API were found. Waiting for its maintainers (#84). | 2026-09-27 |
| [ASD (Allosteric Database)](http://mdl.shsmu.edu.cn/ASD/) | Binding sites, cavities and specialised families | Allosteric modulators, regulatory sites and conformational communication. | under review | 2026-09-25 |
| [BRENDA](https://brenda-enzymes.org/) | Binding sites, cavities and specialised families | Enzyme information: kinetics (Km, kcat), inhibitors, cofactors and conditions. | Reviewed 2026-09-29 (#94): data CC BY 4.0 (its licence page); the SOAP web service needs a registered account (email and password). Fits every terms profile. Strong candidate: kinetics (Km, kcat, Ki) and inhibitors per EC number and organism, e.g. TIM (EC 5.3.1.1) of T. cruzi and human. Waits on a user's account for the key rule. | 2026-09-25 |
| [GPCRdb](https://gpcrdb.org/) | Binding sites, cavities and specialised families | GPCR structures, mutations, activation states and Ballesteros–Weinstein numbering. | under review | 2026-09-25 |
| [KLIFS](https://klifs.net/) | Binding sites, cavities and specialised families | Kinase pocket anatomy aligned to 85 reference positions, with DFG/αC conformations. | under review | 2026-09-25 |
| [mpstruc](https://blanco.biomol.uci.edu/mpstruc/) | Binding sites, cavities and specialised families | Membrane proteins of known structure, classified by topology and family. | under review | 2026-09-25 |
| [OPM (Orientations of Proteins in Membranes)](https://opm.phar.umich.edu/) | Binding sites, cavities and specialised families | Position and orientation of PDB structures in the lipid bilayer. | under review | 2026-09-25 |
| [SAbDab / Thera-SAbDab](https://opig.stats.ox.ac.uk/webapps/sabdab/) | Binding sites, cavities and specialised families | Antibody and nanobody structures with standard numbering, CDRs and clinical metadata. | under review | 2026-09-25 |
| [sc-PDB](http://bioinfo-pharma.u-strasbg.fr/scPDB/) | Binding sites, cavities and specialised families | Druggable binding sites extracted from the PDB, cleaned of crystallographic artefacts. | under review | 2026-09-25 |
| [ESM Metagenomic Atlas](https://esmatlas.com/) | Macromolecular structures, models and dynamics | Structures predicted at scale by a protein language model. | under review | 2026-09-25 |
| [ModelArchive](https://modelarchive.org/) | Macromolecular structures, models and dynamics | Open repository of computational macromolecular models with mmCIF metadata. | under review | 2026-09-25 |
| [ProThermDB](https://web.iitm.ac.in/bioinfo2/prothermdb/) | Macromolecular structures, models and dynamics | Experimental protein stability data (ΔΔG, Tm) for point mutations. | under review | 2026-09-25 |
| [DepMap](https://depmap.org/) | Target validation, genetics and functional networks | CRISPR and RNAi screens of gene essentiality and dependencies in cancer cell lines. | under review | 2026-09-25 |
| [DGIdb](https://dgidb.org/) | Target validation, genetics and functional networks | Aggregated drug–gene interactions and druggability categories. | under review | 2026-09-25 |
| [Pharos / TCRD (IDG)](https://pharos.nih.gov/) | Target validation, genetics and functional networks | Human target development levels (Tclin, Tchem, Tbio, Tdark) and aggregated target knowledge, keyed by UniProt, HGNC, Ensembl and NCBI Gene. | under review | 2026-09-27 |
| [TTD (Therapeutic Target Database)](https://idrblab.org/ttd/) | Target validation, genetics and functional networks | Molecular targets, their clinical status, diseases and resistance mutations. | under review | 2026-09-25 |
| [Ensembl](https://www.ensembl.org/) | Targets, sequence and basic pharmacology | Gene and transcript annotation, homology and population variants. | under review | 2026-09-25 |

## Deferred

| Resource | Reason | Revisit when | Since |
| --- | --- | --- | --- |
| [VEuPathDB services (expression by stage, phenotype screens)](https://veupathdb.org/) | Blocked (2026-09-28): the web services now need a registered user's API key (HTTP 401 without one), and no reuse terms were found (#84). The curated biological-context fields (#60) exist meanwhile. | VEuPathDB answers #84 on terms and on a tool using a user's key; then a user supplies their own key through an environment variable. | 2026-09-25 |
| [BioGRID](https://thebiogrid.org/) | The API needs a personal access key; IntAct (via UniProt) and STRING cover current needs. Reviewed 2026-09-29 (#94): MIT licence (its terms page), so every terms profile admits it; key management now exists (tools/db/_keys). | Genetic interactions are needed, and a user supplies their own key. | 2026-09-23 |
| [DrugBank (open data)](https://go.drugbank.com/) | Reviewed for terms profiles (2026-09-29, #94). The full database (XML 5.1.22 of 2026-06-27, 204 MB) is CC BY-NC 4.0, and its download needs an account under DrugBank's Academic License (an academic institution, research not primarily for a commercial third party). It would fit only the non_commercial profile, with the user's own account, and would bring what the clinical layer still lacks: pharmacology, mechanisms, interactions, transporters. The Open Data (vocabulary, structures) is CC0, but its download also needs a login (HTTP 403 without one). | A user with a DrugBank academic account asks for it; the account's credentials are theirs, through tools/db/_keys, never stored. | 2026-09-23 |
| [Guide to PHARMACOLOGY (IUPHAR/BPS)](https://www.guidetopharmacology.org/) | Its web services now need a personal API key (HTTP 401 without one), its data is under ODbL (share-alike), and UniProt links neither test target to it. Reviewed 2026-09-29 (#94): the database is under ODbL 1.0 and its contents under CC BY-SA 4.0 (its about page); every terms profile would admit it with share-alike, and key management now exists. | A target of interest has a GuidetoPHARMACOLOGY cross-reference in UniProt, and key management exists for deployments (as for BioGRID). | 2026-09-25 |
| [KEGG PATHWAY](https://www.kegg.jp/) | Not a public database: free academic use of the website only; services, downloads and non-academic use need a licence, which does not fit redistribution across MOLI. Reviewed 2026-09-29 (#94): even academic users who provide services with KEGG need an academic service provider licence, so no terms profile admits it without one. | A licence covering MOLI use is in place, or a pathway need is not met by Reactome (CC0). | 2026-09-25 |
| [PharmacoDB](https://pharmacodb.pmgenomics.ca/) | HTTP 503 on 2026-09-29. | It answers again. | 2026-09-25 |
| [2P2Idb](http://2p2idb.cnrs-mrs.fr/) | Did not answer on 2026-09-27/29. | It answers again; then evaluate with iPPI-DB. | 2026-09-25 |
| [NDB (Nucleic Acid Database)](https://ndbserver.rutgers.edu/) | Nucleic-acid structures; Sabueso has no nucleic-acid entities yet. | Nucleic-acid cards exist. | 2026-09-25 |
| [CoDNaS](https://codnas.inf.unlp.edu.ar/) | Did not answer on 2026-09-29. | It answers again. | 2026-09-25 |
| [BioLiP](https://zhanggroup.org/BioLiP/) | Bulk downloads of a third-party pipeline, not a per-record service; the PDB subject-of-investigation flag already separates ligands from additives, and PDBe-KB gives contacts. | A batch import exists, or a question needs curated biologically relevant sites that PDBe-KB and the PDB flag do not give. | 2026-09-23 |
| [Binding MOAD](https://bindingmoad.org/) | Sunset: online until mid-2024, with its affinity backend licensed to Chemical Abstracts Service; earlier terms non-commercial. | An open release of its data exists. | 2026-09-25 |
| [M-CSA (Mechanism and Catalytic Site Atlas)](https://www.ebi.ac.uk/thornton-srv/m-csa/) | Evaluated: it links both TIMs to an entry but states catalytic residues and roles only in the numbering of a reference species; placing them on another sequence needs an alignment. | A residue mapping from an alignment (MolSysMT) can be applied to curated sites (#30). | 2026-09-23 |
| [SABIO-RK](http://sabiork.h-its.org/) | Non-commercial use only (HITS terms, CC BY-NC). Reviewed 2026-09-29 (#94): the non_commercial profile could admit it, but its site and REST API did not answer that day. | Its services answer, and kinetics a target needs that BRENDA (CC BY 4.0) does not give; then for the non_commercial profile only. | 2026-09-25 |
| [CovPDB](https://bioinfo.fudan.edu.cn/CovPDB/) | Did not answer on 2026-09-29. | It answers again; covalent complexes are also in the PDB. | 2026-09-25 |
| [PDBbind-CN](http://www.pdbbind.org.cn/) | Did not answer on 2026-09-29, and needs registration; affinities also come from ChEMBL and BindingDB. | It answers, and its terms fit MOLI. | 2026-09-25 |
| [OpenBind](https://openbind.uk/) | Open-science structures and affinities; most reach Sabueso through the PDB and ChEMBL already. | A target has data here that the PDB and ChEMBL do not hold. | 2026-09-25 |
| [Fragalysis / XChem](https://fragalysis.diamond.ac.uk/) | Open-science structures and affinities; most reach Sabueso through the PDB and ChEMBL already. | A target has data here that the PDB and ChEMBL do not hold. | 2026-09-25 |
| [COVID Moonshot / ASAP Discovery](https://asapdiscovery.org/) | Open-science structures and affinities; most reach Sabueso through the PDB and ChEMBL already. | A target has data here that the PDB and ChEMBL do not hold. | 2026-09-25 |
| [ZINC (ZINC20 / ZINC-22)](https://zinc.docking.org/) | Free to use, but major portions may not be redistributed without written permission. | A purchasable-compound need that a permission or another open catalogue covers. | 2026-09-25 |
| [Enamine REAL Space](https://enamine.net/compound-collections/real-compounds) | A commercial catalogue. | A licence covering MOLI use. | 2026-09-25 |
| [eMolecules](https://www.emolecules.com/) | A commercial catalogue; data downloads may need a licence agreement. | A licence covering MOLI use. | 2026-01-31 |
| [ChemSpider](https://www.chemspider.com/) | API key and usage conditions; PubChem and UniChem cover identity. | A structure or name need that PubChem, ChEBI and UniChem do not cover. | 2026-01-31 |
| [PiSITE](https://pisite.pdbj.org/) | Did not answer on 2026-09-27/29; interfaces come from PDBe-KB. | It answers again, and a need PDBe-KB does not cover appears. | 2026-01-31 |
| [CPPsite](https://webs.iiitd.edu.in/raghava/cppsite/) | Cell-penetrating peptides need peptide cards, which are scoped before any source (use case 5). | Peptide cards are scoped. | 2026-01-31 |

## Retired

| Resource | Reason | Since |
| --- | --- | --- |
| [SCOPe](https://scop.berkeley.edu/) | Removed with the per-database card tools; classifications come from UniProt and InterPro. | 2026-09-23 |
| [TED (The Encyclopedia of Domains)](https://ted.cathdb.info/) | Removed with the per-database card tools. | 2026-09-23 |
| [PhosphoSitePlus](https://www.phosphosite.org/) | Removed with the per-database card tools; its licence restricts redistribution. | 2026-09-23 |

## Out of scope for Sabueso

| Resource | Reason | Belongs to | Since |
| --- | --- | --- | --- |
| [TeachOpenCADD](https://projects.volkamerlab.org/teachopencadd/) | Software and tutorials, not a knowledge source. | Praxis (methodology) and MolSysSuite | 2026-09-25 |
| [ProLIF](https://prolif.readthedocs.io/) | A computation on structures, not a knowledge source. | MolSysSuite | 2026-09-25 |
| [Open Drug Discovery Toolkit (ODDT)](https://github.com/oddt/oddt) | Software, not a knowledge source. | MolSysSuite (DockingMT) | 2026-09-25 |
| [PoseBusters](https://github.com/maabuu/posebusters) | A validation tool for modelling results, not a knowledge source. | MolSysSuite (DockingMT) and Praxis | 2026-09-25 |
| [PPI3D](http://bioinformatics.ibt.lt/ppi3d/) | An interface search and modelling service: a computation on structures, not a knowledge source. | MolSysSuite | 2026-09-25 |
| [MoDEL Library](https://mmb.irbbarcelona.org/MoDEL/) | Molecular dynamics trajectories, not source knowledge about entities. | MolSysSuite | 2026-09-25 |
| [Proteins.plus (DoGSiteScorer)](https://proteins.plus/) | A computation service (pockets, descriptors), not a knowledge source. | MolSysSuite | 2026-09-25 |
| [D3R (Drug Design Data Resource)](https://drugdesigndata.org/) | A benchmark and challenge dataset, not a knowledge source. | Praxis (methodology) and MolSysSuite (evaluation) | 2026-09-25 |
| [CACHE Challenge](https://cache-challenge.org/) | A hit-finding challenge, not a knowledge source. | Praxis (methodology) and MolSysSuite (evaluation) | 2026-09-25 |
| [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) | AI-ready benchmark datasets, not a knowledge source. | MolSysSuite and Praxis | 2026-09-25 |
| [CSAR](http://www.csardock.org/) | A benchmark set for scoring functions (and unreachable on 2026-09-29). | MolSysSuite (evaluation) | 2026-09-25 |
| [RNA-Puzzles](https://rnapuzzles.org/) | A structure-prediction assessment, not a knowledge source. | MolSysSuite (evaluation) | 2026-09-25 |
| [IUPAC resources](https://iupac.org/) | Nomenclature and standard definitions, not entity knowledge; listed in the original plan without detail. | MOLI (shared terminology), if needed | 2026-01-31 |
