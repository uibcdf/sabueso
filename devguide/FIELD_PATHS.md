# Sabueso — Canonical Field Paths

This document defines the **canonical field paths** for Sabueso cards. These are the
paths used by mappings, resolver rules, evidence objects, and downstream tools.

Versioning: **x.y.z** (no leading `v`).

---

## 1) Global Base Paths (all card types)

### meta.*
- `meta.entity_type`
- `meta.created_at`
- `meta.updated_at`
- `meta.sources`

### identifiers.*
- `identifiers.uniprot`
- `identifiers.pdb`
- `identifiers.chembl`
- `identifiers.pubchem`
- `identifiers.drugbank`
- `identifiers.inchi`
- `identifiers.inchikey`
- `identifiers.smiles`
- `identifiers.other` (list/dict for rare IDs)

### names.*
- `names.canonical_name`
- `names.synonyms`
- `names.abbreviations`

### properties.*
- `properties.physchem.formula`
- `properties.physchem.molecular_weight`
- `properties.physchem.logp`
- `properties.physchem.tpsa`
- `properties.physchem.hbd`
- `properties.physchem.hba`
- `properties.physchem.rotatable_bonds`
- `properties.physchem.aromatic_rings`
- `properties.physchem.molecule_type`

### annotations.*
- `annotations.function`
- `annotations.catalytic_activity`
- `annotations.pathway`
- `annotations.subunit`
- `annotations.subcellular_location`
- `annotations.tissue_specificity`
- `annotations.organism`
- `annotations.go_terms`
- `annotations.domains` (non-positional summary)

### features_positional.*
- `features_positional.domains` (positional domains)
- `features_positional.active_site`
- `features_positional.binding_site`
- `features_positional.modified_residue`
- `features_positional.disulfide_bond`
- `features_positional.glycosylation`

### interactions.*
- `interactions.binding_partners`

### clinical.*
- `clinical.pharmacology`
- `clinical.admet`
- `clinical.clinical_trials`
- `clinical.pharmacovigilance`
- `clinical.indications`
- `clinical.contraindications`
- `clinical.interactions`

### quality.*
- `quality.conflicts`
- `quality.notes`

---

## 2) ProteinCard Extensions

- `annotations.enzyme_class`
- `annotations.family`
- `annotations.similar_proteins`
- `annotations.isoforms`
- `disease.associations`
- `ligands.items` (each has `role` + evidence)
- `sequence.primary`
- `structure.primary`

---

## 3) PeptideCard Extensions

- Same as ProteinCard, but may omit `structure.*` if not available.

---

## 4) SmallMoleculeCard Extensions

- `annotations.drug_class`
- `clinical.*` (same keys as base)

---

## Notes
- `annotations.domains` and `features_positional.domains` are both valid.
- If only positional data exists, populate `features_positional.domains`.
- If only non-positional data exists, populate `annotations.domains`.
- If both exist, keep both.
