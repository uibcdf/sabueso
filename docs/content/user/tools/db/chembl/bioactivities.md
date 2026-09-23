# Bioactivities of a protein

ChEMBL activity records of a resolved protein become `has_bioactivity` relationships
from the protein to each tested molecule. Each measurement is one relationship. It keeps
the measured value, the assay (including how ChEMBL assigned it to the target) and the
document it comes from:

```python
import sabueso

card, resolution = sabueso.resolve_protein_card("P52270", chembl={})
# Outcome: added / not_found / error, with the ChEMBL release and any truncation.
print(card.quality["enrichments"])

view = card.bioactivities()
for item in view["items"][:5]:
    print(item["molecule_ref"], item["class"], item["best_pchembl"], item["classes"])
print(view["documents"])  # measurements per document: source bias is visible
print(view["excluded"])  # e.g. assays assigned to the target by homology
print(view["classification"])  # rule bioactivity_class@1 and its thresholds
```

The classes (`active`, `weak`, `inactive`, `inconclusive`, `not_determined`,
`unclassified`) are derived by Sabueso from explicit thresholds. ChEMBL does not state
them. Pass `thresholds={"active_max_uM": 1.0}` to change the thresholds, or
`include_indirect=True` to include measurements that ChEMBL assigned by homology.

Clients: `sabueso.tools.db.chembl.OnlineChEMBLClient` and `FixtureChEMBLClient`.

## Ligand decks

Each measured molecule, and optionally each ligand seen in the protein's structures,
becomes a SmallMoleculeCard anchored at its standard InChIKey. When a structure ligand and
a measured molecule have the same InChIKey, they share one card:

```python
card, _ = sabueso.resolve_protein_card("P52270", structures=["1SUX"], chembl={})
deck = sabueso.ligand_deck(card)
print(deck.meta["sources"], deck.meta["notes"])

for item in card.ligands(deck)["items"][:5]:
    print(item["name"], item["observed_in"], item["bioactivity"], item["structures"])

# Two proteins side by side, e.g. a parasite enzyme and its human counterpart.
other, _ = sabueso.resolve_protein_card("P60174", chembl={})
comparison = card.compare_ligands(deck, other, sabueso.ligand_deck(other))
print(len(comparison["shared"]), comparison["shared"][0])
```

Structure ligands are not filtered for crystallisation additives or ions, and
`deck.meta["notes"]` says so. Resolve a single molecule with
`sabueso.resolve_molecule_card("pdb.ligand:BTS")` (or `chembl:<id>`, `inchikey:<key>`).
