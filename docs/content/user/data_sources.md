# Data sources

<!-- Generated from devguide/sources/registry.yaml by
     `python tools/source_registry.py --write`. Do not edit by hand. -->

The online resources Sabueso uses, has set aside, or has yet to review. To
propose one, open a discussion in the **Data sources** category of the
repository's GitHub Discussions; triage adds it here as *queued*.

Summary: in use 17, evaluating 1, queued 48, deferred 8, retired 3, out of scope 4.

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
| [NCBI Gene / RefSeq](https://www.ncbi.nlm.nih.gov/gene/) | Targets, sequence and basic pharmacology | via UniProt cross-references | US public domain (NLM policy) | 2026-09-25 |
| [VEuPathDB gene identifiers](https://veupathdb.org/) | Organism, orthology and biological context | via UniProt cross-references | Identifiers only | 2026-09-25 |

## Being evaluated

| Resource | Category | What it would bring | Since |
| --- | --- | --- | --- |
| [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy) | Organism, orthology and biological context | Taxonomic names, ranks and lineages; would make strain–species relations exact (today they are read from UniProt names and lineages). | 2026-09-25 |

## Queued for review

| Resource | Category | What it would bring | Since |
| --- | --- | --- | --- |
| [CACHE Challenge](https://cache-challenge.org/) | Benchmarks, open challenges and open-science consortia | Blind computational hit-finding challenges with independent experimental validation. | 2026-09-25 |
| [COVID Moonshot / ASAP Discovery](https://asapdiscovery.org/) | Benchmarks, open challenges and open-science consortia | Open collaborative discovery: chemical series, affinities, synthesis and structures without IP barriers. | 2026-09-25 |
| [CSAR](http://www.csardock.org/) | Benchmarks, open challenges and open-science consortia | High-resolution crystallographic complexes for evaluating scoring functions. | 2026-09-25 |
| [D3R (Drug Design Data Resource)](https://drugdesigndata.org/) | Benchmarks, open challenges and open-science consortia | Blind challenges and datasets with experimental affinities for docking and free-energy prediction. | 2026-09-25 |
| [Fragalysis / XChem](https://fragalysis.diamond.ac.uk/) | Benchmarks, open challenges and open-science consortia | Crystallographic data from open fragment-screening campaigns at Diamond. | 2026-09-25 |
| [OpenBind](https://openbind.uk/) | Benchmarks, open challenges and open-science consortia | Open initiative generating protein–ligand structures and affinity profiles at scale. | 2026-09-25 |
| [RNA-Puzzles](https://rnapuzzles.org/) | Benchmarks, open challenges and open-science consortia | Blind community assessment of RNA tertiary structure prediction. | 2026-09-25 |
| [Target 2035 / SGC](https://www.thesgc.org/) | Benchmarks, open challenges and open-science consortia | Selective chemical probes and negative controls for understudied targets. | 2026-09-25 |
| [Therapeutics Data Commons (TDC)](https://tdcommons.ai/) | Benchmarks, open challenges and open-science consortia | Standardised AI-ready datasets for drug design, affinity and ADMET. | 2026-09-25 |
| [PDBbind-CN](http://www.pdbbind.org.cn/) | Binding affinity and experimental bioactivity | 3D complexes paired with experimental binding affinities (core and refined sets). | 2026-09-25 |
| [ChEBI](https://www.ebi.ac.uk/chebi/) | Chemical space, synthesis, ADMET and safety | Ontology of chemical entities, endogenous metabolites and cofactors. | 2026-09-25 |
| [Enamine REAL Space](https://enamine.net/compound-collections/real-compounds) | Chemical space, synthesis, ADMET and safety | Billions of make-on-demand molecules from validated reactions. | 2026-09-25 |
| [SureChEMBL](https://surechembl.org/) | Chemical space, synthesis, ADMET and safety | Chemical structures text-mined from patents. | 2026-09-25 |
| [Tox21 / ToxCast](https://www.epa.gov/chemical-research/toxicity-forecasting) | Chemical space, synthesis, ADMET and safety | In vitro toxicity screening profiles, cellular stress and assay-interference flags. | 2026-09-25 |
| [ZINC (ZINC20 / ZINC-22)](https://zinc.docking.org/) | Chemical space, synthesis, ADMET and safety | 3D models of purchasable and make-on-demand compounds for virtual screening. | 2026-09-25 |
| [PROTAC-DB](http://cadd.zju.edu.cn/protacdb/) | Emerging modalities (targeted degradation) | Targeted-degradation chimeras: E3 ligases, warheads, linkers, ternary complexes and DC50/Dmax. | 2026-09-25 |
| [2P2Idb](http://2p2idb.cnrs-mrs.fr/) | Protein–protein interactions and structural modulation | Curated structures of protein–protein complexes modulated by orthosteric small molecules, with interface parameters and druggability. | 2026-09-25 |
| [iPPI-DB](https://ippidb.pasteur.fr/) | Protein–protein interactions and structural modulation | Non-peptide inhibitors and modulators of protein–protein interactions, with pharmacological, chemical and structural data. | 2026-09-25 |
| [PPI3D](http://bioinformatics.ibt.lt/ppi3d/) | Protein–protein interactions and structural modulation | Search, analysis and modelling of inter-chain interfaces and complexes (Voronoi tessellation). | 2026-09-25 |
| [SKEMPI 2.0](https://life.bsc.es/pid/skempi2/) | Protein–protein interactions and structural modulation | Changes in binding affinity (ΔΔG) and kinetics caused by mutations at protein–protein interfaces. | 2026-09-25 |
| [ASD (Allosteric Database)](http://mdl.shsmu.edu.cn/ASD/) | Binding sites, cavities and specialised families | Allosteric modulators, regulatory sites and conformational communication. | 2026-09-25 |
| [Binding MOAD](https://bindingmoad.org/) | Binding sites, cavities and specialised families | High-resolution complexes linked to validated binding affinities. | 2026-09-25 |
| [BRENDA](https://brenda-enzymes.org/) | Binding sites, cavities and specialised families | Enzyme information: kinetics (Km, kcat), inhibitors, cofactors and conditions. | 2026-09-25 |
| [CovPDB](https://bioinfo.fudan.edu.cn/CovPDB/) | Binding sites, cavities and specialised families | Covalent protein–ligand complexes, with nucleophilic residues and warheads. | 2026-09-25 |
| [GPCRdb](https://gpcrdb.org/) | Binding sites, cavities and specialised families | GPCR structures, mutations, activation states and Ballesteros–Weinstein numbering. | 2026-09-25 |
| [KLIFS](https://klifs.net/) | Binding sites, cavities and specialised families | Kinase pocket anatomy aligned to 85 reference positions, with DFG/αC conformations. | 2026-09-25 |
| [mpstruc](https://blanco.biomol.uci.edu/mpstruc/) | Binding sites, cavities and specialised families | Membrane proteins of known structure, classified by topology and family. | 2026-09-25 |
| [OPM (Orientations of Proteins in Membranes)](https://opm.phar.umich.edu/) | Binding sites, cavities and specialised families | Position and orientation of PDB structures in the lipid bilayer. | 2026-09-25 |
| [Proteins.plus (DoGSiteScorer)](https://proteins.plus/) | Binding sites, cavities and specialised families | Pocket detection, physico-chemical descriptors and druggability scores (a computation service). | 2026-09-25 |
| [SAbDab / Thera-SAbDab](https://opig.stats.ox.ac.uk/webapps/sabdab/) | Binding sites, cavities and specialised families | Antibody and nanobody structures with standard numbering, CDRs and clinical metadata. | 2026-09-25 |
| [SABIO-RK](http://sabiork.h-its.org/) | Binding sites, cavities and specialised families | Kinetic constants of purified biochemical reactions under stated conditions (REST API). | 2026-09-25 |
| [sc-PDB](http://bioinfo-pharma.u-strasbg.fr/scPDB/) | Binding sites, cavities and specialised families | Druggable binding sites extracted from the PDB, cleaned of crystallographic artefacts. | 2026-09-25 |
| [CoDNaS](https://codnas.inf.unlp.edu.ar/) | Macromolecular structures, models and dynamics | Conformational diversity of native states: experimental conformers in the PDB. | 2026-09-25 |
| [ESM Metagenomic Atlas](https://esmatlas.com/) | Macromolecular structures, models and dynamics | Structures predicted at scale by a protein language model. | 2026-09-25 |
| [MoDEL Library](https://mmb.irbbarcelona.org/MoDEL/) | Macromolecular structures, models and dynamics | Standardised atomistic molecular dynamics trajectories and conformations. | 2026-09-25 |
| [ModelArchive](https://modelarchive.org/) | Macromolecular structures, models and dynamics | Open repository of computational macromolecular models with mmCIF metadata. | 2026-09-25 |
| [NDB (Nucleic Acid Database)](https://ndbserver.rutgers.edu/) | Macromolecular structures, models and dynamics | Structures and conformations of nucleic acids and their complexes. | 2026-09-25 |
| [ProThermDB](https://web.iitm.ac.in/bioinfo2/prothermdb/) | Macromolecular structures, models and dynamics | Experimental protein stability data (ΔΔG, Tm) for point mutations. | 2026-09-25 |
| [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) | Target validation, genetics and functional networks | Human genomic variants and their clinical significance. | 2026-09-25 |
| [DepMap](https://depmap.org/) | Target validation, genetics and functional networks | CRISPR and RNAi screens of gene essentiality and dependencies in cancer cell lines. | 2026-09-25 |
| [DGIdb](https://dgidb.org/) | Target validation, genetics and functional networks | Aggregated drug–gene interactions and druggability categories. | 2026-09-25 |
| [gnomAD](https://gnomad.broadinstitute.org/) | Target validation, genetics and functional networks | Population allele frequencies, e.g. to assess the conservation of a binding pocket. | 2026-09-25 |
| [KEGG PATHWAY](https://www.kegg.jp/) | Target validation, genetics and functional networks | Metabolic and signalling pathway maps and human diseases. | 2026-09-25 |
| [Open Targets Platform](https://platform.opentargets.org/) | Target validation, genetics and functional networks | Integrated target–disease association evidence, tractability for small molecules and biologics, preclinical data. | 2026-09-25 |
| [PharmacoDB](https://pharmacodb.pmgenomics.ca/) | Target validation, genetics and functional networks | Harmonised pharmacogenomic screens and cellular dose–response curves. | 2026-09-25 |
| [Reactome](https://reactome.org/) | Target validation, genetics and functional networks | Curated human pathways, reactions and signalling networks (REST API). | 2026-09-25 |
| [TTD (Therapeutic Target Database)](https://idrblab.org/ttd/) | Target validation, genetics and functional networks | Molecular targets, their clinical status, diseases and resistance mutations. | 2026-09-25 |
| [Ensembl](https://www.ensembl.org/) | Targets, sequence and basic pharmacology | Gene and transcript annotation, homology and population variants. | 2026-09-25 |

## Deferred

| Resource | Reason | Revisit when | Since |
| --- | --- | --- | --- |
| [VEuPathDB services (expression by stage, phenotype screens)](https://veupathdb.org/) | A large connector; structured fields for biological context should be used first, through curation. | Curated biological-context fields are in use and a workflow needs them for many genes. | 2026-09-25 |
| [BioGRID](https://thebiogrid.org/) | The API needs a personal access key; IntAct (via UniProt) and STRING cover current needs. | Genetic interactions are needed, or key management exists for deployments. | 2026-09-23 |
| [DrugBank (open data)](https://go.drugbank.com/) | Licensing constrains redistribution and caching; only DrugBank ids are kept, through UniChem. | A licence compatible with Sabueso's caching and redistribution is confirmed. | 2026-09-23 |
| [Guide to PHARMACOLOGY (IUPHAR/BPS)](https://www.guidetopharmacology.org/) | Its web services now need a personal API key (HTTP 401 without one), its data is under ODbL (share-alike), and UniProt links neither test target to it. | A target of interest has a GuidetoPHARMACOLOGY cross-reference in UniProt, and key management exists for deployments (as for BioGRID). | 2026-09-25 |
| [BioLiP](https://zhanggroup.org/BioLiP/) | Bulk downloads of a third-party pipeline, not a per-record service; the PDB subject-of-investigation flag already separates ligands from additives, and PDBe-KB gives contacts. | A batch import exists, or a question needs curated biologically relevant sites that PDBe-KB and the PDB flag do not give. | 2026-09-23 |
| [M-CSA (Mechanism and Catalytic Site Atlas)](https://www.ebi.ac.uk/thornton-srv/m-csa/) | Evaluated: it links both TIMs to an entry but states catalytic residues and roles only in the numbering of a reference species; placing them on another sequence needs an alignment. | A residue mapping from an alignment (MolSysMT) can be applied to curated sites (#30). | 2026-09-23 |
| [BindingDB](https://www.bindingdb.org/) | Overlaps ChEMBL; without an identity of a measurement across sources, shared measurements would look like independent confirmations. | A design for the identity of a measurement across sources exists (#66). | 2026-09-25 |
| [PubChem BioAssay](https://pubchem.ncbi.nlm.nih.gov/) | Overlaps ChEMBL; without an identity of a measurement across sources, shared measurements would look like independent confirmations. | A design for the identity of a measurement across sources exists (#66). | 2026-09-25 |

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
