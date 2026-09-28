"""The clinical layer of a molecule: ChEMBL indications and the trials they cite (#81).

- ``investigated_for`` (molecule → disease term): one per ChEMBL drug indication, with
  the maximum phase ChEMBL states for it, the MeSH heading, and the references it cites
  (ClinicalTrials.gov, ATC, FDA, EMA, DailyMed…). Phase 4 is approval as ChEMBL states
  it; phases 1 to 3 are investigational. Two indications with different terms stay two,
  even when they share a MeSH heading: which term is meant is ChEMBL's statement.
- ``tested_in`` (molecule → ``nct:<id>``): one per trial a ChEMBL indication cites. It
  is supported by the ChEMBL assertions that cite it, which are the link's basis, and
  by the ClinicalTrials.gov record, which describes the trial. The trial's intervention
  text is kept verbatim, never matched to a molecule. A cited trial that
  ClinicalTrials.gov does not hold keeps ChEMBL's statement, with ``registry:
  not_found``.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

CHEMBL = "ChEMBL"
REGISTRY = "ClinicalTrials.gov"
TRIAL_BASIS = "chembl_drug_indication"


def disease_ref(indication: Dict[str, Any]) -> str | None:
    """``<namespace>:<CURIE>`` of the indication's term (``efo:EFO:0008559``,
    ``mondo:MONDO:0001444``), else its MeSH heading's (``mesh:D014355``)."""
    term = indication.get("efo_id")
    if term and ":" in term:
        return f"{term.split(':', 1)[0].lower()}:{term}"
    if indication.get("mesh_id"):
        return f"mesh:{indication['mesh_id']}"
    return None


def trial_ids(indication: Dict[str, Any]) -> List[str]:
    """The NCT ids an indication cites."""
    return sorted(
        {
            nct.strip().upper()
            for ref in indication.get("indication_refs") or []
            if ref.get("ref_type") == "ClinicalTrials"
            for nct in (ref.get("ref_id") or "").split(",")
            if nct.strip()
        }
    )


def _phase(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def map_indications(
    indications: Dict[str, List[Dict[str, Any]]],
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    """``investigated_for`` relationships, and the ChEMBL assertions citing each trial:
    ``{"relationships", "source_assertions", "citations": {(molecule, nct): [...]}}``,
    where each citation is ``(disease_ref, assertion_id)``."""
    assertions, relationships = [], []
    citations: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
    for molecule, records in sorted(indications.items()):
        subject = f"chembl:{molecule}"
        for record in sorted(records, key=lambda r: r.get("drugind_id") or 0):
            obj = disease_ref(record)
            if obj is None:
                continue
            assertion = make_source_assertion(
                "relationships.investigated_for",
                record,
                CHEMBL,
                f"drug_indication:{record.get('drugind_id')}",
                retrieved_at,
                subject_ref=subject,
            )
            if version is not None:
                assertion["source"]["version"] = str(version)
            assertions.append(assertion)
            trials = trial_ids(record)
            for nct in trials:
                citations.setdefault((molecule, nct), []).append((obj, assertion["id"]))
            qualifiers = {
                "max_phase": _phase(record.get("max_phase_for_ind")),
                "disease_term": record.get("efo_term"),
                "mesh_id": record.get("mesh_id"),
                "mesh_heading": record.get("mesh_heading"),
                "trials": trials,
                "references": [
                    {"type": r.get("ref_type"), "id": r.get("ref_id")}
                    for r in record.get("indication_refs") or []
                ],
            }
            relationships.append(
                make_relationship(
                    subject,
                    "investigated_for",
                    obj,
                    qualifiers={k: v for k, v in qualifiers.items() if v is not None},
                    source_assertion_ids=[assertion["id"]],
                )
            )
    return {
        "relationships": relationships,
        "source_assertions": assertions,
        "citations": citations,
    }


def _date(struct: Dict[str, Any] | None) -> str | None:
    return (struct or {}).get("date")


def trial_qualifiers(study: Dict[str, Any]) -> Dict[str, Any]:
    """What ClinicalTrials.gov states about a study, as ``tested_in`` qualifiers."""
    protocol = study.get("protocolSection") or {}
    status = protocol.get("statusModule") or {}
    design = protocol.get("designModule") or {}
    enrollment = design.get("enrollmentInfo") or {}
    out = {
        "title": (protocol.get("identificationModule") or {}).get("briefTitle"),
        "status": status.get("overallStatus"),
        "study_type": design.get("studyType"),
        "phases": design.get("phases"),
        "enrollment": {k: enrollment[k] for k in ("count", "type") if k in enrollment}
        or None,
        "start": _date(status.get("startDateStruct")),
        "completion": _date(status.get("completionDateStruct")),
        "last_update": _date(status.get("lastUpdatePostDateStruct")),
        "conditions": (protocol.get("conditionsModule") or {}).get("conditions"),
        "interventions": [
            {
                k: v
                for k, v in (
                    ("type", i.get("type")),
                    ("name", i.get("name")),
                    ("other_names", i.get("otherNames")),
                )
                if v
            }
            for i in (protocol.get("armsInterventionsModule") or {}).get(
                "interventions"
            )
            or []
        ],
        "lead_sponsor": (
            (protocol.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}
        ).get("name"),
        "has_results": study.get("hasResults"),
    }
    return {k: v for k, v in out.items() if v not in (None, [], {})}


def map_trials(
    citations: Dict[Tuple[str, str], List[Tuple[str, str]]],
    studies: Dict[str, Dict[str, Any]],
    wanted: Iterable[str],
    retrieved_at: str,
    version: str | None,
) -> Dict[str, Any]:
    """``tested_in`` relationships for the cited trials in ``wanted``."""
    wanted = set(wanted)
    assertions, relationships = [], []
    registry: Dict[str, str] = {}
    for nct in sorted(wanted & set(studies)):
        assertion = make_source_assertion(
            "relationships.tested_in",
            studies[nct],
            REGISTRY,
            nct,
            retrieved_at,
            subject_ref=f"nct:{nct}",
        )
        if version is not None:
            assertion["source"]["version"] = str(version)
        assertions.append(assertion)
        registry[nct] = assertion["id"]
    for (molecule, nct), cited in sorted(citations.items()):
        if nct not in wanted:
            continue
        qualifiers: Dict[str, Any] = {
            "basis": TRIAL_BASIS,
            "cited_for": sorted({disease for disease, _ in cited}),
        }
        support = [assertion_id for _, assertion_id in cited]
        if nct in registry:
            qualifiers.update(trial_qualifiers(studies[nct]))
            support.append(registry[nct])
        else:
            qualifiers["registry"] = "not_found"
        relationships.append(
            make_relationship(
                f"chembl:{molecule}",
                "tested_in",
                f"nct:{nct}",
                qualifiers=qualifiers,
                source_assertion_ids=support,
            )
        )
    return {"relationships": relationships, "source_assertions": assertions}
