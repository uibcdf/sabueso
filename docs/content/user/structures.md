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
- per chain, the UniProt ranges that have coordinates (`observed`);
- per chain, the helices and strands the entry assigns, in UniProt numbering, with the
  program that assigned them (`secondary_structure`, e.g. PROMOTIF).
- per chain, for a membrane protein, the transmembrane segments each resource RCSB
  integrates assigns, in UniProt numbering, each resource apart (`membrane_segments`:
  OPM, PDBTM).

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
(`missing_in_region`), the chains that have them all (`complete_chains`), and the
region's positions in a helix or a strand (`secondary_structure_in_region`). A chain the
entry assigns no secondary structure to is left out: not stated, never coil.

Each structure has a derived `state`:

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
side, grouped by state (rule `structure_inventory@2`). A state that every protein has is
marked `shared`: it is where like can be compared with like, e.g. the apo wild-type
dimers of two orthologs.

```python
from sabueso.core.deck import Deck

focus, _ = sabueso.resolve("P52270", structures="all")
other, _ = sabueso.resolve("P60174", structures="all")
deck = Deck([focus, other])
regions = {focus.id: [[12, 20]], other.id: [[12, 20]]}  # each in its own numbering
inventory = deck.structure_inventory(regions=regions)
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

### Explain an inventory item

The relationship-scoped behavior below is development work for 0.15.0.
Published 0.14.0 uses explanation @1 and has no `relationship_id` selector.

Pass the same inventory options to `deck.explain`, with the protein's card id and a
`structure_ref`:

```python
why = deck.explain(focus.id, structure_ref="pdb:1SUX", regions=regions)
print(why["status"], why["reason"], why["item"], why["group"])
for member in why["members"]:
    print(member["relationship_ref"])
    for assertion in member["source_assertions"]:
        print(assertion["source_assertion_ref"], assertion["asserted_value"])
```

`structure_inventory_explanation@3` records every protein card's exact pin and the
normalized options, including residue maps. `rules` names the coverage, state and
inventory rules. For a grouped item, `members` holds the stored relationship and
supporting SourceAssertions of **every member of its group**. Each reference is pinned
to the card state read. The statements retain their own subject, source, version,
retrieval and acquisition, together with retrieval-archive links when recorded.

When several retained relationships name the same PDB, a reference-only request
returns `status="ambiguous"`, every original candidate and its relationship-level
support. It does not choose a declaration. Pass the exact original id to select one:

```python
if why["status"] == "ambiguous":
    for candidate in why["candidates"]:
        print(candidate["relationship_id"], candidate["relationship_ref"])
    # Choose the original declaration you want to inspect.
    selected_id = input("Exact relationship id to inspect: ")
    one_declaration = deck.explain(
        focus.id,
        structure_ref="pdb:1SUX",
        relationship_id=selected_id,
        regions=regions,
    )
    assert one_declaration["relationship_id"] == selected_id
