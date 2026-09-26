# Overview

Sabueso turns what public databases and publications state about a molecular entity into
structured, traceable knowledge. It is the knowledge component of the MOLI platform:
**Sabueso knows; it does not discover.**

## What Sabueso produces

- **Card**: one entity (a protein or a small molecule) with its resolved field values,
  each linked to the SourceAssertions that support it, and its relationships to other
  entities (structures, bioactivities, interactions, classifications…).
- **Deck**: a collection of cards that records why each card is in it and how it was
  derived.
- **Views**: knowledge derived on demand, such as structures, bioactivities, ligands,
  oligomer, literature, knowledge states, comparisons and identity audits. Each view
  names the rule that derived it.

## What Sabueso preserves

- **Every assertion.** Selection chooses a value to show, and never discards the others.
- **Conflicts and alternatives**, where sources disagree or are not comparable.
- **What is not known.** It tells apart what a source does not state, what was not
  asked, and what failed.
- **Identity with care.** Ambiguity is reported, and entries are never merged by
  similarity.
- **Exact states**, which can be cited by a pinned reference and read back unchanged.

## Sources

Proteins come from UniProt, with RCSB PDB, PDBe-KB, InterPro, AlphaFold DB, STRING,
NCBI Taxonomy and NCBI Gene. Small molecules and bioactivities come from ChEMBL,
BindingDB, PubChem, PubChem BioAssay, the PDB Chemical Component Dictionary and UniChem.
The full list, with what is queued, deferred or set aside, is in {doc}`data_sources`.

## Where to go next

- {doc}`quickstart`: a first session.
- {doc}`resolving`: queries, options, ambiguity and profiles.
- {doc}`concepts`: cards, SourceAssertions, conflicts, quantities, tables.
- {doc}`structures`, {doc}`sites_and_interfaces`, {doc}`bioactivities`,
  {doc}`literature_and_curation`: what a protein card knows.
- {doc}`decks`: cohorts, audits and inventories.
- {doc}`storage` and {doc}`upgrading`: keeping and citing knowledge.
