# Disease association

A human protein card can hold what DISEASES, Open Targets and Orphanet state about the
diseases its gene is associated with. Each source, and each DISEASES channel, is kept
apart.

```{note}
Disease associations are on main, not yet in a release.
```

```python
import sabueso

card, _ = sabueso.resolve("P60174", diseases={})  # human triosephosphate isomerase
for rel in card.relationships("associated_with"):
    q = rel["qualifiers"]
    print(rel["object_ref"], q["disease_name"], q["channel"], q.get("source_database"))
```

## Channels

- `knowledge` (default): associations curated by other resources (MedlinePlus, UniProt
  keywords…), with the resource and DISEASES's confidence.
- `experiments` (default): associations from experimental resources (for example GWAS
  through TIGA), with their own score.
- `textmining` (only when asked, `diseases={"channels": ["knowledge", "textmining"]}`):
  co-mentions in the literature, with a z-score. Text mining links **names**, not
  molecules. The human triosephosphate isomerase is co-mentioned with giardiasis,
  because the parasite's enzyme has the same name.

The same disease in two channels is two relationships, never merged. Scores are
DISEASES's own, as it states them; Sabueso does not rank them.

## How an association reaches the card

DISEASES names genes by Ensembl protein. An association is added only for an Ensembl
protein that the UniProt entry cross-references: `via_protein`, and `uniprot_isoform`
when UniProt maps it to an isoform. It is never matched by gene name.

## Open Targets

`sabueso.resolve("P60174", open_targets={})` adds Open Targets' associations, at most 100
per gene by default (`{"limit": n}`), in Open Targets' own order. A cut is reported with
a warning. Each association keeps:
- the overall `score`, `datatype_scores` (genetic association, literature, known
  drug…) and `rank`. They are Open Targets' own computation, recorded as stated with
  the data version, never recomputed;
- the disease under Open Targets' term (`mondo:MONDO:0014221`). The same disease under
  a DISEASES term (`doid:DOID:0050884`) stays a separate reference.

The association reaches the card through the Ensembl gene the UniProt entry
cross-references (`via_gene`). It is added only when Open Targets also lists the entry
among that gene's products.

## Orphanet (rare disorders)

`sabueso.resolve("P60174", orphadata=True)` adds the rare disorders Orphanet associates
with the gene (`orphanet:ORPHA:868`). Each one comes with Orphanet's wording:
- the association type (for example "Disease-causing germline mutation(s) in") and its
  status ("Assessed");
- the disorder's type and group;
- the publications that validate it.

Orphanet states the gene's UniProt accession itself, so the link is its own. The file
(about 22 MB) is downloaded once per process, and its date is the version.

## ClinVar (variants)

`sabueso.resolve("P60174", clinvar={})` adds ClinVar's variants of the gene
(`annotations.clinical_variants`), found by the NCBI Gene id the UniProt entry
cross-references. At most 500 per gene by default (`{"limit": n}`); a cut is reported.
Each variant keeps what ClinVar states:
- the HGVS title, variant type and consequences;
- the germline classification and its review status. "Conflicting classifications of
  pathogenicity" is ClinVar's own statement, never resolved;
- the conditions, with their cross-references.

**Numbering.** ClinVar lists a protein change in every isoform's numbering ("E142D,
E105D, E23D"). A variant is placed in UniProt numbering (`location`, `numbering:
"uniprot"`) only when two things hold: its transcript is one UniProt states for the
canonical isoform, and the residue ClinVar names is the UniProt residue at that
position. Otherwise `not_placed` says why: `no_protein_change`,
`transcript_not_canonical` or `residue_mismatch`.

ClinVar is not for diagnostic use without review by a genetics professional.

## gnomAD (population frequencies)

`sabueso.resolve("P60174", gnomad={})` adds gnomAD's variants of the gene with a protein
change, each with its allele count, allele number and frequency in exomes and genomes
(`annotations.population_variants`). They are placed in UniProt numbering by the same
rule as ClinVar, through an Ensembl transcript UniProt states for the canonical
isoform. Variants without a protein change are left out, and the enrichment record
counts them. At most 1000 per gene by default (`{"limit": n}`).

## Coverage

DISEASES, Open Targets, Orphanet and ClinVar cover human genes only. For a protein of another organism,
the knowledge state says `not_queried`, with that reason, never `not_stated`.

The files are downloaded once per process, about 50 MB with text mining. Set
`$SABUESO_CACHE_DIR` to keep them between sessions. The version recorded is each file's
publication date.