```

The id is scoped to that Card and structure. A different/missing id returns
`not_on_card`; it never falls back to another declaration. Human explorer items
already know their exact relationship id, so `item.explain()` selects that row
directly. Exact original row/state membership binds group support, even when
several groups share a PDB label. An excluded fragment does not exclude an admitted
sibling. Existing saved @1 readings retain their original policy without backfill.
Rows and support members count retained declarations. Repeated PDB labels do not
establish distinct physical structures, independent observations or experiments.

Experimental declarations now use `experimental_structure_admission@1`. Their
subject must match the protein explicitly named by the Card id; its retained
UniProt identifier must agree and have no identity conflict. Missing or foreign
subjects and uncertain Card identities remain in `card.structures()["unplaced"]`
(or `deck.structure_inventory()["unplaced"][card.id]`), with the original
relationship, reason and source locations. They never enter focal groups. This
scopes a declaration; it does not validate a sequence/coordinate mapping or merge
entities. An exact explanation of such a declaration has `status="unplaced"` and
keeps its original source support. In the human explorer, `view.exclusions` also
lists these records with their explanations, apart from display filters. An empty
admitted set does not mean the protein has no structures.

Compact pages include `declaration_admission`: counts refer to the whole captured
inventory before display filtering, with a bounded inspection link for excluded
and unplaced originals. Those counts do not describe independent experiments or
external absence. An inapplicable or identity-less request instead reports
`status="not_evaluated"` with null counts and link, retaining the original reason.
Reading an available link makes no source query:

```python
reader = focus.access()
page = reader.select("structures", fields=["structure_ref"]).page(max_bytes=8192)
admission = page["declaration_admission"]
print(admission["unplaced_declarations"])
originals = reader.read(admission["exclusions_location"]).page(max_bytes=8192)
```

Fragment exclusion remains a separate option. `include_fragments=True` does not
admit a foreign subject. Inventory Card ids must be distinct: separate snapshots
with equal ids cannot be addressed independently by that result. Original saved
inventory @1 and explanation @1/@2 readings retain their original decisions.

The experimental regional reader still has a separate original-reference gap
([#170](https://github.com/uibcdf/sabueso/issues/170)): a selected sequence changed
against its retained source support can receive an old coordinate projection.
Regional outputs currently describe retained mapping qualifiers; they do not
certify that those coordinates belong to the current selected sequence.

Other `status` values are `grouped`, `excluded`, `not_inventoried` or `not_on_card`. Excluded fragments
keep their classification; unknown states keep the inventory's reason. `not_on_card`
means no such relationship is recorded, never that the structure does not exist.
Conflicts, unknown values and assembly disagreements remain inspectable.

Support is attributed to the relationship (`support_basis: relationship`), rather than
inventing separate attribution for each qualifier. `reference_context` shows the pinned
card's sequence and length with their support and conflicts. These are stored context;
older mappings did not record the exact sequence and length they read when building
their qualifiers. The explanation does not claim to recover those historical inputs.

Explaining reads stored knowledge and does not contact a source. To revisit an exact
historical state, save the deck and load its returned pin:

```python
store = sabueso.KnowledgeStore("knowledge.db")
deck_ref = store.save_deck(deck, "comparison")
historical = store.load_deck(deck_ref)
why = historical.explain(focus.id, structure_ref="pdb:1SUX", regions=regions)
assertion = why["members"][0]["source_assertions"][0]
stored = store.source_assertion(assertion["source_assertion_ref"])
```

The pin stays readable after another acquisition is saved. A store lacking that pin
raises an error. Saving is required before resolving the returned item references in a
store; computing an explanation does not save anything.

## Predicted structures

`sabueso.resolve(..., predicted_structures=True)` adds the AlphaFold DB models of a
protein, and `card.predicted_structures()` lists them:

- the model version and the mean pLDDT with its bands;
- the range covered;
- the whole-sequence checksum comparison against the original reference input;
- the isoform only where UniProt explicitly states that membership. A different
  accession alone does not establish an isoform.

In development, `predicted_structure_scope@1` verifies the stored
`alphafold_sequence_context@1` inputs instead of using present Card fields as a
substitute. Coverage refers to the **original whole-reference input** and is
computed only for a source-declared focal accession, supported matching MD5 and
valid whole-sequence range/length. It describes the declared sequence span, not
observed atoms or experimental equivalence. Partial fragments, missing/conflicting
inputs, other accessions and unbound historical context remain uncomputed.
`coverage_scope`, `context_state` and the complete `sequence_context` explain the
result. `recorded_isoform` and `recorded_sequence_matches` preserve old flags
without certifying their missing original basis. A differing checksum does not
identify the cause or age of a sequence difference. Migration reports the gap;
refresh acquires a new context while the original pin remains unchanged.

Models are kept apart from experimental structures: `card.structures()` never counts
them.

## Secondary structure and isoforms (UniProt)

A protein card keeps what UniProt states about both:

- `features_positional.secondary_structure`: helix, strand and turn segments, in UniProt
  numbering. Each one names the structures it was read from (`structures`, e.g.
  `["pdb:9F69"]`), and one entry often mixes several. They describe those structures,
  not the protein in every state or construct. For one structure and chain, use the
  structure's own `secondary_structure` (above).
- `annotations.isoforms`: the isoforms of the entry, with their ids, names, synonyms and
  sequence status. `annotations.alternative_products` keeps what produces them and
  UniProt's note on the list (e.g. "Additional isoforms seem to exist.").
- `features_positional.alternative_sequence`: the segment each isoform replaces or
  lacks, with the isoforms the entry links to it. A segment an isoform lacks is
  `substitution: {"missing": true}`.

```python
card, _ = sabueso.resolve("P60174")
for item in card.get("features_positional.secondary_structure")["value"][:3]:
    print(item["element"], item["location"]["sequence"]["start"], item["structures"])
```

An entry with no isoform list gives `not_stated` in `card.knowledge_state()`, never "one
isoform". Isoform sequences are not fetched.

## Oligomer, interfaces and ligand sites

What sources state about the oligomer, the interfaces between chains and the residues
ligands contact is in {doc}`sites_and_interfaces`.
