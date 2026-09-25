---
summary: Small-molecule identity anchored at the standard InChIKey, linking structure ligands, measured molecules and other chemistry resources.
issue: uibcdf/sabueso#25
status: resolved
opened: 2026-09-23
closed: 2026-09-25
verification: measured
area: [identity, small-molecules, chembl, pdb-ccd, unichem]
blocked_by: []
supersedes: []
---

# Summary

## What

A protein card held two sets of ligands that could not be related:

- **Structure ligands:** chemical-component codes in `has_structure` qualifiers, e.g. `BTS` in 1SUX.
- **Measured molecules:** ChEMBL molecule references in `has_bioactivity`, e.g. `chembl:CHEMBL1161789`.

Nothing said whether a molecule measured in an assay was the one seen in a structure. This theme gives small molecules an identity.

**Anchor (decided by the Sabueso owner on 2026-09-23).** A small molecule is anchored at its **standard InChIKey**, the way a protein is anchored at its UniProt accession. Its card id is `sabueso:small_molecule:inchikey:<key>`.

**Links to the anchor.** Every source record of the molecule is linked to `inchikey:<key>` with `same_as`, supported by what the source itself states:

| Record | Stated by | Support |
| --- | --- | --- |
| `chembl:<id>` | ChEMBL | its standard InChIKey |
| `pdb.ligand:<code>` | PDB CCD (the wwPDB Chemical Component Dictionary, served by RCSB) | the InChIKey of its standard InChI |
| DrugBank, PubChem, ChEBI, BindingDB, and the ChEMBL and PDB records again | UniChem | the records it groups under one standard InChI |

**Fields.** Only the records linked to the anchor feed the card's fields (`entity_subjects` guard).

