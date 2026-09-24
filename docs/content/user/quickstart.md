# Quickstart

This guide walks through a minimal but real Sabueso workflow:

1. install
2. build Cards from online/offline sources
3. save/load Cards and Decks
4. run offline tests

## Prerequisites

- conda or mamba, with the `uibcdf` and `conda-forge` channels
- Python 3.11–3.14

## Install

Sabueso is distributed through the `uibcdf` conda channel:

```bash
conda install -c uibcdf -c conda-forge 'sabueso>=0.1.1'
```

To work on Sabueso itself, create the development environment instead and install the
checkout into it (pip is used only for this local, editable install):

```bash
conda env create -n sabueso-dev -f devtools/conda-envs/development_env.yaml
conda activate sabueso-dev
pip install --no-deps --editable .
```

## Resolve an entity (online)

`sabueso.resolve` takes any supported identifier and returns the entity's card together
with the resolution that explains it. You do not need to know which source or tool
applies:

```python
import sabueso
from sabueso.resolver import EntityQuery

protein, resolution = sabueso.resolve("P52270")  # a UniProt accession
print(resolution.status, resolution.decision["route"])

ligand, _ = sabueso.resolve("pdb.ligand:BTS")  # also chembl:<id> or inchikey:<key>

# A name needs an organism; if several entries match, the result is "ambiguous" and
# lists the candidates. Sabueso never picks one silently.
card, resolution = sabueso.resolve(
    EntityQuery(name="triosephosphate isomerase", organism=5693)
)
```

Options are passed to the tool that answers the query. For proteins these include
`structures`, `chembl`, `ligand_sites`, `interfaces` and `family_sites`; for molecules,
`unichem`. An option that does not apply is refused.

A **profile** names a versioned set of options, so a study states which baseline it builds:

```python
card, resolution = sabueso.resolve("P52270", profile="structural_baseline@1")
print(resolution.decision["profile"])  # name, the options it gave, those you overrode
```

- The profiles are `identity@1` and `structural_baseline@1`, listed in
  `sabueso/resolver/enrichment_profiles.json`.
- A published profile never changes; a change becomes a new version.
- Options you pass explicitly override the profile, and the override is recorded on the
  card.

## Query a source directly (online)

Every database module also returns its raw records, with when they were retrieved and
from which release, without building a card:

```python
from sabueso.tools.db import uniprot

entry = uniprot.get_entry("P52789")
print(entry["version"], entry["retrieved_at"], entry["record"]["primaryAccession"])
```

See {doc}`tools/db/sources` for every source.

## Create a Small Molecule Card (offline)

If you already have source JSON files, build a Card without network access.

```python
import sabueso

card = sabueso.create_molecule_card_from_file(
    "temp_data/CHEMBL90555.json",
    retrieved_at="2026-02-10",
)
print(card.id)  # sabueso:small_molecule:inchikey:OGWKCGZFUXNPDA-XQKSVPLYSA-N
print(card.get("identifiers.chembl"))
print(card.get("properties.physchem.molecular_weight"))
```

A small molecule card is anchored at the molecule's standard InChIKey, whichever source
the record comes from, so ChEMBL and PubChem records of the same structure give the same
card id. To resolve an identifier and link the molecule's records across sources, use
`sabueso.resolve_molecule_card("chembl:CHEMBL90555")`.

## Save and Load a Card

Cards support JSON and SQLite persistence.

```python
# Save
card.to_json("card.json")
card.to_sqlite("cards.db", id_field="identifiers.chembl")

# Load
loaded_from_json = card.__class__.from_json("card.json")
loaded_from_sqlite = card.__class__.from_sqlite(
    "cards.db",
    card_id="CHEMBL90555",
)
```

## Save and Load a Deck

Decks support JSONL and SQLite persistence.

```python
from sabueso.core.deck import Deck

deck = Deck([card])

# Save
deck.to_jsonl("deck.jsonl")
deck.to_sqlite("deck.db", id_field="identifiers.chembl")

# Load
loaded_deck_jsonl = Deck.from_jsonl("deck.jsonl")
loaded_deck_sqlite = Deck.from_sqlite("deck.db")
```

## Run Offline Tests

Run the full offline suite:

```bash
pytest -m "not online"
```

Run only schema alignment and validation:

```bash
pytest tests/core/test_schema_alignment.py \
       tests/core/test_card_schema_validation_offline.py \
       tests/core/test_deck_schema_validation_offline.py
```

## Next Steps

- Read {doc}`concepts` for Card/Deck/SourceAssertion/Resolver semantics.
- Review {doc}`field_paths` for canonical paths.
- Review {doc}`selection_rules` to understand canonical value selection.

