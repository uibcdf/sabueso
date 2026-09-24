# Ligand binding sites (PDBe-KB)

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
    print(item["ligand"], item["positions"], item["site_class"], item["spans_chains"])
print(view["classification"])  # rule annotated_site_overlap@2
```

- `family_sites=True` adds the sites InterPro member databases place on the protein's
  own sequence (e.g. CDD catalytic triad, substrate binding site, dimer interface).
- `site_class` is derived by Sabueso: an exact residue match against the annotated sites,
  and each overlap names the annotation and its source. `no_annotated_overlap` does not
  mean the ligand binds elsewhere; proximity over coordinates is not computed (see
  uibcdf/sabueso#30).
- `spans_chains` says whether one ligand instance contacts more than one chain. It is
  read from RCSB per-instance contacts of the structures the card holds, and it is `None`
  when none are available. PDBe-KB aggregates ligand copies, so its chains cannot answer
  this.
- `is_solvent` and `significance` are PDBe-KB's own descriptors. The PDB flag
  `subject_of_investigation` is shown next to them; neither overrides the other.

Clients: `sabueso.tools.db.pdbe_kb.OnlinePDBeKBClient` and `FixturePDBeKBClient`.
PDBe-KB data is CC BY 4.0; cite the PDBe-KB consortium paper.

# Oligomer and interfaces

`card.oligomer()` puts together what sources state about a protein's quaternary
structure:

```python
card, _ = sabueso.resolve_protein_card(
    "P52270", structures="all", interfaces=True, family_sites=True
)
view = card.oligomer()

print(view["subunit"])  # UniProt SUBUNIT text, with its evidence
for entry in view["assemblies"]:  # RCSB biological assemblies, per structure
    print(entry["structure"], [a["oligomeric_state"] for a in entry["assemblies"]])
print(view["without_assembly_data"])  # structures the card has not fetched from RCSB

for interface in view["interfaces"]:  # PDBe-KB interface residues, per partner
    print(interface["partner_ref"], interface["class"], len(interface["positions"]))
    print(interface["basis"])  # why, structure by structure

for row in view["agreement"]:  # family dimer interface vs observed interface
    print(row["family_site"], row["both"], row["family_only"], row["observed_only"])
```

- `interfaces=True` adds `has_interface_with` relationships from PDBe-KB.
- Each partner's `class` is derived by Sabueso (`interface_partner_class@1`):
  - `homomeric`: another copy of the protein;
  - `heteromeric`: seen in a structure where the protein is neither a fragment nor a
    chimera with that partner;
  - `chimera`: the entity maps to both proteins, so the "partner" is the protein itself.
    For example, 3Q37 is a TcTIM/TbTIM chimera;
  - `fragment_complex`: the protein appears only as a peptide, for example a TIM peptide
    presented by HLA-DR;
  - `undetermined`: the structures are not on the card. Pass `structures="all"` to fetch
    them.
- Interfaces are not computed from coordinates; that is modelling (uibcdf/sabueso#30).