**Interfaces.**
- `resolve_molecule_card(identifier)` accepts `chembl:<id>`, `pdb.ligand:<code>` or `inchikey:<key>`.
- `build_molecule_cards(...)` builds cards from records already retrieved.
- `ligand_deck(protein_card)` builds the deck of the molecules a protein card refers to, and `protein_card.ligands(deck)` crosses them (uibcdf/sabueso#23, `devguide/archive/chembl_bioactivities.md`).

## How / evidence

Measured on 2026-09-23 against RCSB (CCD), ChEMBL_37 and UniChem. The fixtures are in `temp_data/pdb_ccd/`, `temp_data/chembl/molecules.json`, `temp_data/unichem/` and `temp_data/rcsb/1SUX.json`.

**Structure ligands of TIM.**
- The 7 PDB structures of TcTIM (P52270) hold 6 ligand codes: BTS, GOL, HEX, PEG, PGE and SO4.
- The 29 structures of HsTIM (P60174) hold 10: BR, CA, DXX, G3P, GOL, IPA, K, NA, PGA and PO4.
- Most are crystallisation additives or ions (item 3 of #25).

**Structure meets bioactivity.** BTS, 3-(2-benzothiazolylthio)-1-propanesulfonic acid, in 1SUX, is CHEMBL1161789. ChEMBL reports an IC50 of 33 µM for it on TcTIM. Three independent statements agree:

- the CCD InChIKey;
- the ChEMBL standard InChIKey (`XBNHRNFODJOFRU-UHFFFAOYSA-N`);
- UniChem compound 336651.

**Duplicate components.** 2-phosphoglycolate is in the CCD twice, as `PGA` and `2PL`. Both link to one anchor.

**ChEMBL coverage.** All 275 parent molecules measured on TcTIM or HsTIM have a standard InChIKey, and no two share one. `max_phase` is present for 4 of them:

- benznidazole (CHEMBL110): 4, approved;
- bexarotene (CHEMBL1023): 4, approved;
- flavone (CHEMBL275638): 2;
- anethole trithione (CHEMBL178862): -1, unknown.

**Source quirks.**
- RCSB omits unknown component codes from a batch without an error, so the client computes the missing codes.
- UniChem answers an unknown key with HTTP 200 and `"response": "Not found"`.
- ChEMBL serialises `max_phase` as a string.

**Biological relevance of structure ligands (item 3).** The PDB flags each ligand instance as `is_subject_of_investigation`, with a provenance. The provenance is `Author` when the depositor declared it (entries from 2019 on) and `RCSB` when RCSB assigned it for older entries. On the ligands of the 36 TIM structures, the flag separates exactly:

- **Y:** PGA (1HTI by RCSB; 6UP5, 6UPF, 7T0Q and 7UXV by the authors), BTS (1SUX, RCSB), DXX (9F69, authors) and G3P (9FFC, authors). These are the substrate, analogues and an inhibitor.
- **N:** sulfate, glycerol, PEG, triethylene glycol, hexane, isopropanol, phosphate, and Na, K, Br and Ca ions.

**Tests.** `tests/core/test_molecule_identity_offline.py` covers these cases. The online counterpart is in `tests/core/test_online_molecule_card.py`.

## Why

Known ligands are only knowledge when they can be identified across the sources that report them. Without a shared anchor, every new ligand source adds another isolated set of references, and the MOLI operations over ligand decks (`devguide/SCIENTIFIC_POTENTIAL.md`: "which ligands occur in both sets?") cannot be answered.

## Alternatives

Considered with the owner:

1. **Standard InChIKey (chosen).** It is source-independent and decidable, and it is the basis of UniChem.
2. **A preferred source record** (ChEMBL > PubChem > PDB CCD), as UniProt is for proteins. Rejected: there is no universal chemistry source. PDB-only ligands and PubChem-only compounds would get anchors in different namespaces, and the anchor would depend on where resolution started.
3. **The UniChem compound id (UCI).** It is stable and structure-derived, but internal to UniChem. It would make identity depend on one service.

## Decisions (MVP)

- **Standard keys only.** A ChEMBL key must match the standard pattern (`...SA-X`). A CCD key counts only when its InChI is standard (`InChI=1S/`). A record without one is reported as unanchored (status `unsupported`, rule `no_standard_inchikey`), never guessed.
- **UniChem sources that become `same_as` links:** chembl, rcsb_pdb and pdbe (both map to `pdb.ligand`), pubchem, drugbank, chebi and bindingdb. The full UniChem source list is kept verbatim in the supporting SourceAssertion. ChEBI ids drop their `CHEBI:` banana: `chebi:17150`.
- **Fields.**
  - CCD SMILES are not mapped to `identifiers.smiles`: they are a different representation from ChEMBL's canonical SMILES (uibcdf/sabueso#10). They stay in the CCD assertion.
  - The CCD formula is normalized, e.g. `C10 H11 N O3 S3` becomes `C10H11NO3S3`.
  - `clinical.max_phase` is ChEMBL's value, normalized to a number. `-1` means unknown.
- **UniChem is on by default** for a single molecule (one call), and opt-in for decks (one call per molecule). When it fails, the card is still built and the failure is recorded in `quality.enrichments`.
- **Structure ligands of interest (item 3).**
  - The PDB flag is mapped into each ligand of the `has_structure` qualifiers and into the RCSB SourceAssertion that supports them. Before this, the ligands were a qualifier without an assertion.
  - `ligand_deck` keeps, by default, only ligands flagged in at least one structure. The others are listed in `deck.meta["excluded_structure_ligands"]` with the reason: `not_subject_of_investigation`, or `subject_of_investigation_unknown` when the entry states nothing. `structure_ligands="all"` keeps them all.
  - `Card.ligands` reports `structures_of_interest` next to `structures`.
  - Alternatives rejected:
    - BioLiP: a third-party curation pipeline available as bulk downloads, not a record-level API;
    - a Sabueso-curated artifact list: Sabueso would be asserting relevance, which it must not do.
- **Discrepancies are reported.** A record that UniChem links but whose own InChIKey differs from the anchor is listed in `decision.discrepancies`, not merged.

## Risks and future problems

- **Charge, salts, stereochemistry and tautomers.** Structures that differ only in these have different standard InChIKeys, and therefore different anchors:
  - CCD ions are charged (sulfate `-L`, phosphate `-K`), while ChEMBL parents are neutralised;
  - an undefined stereocentre does not match a defined one.

  The MVP does not link them. A future connectivity-level link (same first InChIKey block) must be a derived `possibly_same_as` with its rule, never `same_as`.
- **ChEMBL salts.** The ligand deck anchors ChEMBL parent molecules. The salt forms actually tested stay as `has_bioactivity` objects and are not anchored separately.
- **Legacy molecule cards.** Resolved in uibcdf/sabueso#21, part 3. `create_molecule_card_*` and `create_compound_card_*` now build the InChIKey-anchored card, and PubChem joined the identity sources. There is one identity scheme for small molecules.
- **InChI version.** CCD and ChEMBL compute InChIs with their own software versions. Standard InChI is designed to be stable, but a disagreement would show up as two anchors for one molecule. `decision.discrepancies` makes it visible.
- **Deck persistence.** Resolved in uibcdf/sabueso#26: a saved ligand deck keeps `deck.meta` (JSONL header, SQLite `deck_meta`).
- **"Not of interest" is not "irrelevant".** A catalytic or structural metal, or a cofactor, may be left unflagged. Such ligands are excluded by default but listed, so a consumer can recover them with `structure_ligands="all"`.
- **Provenance quality differs.** `Author` flags are declarations. `RCSB` flags for older entries are assigned by RCSB. The provenance is kept on each ligand, and a consumer can weigh the two differently.
- **The flag is per structure.** A component can be of interest in one entry and not in another. The deck keeps a component if any structure flags it, and `structures_of_interest` says which.
- **UniChem coverage and latency.** One call per molecule. A deck of hundreds of molecules is slow online, which is why decks default to no UniChem.
- **Namespaces.** `pdb.ligand`, `inchikey`, `unichem`, `chebi`, `drugbank` and `bindingdb` follow Bioregistry prefixes. If other MOLI components start to exchange these references, the vocabulary becomes a shared contract to raise in `uibcdf/moli`.

## Acceptance criteria

- [x] Standard-InChIKey anchor with `same_as` links supported by ChEMBL, the PDB CCD and UniChem.
- [x] `resolve_molecule_card` from `chembl:`, `pdb.ligand:` and `inchikey:`, with the statuses resolved, not_found, unsupported and error kept distinct.
- [x] The ligand of a TcTIM structure (BTS, 1SUX) and the molecule measured on TcTIM (CHEMBL1161789) resolve to one card.
- [x] `max_phase` asserted by ChEMBL (item 5 of #25).
- [x] Item 3: biological relevance of structure ligands, from the PDB "subject of investigation" flag.
- [ ] Item 4: binding sites, moved to its own theme (uibcdf/sabueso#28, `devguide/archive/ligand_binding_sites.md`).
- [ ] Item 6: further bioactivity sources, after cross-source measurement identity is designed.

## Resolution (2026-09-25)

Closed. Items 1, 2, 3 and 5 were implemented on 2026-09-23 (InChIKey anchor, CCD, the PDB subject-of-investigation flag, `max_phase`). Item 4 became #28, which is resolved. Item 6, further bioactivity sources, needs the identity of a measurement across sources first, now designed in its own issue (#66). BindingDB and PubChem BioAssay are recorded as deferred in `devguide/sources/registry.yaml` until then. The rule on computable properties is in `devguide/DECISIONS.md`.
