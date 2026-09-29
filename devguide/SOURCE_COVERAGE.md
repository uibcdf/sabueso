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
| Variants | protein | human first | UniProt variants and mutagenesis, ClinVar (#83) | gnomAD |
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
| gnomAD | population variants | human | CC0 1.0 (core); some annotations CC BY-NC | gene, variant ids | Frequencies; large |
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

## 5. Next waves

- Wave 2: the remaining queued sources by category (structures and models; sites and
  families; interactions; chemistry and ADMET; bioactivity; emerging modalities;
  benchmarks).
- Wave 3: the architecture for many sources (#83, part 3), informed by what waves 1 and
  2 show that sources need.
