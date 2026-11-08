"""The clinical layer of a molecule card, as its sources state it (uibcdf/sabueso#81).

``clinical_view(card)`` lists:

- ``max_phase``: ChEMBL's maximum phase for the molecule (``clinical.max_phase``);
- ``indications``: each ``investigated_for`` relationship, with its maximum phase, term,
  MeSH heading and the trials it cites. Two terms that share a MeSH heading stay two
  rows;
- ``trials``: each ``tested_in`` relationship, with what ClinicalTrials.gov states
  (status, phases, conditions, interventions as written, sponsor, dates) and the
  indications that cite it, or ``registry: not_found``;
- ``not_fetched``: trials the indications cite that the card did not fetch (trials not
  requested, or past the limit). An absence there is not a fact about the trial.

Nothing is ranked or classified: a phase is ChEMBL's statement, a status
ClinicalTrials.gov's.
"""

from __future__ import annotations

from typing import Any, Dict


def clinical_view(card: Any) -> Dict[str, Any]:
    indications = []
    cited = set()
    for rel in card.relationships(predicate="investigated_for"):
        q = rel.get("qualifiers") or {}
        cited |= set(q.get("trials") or [])
        indications.append(
            {
                "molecule": rel["subject_ref"],
                "disease": rel["object_ref"],
                "disease_term": q.get("disease_term"),
                "mesh_heading": q.get("mesh_heading"),
                "max_phase": q.get("max_phase"),
                "trials": q.get("trials") or [],
                "reference_types": sorted(
                    {r["type"] for r in q.get("references") or [] if r.get("type")}
                ),
            }
        )
    indications.sort(
        key=lambda i: (-(i["max_phase"] or -1), i["disease_term"] or "", i["disease"])
    )
    trials = []
    for rel in card.relationships(predicate="tested_in"):
        q = rel.get("qualifiers") or {}
        trials.append(
            {
                "molecule": rel["subject_ref"],
                "trial": rel["object_ref"],
                **{k: v for k, v in q.items() if k != "basis"},
            }
        )
    trials.sort(key=lambda t: t["trial"])
    fetched = {t["trial"].split(":", 1)[1] for t in trials}
    phase = card.get("clinical.max_phase")
    return {
        "max_phase": phase.get("value") if isinstance(phase, dict) else None,
        "indications": indications,
        "trials": trials,
        "not_fetched": sorted(cited - fetched),
    }
