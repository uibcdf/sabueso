---
summary: Which residues each ligand contacts, from which source, and how that relates to the protein's annotated sites.
issue: uibcdf/sabueso#28
status: partial
opened: 2026-09-23
closed:
verification: measured
area: [relationships, ligands, structures, pdbe-kb, rcsb, uniprot]
blocked_by: []
supersedes: []
---

# Summary

## What

Where on the protein each ligand binds, and how that relates to the functional site the protein already has annotated.

Three statements now meet on a protein card:

1. **UniProt annotated sites.** `features_positional.active_site` and `binding_site`, each with its ECO evidence. Binding sites now keep their ligand (name, ChEBI id, and the `label` that tells two sites of the same ligand apart). Before this, the mapping dropped the ligand.
2. **PDBe-KB ligand sites.** `has_ligand_site` relationships (protein → `pdb.ligand:<code>`): the residues each ligand contacts in UniProt numbering, aggregated over all structures of the protein, with PDBe-KB's own descriptors.
3. **RCSB per-instance contacts.** In the `ligands` qualifier of `has_structure`, each ligand instance keeps its neighbour residues. They are mapped from structure `seq_id` to UniProt numbering through the entity alignment the card already holds.

`Card.ligand_sites()` puts them side by side. `Card.ligands(deck)` and `Card.compare_ligands(...)` carry each molecule's site, so a ligand's site can be compared between two proteins.

## How / evidence

Measured on 2026-09-23. Fixtures: `temp_data/pdbe_kb/`, and `temp_data/rcsb/` refreshed with ligand neighbours.

**The sources agree on the human active site.** On HsTIM, UniProt annotates binding sites 12 and 14 (substrate) and active sites 96 and 166, with ECO:0000255 (PROSITE-ProRule) and ECO:0000269 (published experiment). PDBe-KB states that 2-phosphoglycolate, a transition-state analogue, contacts all four.

**BTS binds away from the annotated site, across the dimer.**
- On TcTIM, PDBe-KB states that BTS contacts Arg71, Phe75 and Tyr102. None of them is annotated (12, 14, 96, 168).
- RCSB states that a single BTS instance in 1SUX (asym J) contacts Arg71 and Phe75 of chain A and Tyr102 of chain B.
- The TcTIM annotations are all ECO:0000250, inferred from similarity.

**PDBe-KB chains are not instance data.**
- In 1HTI, PDBe-KB attributes Asn12 to chain B and His96 to chain A. The only PGA instance of 1HTI contacts chain B alone (RCSB).
- A view computed from PDBe-KB chains had first reported that PGA "spans chains" in all five of its structures. That was wrong, and it was caught before commit. Chain spanning is now read only from RCSB instance contacts. It is `None` when the card holds no instance-level data.

**Numbering.** RCSB states neighbours in structure numbering. In 1HTI the construct lacks the initiator Met, so structure residue 11 is UniProt Asn12. The mapping uses the alignment's `entity_beg_seq_id` and `ref_beg_seq_id`.

**Relevance descriptors do not agree.** On TIM, PDBe-KB flags only isopropanol and sodium as solvents. Glycerol, PEG, sulfate and hexane are not flagged, and glycerol has the same `significance` (10) as BTS. The PDB `subject_of_investigation` flag, used by `ligand_deck` since #25, separates them. Both statements are kept as their sources state them.

**Also observed.** One of seven sulfate instances in 1SUX (asym F) contacts Lys14, Gly174, Ser214, Gly235 and Gly236, the phosphate-binding residues.

**Order.** RCSB returns polymer entities and instances in no fixed order. The mapping sorts them, and a test checks that shuffled input gives the same output.

**Tests.** `tests/core/test_ligand_sites_offline.py` covers these cases. The online counterpart is in `tests/core/test_online_protein_card.py`.

## Why

Knowing that a molecule is active on a target is incomplete without knowing where it binds. A binder at a site that differs from the host enzyme's is the usual basis for selectivity. Where the annotated site of a parasite protein is only inferred by similarity, experimental contacts are the first direct evidence of where anything binds.

## Decisions (MVP)

- **Predicate `has_ligand_site`** (protein → `pdb.ligand:<code>`). There is one relationship per protein–ligand pair, identified by the pair, as PDBe-KB aggregates per ligand. It is supported by a PDBe-KB SourceAssertion holding the ligand record verbatim. The subject namespace is `pdbekb:<accession>`, because PDBe-KB records are keyed by UniProt accession.
- **Overlap is derived** (`annotated_site_overlap@1`): an exact residue match in UniProt numbering. The classes are `overlaps_annotated_site`, `no_annotated_overlap`, `no_annotated_sites` and `numbering_not_comparable`. "No annotated overlap" is not "binds elsewhere", because annotations are sparse; the rule's docstring says so.
- **Chain spanning comes only from instance-level contacts.** It is `None` when unknown, never `[]`.
- **Relevance.** PDBe-KB's descriptors and the PDB flag stay separate. Neither overrides the other.
- **Deck.** `ligand_deck` includes ligands PDBe-KB reports in structures the card has not fetched. Their PDB flag is unknown, so with the default `"of_interest"` they are listed as excluded with reason `subject_of_investigation_unknown`.

## Risks and future problems

- **Spatial proximity is not computed.** "Next to an annotated site" would need coordinates and a distance calculation. That is modelling (`devguide/DECISIONS.md`) and stays out of Sabueso. Where it could be computed (MolSysSuite, as a Praxis Capability) and how a promoted result could come back as knowledge are evaluated in uibcdf/sabueso#30.
- **Cutoffs differ.** PDBe-KB and RCSB use their own contact definitions, so residue sets do not coincide exactly (PGA: PDBe-KB lists 210 and 212; the 1HTI instance lists 170 and 234). Both are shown; neither is treated as the reference.
- **Instance data covers only fetched structures.** A protein with many structures needs `structures="all"` to know chain spanning everywhere, and every fetch adds to the card size (#19, #27).
- **Canonical numbering.** Positions refer to the canonical UniProt sequence. Isoform-specific or mutant constructs need the alignment, which RCSB gives; residues outside aligned regions keep `position: None`.
- **Heteromeric complexes.** A contact with another protein of a complex keeps that protein's accession on the contact. The view counts chains, not proteins.
- **PDBe-KB API stability.** The graph API has no version in its response. Fixtures pin the retrieval date.

## Acceptance criteria

- [x] The residues BTS contacts on TcTIM are on the card, traceable to PDBe-KB, and comparable with the UniProt-annotated active site.
- [x] UniProt binding sites keep their ligand.
- [x] Chain spanning read from instance-level contacts, never from aggregated chains.
- [x] Sites carried into `Card.ligands` and `Card.compare_ligands`.
- [ ] M-CSA catalytic roles (why a residue is catalytic).
- [ ] InterPro/PROSITE positional site matches.
- [ ] BioLiP as a batch import, if a use appears.

## Resolution

Partial: plan steps 1 and 2, the RCSB instance contacts of step 4, and the carrying of sites into the ligand comparison (step 3) were implemented on 2026-09-23. M-CSA, InterPro positions and BioLiP remain open in uibcdf/sabueso#28.
