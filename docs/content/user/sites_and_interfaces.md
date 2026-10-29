# Sites and interfaces

Where ligands bind and where chains meet, as the sources state it: PDBe-KB from the
protein's structures, UniProt and InterPro from its sequence, and RCSB from each
structure's assemblies. Sabueso does not compute contacts from coordinates; that is
modelling.

## Ligand binding sites (PDBe-KB)

PDBe-KB states, for each ligand seen in a protein's structures, the residues it contacts,
in UniProt numbering. Sabueso records them as `has_ligand_site` relationships and puts
them next to the sites UniProt annotates:

```python
import sabueso

card, _ = sabueso.resolve_protein_card(
    "P52270", structures=["1SUX"], ligand_sites=True, family_sites=True
)
view = card.ligand_sites()

# UniProt active and binding sites (with ECO codes) and InterPro family sites
for site in view["annotated_sites"]:
    print(site["kind"], site["source"], site["description"], site["positions"])

for item in view["items"]:
    print(
        item["ligand_ref"], item["positions"], item["site_class"], item["spans_chains"]
    )
print(view["classification"])  # rule annotated_site_overlap@3
```

- `family_sites=True` adds the sites InterPro member databases place on the protein's
  own sequence (e.g. CDD catalytic triad, substrate binding site, dimer interface).
