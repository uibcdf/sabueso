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
        print("  supports:", s["field_path"], s["value"], s["eco_code"])
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

## Curated literature assertions

When you read a paper, record what it states on the card. Sabueso keeps where the
statement comes from and compares it with what databases state:

```python
record = card.add_literature_assertion(
    "features_positional.natural_variant",
    {
        "start": 105,
        "substitution": {"original": "E", "alternatives": ["D"]},
        "description": "destabilizes the dimer",
    },
    publication="pubmed:18562316",  # or "doi:10...."
    curator="your-name",
    locator="Fig. 2",  # where in the paper
    quote="...",  # optional, a short excerpt (at most 300 characters)
)
print(record["outcome"])  # new, corroborates, differs, not_comparable or not_compared
```

- **Fields.** Knowledge fields only: `annotations.*`, `features_positional.*` and
  `properties.physchem.*`. A positional item can give `start` (and `end`) in the card's
  UniProt numbering instead of a full location.
- **Outcomes.** The same item, identified for example by position and substitution:
  - with the same content, it `corroborates`;
  - with a different content, it `differs`. It is recorded in `quality.conflicts` and a
    `CuratedDisagreementWarning` is shown.

  Sabueso cannot tell whether two texts mean the same thing, so it flags the
  difference for you to judge. Free-text fields such as `annotations.subunit` are
  `not_compared`.
- **Priority.** A curated assertion never takes priority automatically, and nothing is
  discarded or overridden.
- **Quantities.** Give the unit (`"0.825 kDa"`, `puw.quantity(825, "Da")`). The value is
  kept as written and compared at the precision it was stated with.
- **Relationships.** `card.add_literature_relationship(predicate, object_ref,
  qualifiers, publication=..., curator=...)` records an interaction, the residues at an
  interface, and so on. It merges with the same relationship from other sources, and
  qualifiers stated differently are kept as conflicts and flagged. Curated bioactivity
  measurements are not supported yet (uibcdf/sabueso#44).
- **Where it shows.** `card.literature()` lists each publication's curated assertions
  with their outcome.
- **Scope.** How a statement bears on a project's hypotheses is not Sabueso's: that is
  Evidence, in Nextia.
