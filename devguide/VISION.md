# Sabueso — Vision

## Definition
Sabueso is a scientific Python library that aggregates, normalizes, and traces biomolecular data across multiple public databases. It transforms **SourceAssertions** from multiple sources into **resolved molecular knowledge**, preserving conflicts, traceability, and the original assertions. Given a molecular system (protein, peptide, small molecule, etc.), Sabueso returns a structured **card** that contains curated, ordered information in which every value is linked to the SourceAssertions that support it.

**A SourceAssertion records what an external source asserts about an entity or property.** In MOLI Platform Architecture 1.0 (`uibcdf/moli`), Sabueso is the Knowledge component of the Scientific Context: `SourceAssertion` belongs to Sabueso, `Evidence` belongs to Nextia, and `Provenance` is cross-cutting (`SourceAssertion ≠ Evidence ≠ Provenance`).

## Mission
Provide a reliable, traceable, and extensible foundation for biomolecular data discovery and integration, that scientists, MOLI Agent, and MolSysSuite modeling components can consume.

## Purpose
- Provide a single entry point to query biological, biochemical, and chemical databases.
- Deliver a unified, structured object (the **card**) ready for downstream computational workflows, especially drug‑design pipelines.
- Preserve **all values** from sources while selecting a canonical value per field.
- Make every value traceable to the SourceAssertions that support it, through one uniform mechanism with transparent, auditable provenance.

## Objectives (Initial)
- Implement Protein, Peptide, and Small Molecule cards with stable, nested structure.
- Provide public tools for database access and card/deck operations.
- Maintain a perfect developer checkpoint in `devguide/`.

## Users
Primary users are computational scientists in biophysics, biochemistry, computational biology, and computer‑assisted molecular design.

## Scope (Initial)
- Entities: **protein**, **peptide**, **small molecule**.
- Sources: **UniProt**, **PDB**, **ChEMBL**, **PubChem**, **eMolecules**, **ChemSpider**, **DrugBank**.
- Output: one **card** per entity with nested sections and standardized field paths.

## Platform Context
Sabueso is the Knowledge-context component of the **MOLI Platform** (`uibcdf/moli`). Together with Praxis (Know-how) and Nextia (Discovery) it forms the platform's **Scientific Context**. **Sabueso knows; it does not discover.**

Sabueso is **not** a MolSysSuite component. MolSysSuite is the platform's molecular modeling ecosystem. Its components may consume Sabueso Cards, entity mappings, annotations and relationships through stable interfaces, while Sabueso keeps semantic ownership of that knowledge. Interoperability does not require circular package dependencies.

Expected consumers of Sabueso knowledge:
- **MOLI Agent**: assembles Scientific Context (resolved knowledge, SourceAssertions, conflicts, provenance) for scientific reasoning.
- **Nextia**: references versioned Sabueso knowledge; a DiscoveryProject may cite SourceAssertions as the basis of its own Evidence.
- **MolSysSuite** components such as MolSysMT (molecular systems), TopoMT (cavities, channels), ElastNetMT (elastic networks), PharmacophoreMT (pharmacophores) and DockingMT (docking), and MolSys-AI, the MolSysSuite specialist agent.

## Long-term scientific potential

The initial scope deliberately remains narrow, but early design decisions should not prevent Sabueso from evolving toward composable scientific knowledge objects, first-class relationships, reproducible derived knowledge, literature-derived SourceAssertions, explicit conflicts/unknowns, and knowledge-gap discovery.

See [SCIENTIFIC_POTENTIAL.md](SCIENTIFIC_POTENTIAL.md) for this non-binding long-term scientific direction. It is a vision document, not an MVP commitment or frozen API.

## Non‑Goals (for now)
- No offline‑only mode. Sabueso is online‑first, but supports local card caching.
- No forced selection rules until SourceAssertions are fully collected and traceable.
- Sabueso does not produce project Evidence, hypotheses, or decisions (those belong to Nextia).
