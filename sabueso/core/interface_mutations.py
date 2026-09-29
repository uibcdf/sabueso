"""Interface mutations and their binding changes (``annotations.interface_mutations``).

The items are SKEMPI's statements, as stored (#83). The view adds one derived value,
ΔΔG, under the rule ``binding_ddg@1``:

    ΔΔG = R · T · ln(K_mutant / K_wild_type)

in kcal/mol, with R = 1.98720425864083e-3 kcal/(mol·K), from the two stated affinities
and the stated temperature. Positive ΔΔG means the mutant binds more weakly.

- It is derived only when both affinities are values. When one of them is a bound
  (``>`` or ``<``), ΔΔG is a bound in the corresponding direction
  (``ddg_relation``). When both are bounds, or the mutant does not bind (``n.b.``), it
  is not derived, and ``ddg_basis`` says why.
- A temperature SKEMPI marks as assumed (298 K) is used, and the item says so
  (``temperature_assumed``).
- ΔΔG is never stored: it is recomputed from the stored affinities, so a change of rule
  is a new rule version, not a change of knowledge.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from .relationship_store import make_derivation

RULE = "binding_ddg@1"
FIELD = "annotations.interface_mutations"
GAS_CONSTANT = 1.98720425864083e-3  # kcal / (mol K)
#: A bound on K_mutant gives ΔΔG the same direction; a bound on K_wild_type, the
#: opposite one.
FLIP = {">": "<", "<": ">"}


def _ddg(item: Dict[str, Any]) -> Dict[str, Any]:
    affinity = item.get("affinity") or {}
    if affinity.get("mutant_no_binding"):
        return {"ddg_basis": "mutant_no_binding"}
    mutant, wild = affinity.get("mutant"), affinity.get("wild_type")
    temperature = item.get("temperature")
    if not mutant or not wild:
        return {"ddg_basis": "affinity_not_stated"}
    if not temperature:
        return {"ddg_basis": "temperature_not_stated"}
    relations = {
        affinity.get("mutant_relation"),
        FLIP.get(affinity.get("wild_type_relation")),
    }
    relations.discard(None)
    if len(relations) > 1 or (
        affinity.get("mutant_relation") and affinity.get("wild_type_relation")
    ):
        return {"ddg_basis": "both_affinities_bounded"}
    value = (
        GAS_CONSTANT * temperature["value"] * math.log(mutant["value"] / wild["value"])
    )
    out: Dict[str, Any] = {
        "ddg": {"value": round(value, 6), "unit": "kilocalorie / mole"}
    }
    if relations:
        out["ddg_relation"] = relations.pop()
    return out


def interface_mutations_view(card: Any) -> Dict[str, Any]:
    """The protein's interface mutations as SKEMPI states them, each with ΔΔG under
    ``binding_ddg@1``; see the module docstring."""
    node = card.get(FIELD) or {}
    items: List[Dict[str, Any]] = [
        {**item, **_ddg(item)} for item in node.get("value") or []
    ]
    return {
        "items": items,
        "source_assertion_ids": list(node.get("source_assertion_ids") or []),
        "rule": make_derivation(
            RULE,
            inputs=[f"{FIELD}.affinity", f"{FIELD}.temperature"],
            parameters={
                "formula": "R * T * ln(K_mutant / K_wild_type)",
                "gas_constant": {"value": GAS_CONSTANT, "unit": "kcal/(mol*K)"},
                "unit": "kilocalorie / mole",
            },
        ),
    }
