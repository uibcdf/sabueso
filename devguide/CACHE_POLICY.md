# Sabueso — Cache/Storage Policy (Draft)

This document defines how Sabueso stores data locally for reproducibility and performance.

## Scope
- **Raw source payloads** (JSON/XML dumps from external DBs)
- **Canonical Cards** (resolved, evidence-linked)

## Options

### Option A — Raw only
- Pros: full provenance, easy reprocessing.
- Cons: expensive rebuild; no fast access.

### Option B — Cards only
- Pros: fast access, compact.
- Cons: loses raw detail unless evidence store embedded.

### Option C — Raw + Cards (recommended)
- Store raw payloads + resolved cards.
- Allows re‑resolution when rules change.

## Draft Decision (to confirm)
## Decision (Confirmed)
- Default: **Option C (Raw + Cards)** with size‑aware pruning.
- Policy:
  - Keep **raw payloads** for recent N days or N entities.
  - Keep **cards** for long‑term access.
  - Allow user overrides via config.

## Open Questions
- Where to store (path, DB, SQLite)?
- How to handle licensing restrictions.
- How to manage versioned selection_rules changes.
