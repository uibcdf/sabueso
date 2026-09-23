# Sabueso — Resolver (0.2.0 Contract)

This document defines the minimal **Resolver** contract for selecting canonical values from
SourceAssertions (what external sources assert about a field).
Versioning for resolver and selection rules follows **x.y.z**. Contract 0.2.0 renames the
0.1.0 `evidences`/`evidence_ids` inputs and outputs to `assertions`/`source_assertion_ids`;
the selection-rules format is unchanged and remains 0.1.0.

## Purpose
- Take **all SourceAssertions** for a field and select a **canonical value** (or set of values).
- Preserve traceability by linking selected values to the supporting `source_assertion_ids`.
- Record conflicts explicitly when assertions disagree; alternatives are never discarded.

## Inputs
Resolver operates on a **field-level** view:

- `field_path: str`
- `assertions: list[dict]` (SourceAssertions, each with `id`, `asserted_value`, optional `normalized_value`, `source`, `retrieved_at`; the resolver compares `normalized_value` when present, else `asserted_value`)
- `selection_rules: dict` (global + per-field overrides)

## Outputs
For each field, the Resolver produces:
- `selected_value`: the chosen value (or list of values)
- `source_assertion_ids`: list of SourceAssertion IDs supporting the selected value
- `conflict`: optional object if unresolved disagreement exists

## Minimum API (conceptual)

```
resolve_field(
    field_path: str,
    assertions: list[dict],
    selection_rules: dict,
    mode: str = "strict"
) -> dict
```

Return structure:

```
{
  "field": "annotations.domains",
  "selected_value": <value|list>,
  "source_assertion_ids": ["sa1", "sa2"],
  "conflict": null | {
      "type": "disagreement",
      "values": [<valueA>, <valueB>, ...],
      "source_assertion_ids": [["sa1"], ["sa2"], ...]
  }
}
```

## Resolution Policy (0.2.0)

Resolver follows this minimal rule stack, in order:

1) **Per-field rule override** (if defined in `selection_rules[field_path]`).
2) **Global rule** (default policy).
3) **Tie-break by most recent `retrieved_at`** (if still tied).
4) **If still tied** → mark `conflict` and choose a stable default (first by deterministic ordering).

### Default Global Rule (0.2.0)
- Prefer SourceAssertions from **priority sources** (if `selection_rules.priority_sources` is provided).
- Otherwise, choose the **most frequent identical value** across assertions.
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
- **Any discrepancy** (multiple distinct values for a field) must be reported.
- Conflicts are surfaced in `quality.conflicts` on the Card.
- Conflicts must retain the full set of contradictory values and SourceAssertion IDs.

## Notes
- This is the **minimal** policy; future versions can add confidence scoring, LLM assistance,
  or probabilistic aggregation.
