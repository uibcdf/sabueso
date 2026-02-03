# Sabueso — Vision

## Definition
Sabueso is a scientific Python library that aggregates, normalizes, and traces biomolecular data across multiple public databases. Given a molecular system (protein, peptide, small molecule, etc.), Sabueso returns a structured **card** that contains curated, ordered information with explicit, uniform provenance.

## Mission
Provide a reliable, traceable, and extensible foundation for biomolecular data discovery and integration, enabling downstream scientific workflows in MolSysSuite.

## Purpose
- Provide a single entry point to query biological, biochemical, and chemical databases.
- Deliver a unified, structured object (the **card**) ready for downstream computational workflows, especially drug‑design pipelines.
- Preserve **all values** from sources while selecting a canonical value per field.
- Make all provenance transparent and auditable via a uniform evidence mechanism.

## Objectives (Initial)
- Implement Protein, Peptide, and Small Molecule cards with stable, nested structure.
- Provide public tools for database access and card/deck operations.
- Maintain a perfect developer checkpoint in `dev_guide/`.

## Users
Primary users are computational scientists in biophysics, biochemistry, computational biology, and computer‑assisted molecular design.

## Scope (Initial)
- Entities: **protein**, **peptide**, **small molecule**.
- Sources: **UniProt**, **PDB**, **ChEMBL**, **PubChem**, **eMolecules**, **ChemSpider**, **DrugBank**.
- Output: one **card** per entity with nested sections and standardized field paths.

## Integration Context
Sabueso is part of the **MolSysSuite** ecosystem. It should be designed to interoperate with other scientific libraries in that suite.

MolSysSuite tools explicitly referenced so far:
- **MolSysMT**: handling molecular system models and simulation trajectories.
- **TopoMT**: topographic analysis of molecular surfaces (cavities, channels, etc.).
- **ElastNet**: elastic network models for proteins.
- **PharmacophoreMT**: pharmacophore workflows.
- **MolSys‑AI**: RAG/finetuned LLM for MolSysSuite; expected to evolve into an agent that uses Sabueso and other tools.

## Non‑Goals (for now)
- No offline‑only mode. Sabueso is online‑first, but supports local card caching.
- No forced selection rules until evidence is fully collected and traceable.
