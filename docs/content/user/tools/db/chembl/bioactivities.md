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
print(view["classification"])  # rule bioactivity_class@3 and its thresholds
```

The classes (`active`, `weak`, `inactive`, `inconclusive`, `not_determined`,
`unclassified`) are derived by Sabueso from explicit thresholds. ChEMBL does not state
them. The thresholds are quantities: pass, for example,
`thresholds={"active_max": puw.quantity(1, "uM")}` or `thresholds={"active_max": "1 uM"}`
to change them (`active_max`, `weak_max`, `single_point_min`). A bare number is refused,
because its unit would be a guess. Pass `include_indirect=True` to include measurements
that ChEMBL assigned by homology.

Each measurement keeps ChEMBL's value and unit as stated (`value`, `units`). It also
carries `normalized`, a quantity in nanomolar (or percent), or None when ChEMBL's unit
cannot be normalized. The test concentration of a single-point measurement is also
returned as a quantity (`test_concentration`).

Two consistency checks add flags to a measurement. Both rules are listed in
`view["checks"]`:

- `pchembl_inconsistent`: ChEMBL's pChEMBL does not match -log10 of the normalized molar
  potency, to within 0.01. That is one unit of its second decimal; ChEMBL does not round
  half up.
- `scale_discrepancy:<orders>:<activity_id>`: another measurement of the same molecule,
  of the same type and with relation `=`, differs by exactly 3 or 6 orders of magnitude.
  This is the signature of a unit slip.

Neither check corrects a value; they point at the measurements to look at.

Clients: `sabueso.tools.db.chembl.OnlineChEMBLClient` and `FixtureChEMBLClient`.

## Ligand decks

Each measured molecule, and each ligand that a structure of the protein was determined
to study, becomes a SmallMoleculeCard anchored at its standard InChIKey. When a structure ligand and
a measured molecule have the same InChIKey, they share one card:

```python
card, _ = sabueso.resolve_protein_card("P52270", structures=["1SUX"], chembl={})
deck = sabueso.ligand_deck(card)
print(deck.meta["sources"], deck.meta["notes"])

for item in card.ligands(deck)["items"][:5]:
    # label: the name, else the ChEMBL id, else the PDB code (label_source says which)
    print(item["label"], item["bioactivity"], item["structures_of_interest"])

# Two proteins side by side, e.g. a parasite enzyme and its human counterpart.
other, _ = sabueso.resolve_protein_card("P60174", chembl={})
comparison = card.compare_ligands(deck, other, sabueso.ligand_deck(other))
print(len(comparison["shared"]), comparison["shared"][0])
```

By default, the deck keeps only the structure ligands that the PDB declares subject of
investigation: declared by the depositor, or assigned by RCSB for older entries. The
others, mostly crystallisation additives and ions, are listed in
`deck.meta["excluded_structure_ligands"]`. Being left out does not mean irrelevant; a
catalytic metal may not be flagged. Pass `structure_ligands="all"` to keep every ligand. Resolve a single molecule with
`sabueso.resolve_molecule_card("pdb.ligand:BTS")` (or `chembl:<id>`, `inchikey:<key>`).
