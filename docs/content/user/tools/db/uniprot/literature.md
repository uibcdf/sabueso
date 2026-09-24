# Literature on a card

`card.literature()` answers "which publications support which statements on this
card?". It does not read papers. It collects what sources state about publications:

```python
import sabueso

card, _ = sabueso.resolve("P60174", structures="all")
for pub in card.literature()["publications"]:
    print(pub["ref"], pub["year"], pub["title"])
    for cited in pub["cited_by"]:  # e.g. UniProt, with what it cites the paper for
        print("  cited for:", cited["scope"])
    print("  primary citation of:", pub["primary_citation_of"])  # PDB entries
    for s in pub["supports"]:  # statements whose evidence names the paper
        print("  supports:", s["field_path"], s["value"], s["evidence_code"])
```

- A publication is named `pubmed:<id>`, or `doi:<doi>` when it has no PubMed id. If it
  has neither, it keeps UniProt's own citation id (`uniprot.citation:<id>`).
- `cited_by` comes from `described_in` relationships: the references of the UniProt
  entry, with their scope (for example `HOMODIMERIZATION` or `VARIANT TPID ASP-105`).
- `primary_citation_of` lists the structures on the card whose primary citation it is.
  Only structures fetched from RCSB have one.
- `supports` lists the statements whose ECO evidence names the paper. UniProt's
  `Ref.<n>` evidences are resolved through the entry's reference numbers.
- A paper cited only as evidence (for example by a GO annotation) appears with its id
  and no title.

What a paper says beyond what a database states about it is not on the card yet: curated
literature assertions are uibcdf/sabueso#41, part 2.
