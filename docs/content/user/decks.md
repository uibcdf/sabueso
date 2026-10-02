# Decks

A `Deck` is a collection of cards that a scientist can reproduce and cite. It records why
each card is in it, which candidates were left out, and how it was derived from another
deck.

## Building a deck, and saying why

```python
import sabueso
from sabueso.core.deck import Deck

deck = Deck([])
for accession in ("P52270", "Q4DV43"):
    card, resolution = sabueso.resolve(accession, taxonomy=True)
    deck.add(
        card,
        basis={
            "query": "TIM of trypanosomatids",
            "rules": resolution.decision["rules"],
        },
    )

deck.exclude(
    "sabueso:protein:uniprot:Q4DV43", reason="strain variant of P52270", by="curator"
)
print(deck.meta["membership"], deck.meta["excluded"])
```

- `add(card, basis=...)` records why a card belongs: a query, a rule, a curator
  (`meta["membership"]`).
- `exclude(candidate, reason, by=None)` leaves a candidate out, with its reason
  (`meta["excluded"]`). An exclusion needs a reason.
- `sabueso.ambiguity_deck(resolution)` turns the candidates of an ambiguous resolution
  into a deck, and `sabueso.ligand_deck(card)` builds the deck of a protein's ligands
  ({doc}`bioactivities`).

## Following relationships into a deck

`sabueso.expand(card, predicate)` follows a card's relationships and returns a deck of
the related entities' cards (rule `relationship_expansion@1`):

```python
diseases = sabueso.expand(card, "associated_with")
molecules = card.expand("has_bioactivity", limit=20)
both = deck.expand(["associated_with", "has_bioactivity"])  # from every card
```

- Each member's basis names the card it came from, and every relationship and
  SourceAssertion that brought it: source, record, version and retrieval time.
- Refs that name the same entity become one member, with all their statements. A DOID
  term from DISEASES, a MONDO term from Open Targets and an Orphanet code from Orphadata
  are one disease card when MONDO states it; a ChEMBL id and an InChIKey are one
  molecule when the molecule's sources state it.
- What cannot be followed is excluded, with the reason:
  - `no_card_type`: Sabueso has no card for it, e.g. a Reactome pathway;
  - `not_resolved: <status>`: the resolution did not give a card;
  - `limit`: past the limit (50 by default). Each member is a whole card, so the limit
    keeps expansion affordable. The entities with the most statements are followed
    first, and a cut is reported.
- `options` passes resolve options per entity type:
  `{"protein": {...}, "small_molecule": {...}, "disease": {...}}`. `terms` builds every
  member under a terms profile ({doc}`terms`).
- A predicate outside the relationship vocabulary is refused.

## Explaining why

`deck.explain(card_id)` answers why a card is in a deck: its membership basis, the rule
and origin of the deck, and the operations that derived it. For a candidate that was
left out, it gives the exclusion and its reason. A card's SourceAssertions are traced
back with `card.explain(source_assertion_ids)`:

```python
why = diseases.explain("sabueso:disease:mondo:MONDO:0014221")
ids = [a["id"] for s in why["basis"]["statements"] for a in s["source_assertions"]]
card.explain(ids)  # field, subject, source, record, version, retrieval, value
```

`deck.explain(card_id, structure_ref="pdb:1SUX", ...)` instead explains an item of the
structural inventory, including the pinned support of every member of its group. Pass
the same inventory options; see {doc}`structures`.

An id the card does not hold is reported as `found: False`, never dropped.

## Deriving decks

Each derived deck lists the operations that produced it in `meta["operations"]`. An
operation whose parameters cannot be recorded (a Python predicate) says so.

- `filter(predicate)` and `sort(field_path, reverse=False)`. Cards without a value go
  last.
- `intersect(other)` and `difference(other)`, by card id.
- `in_lineage(taxon)` keeps the cards whose organism is `taxon` or descends from it, by
  lineage name as UniProt states it (`"Trypanosomatida"`, `"Metazoa"`). Cards whose
  lineage is not stated are left out and listed in `meta["lineage_not_stated"]`: not
  stated is not "outside".
- `group_by(field_path)` groups cards by a resolved value, e.g. `annotations.taxon_id`.
- `group_by_rank(rank)` groups cards by genus, family or any NCBI rank. It needs cards
  built with `taxonomy=True`; cards without it are grouped under `None`. A misspelt rank
  is refused.

## Views across the deck

- **`identity_audit()`** reports redundant entries, strain variants, fragments and
  paralogs among the protein cards, each with its basis (rule
  `protein_identity_audit@1`). It never merges cards. When two entries state their gene
  in databases that do not overlap, the basis says `gene_loci: not_comparable`. A
  resolution by name can ask NCBI Gene to decide it: pass `ncbi_gene=True`
  ({doc}`resolving`).
- **`unique_names(return_cards=False)`** lists the distinct names the cards carry
  (canonical names, synonyms, abbreviations and gene names), as `numpy.unique` lists
  distinct values.
  - Spellings that differ only in case, spaces or hyphens are one name.
  - With `return_cards=True` it also gives, per name, the cards that carry it.
  - Names are shared on purpose: "TIM" abbreviates the enzyme's name, so every
    organism's triosephosphate isomerase carries it. A shared name never joins cards;
    accessions and gene loci identify an entry.
- **`structure_inventory(...)`** puts the proteins' structures side by side, grouped by
  state ({doc}`structures`).
- **`summarize(field_paths)`, `compare(other, key_fields)`, `map(fn)`**: tabular summaries
  and comparisons.

## Saving and citing a deck

```python
store = sabueso.KnowledgeStore("knowledge.db")
ref = store.save_deck(deck, "trypanosomatid_tims", note="first cohort")
print(ref)  # sabueso:deck:trypanosomatid_tims@sha256:… pins this exact revision
same = store.load_deck(ref)  # each card in the state it was saved in
```

Decks can also be written as JSONL or SQLite files (`deck.to_jsonl(path)`,
`deck.to_sqlite(path, ...)`, `Deck.from_jsonl(path)`, `Deck.from_sqlite(path, ...)`), which
keep the deck's meta. See {doc}`storage`.
