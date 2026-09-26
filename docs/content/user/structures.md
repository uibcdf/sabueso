# Structures

A protein's structures are knowledge about the protein. Experimental structures are
`has_structure` relationships; predicted models are `has_predicted_structure`. The two
are never mixed, and no single structure stands for the protein. Sabueso retrieves what
the sources state about each structure; loading coordinates belongs to MolSysMT.

## Experimental structures

`sabueso.resolve(..., structures="all")` fetches from RCSB every PDB entry UniProt lists
for the protein (or pass a list of PDB ids). `card.structures()` then gives, per
structure:

- method, resolution, R-free and release date;
- UniProt ranges and coverage, with a derived coverage class (`full_length`, `partial`,
  `fragment_or_peptide`; fragments are excluded unless `include_fragments=True`, and the
  exclusion is reported);
- the construct: sample length, expression host and expression tags;
- the substitutions against the reference sequence (`N16D`, in UniProt numbering) and
  the modified residues;
- ligands, flagged when the PDB declares them the subject of investigation;
- per chain, the UniProt ranges that have coordinates (`observed`).

```python
import sabueso

card, _ = sabueso.resolve("P60174", structures="all")
view = card.structures(region=[[12, 20], [95, 100]])  # UniProt positions and ranges
for item in view["items"]:
    print(item["structure_ref"], item["resolution"], item["r_free"], item["released"])
    print("  ", item["state"], item["substitutions"], item["ligands_of_interest"])
    print("  ", item["complete_chains"], item["missing_in_region"])
print(view["excluded"])  # fragments and peptides, by default

rows = card.table("structures", region=[[12, 20]])  # the same, as flat rows
```

`region` adds, per chain, the residues of that region without coordinates
(`missing_in_region`), and the chains that have them all (`complete_chains`).

Each structure has a derived `state`, following the named rule `structure_state@1`:

- method and coverage class;
- sequence: `reference`, `mutant` (RCSB states an engineered mutation), `chimera`, or
  `differs` (a difference no source calls engineered);
- ligands: `ligand_of_interest`, `no_ligand_of_interest`, `no_ligands` or `unstated`;
- the oligomeric state of the assemblies the authors defined; the software's only when
  the authors defined none. `oligomer_basis` says which, and `oligomer_disagreement`
  flags a software prediction the authors' assemblies do not include. An example is
  2V5B, a monomerization structure that software predicts as a dimer;
- whether other entities are present (`in_complex`).

The state follows rule `structure_state@2`.

**Numbering.** Positions are in UniProt numbering. Depositors and papers often use their
own numbering, often the mature protein's. `author_substitutions` gives each substitution
as the authors number it (UniProt `E105D` is `E104D` in 2VOM). `author_numbering` gives,
per chain, the author residue numbers of UniProt positions;
`sabueso.mappings.rcsb_structures.author_position(segments, position)` reads them.

**Partial entries.** When RCSB fails on the per-chain data of an entry, the entry is kept
without it and recorded as `partial`, with a warning. What is missing (observed
residues, ligand contacts) is then `None`, never assumed.

A structure fetched before card schema 0.3.4 has no construct data, and its state is
`None`, never assumed. Refresh the card to fetch it again ({doc}`upgrading`).

## Several proteins side by side

`deck.structure_inventory(regions=...)` puts the structures of several proteins side by
side, grouped by state (rule `structure_inventory@1`). A state that every protein has is
marked `shared`: it is where like can be compared with like, e.g. the apo wild-type
dimers of two orthologs.

```python
from sabueso.core.deck import Deck

focus, _ = sabueso.resolve("P52270", structures="all")
other, _ = sabueso.resolve("P60174", structures="all")
inventory = Deck([focus, other]).structure_inventory(
    regions={focus.id: [[12, 20]], other.id: [[12, 20]]},  # each in its own numbering
)
for group in inventory["states"]:
    print(group["shared"], group["state"], group["structures"])
print(inventory["not_inventoried"])  # structures without a known state, with the reason
```

- **Regions per card.** Numbering differs between proteins, so give `regions` per card
  (`{card.id: region}`).
- **Unknown states.** Structures whose state is unknown are listed apart
  (`not_inventoried`), with the reason: not requested, not found, source error, or
  fetched before schema 0.3.4.
- **Choosing the grouping keys.** `group_by` chooses what defines a group. For example,
  `group_by=("method", "coverage", "sequence", "ligands:interest")` reads ligands
  coarsely: a structure without ligands and one with only additives are both
  `none_of_interest`.
- **Relating substitutions across proteins.** Give `residue_maps={card.id: {position:
  reference position}}` and `reference=other.id`, for example from a MolSysMT
  alignment.
  - Substitutions are then placed in the reference protein's numbering.
  - `shared_substitutions` lists those found in several proteins, e.g. E105D in both
    orthologs.
  - The key `substitutions` groups mutants by them.
  - Without a map, equal numbers in two proteins are never taken as equivalent
    positions.

The inventory states facts and groups them; it never chooses a structure.

## Predicted structures

`sabueso.resolve(..., predicted_structures=True)` adds the AlphaFold DB models of a
protein, and `card.predicted_structures()` lists them:

- the model version and the mean pLDDT with its bands;
- the range covered;
- whether the model is of the entry's current sequence;
- the isoform, when AlphaFold DB models one of the entry's isoforms. Such a model gives
  no coverage of the entry.

Models are kept apart from experimental structures: `card.structures()` never counts
them.

## Oligomer, interfaces and ligand sites

What sources state about the oligomer, the interfaces between chains and the residues
ligands contact is in {doc}`sites_and_interfaces`.
