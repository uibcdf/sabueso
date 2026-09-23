# Ligand binding sites (PDBe-KB)

PDBe-KB states, for each ligand seen in a protein's structures, the residues it contacts,
in UniProt numbering. Sabueso records them as `has_ligand_site` relationships and puts
them next to the sites UniProt annotates:

```python
import sabueso

card, _ = sabueso.resolve_protein_card("P52270", structures=["1SUX"], ligand_sites=True)
view = card.ligand_sites()

for site in view["annotated_sites"]:  # UniProt active and binding sites, with ECO codes
    print(site["kind"], site["start"], site["ligand"], site["evidence"])

for item in view["items"]:
    print(item["ligand"], item["positions"], item["site_class"], item["spans_chains"])
print(view["classification"])  # rule annotated_site_overlap@1
```

- `site_class` is derived by Sabueso: an exact residue match against the annotated sites.
  `no_annotated_overlap` does not mean the ligand binds elsewhere, because annotations are
  sparse.
- `spans_chains` says whether one ligand instance contacts more than one chain. It is
  read from RCSB per-instance contacts of the structures the card holds, and it is `None`
  when none are available. PDBe-KB aggregates ligand copies, so its chains cannot answer
  this.
- `is_solvent` and `significance` are PDBe-KB's own descriptors. The PDB flag
  `subject_of_investigation` is shown next to them; neither overrides the other.

Clients: `sabueso.tools.db.pdbe_kb.OnlinePDBeKBClient` and `FixturePDBeKBClient`.
PDBe-KB data is CC BY 4.0; cite the PDBe-KB consortium paper.
