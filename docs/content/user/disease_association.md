# Disease association

A human protein card can hold what DISEASES and Open Targets state about the diseases
its gene is associated with. Each source, and each DISEASES channel, is kept apart.

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

## Coverage

DISEASES and Open Targets cover human genes only. For a protein of another organism,
the knowledge state says `not_queried`, with that reason, never `not_stated`.

The files are downloaded once per process, about 50 MB with text mining. Set
`$SABUESO_CACHE_DIR` to keep them between sessions. The version recorded is each file's
publication date.