- `site_class` is derived by Sabueso: an exact residue match against the annotated sites,
  and each overlap names the annotation and its source. `no_annotated_overlap` does not
  mean the ligand binds elsewhere; proximity over coordinates is not computed (see
  uibcdf/sabueso#30).
- Comparison first checks the canonical sequence, original source support and exact
  coordinate scope (`ligand_site_coordinate_scope@1`). Unknown, foreign, uncertain,
  conflicting or unsupported coordinates stay visible in `recorded_annotation`,
  `recorded_residues` and the corresponding `scope` / `comparison` reason.
  `comparison_not_computed` is not a negative overlap. A positive can be `partial`
  when other annotations could not be compared; a negative requires every retained
  annotation to be comparable. Unstated sequence revisions remain explicit and do
  not establish revision agreement. This compares source-declared numbering, not
  atomic contacts or proximity. `no_annotated_sites` only describes this Card.
- `spans_chains` says whether one ligand instance contacts more than one chain. It is
  read from RCSB per-instance contacts of the structures the card holds, and it is `None`
  when none are available. PDBe-KB aggregates ligand copies, so its chains cannot answer
  this.
- `is_solvent` and `significance` are PDBe-KB's own descriptors. The PDB flag
  `subject_of_investigation` is shown next to them; neither overrides the other.

Clients: `sabueso.tools.db.pdbe_kb.OnlinePDBeKBClient` and `FixturePDBeKBClient`.
PDBe-KB data is CC BY 4.0; cite the PDBe-KB consortium paper.

## Oligomer and interfaces

The examples below describe development behavior planned for 0.15.0: default
`interface_site_agreement@3` and `oligomer_explanation@3`. Published 0.14.0 uses
`@2`; explicit historical readers remain available as described below.

`card.oligomer()` puts together what sources state about a protein's quaternary
structure:

```python
card, _ = sabueso.resolve_protein_card(
    "P52270", structures="all", interfaces=True, family_sites=True
)
view = card.oligomer()

print(view["subunit"])  # Original subunit text and complete supporting source IDs
for entry in view["assemblies"]:  # RCSB biological assemblies, per structure
    print(entry["structure_ref"], entry["relationship_id"], entry["declaration_state"])
    if isinstance(entry["assemblies"], list):
        print(
            [
                a.get("oligomeric_state")
                for a in entry["assemblies"]
                if isinstance(a, dict)
            ]
        )
print(
    view["without_assembly_data"]
)  # structures without a retained assembly declaration

for interface in view["interfaces"]:  # PDBe-KB interface residues, per partner
    print(interface["partner_ref"], interface["class"], interface["positions"])
    print(interface["coordinate_scope"])
    print(interface["basis"])  # why, structure by structure

for row in view["agreement"]:  # family dimer interface vs observed interface
    print(row["family_site"], row["both"], row["family_only"], row["observed_only"])
```

- `interfaces=True` adds `has_interface_with` relationships from PDBe-KB.
- Each partner's `class` is derived by Sabueso (`interface_partner_class@2` in development):
  - `homomeric`: an admitted source interface whose two references name the same entry;
  - `heteromeric`: seen in a structure where the protein is neither a fragment nor a
    chimera with that partner;
  - `chimera`: the entity maps to both proteins, so the "partner" is the protein itself.
    For example, 3Q37 is a TcTIM/TbTIM chimera;
  - `fragment_complex`: the protein appears only as a peptide, for example a TIM peptide
    presented by HLA-DR;
  - `undetermined`: identity, source or structural context is missing, invalid or conflicting.
    Inspect its original classification inputs and reasons.
- Interfaces are not computed from coordinates; that is modelling (uibcdf/sabueso#30).

### Explain the stored oligomer view (since 0.13.0)

```python
explanation = card.explain_oligomer()
assert explanation["view"] == card.oligomer()
print(explanation["card_ref"], explanation["status"], explanation["gaps"])
for row in explanation["interfaces"]:
    print(row["item"]["class"], row["classification_inputs"])
    for support in row["interface"]["source_assertions"]:
        print(support["source_assertion_ref"], support["source"], support["version"])
```

Development behavior (planned 0.15.0) uses `oligomer_explanation@3`,
`interface_partner_class@2` and default `interface_site_agreement@3`. Each
structure declaration and original family index is preserved. Distinct declarations
with the same PDB label stay distinct; conflicting structure context does not
silently select the last one. Missing coverage does not establish a non-fragment
complex. An interface for another subject cannot become a focal self-interface.

The explanation keeps complete original relationships, source assertions,
selected and alternative field support, assembly methods, qualifiers, locators
and stored quality/request records. RCSB statements whose subject is the structure
are admitted only with their explicit native structure-to-focal-protein binding.
Relationship support does not reconstruct unrecorded per-qualifier mapping lineage.
Family signatures and assembly methods describe retained source information;
they are not locally executed analyses.

Every focal self-interface/family-annotation pair is compared separately after
source-bound canonical coordinate admission. Missing/foreign support, uncertain
endpoints, invalid/out-of-range positions, conflicting coordinates or incompatible
stated sequence revisions remain `not_computed`. Unstated revision agreement is
explicit. A partial result preserves qualified positives and uncomputed pairs.
`None` denotes an uncomputed residue set; an empty list is a computed empty set.
Neither means that an external source has no information. Source aggregates are
not projected into physical assembly occurrences or used to infer biological
relevance, affinity or geometry.

Published 0.14.0 used default `@2`. Both original interpretations remain available
explicitly for historical reproduction, including their original limitations:

```python
legacy = card.oligomer(agreement_rule="interface_site_agreement@2")
why_legacy = card.explain_oligomer(agreement_rule="interface_site_agreement@2")
assert why_legacy["view"] == legacy
```

Use explicit `@1` for the earlier integer-only interpretation. Original versions
are preserved; choosing them does not apply the corrected admission rules.

The same method works on `store.load(pin)`: later acquisition cannot rewrite
historical assertion/relationship references. Readers change no card, make no
source call and add no Ackredit credit. Keep original operation/attribution
sidecars separately when a workflow needs execution history and citation credit.
New full/index packets use `packet_aspects@14` (inheriting quaternary mapping `@12`), name agreement `@3` and include
its canonical reference and structure dependencies. Existing saved packets retain
their original rule, facts and hashes. The stored Card schema is unchanged.

## Interface mutations (SKEMPI 2.0)

SKEMPI 2.0 curates, from publications, how mutations at the interface of a complex of
known structure change its binding: the affinities of mutant and wild type, and, where
measured, kinetics and thermodynamics.

```{note}
Interface mutations are on main, not yet in a release (card schema 0.3.7).
```

```python
import sabueso

# Barnase, with its complex with barstar
card, _ = sabueso.resolve("P00648", structures=["1BRS"], skempi=True)
view = card.interface_mutations()
for item in view["items"]:
    for m in item["mutations"]:
        where = m.get("location", {}).get("start", m.get("not_placed"))
        print(
            item["structure"],
            m["original"],
            m["author_residue"],
            m["change"],
            m["on"],
            where,
        )
    print(item["affinity"], item.get("ddg"), item.get("method"), item.get("reference"))
print(view["rule"]["rule"])  # binding_ddg@1
```

- **Joined through stated identity.** A SKEMPI row joins the card only when UniProt
  states that one of the chains of its PDB entry is this protein. The protein names SKEMPI
  writes are kept as text, never used to join.
- **Placed through stated numbering.** SKEMPI writes mutations in the entry's author
  numbering (barnase's Lys 27 is UniProt's 74). A mutation is placed in UniProt numbering
  only through the author numbering RCSB states for that chain, so ask for the
  structures (`structures=[...]` or `"all"`), and only when its residue matches.
  Otherwise `not_placed` says why: `partner_chain` (the mutation is on the partner),
  `structure_not_loaded`, `author_residue_not_mapped` or `residue_mismatch`.
- **Quantities as stated.** Affinities are in molar, kinetics in 1/(M·s) and 1/s, ΔH in
  kcal/mol, ΔS in cal/(mol·K) and temperatures in kelvin. A bound (`>1E-04`) keeps its
  relation, "n.b." is `mutant_no_binding`, and SKEMPI's assumed 298 K is flagged
  (`temperature_assumed`).
- **ΔΔG is derived, never stored.** The view computes ΔΔG = R·T·ln(K_mutant /
  K_wild_type) under the rule `binding_ddg@1`. A bound gives a bound (`ddg_relation`),
  and when ΔΔG cannot be derived, `ddg_basis` says why.
