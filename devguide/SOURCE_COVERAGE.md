# Sabueso — Source coverage

Sabueso is MOLI's tracker of the outside world. The more sources it reaches, the more MOLI
can reason about, as long as every statement stays traceable and identity is never merged
by similarity. This document is the plan for reaching them (uibcdf/sabueso#83):

- what Sabueso should know;
- the rubric every source is evaluated with;
- the evaluations so far, in waves.

The registry (`sources/registry.yaml`) stays the source of truth for each source's
status. This document holds the reasoning across sources.

## 1. Knowledge areas

| Area | Entities | Organisms | Sources in use | Gap |
|---|---|---|---|---|
| Identity and names | all | all | UniProt, NCBI Gene, NCBI Taxonomy, UniChem, PubChem | Ensembl (queued) |
| Sequence and annotation | protein | all | UniProt, InterPro, GO, Rhea | isoform sequences |
| Structures and models | protein | all | RCSB PDB, AlphaFold DB | ModelArchive, ESM Atlas (queued) |
| Sites and families | protein | all | UniProt, PDBe-KB, InterPro | pockets and allosteric sites (queued) |
| Interactions | protein | all | IntAct (via UniProt), STRING | PPI-inhibitor resources (queued) |
| Bioactivity | molecule–protein | all | ChEMBL, BindingDB, PubChem BioAssay | PDBbind (queued) |
| Chemistry and ADMET | molecule | — | PubChem, PDB CCD, UniChem | ChEBI, Tox21/ToxCast (queued) |
| Clinical | molecule | human | ChEMBL max phase and indications, ClinicalTrials.gov (#81) | adverse events (openFDA, later) |
| Disease association | protein, disease | human | UniProt DISEASE comments, DISEASES, Open Targets, Orphanet (#82) | disease → targets (#82) |
| Variants | protein | human first | UniProt variants and mutagenesis, ClinVar, gnomAD (#83) | — |
| Pathways | protein | all | UniProt pathway (text), Rhea, Reactome (#83) | — |
| **Pathogen and organism context** | protein | pathogens | curation (#60), PHI-base | stage expression and screens (VEuPathDB), target prioritisation (TDR Targets): terms pending (#84) |
| Literature | all | all | UniProt citations, human curation | automated extraction (later) |

## 2. The rubric

Each source is checked live, and the date is recorded:

1. **Areas and fields** it would fill, and the **organisms** it covers.
2. **Access**: API or bulk files, key, rate limits, stability, and whether the site
   answers.
3. **Licence for MOLI**: can records be cached and redistributed across components
   (`LICENSING_AND_COMPLIANCE.md`)? Share-alike and non-commercial terms are flagged.
4. **Identity basis.** This is the decisive test. Does the source state identifiers
   that join a card: UniProt, InChIKey, NCBI Gene, Ensembl, PDB, EFO/MONDO? Or does it
   give names only? A source joined only by name needs another source that states the
   link (as ChEMBL does for ClinicalTrials.gov, #81), or it is not used.
5. **Versioning**: releases that can be recorded on every SourceAssertion.
6. **Derived content.** Scores or classes computed by the source (Open Targets
   association scores, TCRD development levels) are recorded as that source's
   statement, with its version, never recomputed or re-ranked by Sabueso.
7. **Overlap and cost**: what it adds over the sources in use, and the size of the
   connector.

## 3. Wave 1: target validation, disease and pathogen context (2026-09-27)

| Source | Areas | Organisms | Licence (checked 2026-09-27) | Identity basis | Notes |
|---|---|---|---|---|---|
| Open Targets | disease association, tractability | human | CC0 1.0 | Ensembl gene, listing its UniProt products | **In use** since 2026-09-28: associations, both sides stating the gene–protein link; tractability not yet |
| DISEASES (Jensen lab) | disease association | human | CC BY 4.0 | Ensembl proteins (joined through UniProt's cross-references); DOID | **In use** since 2026-09-28. Channels kept apart: curated knowledge, experiments, text mining (name-based, only when asked) |
| Orphadata | rare disease genes | human | CC BY 4.0, citing the data version | Swiss-Prot accession per gene (stated by Orphanet) | **In use** since 2026-09-28: typed, assessed associations |
| Pharos / TCRD | target development level | human | none of its own; each primary source's terms apply | UniProt, HGNC, Ensembl, NCBI Gene | The development level is TCRD's classification; licence tracing per field needed |
| Reactome | pathways | human, with inferred species | CC0 1.0 (data) | UniProt | **In use** since 2026-09-28; replaces the need for KEGG |
| KEGG | pathways | many | not public; licence needed beyond academic web use | KEGG ids | Deferred |
| ClinVar | variant clinical significance | human | Freely available; credit ClinVar; not for diagnostic use without professional review | NCBI Gene id; HGVS on RefSeq transcripts | **In use** since 2026-09-29; placed in UniProt numbering only through a canonical transcript UniProt states and a matching residue |
| gnomAD | population variants | human | CC0 1.0 (core); some annotations CC BY-NC (not read) | Ensembl gene; Ensembl transcripts | **In use** since 2026-09-29: protein-level variants and frequencies, placed through a canonical transcript |
| DepMap | essentiality in cancer cell lines | human | CC BY 4.0 (public release; some files differ) | gene ids | Bulk releases |
| DGIdb | drug–gene interactions | human | aggregated; each source keeps its terms | gene ids; drugs grouped by name normalisation | Its drug grouping merges by name, so a drug's identity would need re-anchoring |
| ClinicalTrials.gov | trials | human | US government work; NLM asks credit | NCT id; interventions as text only | **In use** since 2026-09-28, only through NCT ids ChEMBL states (#81) |
| TDR Targets | pathogen target prioritisation | NTD pathogens | not checked | not checked | Did not answer on 2026-09-27; recheck |
| PHI-base | pathogen–host phenotypes of mutants | 339 pathogens, trypanosomatids included | CC BY 4.0 (Zenodo releases) | UniProt accession per gene | **In use** since 2026-09-27; its HTTPS site did not answer from our network, but the releases are on Zenodo |
| VEuPathDB services | stage expression, RNAi/CRISPR phenotypes | eukaryotic pathogens | no licence statement found; a data release policy exists | VEuPathDB gene ids (in use, #54) | #60 step 2; terms to be asked of the providers |

### What wave 1 shows

- **Human disease knowledge is open and well identified.** Open Targets, DISEASES,
  Orphadata, Reactome, gnomAD and ClinVar are CC0, CC BY or public domain, and state gene
  or protein identifiers. Associations are per gene, so they reach a protein card only
  through the gene's stated products.
- **Pathogen-target knowledge is where the gap is.** None of the human sources covers a
  parasite protein. Of the sources that do, PHI-base is open (CC BY 4.0) and now in use.
  VEuPathDB and TDR Targets are unclear on terms or access, and the maintainers will ask
  them (#84). Meanwhile a connector may read them live, but nothing of theirs is
  committed or redistributed.
- **Integrated scores need care.** Open Targets and TCRD give scores and classes of
  their own. DISEASES keeps its evidence channels apart, which fits recording "who says
  this".

### Proposed order (for discussion)

1. **Clinical layer step 1** (#81): ChEMBL indications, and trials by stated NCT ids.
2. **Human disease association**: DISEASES (channels) and Open Targets (#82), with
   Orphadata for rare diseases.
3. **Pathways**: Reactome.
4. **Pathogen context**: settle VEuPathDB's terms and recheck TDR Targets and PHI-base,
   then #60 step 2.
5. **Variants**: ClinVar, then gnomAD.

## 4. Blocked and set aside (2026-09-28)

What cannot be used now, and why. The registry holds each decision with its reason and
when to look again.

| Source | Kind | Why | What would unblock it |
|---|---|---|---|
| VEuPathDB services (TriTrypDB…) | **blocked: key and terms** | Web services need a registered user's API key; no reuse terms found (#84) | An answer on terms and on per-user keys; a key from the user, never stored |
| iPPI-DB | **blocked: access and terms** | Targets, activities and InChIKeys only in HTML pages (the CSV has SMILES only, the API covers structures and cavities); no data licence found (2026-09-29) | A documented export or API, and stated terms (#84) |
| Chemical Probes Portal | **blocked: access** | No documented API or download; its search states target gene symbols but no UniProt accession or structure, target search needs a login, and accessions and InChI appear only in rendered pages (2026-09-30) | A documented export or API |
| TDR Targets | **blocked: unreachable** | Its site did not answer from our network (2026-09-27/28); no terms or API found | An answer from its maintainers (#84) |
| Guide to PHARMACOLOGY | **blocked: key and licence** | Personal API key needed; ODbL (share-alike) | Key management for deployments, and a target that needs it |
| BioGRID | **blocked: key** | Personal access key | Genetic interactions needed, and key management (#22) |
| KEGG | set aside: **licence** | Not public; services and downloads need a licence | A MOLI-wide licence, or a need Reactome (CC0) does not meet |
| DrugBank (clinical content) | set aside: **licence** | Full data CC BY-NC 4.0; only its CC0 vocabulary is open | A licence compatible with MOLI redistribution |
| PhosphoSitePlus | retired: **licence** | Restricts redistribution | — |
| M-CSA | set aside: **numbering** | Catalytic residues only in a reference species' numbering | A residue mapping from alignments (#30) |
| BioLiP | set aside: **bulk, overlap** | Bulk files of a third-party pipeline; PDBe-KB and the PDB flag cover ligand sites | A batch-import need |
| DGIdb | caution: **identity** | Groups drugs by name normalisation | Re-anchoring each drug at a stated identifier |
| SCOPe, TED | retired | Removed with the per-database card tools | — |
| TeachOpenCADD, ProLIF, ODDT, PoseBusters | out of scope | Software or computations, not knowledge | Belong to MolSysSuite or Praxis |

Three reasons recur:
- **Keys.** More sources now require a personal API key. A general rule is needed:
  a user supplies their own key through the environment; Sabueso never stores, logs
  or ships it, and records only that the source was reached with a key.
- **Licences** that forbid redistribution: KEGG, DrugBank and PhosphoSitePlus.
- **Identity by name**, as in DGIdb and in ClinicalTrials.gov's interventions. A second
  source that states the link solves it, as ChEMBL does for trials.

## 5. Wave 2: the remaining queued sources (2026-09-29)

Every queued source was checked: whether it answers, and its terms (from its own pages
or its maintainers' statements). **Caution:** some databases state only the licence of
the article that describes them (e.g. Oxford University Press's CC BY or CC BY-NC).
That is not a data licence, and is recorded as "no data licence found".

### Strong candidates (open terms, stated identifiers)

| Source | Area | Terms | Identity basis | Why |
|---|---|---|---|---|
| SKEMPI 2.0 | interactions | CC BY 4.0 (CSV) | PDB entry, chains, mutations in PDB numbering | Binding-energy changes of mutations at protein–protein interfaces; placed through author numbering (#73) |
| iPPI-DB | interactions | no data licence found (2026-09-29; the earlier "CC BY-SA 3.0" could not be confirmed) | UniProt targets; InChIKeys, in HTML pages only | Small-molecule modulators of protein–protein interactions; blocked (section 4) |
| ChEBI (2.0) | chemistry | CC BY 4.0; new JSON API | ChEBI ids (already linked through UniChem), InChIKey | Chemical roles and classes, metabolites, cofactors |
| Chemical Probes Portal | chemistry | CC BY-SA 4.0 (2026-09-30) | UniProt targets and structures, in rendered pages only | Expert-reviewed probes and their targets; blocked (section 4) |
| KLIFS | sites (kinases) | CC BY 4.0; REST API | UniProt / kinase ids; PDB | Kinase pocket residues and conformations |
| GPCRdb | sites (GPCRs) | CC BY 4.0; REST API | UniProt entry names; PDB | GPCR numbering, states, mutations |
| Ensembl | identity | No restrictions; REST API (15 req/s) | Ensembl gene, transcript, protein | Transcripts and orthology: supports variant placement (#85) |
| SureChEMBL | chemistry (patents) | CC BY 4.0 (API and new bulk data) | InChIKey / structures | Patent chemistry |
| SAbDab | structures (antibodies) | CC BY 4.0 | PDB, chains | Antibody structures; a modality Sabueso does not model yet |
| OPM | structures (membranes) | CC BY 3.0 | PDB | Membrane orientation of structures |
| ESM Atlas | predicted structures | CC BY 4.0; API | MGnify / sequence ids | Predicted models, like AlphaFold DB; mostly metagenomic |

### Usable only with a key, or with care

| Source | Why |
|---|---|
| BRENDA | CC BY 4.0, but its API needs a registered account (email and password): the key rule applies |
| Tox21 / ToxCast | Summary files CC0; the CTX API needs a key. Bulk files are usable |
| DGIdb, Pharos/TCRD | Aggregators: each field keeps its primary source's terms (wave 1) |

### Terms that do not fit MOLI redistribution

| Source | Terms |
|---|---|
| SABIO-RK | Non-commercial use only (HITS terms, CC BY-NC) |
| ZINC | Free to use, but no redistribution of major portions without permission |
| Enamine REAL, eMolecules | Commercial catalogues |
| ChemSpider | API key and usage conditions (already known) |

### No data licence found (the article's licence only), or not reachable

| Source | Status on 2026-09-29 |
|---|---|
| TTD | Only the article's CC BY-NC; downloads available |
| ProThermDB | Only the article's CC BY-NC; download by form |
| PROTAC-DB | Only the article's CC BY 4.0 |
| ModelArchive | Terms page gave no text |
| sc-PDB, ASD | Only the article's CC BY 4.0; data terms to confirm |
| mpstruc | No licence found |
| Binding MOAD | Sunset; its affinity backend licensed to Chemical Abstracts Service (deferred) |
| 2P2Idb, CoDNaS, CovPDB, PDBbind, CSAR, PiSITE | No answer; PDBbind also needs registration |
| PharmacoDB | HTTP 503 |

### Not knowledge sources for Sabueso (out of scope)

| Source | Belongs to |
|---|---|
| D3R, CACHE, CSAR, TDC, RNA-Puzzles | Benchmarks and challenges: Praxis (methodology) and MolSysSuite (evaluation) |
| PROTEINS+ | A computation service (pockets, descriptors): MolSysSuite |
| MoDEL | Molecular dynamics trajectories: MolSysSuite |
| NDB | Nucleic-acid structures: deferred until Sabueso has nucleic-acid entities |
| PPI3D | An interface search and modelling service: MolSysSuite |
| IUPAC resources | Nomenclature and definitions: MOLI terminology, if needed |
| CPPsite | Deferred until peptide cards are scoped |

Open-science data projects (OpenBind, Fragalysis, ASAP Discovery, SGC chemical probes)
are knowledge (structures, affinities, probes), but most of their data reach Sabueso
through the PDB and ChEMBL already. They are reviewed when a target needs them.

### Proposed order (wave 2)

1. **Interfaces:** SKEMPI (mutations and binding energy): **done** (2026-09-29, schema
   0.3.7). iPPI-DB (modulators): blocked on access and terms (section 4).
2. **Chemistry:** ChEBI roles and classes: **done** (2026-09-30, schema 0.3.8). The
   Chemical Probes Portal: blocked on access (section 4).
3. **Identity:** Ensembl transcripts and orthology, which also serve #85.
4. **Family-specific sources:** KLIFS and GPCRdb, when a target needs them.
5. **SureChEMBL**, and then structures: OPM, SAbDab, ESM Atlas.

## 6. Sources set aside, reviewed for terms profiles and keys (2026-09-29)

Terms profiles (#94) and personal keys (`tools/db/_keys`) change why some sources were
set aside. A source whose licence is non-commercial can fit the `non_commercial`
profile, and one that needs a key can take the user's own. Checked live on 2026-09-29:

| Source | Terms, as stated | Access | Profiles that admit it | Worth it |
|---|---|---|---|---|
| **BRENDA** | CC BY 4.0 (licence page) | SOAP service, registered account | every profile | **High:** Km, kcat, Ki and inhibitors per EC number and organism (TIM is EC 5.3.1.1) |
| **DrugBank** (full) | CC BY-NC 4.0, under DrugBank's Academic License (academic institution, research not primarily for a commercial third party) | download (204 MB, 5.1.22) with the user's account | `non_commercial`, with an academic account | **High:** the clinical layer still lacks pharmacology, mechanisms, interactions and transporters |
| DrugBank (Open Data) | CC0 (vocabulary, structures) | download, also behind a login (403) | every profile | Low: drug names and synonyms; identity already comes from UniChem |
| **BioGRID** | MIT | REST, personal key | every profile | Medium: genetic interactions IntAct does not hold |
| Guide to PHARMACOLOGY | database ODbL 1.0, contents CC BY-SA 4.0 | REST, personal key (401) | every profile, with share-alike | Medium: curated ligand-target pharmacology; no test target is linked yet |
| SABIO-RK | CC BY-NC (earlier review) | REST; did not answer | `non_commercial` | Low while BRENDA covers kinetics |
| KEGG | academic website use only; services need a licence, academic ones too | licence | none without a licence | stays out; Reactome covers pathways |
| ZINC | major portions may not be redistributed | downloads | none | stays out |
| PhosphoSitePlus | internal research use only: no downloads, no commercial use, no sharing, no automated access (terms read on 2026-09-29, beta site) | login | none | stays retired; querying it would need a written agreement with Cell Signaling Technology |

**Proposed order:**
1. **BRENDA**, for every profile.
2. **DrugBank**, full data for `non_commercial`. Its terms record states both the licence
   (CC BY-NC 4.0) and the access condition (the Academic License), so the report says
   which one binds.
3. **BioGRID**, then **Guide to PHARMACOLOGY** when a target needs them.

**What it needs from a user.** Each of the first three needs the user's own account or
key: a BRENDA account, a DrugBank academic account, a BioGRID key. Every source that needs
an account, a key or a licence is listed on the *Data sources* page and tracked in #95. Sabueso never stores,
logs or ships any of them. Fixtures are then the public responses of those accounts,
under each source's licence.

## 7. Next wave

- Wave 3: the architecture for many sources (#83, part 3), informed by what waves 1 and
  2 show that sources need:
  - keys supplied by users;
  - release caches;
  - one user agent;
  - numbering through stated maps.
