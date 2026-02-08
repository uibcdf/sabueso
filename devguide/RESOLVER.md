# Sabueso — Resolver (0.1.0 Contract)

This document defines the minimal **Resolver** contract for selecting canonical values from evidence.
Versioning for resolver and selection rules follows **x.y.z**.

## Purpose
- Take **all evidence** for a field and select a **canonical value** (or set of values).
- Preserve traceability by linking selected values to evidence IDs.
- Record conflicts explicitly when evidence disagrees.

## Inputs
Resolver operates on a **field-level** view:

- `field_path: str`
- `evidences: list[dict]` (each with `evidence_id`, `value`, `source`, `retrieved_at`)
- `selection_rules: dict` (global + per-field overrides)

## Outputs
For each field, the Resolver produces:
- `selected_value`: the chosen value (or list of values)
- `evidence_ids`: list of evidence IDs supporting the selected value
- `conflict`: optional object if unresolved disagreement exists

## Minimum API (conceptual)

```
resolve_field(
    field_path: str,
    evidences: list[dict],
    selection_rules: dict,
    mode: str = "strict"
) -> dict
```

Return structure:

```
{
  "field": "annotations.domains",
  "selected_value": <value|list>,
  "evidence_ids": ["ev1", "ev2"],
  "conflict": null | {
      "type": "disagreement",
      "values": [<valueA>, <valueB>, ...],
      "evidence_ids": [["ev1"], ["ev2"], ...]
  }
}
```

## Resolution Policy (0.1.0)

Resolver follows this minimal rule stack, in order:

1) **Per-field rule override** (if defined in `selection_rules[field_path]`).
2) **Global rule** (default policy).
3) **Tie-break by most recent `retrieved_at`** (if still tied).
4) **If still tied** → mark `conflict` and choose a stable default (first by deterministic ordering).

### Default Global Rule (0.1.0)
- Prefer evidence from **priority sources** (if `selection_rules.priority_sources` is provided).
- Otherwise, choose the **most frequent identical value** across evidences.
- If frequency is tied, prefer most recent.

## Selection Rules Schema (minimal)

```
{
  "version": "0.1.0",
  "priority_sources": ["UniProt", "PDB", "ChEMBL", ...],
  "field_rules": {
    "annotations.domains": {
      "strategy": "priority_sources",
      "allow_multiple": true
    },
    "properties.physchem.molecular_weight": {
      "strategy": "most_recent",
      "allow_multiple": false
    }
  }
}
```

## Conflict Handling
- Conflicts are surfaced in `quality.conflicts` on the Card.
- Conflicts must retain the full set of contradictory values and evidence IDs.

## Notes
- This is the **minimal** policy; future versions can add confidence scoring, LLM assistance,
  or probabilistic aggregation.
