# Sabueso — Use Cases

Two sets of scenarios. The first was agreed during the original design (2026-01/02); the
second came from the pilot-driven route (since 2026-09-23). Both are objectives. Their
status is tracked in `ROADMAP.md`.

## Use cases of the original design

### 1) Protein interactions, ligands, pathways
Given a protein:
- retrieve interacting proteins
- retrieve known ligands and inhibitors (when applicable)
- retrieve pathway involvement

### 2) Clinical usage of ligands
Given candidate ligands:
- identify which have reported clinical use
- surface clinical data from DrugBank datasets

### 3) TopoMT integration
- map catalytic residues and inhibitory mutations to structural features
- provide positional features for cavity analysis

### 4) PharmacophoreMT screening
- screen a molecule library using a Deck of ligands

### 5) Commercial availability of peptides
- list peptide availability and vendors

### 6) Tissue‑specific isoforms
- report isoforms and tissue‑specific expression

### 7) Visualization (MolSysViewer)
- visualize secondary structure, protein‑protein interfaces, known mutations

### 8) Clinical trials for ligands
- report whether a ligand has clinical trials

### 9) Disease associations
- find diseases associated with a protein
- list possible targets for a disease

## Use cases from the pilot-driven route

Phrased generically; the pilots themselves are private.

### 10) A traceable knowledge baseline for a target and a comparator
- resolve both proteins by name and organism, and report the entries that could be
  mistaken for them (redundant entries, strain variants, paralogs);
- say who states each fact, where sources disagree, and what is not known;
- gather structures, oligomer and interface, ligands and measurements, variants, and
  the literature the sources cite.

### 11) Curating what the literature states
- record statements from papers, structured when a field fits and as typed claims
  otherwise;
- compare them with the databases without giving them priority, and keep them across
  rebuilds.

### 12) Citing knowledge from a project
- cite an exact card state or a single SourceAssertion, whose meaning never changes when
  the card is refreshed, so that a Discovery project can build Evidence on it.

### 13) Choosing structures to model
- list every experimental structure with its construct, mutations, ligands, assembly,
  method, resolution and missing residues in a region;
- put two proteins side by side, grouped by state, with substitutions related through
  residue maps.

### 14) A cohort of related proteins
- build a deck of orthologs or paralogs across organisms;
- filter by lineage and group by rank;
- audit identities, and record membership and exclusions, reproducibly.

