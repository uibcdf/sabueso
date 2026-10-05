# Bioactivities of a protein

Measured bioactivities come from ChEMBL, BindingDB and PubChem BioAssay, and from papers
a curator reads ({doc}`literature_and_curation`).

ChEMBL activity records of a resolved protein become `has_bioactivity` relationships from
the protein to each tested molecule. Each measurement is one relationship. It keeps
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

## Explain a stored measurement or class (since 0.13.0)

Use an item key or measurement group from the view being explained:

```python
item = view["items"][0]
group = item["measurements"][0]["group"]
measurement_support = card.explain_measurement(group)
class_support = card.explain_bioactivity(item["molecule_ref"])
# Pass the same include_indirect/thresholds options if the view used custom ones.
print(measurement_support["joins"], measurement_support["diagnostics"])
print(class_support["groups"])  # actual voters and each group's class
```

These read-only explanations carry named rules and exact pinned relationship and
SourceAssertion references, retaining original source versions. Group joins expose
publication/molecule keys, coarser precision as quantities and declared-copy selectors.
Each class group says which included records vote: copies do not vote alongside an
original, and copy-only fallback is explicit. Disagreement within a group remains
inconclusive; discordance across groups remains visible beside the strongest class.

Whole-card candidate/glossary inputs are separate context. Stored identity metadata
has locators into the pinned card, without invented assertion membership. Missing
source support is `partial`; an unknown native key is `not_on_card`, never inactive.
Load an original card pin from `KnowledgeStore` to explain that version. The readers
fetch no source, change no card and add no execution credit. They explain measured
molecule items; ligand deck crossings and binding-site classes remain separate work.

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

The readers released in 0.13.0 explain that crossing and a stored site:

```python
item = card.ligands(deck)["items"][0]
support = card.explain_ligand(item["molecule_ref"], deck)
for explained in support["items"]:
    print(explained["identity"], explained["bioactivities"], explained["sites"])
sites = card.ligand_sites()["items"]
if sites:  # When the card also holds ligand-site statements.
    site_support = card.explain_ligand_site(sites[0]["relationship_id"])
```

Protein and molecule support keep distinct pins, original source versions and
actual identity, class and name choices. Deck membership and its snapshot describe
the supplied deck; load the original saved deck separately for historical reads.
Duplicate members are retained as multiple partial items. Since 0.13.0,
`bioactivity.measurements` counts distinct included measurement groups across all
matched molecule records; `bioactivity.records` counts included source records.
An original and its declared copy are one group and two records, even when they
appear in separate matched molecule items. Counts do not imply independent
experimental confirmation. The named default is `ligand_measurement_count@2` (#118).

Release 0.12.0 counts source records in `bioactivity.measurements`. To reproduce
that numeric policy in development, pass
`counting_rule="ligand_measurement_count@1"` to `ligands`, `compare_ligands` or
`explain_ligand`. Both policies retain the new `records` field and
`measurement_counting` metadata. The explanation uses `ligand_deck_explanation@2`
and lists exact counted group/record ids beside the pinned source support.
Load historical card/deck pins separately; the count policy is explicit and changes
no stored card, measurement grouping, class voters or attribution.

Site support retains selected annotated fields, alternatives/conflicts and stored
structure instances. No annotated overlap is not external absence or proof of
binding elsewhere. Missing instance data keeps `spans_chains=None`; relevance
statements from different sources remain separate. These readers fetch nothing,
change no cards/decks and add no execution credit.


## A second source: BindingDB

`sabueso.resolve(..., chembl={}, bindingdb={})` adds BindingDB's affinities for the
protein. Many of them restate ChEMBL measurements, so Sabueso groups the records that
state one measurement (rule `measurement_identity@1`). Records from different sources
are grouped when they share the publication, the molecule (anchored at its InChIKey
through UniChem), the type, the relation, and a value that agrees at the coarser
stated precision (62 and 62.46 nM agree).

- `card.bioactivities()` counts measurements, not records: each item has
  `measurement_count`, `record_count` and `sources`, and each record its `group`.
- `view["measurement_identity"]["review"]` lists pairs with the same paper, type and
  value but different molecules according to the sources. These are worth reading,
  because one of the sources may have attributed the value to the wrong compound.
  Each pair of molecules is listed once. A pair is left out when both compounds are
  already matched to their own records: two compounds of one paper that happen to share
  a value.
- Records are never merged or dropped: every source keeps its own record and context.
- Up to 5000 records are asked by default, ordered by monomer id, type and value
  (`bindingdb_record_order@1`), and a cut is reported. `bindingdb={"limit": n}` asks
  for another number. Each kept monomer needs one UniChem lookup for its identity.

## A third source: PubChem BioAssay

`sabueso.resolve(..., pubchem_bioassay=True)` (or `{"limit": n}`) adds the results
PubChem states for the protein, all fetched in one request. Up to 5000 rows are kept by
default: confirmatory rows with a value first, then other rows with a value, then rows
without one (`pubchem_row_order@1`), and a cut is reported. Most are copies of ChEMBL or BindingDB data, and PubChem says so: each
assay names its depositor and the depositor's assay id.

- A copy joins its original through `copy_of` and does not vote alongside non-copy
  records. When only copies are included, the group uses an explicit copy-only
  fallback; these records remain copies, never independent confirmation. PubChem's
  table can drop the original relation (`>`).
- A copy whose original the card lacks leads to it: the ChEMBL assay it names is
  fetched from ChEMBL. This recovers measurements a truncated or target-based query
  missed.
- `card.explain_bioactivity(item_key)["measurement_identity"]["unresolved_copies"]`
  (since 0.13.0) retains the grouping engine's unresolved-copy diagnostics. The
  ordinary bioactivity view retains its existing groups, ambiguity and review output.
  The #117 fix released in 0.13.0 also reports missing activity-only originals, retaining
  the exact pointer and `original_not_on_card`. A later provenance or statement
  join removes that singleton diagnostic. This describes grouping on the stored
  card; it does not establish absence from an external source or prove that the
  named original was acquired. Raw `copy_of` remains in pinned relationship support.
