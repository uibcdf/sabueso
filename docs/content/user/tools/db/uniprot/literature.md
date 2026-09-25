# Literature on a card

`card.literature()` answers "which publications support which statements on this
card?". It does not read papers. It collects what sources state about publications:

```python
import sabueso

card, _ = sabueso.resolve("P60174", structures="all")
for pub in card.literature()["publications"]:
    print(pub["publication_ref"], pub["year"], pub["title"])
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
  qualifiers stated differently are kept as conflicts and flagged. Bioactivity
  measurements have their own method, below.
- **Bioactivities read in a paper.** `card.add_literature_bioactivity(molecule,
  "IC50", "33 uM", publication=..., curator=..., target_assignment="direct")`.
  - The molecule can be a small-molecule card, an identifier (`chembl:`, `pubchem:`,
    `pdb.ligand:` or `inchikey:`), or a recorded identity. Sabueso keeps its InChIKey
    and every record linked to it.
  - The measurement is compared with ChEMBL's measurements from the same paper, the
    same molecule and the same type. ChEMBL now states each measurement's PubMed id.
  - Curated measurements appear in `card.bioactivities()`, marked `curated`.
    `target_assignment="homology"` (measured on an ortholog) is left out by default, as
    ChEMBL's homology assignments are.
  - A range is `value="10 uM", upper_value="20 uM"`. It is classified by its band when
    both ends share one, and as inconclusive when it spans a threshold.
  - An uncertainty the paper states goes in `uncertainty`:
    `{"kind": "sd", "value": "3 nM", "n": 3}` (also `"sem"`, or `"unspecified"` for a
    bare "±"), or `{"kind": "ci", "lower": "8 nM", "upper": "18 nM", "level": 0.95}`.
    It is part of the statement and appears in `card.bioactivities()` and the table.
    It does not change the class, which is read from the value itself. It does not change
    the comparison with ChEMBL either: both read the same paper, so they should state
    the same number.
- **Where it shows.** `card.literature()` lists each publication's curated assertions
  with their outcome.
- **Scope.** How a statement bears on a project's hypotheses is not Sabueso's: that is
  Evidence, in Nextia.

## Keep curations across rebuilds

A card is rebuilt whenever you query the sources again, for example to get a newer
UniProt release. Keep what you curated in a **curation store**, a JSONL file you own, and
apply it when the card is built:

```python
store = sabueso.CurationStore("curation.jsonl")
store.save(card)  # records the card's curated assertions; saving twice changes nothing

# Another day: the card is rebuilt from the sources, and the curations are applied.
card, _ = sabueso.resolve("P60174", curations=store)  # or curations="curation.jsonl"
print(card.quality["curation_store"])  # applied, skipped_retracted, changed
```

- **Same ids.** Each curated assertion gets back the same SourceAssertion id, because the
  id is derived from what was stated: publication, field, value and locator. A reference
  to it keeps meaning the same thing.
- **Recomputed outcomes.** Outcomes are compared again against the fresh sources. An
  outcome that changed since it was last recorded is listed in `changed`, for example
  `new` → `corroborates` when a database starts to state the same thing. Save again to
  record the outcome last seen.
- **Retraction.** `store.retract(source_assertion_id, reason, curator)` keeps the record,
  with who retracted it, why and when. It is never applied again.
- **Scope.** Records of other entities in the same store are ignored.

