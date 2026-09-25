# Sabueso — Canonical Field Paths

This document defines the **canonical field paths** for Sabueso cards. These are the
paths used by mappings, resolver rules, SourceAssertions, and downstream tools.

Versioning: **x.y.z** (no leading `v`).

---

## 1) Global Base Paths (all card types)

### meta.*
- `meta.card_id`
- `meta.schema_version`
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
- `identifiers.smiles` (isomeric: keeps stereochemistry where the source defines it)
- `identifiers.smiles_connectivity` (connectivity only, no stereochemistry)
- `identifiers.gene_loci` (list of `{database, id}`: gene loci in organism databases, e.g. `{"database": "TriTrypDB", "id": "TcCLB.508647.200"}` from UniProt's VEuPathDB cross-references, and `{"database": "NCBI Gene", "id": "7167"}`; identity anchors that tell paralogs apart, #54)
- `identifiers.other` (list/dict for rare IDs)

### names.*
- `names.canonical_name`
- `names.synonyms`
- `names.abbreviations`

### properties.*
- `properties.physchem.formula`
- `properties.physchem.molecular_weight` (quantity node, `dalton`)
- `properties.physchem.logp`
- `properties.physchem.tpsa` (quantity node, `angstrom ** 2`)
- `properties.physchem.hbd`
- `properties.physchem.hba`
- `properties.physchem.rotatable_bonds`
- `properties.physchem.aromatic_rings`
- `properties.physchem.molecule_type`

### annotations.*
- `annotations.function`
- `annotations.catalytic_activity` (list of `{reaction, ec_number, rhea_id, molecule?}`)
- `annotations.pathway`
- `annotations.subunit`
- `annotations.subcellular_location` (list of `{location, topology?, orientation?, molecule?}`)
- `annotations.disease` (list of `{name, accession?, acronym?, description?, cross_references?, note?}`; UniProt DISEASE comments, with their evidences in each SourceAssertion's `eco`)
- `annotations.tissue_specificity`
- `annotations.organism`
- `annotations.taxon_id` (NCBI taxonomy id; strain-level when the entry is, #54)
- `annotations.lineage` (list of taxon names from the root down, the organism itself excluded, as UniProt states it, #54)
- `annotations.ptm`
- `annotations.polymorphism`
- `annotations.domains` (non-positional summary; reserved, not currently produced)

### features_positional.*
- `features_positional.domains` (positional domains)
- `features_positional.active_site`
- `features_positional.binding_site`
- `features_positional.family_site` (sites an InterPro member database places on the sequence, e.g. CDD catalytic triad; one item per site, with its signature)
- `features_positional.modified_residue`
- `features_positional.disulfide_bond`
- `features_positional.natural_variant` (a variant observed in a population: substitution, verbatim description, `VAR_` id, dbSNP)
- `features_positional.mutagenesis` (a substitution the authors made, with the effect they report)
- `features_positional.glycosylation`

### clinical.*
- `clinical.pharmacology`
- `clinical.pharmacokinetics`
- `clinical.pharmacodynamics`
- `clinical.admet`
- `clinical.clinical_trials`
- `clinical.pharmacovigilance`
- `clinical.adverse_events`
- `clinical.toxicity`
- `clinical.indications`
- `clinical.contraindications`
- `clinical.interactions`
- `clinical.dosing`
- `clinical.regulatory_status`
- `clinical.max_phase` (ChEMBL highest development phase: 4 approved, 3–1 clinical, 0.5 early phase 1, -1 unknown)

### quantities.*
The seal over every quantity node of a stored card (uibcdf/sabueso#32):
- `quantities.*` (PyUnitWizard QuantityRecordBundle; one column per path and unit)

### quality.*
Records of how the card was resolved and enriched, not source-stated fields:
- `quality.conflicts` (disagreements among comparable assertions)
- `quality.alternatives` (values of different methods, representations or sources, not compared)
- `quality.enrichments` (per-source enrichment outcomes)
- `quality.entity_resolution` (resolution trace)

---

## 2) ProteinCard Extensions

- `annotations.enzyme_class`
- `annotations.family`
- `annotations.similar_proteins`
- `annotations.isoforms`
- `disease.associations`
- `sequence.primary`
- `sequence.length`
- `sequence.molecular_weight` (quantity node, `dalton`)
- `sequence.checksums` (`crc64`, `md5`)
- `structure.primary`
- `structure.secondary_structure`
- `structure.chains`
- `structure.entities`

---

## 3) PeptideCard Extensions

- Same as ProteinCard, but may omit `structure.*` if not available.

---

## 4) SmallMoleculeCard Extensions

- `annotations.drug_class`
- `clinical.*` (same keys as base)

---

## Notes
- GO annotations, family/domain classifications, curated interactions and experimental
  structures are **relationships**, not field paths: `annotated_with`, `classified_in`,
  `interacts_with` and `has_structure` (see the Relationship contract in `SCHEMA.md`).
- `annotations.domains` and `features_positional.domains` are both valid.
- If only positional data exists, populate `features_positional.domains`.
- If only non-positional data exists, populate `annotations.domains`.
- If both exist, keep both.
