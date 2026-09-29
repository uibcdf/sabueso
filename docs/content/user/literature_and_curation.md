# Literature and curation

What sources say about publications, and what a curator reads in them. A curated
statement is a SourceAssertion whose source is the paper: it is compared with the
databases, never given priority, and kept across rebuilds.

## Literature on a card

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

## Publications that mention the protein

`sabueso.resolve(..., europepmc={})` adds the publications whose text states the
protein's UniProt accession, found by Europe PMC's text mining of abstracts and
open-access full texts:

```python
card, _ = sabueso.resolve("P60174", europepmc={})  # or {"limit": 100}, newest first
for rel in card.relationships("mentioned_in"):
    print(rel["object_ref"], rel["qualifiers"]["year"], rel["qualifiers"]["title"])
```

- Only a stated accession counts. Europe PMC also tags gene and protein *names* with
  UniProt entries, but without the organism: "triosephosphate isomerase" in a paper on
  the human deficiency is tagged with a yeast entry. Sabueso does not use those.
- A mention says that the paper names the entry, not what it states about it. It
  appears in `card.literature()` under `mentions`, never as curated.
- These are not UniProt's curated references, which come as `described_in`
  (`cited_by`).
- Every article is fetched, up to 5000, and a cut is reported. HsTIM is mentioned in
  354.

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

- **Fields.** Knowledge fields only: `annotations.*` (see also the biological context
  below), `features_positional.*` (except
  family sites, alternative sequences and secondary structure), `properties.physchem.*`
  and `names.synonyms`. A positional item can give `start` (and `end`) in the card's
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

### Biological context of a target

Whether a protein is worth studying as a target in an organism depends on facts that
come from papers and organism databases. Four fields hold them, curated as above:

| Field | Item |
|---|---|
| `annotations.stage_expression` | `stage`, `observation`; optional `host`, `method`, `level`, `note` |
| `annotations.essentiality` | `method`, `phenotype`; optional `stage`, `host`, `condition`, `call`, `note` |
| `annotations.accessibility` | `compartment`; optional `exposure`, `stage`, `host`, `method`, `note` |
| `annotations.metabolic_role` | `pathway`, `role`; optional `stage`, `host`, `method`, `note` |

```python
card.add_literature_assertion(
    "annotations.essentiality",
    {"method": "RNAi knockdown", "phenotype": "growth arrest", "stage": "epimastigote"},
    publication="doi:10....",
    curator="your-name",
    locator="Fig. 3",
)
```

- **Values are text, as stated.** A phenotype is never turned into a category. `call`
  records the authors' own word, such as "essential", if they use one.
- **The organism is the card's.** A knockdown done on an ortholog is curated on the
  ortholog's card, not on this one.
- **Comparison.** Two statements under the same condition are compared: essentiality by
  method, stage, host and condition, the others by stage and host. Another stage is
  another statement.
- **Knowledge state.** A field nothing has been curated for is `not_queried` from
  `Literature`, never `not_stated`: nobody has read the literature for it yet.

For pathogen genes, databases also state some of this.
`sabueso.resolve(..., phi_base=True)` adds what PHI-base curates about mutants of the
gene (`annotations.pathogen_phenotypes`): for example "Lethal" for a knockout, or
"reduced virulence" on a host. Each item comes with its whole genotype, the pathogen and
host strains, the publication and the PHI-base release. The first use downloads a
PHI-base release, about 12 MB, and keeps its index in memory. To keep it between
sessions, set `$SABUESO_CACHE_DIR`.

The pathways a protein takes part in come from Reactome:
`sabueso.resolve(..., reactome=True)` adds `participates_in` relationships to its
lowest-level pathways and its reactions. Each pathway comes with its ancestors
(Glycolysis, Glucose metabolism, …, Metabolism), and each event with whether Reactome
inferred it from orthology.
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
- **How a compound acts on residues.** `card.add_literature_engagement(molecule,
  [{"position": 15, "residue": "Cys"}], "covalent", publication=..., curator=...,
  covalent_residue=15, method="mass spectrometry")`.
  - Positions are the entry's UniProt numbering. A residue code, when you give it,
    must match the entry's sequence.
  - The engagement is compared with the residues the same molecule contacts in
    structures (PDBe-KB): shared residues corroborate. Different ones are "not
    comparable", not a contradiction.
  - It shows in `card.ligand_sites()["curated_engagements"]`.
- **A claim that fits no field.** `card.add_literature_claim("interface", "…text…",
  publication=..., curator=..., about=["residues:15"])`.
  - The topic comes from a fixed list: interface, mechanism, selectivity, stability,
    inhibition, structure, dynamics, localization, expression, essentiality, pathway,
    other.
  - Claims are kept and listed by topic (`card.claims()`, `card.table("claims")`), but
    never compared, because two texts need a reader. Their outcome is `not_compared`.
- **Where it shows.** `card.literature()` lists each publication's curated assertions
  with their outcome.
- **Scope.** How a statement bears on a project's hypotheses is not Sabueso's: that is
  Evidence, in Nextia.

## How each statement entered

Every SourceAssertion records how it entered the card (`acquisition`). This is not a
measure of how true the statement is:

```python
card.acquisition()
# {"methods": {"database": {"UniProt": 412, ...}, "curation": {"Literature": 3}},
#  "origins": {"text_mining": {"DISEASES": 42}}, "extractions": []}
card.explain([source_assertion_id])[0]["acquisition"]
```

- `database`: imported from a source's record. When the source states that its record
  was mined from text, for example DISEASES's text-mining channel or Europe PMC's
  mentions, `origin` says `text_mining`.
- `curation`: a person read the publication and recorded it, as above.
- `rule_extraction` and `model_extraction`: extracted from a text by a named tool or
  model, with its version, run by Sabueso or by you. None is run yet. A model-extracted statement is
  never reported as curated.
- Cards saved before this was recorded read as `not_recorded` until they are built
  again.

Knowledge packets report the same per source, in their provenance.

## Names that papers use

A paper may call a protein by a name UniProt does not list, such as a paralog's
"TIM2". Record it once:

```python
card.add_literature_assertion(
    "names.synonyms", {"name": "TIM2"}, "pubmed:...", "curator"
)
store.save(card)
sabueso.resolve(EntityQuery(name="TIM2", organism=5722), curations=store)
```

Resolution then uses that anchor (rule `curated_name`), with the publication in its
decision. A name curated for two entries is reported as ambiguous. A name anchored
in another organism does not answer the query.

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

