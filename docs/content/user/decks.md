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
