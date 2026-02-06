# Sabueso — Location Examples (Real IDs)

This document validates the **location model** using real identifiers. It does not finalize mapping logic; it only tests the shape of `location` for sequence, structure, atom, and substructure contexts.

## 1) Protein feature (sequence‑based)
**Entity:** UniProt **P52789** (from `temp_data/P52789.json`)

Example: a **binding site** feature observed in the UniProt JSON.

```
feature:
  type: "Binding site"
  location:
    kind: "sequence"
    sequence:
      sequence_id: "UniProt:P52789"
      start: 84
      end: 89
      indexing: "1-based"
  evidence_ids: ["E_UniProt_P52789_bs_84_89"]

example_evidence:
  evidence_id: "E_UniProt_P52789_bs_84_89"
  field: "features_positional.binding_site"
  value: { start: 84, end: 89 }
  source:
    type: "database"
    name: "UniProt"
    record_id: "P52789"
  retrieved_at: "2026-02-04"
```

## 2) Structure‑based location (ligand instance in PDB)
**Entity:** PDB **2NZT**

RCSB ligand validation lists **BG6** instances with identifiers like `2NZT_BG6_A_1002` and `2NZT_BG6_B_1002`, which encode **PDB ID**, **residue name**, **chain**, and **residue number**. citeturn0search0

```
feature:
  type: "Ligand instance"
  location:
    kind: "structure"
    structure:
      pdb_id: "2NZT"
      chain_id: "A"
      residue_id: "BG6"
      residue_number: 1002
  evidence_ids: ["E_RCSB_2NZT_BG6_A_1002"]

example_evidence:
  evidence_id: "E_RCSB_2NZT_BG6_A_1002"
  field: "structure.ligand_instances"
  value: "2NZT_BG6_A_1002"
  source:
    type: "database"
    name: "RCSB PDB"
    record_id: "2NZT"
  retrieved_at: "2026-02-04"
```

## 3) Small molecule (substructure‑based)
**Entity:** PubChem **CID 66414** (2‑methoxyestradiol)

A vendor page lists **SMILES** and **InChIKey** along with PubChem CID 66414. citeturn2search0turn2search3

We can represent a substructure location using a SMARTS pattern derived from the SMILES.

```
feature:
  type: "Substructure"
  location:
    kind: "substructure"
    substructure:
      smiles: "CC12CCC3C(C1CCC2O)CCC4=CC(=C(C=C34)OC)O"
      smarts: "c1ccc(OC)cc1"  # aromatic ring with methoxy group
  evidence_ids: ["E_PubChem_66414_substructure"]

example_evidence:
  evidence_id: "E_PubChem_66414_substructure"
  field: "features_positional.substructure"
  value: "c1ccc(OC)cc1"
  source:
    type: "database"
    name: "PubChem"
    record_id: "66414"
  source_meta:
    alias_source: "Fisher Scientific"
  retrieved_at: "2026-02-04"
```

## 4) ChEMBL identifier example (CHEMBL90555)
**Entity:** ChEMBL **CHEMBL90555** (Vincristine)

An external data page lists **SMILES** and links CHEMBL90555 to the compound. citeturn3search0
This can be used to populate identifiers and provide a fallback when the official API is not available.

```
identifiers:
  chembl_id: "CHEMBL90555"
  inchi_key: "OGWKCGZFUXNPDA-XQKSVPLYSA-N"
  smiles: "CCC1(CC2CC(C3=C(CCN(C2)C1)C4=CC=CC=C4N3)(C5=C(C=C6C(=C5)C78CCN9C7C(C=CC9)(C(C(C8N6C=O)(C(=O)OC)O)OC(=O)C)CC)OC)C(=O)OC)O"
```

---

## Notes
- The location model is **validated conceptually** with real IDs.
- Full sequence↔structure residue mapping for proteins is **pending** and will require dedicated mapping logic or external alignment resources.
- Atom‑level indices for small molecules should specify an `atom_id_type` once an internal representation (e.g., RDKit atom indexing) is chosen.

