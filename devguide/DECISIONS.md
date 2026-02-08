# Sabueso — Decision Log

## Language & Ecosystem
- Language: **Python**.
- Scientific OSS standards:
  - tests with **pytest**
  - documentation with **Sphinx**
  - package distribution via **conda**
  - development in a **conda micro‑environment**

## Core Data Model
- Output is a **card** with nested sections and strict field ordering.
- Card types: **ProteinCard**, **PeptideCard**, **SmallMoleculeCard**.
 - **Deck** is a first‑class object for collections of cards.

## Evidence and Provenance (Critical)
- **Uniform evidence model** for all fields, no exceptions.
- Cards store **selected values** only.
- All raw values from all sources are stored in `evidence_store`.
- Each field points to one or more `evidence_ids`.
- `selection_rules` is explicit and versioned.
- `quality.conflicts` records unresolved disagreements.

## All‑Values Policy
- **All values from all sources must be preserved**, never discarded.

## Clinical Layer
- Clinical data is included as a **separate layer**:
  - pharmacology
  - ADMET
  - clinical trials
  - pharmacovigilance
  - indications
  - contraindications
  - interactions

## ProteinCard Enhancements
- Protein cards include a **disease** section with disease associations and evidence.
- Protein cards include **ligands** with a `role` attribute (e.g., inhibitor, activator, substrate).
- Protein cards provide an operation to **extract a Deck of inhibitor cards**.

## Positional Location Model
- Positional features support both **sequence‑based** and **structure‑based** locations.
- This is required for interoperability with TopoMT and visualization tools.

## Ambiguity Handling
- Ambiguous inputs should return a **Deck** rather than a single Card.
- Ambiguity must be explicit in the output (metadata or quality section).

## Tools API (Public)
- Tools are organized into:
  - `tools.db.*` (per‑database modules)
  - `tools.card.*` (operate on Card)
  - `tools.deck.*` (operate on Deck)
- Tools are intentionally **ad‑hoc** and **heterogeneous** (no common protocol).

## Versioning (Pending Decision)
- Version strings use **x.y.z** (no leading `v`).
- Third‑party API URLs may include their own version segments (e.g., `/v1/`); do not change those.
- A formal **schema versioning policy** is required.
- Card and tool versioning must be defined before stable releases.

## Cache/Store Policy (Pending Decision)
- Decide whether local cache stores **raw source data**, **cards only**, or **both**.
- This must respect licensing constraints.

## Core Ops (Pending Decision)
- Define a minimal, consistent set of **CardOps** and **DeckOps** (compare, filter, sort, expand, etc.).

## Online‑First
- Sabueso is **online‑first**.
- Local card caching is optional and does not replace live queries.
