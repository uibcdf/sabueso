"""What may be done with the knowledge: the terms its sources state (#29).

Every value and relationship on a card traces to SourceAssertions, and every
SourceAssertion names its source. The terms of a piece of knowledge are therefore a
function of the sources that support it. ``terms_report`` follows that path, for a use
the caller names:

- ``internal_research``, ``academic_publication``, ``redistribution``,
  ``derived_dataset`` or ``commercial_product``.

For each source it answers with what the source states about its own terms (the
registry, ``devguide/sources/registry.yaml``, packaged as
``sabueso/resolver/source_terms.json``): the licence, the attribution to carry, the
statement's URL and when it was reviewed. The verdict for the use is one of:

- ``allowed``, with its ``obligations`` (``attribution``, ``credit_requested``,
  ``share_alike``);
- ``restricted``, with the reason (e.g. a non-commercial licence for a commercial
  product);
- ``unknown``, with the reason: no terms recorded, or terms that depend on each record
  (a depositor's, a publication's). Unknown is never read as "no restriction".

For each item of knowledge (a field or a relationship) it says whether it **remains**
when only the sources allowed for the use are kept: an item stays if at least one of
the sources that state it is allowed, since each supporting statement stands on its
own. Items with no allowed source are listed as ``lost`` (only restricted) or
``unknown``. Derived knowledge (views, classes) is recomputed from what remains; it
carries the obligations of the statements it is computed from (the strictest governs,
e.g. share-alike), recorded as rule ``terms_propagation@1``.

This is a report of what the sources state, for a person to decide. It is not legal
advice, and it does not rule on what is lawful: facts, compilations and database rights
differ across jurisdictions. The report says so in ``disclaimer``.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

RULE = "terms_propagation@1"
USES = (
    "internal_research",
    "academic_publication",
    "redistribution",
    "derived_dataset",
    "commercial_product",
)
#: A terms record older than this is flagged ``review_due``.
REVIEW_DAYS = 365
DISCLAIMER = (
    "This report states what each source says about its own terms, as recorded on the "
    "review date shown. It is not legal advice, and it does not decide what is lawful "
    "for a given use or jurisdiction. The decision, and the responsibility for it, "
    "stay with whoever acts on it."
)

#: What each licence allows, as its text states. ``None`` for a use means the licence
#: alone does not answer (terms per record).
LICENCES: Dict[str, Dict[str, Any]] = {
    "CC0-1.0": {"name": "CC0 1.0", "attribution": None, "share_alike": False},
    "US-PD": {
        "name": "US public domain (NLM policy)",
        "attribution": "credit_requested",
        "share_alike": False,
    },
    "NO-OWN-RESTRICTIONS": {
        "name": "no restrictions of its own",
        "attribution": None,
        "share_alike": False,
    },
    "CC-BY-3.0": {
        "name": "CC BY 3.0",
        "attribution": "attribution",
        "share_alike": False,
    },
    "CC-BY-4.0": {
        "name": "CC BY 4.0",
        "attribution": "attribution",
        "share_alike": False,
    },
    "CC-BY-SA-3.0": {
        "name": "CC BY-SA 3.0",
        "attribution": "attribution",
        "share_alike": True,
    },
    "CC-BY-SA-4.0": {
        "name": "CC BY-SA 4.0",
        "attribution": "attribution",
        "share_alike": True,
    },
    "ODbL-1.0": {
        "name": "ODbL 1.0",
        "attribution": "attribution",
        "share_alike": True,
    },
    "MIT": {"name": "MIT", "attribution": "attribution", "share_alike": False},
    "FREE-WITH-ACKNOWLEDGEMENT": {
        "name": "free to use, with acknowledgement of the source",
        "attribution": "attribution",
        "share_alike": False,
    },
    "CC-BY-NC-4.0": {
        "name": "CC BY-NC 4.0",
        "attribution": "attribution",
        "share_alike": False,
        "non_commercial": True,
    },
    "DEPOSITOR-TERMS": {"name": "each record's depositor's terms", "per_record": True},
    "PUBLICATION-TERMS": {"name": "each publication's own terms", "per_record": True},
}
#: Uses in which the data leaves the user's hands, so share-alike and attribution bind.
SHARED = {
    "academic_publication",
    "redistribution",
    "derived_dataset",
    "commercial_product",
}
#: Built-in terms of sources that are not registry resources.
BUILT_IN = {
    "Literature": {
        "licence": "PUBLICATION-TERMS",
        "attribution": "Cite the publication each statement was curated from.",
        "statement": None,
        "reviewed": None,
        "caveats": [
            "A curated statement records a fact a publication states, with its locator "
            "and at most a short quote; the publication's own terms are not recorded."
        ],
    }
}


@lru_cache(maxsize=None)
def source_terms() -> Dict[str, Dict[str, Any]]:
    """Terms by SourceAssertion source name, from the packaged registry export."""
    path = Path(__file__).resolve().parents[1] / "resolver" / "source_terms.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {**data["sources"], **BUILT_IN}


RETENTION_RULE = "retention_from_licence@1"


def retention(name: str | None) -> Dict[str, Any]:
    """What a source's stated licence allows with an archived answer (#100), under
    ``retention_from_licence@1``: ``keep`` (a copy for the user's own work) and
    ``share`` (passing the copy on). Derived from the licence, never assumed:

    - no terms recorded, or answers whose terms are each record's (a depositor's, a
      publication's): ``keep: internal``, ``share: unknown``, to review;
    - otherwise ``keep: yes``, and ``share`` with the licence's conditions:
      ``attribution``, ``share_alike``, ``non_commercial`` (none for CC0 and public
      domain). Third-party rights, where a source's terms name them, stay the user's
      to check (``caveats``).
    """
    terms = source_terms().get(name or "")
    licence = LICENCES.get(terms["licence"]) if terms else None
    base: Dict[str, Any] = {"rule": RETENTION_RULE, "source": name}
    if licence is None or licence.get("per_record"):
        return {
            **base,
            "keep": "internal",
            "share": "unknown",
            "reason": "per_record_terms" if licence else "no_terms_recorded",
            **({"licence": terms["licence"]} if terms else {}),
        }
    conditions = [
        c
        for c, holds in (
            ("attribution", licence.get("attribution") is not None),
            ("share_alike", licence.get("share_alike")),
            ("non_commercial", licence.get("non_commercial")),
        )
        if holds
    ]
    return {
        **base,
        "licence": terms["licence"],
        "keep": "yes",
        "share": "yes",
        "conditions": conditions,
        **({"caveats": terms["caveats"]} if terms.get("caveats") else {}),
    }


def verdict(name: str, use: str, today: date | None = None) -> Dict[str, Any]:
    """What a source's stated terms say about ``use``; see the module docstring."""
    terms = source_terms().get(name)
    if terms is None:
        return {"verdict": "unknown", "reason": "no_terms_recorded"}
    licence = LICENCES.get(terms["licence"])
    out: Dict[str, Any] = {
        "licence": terms["licence"],
        "attribution_text": terms.get("attribution"),
        "statement": terms.get("statement"),
        "reviewed": terms.get("reviewed"),
    }
    if terms.get("caveats"):
        out["caveats"] = terms["caveats"]
    reviewed = terms.get("reviewed")
    if reviewed and ((today or date.today()) - date.fromisoformat(reviewed)).days > (
        REVIEW_DAYS
    ):
        out["review_due"] = True
    if licence is None:
        return {**out, "verdict": "unknown", "reason": "licence_not_classified"}
    if licence.get("per_record"):
        return {**out, "verdict": "unknown", "reason": "terms_per_record"}
    if use == "commercial_product" and licence.get("non_commercial"):
        return {**out, "verdict": "restricted", "reason": "non_commercial_licence"}
    obligations: List[str] = []
    if use in SHARED:
        if licence.get("attribution"):
            obligations.append(licence["attribution"])
        if licence.get("share_alike") and use != "academic_publication":
            obligations.append("share_alike")
    return {**out, "verdict": "allowed", "obligations": obligations}


DEPOSITED = " (deposited by "


def record_label(source: str, depositor: str | None) -> str:
    """The name under which a record whose terms are its depositor's is judged:
    ``PubChem BioAssay (deposited by ChEMBL)``, or the source's own name."""
    terms = source_terms().get(source) or {}
    licence = LICENCES.get(terms.get("licence") or "") or {}
    if depositor and licence.get("per_record"):
        return f"{source}{DEPOSITED}{depositor})"
    return source


def labelled_verdict(label: str, use: str, today: date | None = None) -> Dict[str, Any]:
    """``verdict`` for a source name or a ``record_label``: a record deposited by a
    source whose terms the registry names is judged by those terms, and says so."""
    if DEPOSITED not in label:
        return verdict(label, use, today)
    source, depositor = label[:-1].split(DEPOSITED, 1)
    mapped = (source_terms().get(source) or {}).get("depositors", {}).get(depositor)
    basis = {"source": source, "depositor": depositor}
    if mapped is None:
        return {
            "verdict": "unknown",
            "reason": "depositor_terms_not_recorded",
            "basis": basis,
        }
    return {**verdict(mapped, use, today), "basis": {**basis, "terms_of": mapped}}


def _items(card: Any) -> List[Dict[str, Any]]:
    """Every field and relationship of a card, with the sources that state it."""
    store = card.source_assertion_store

    def sources(ids: Iterable[str]) -> List[str]:
        return sorted(
            {
                ((store.get(i) or {}).get("source") or {}).get("name") or "unknown"
                for i in ids
            }
        )

    items = []
    for path in card.list_fields():
        node = card.get(path)
        if isinstance(node, dict) and node.get("source_assertion_ids"):
            items.append(
                {
                    "kind": "field",
                    "path": path,
                    "sources": sources(node["source_assertion_ids"]),
                }
            )
    for rel in card.relationships():
        ids = rel.get("source_assertion_ids") or []
        # A record whose terms are its depositor's is judged by them (#94).
        depositor = ((rel.get("qualifiers") or {}).get("assay") or {}).get("depositor")
        items.append(
            {
                "kind": "relationship",
                "id": rel.get("id"),
                "predicate": rel.get("predicate"),
                "object_ref": rel.get("object_ref"),
                "sources": sorted({record_label(n, depositor) for n in sources(ids)})
                if ids
                else [],
                **({"derived": True} if not ids and rel.get("derivation") else {}),
            }
        )
    return items


def terms_report(
    cards: Iterable[Any], use: str, today: date | None = None
) -> Dict[str, Any]:
    """The terms of the knowledge in ``cards`` for ``use``; see the module docstring."""
    if use not in USES:
        raise ValueError(f"use must be one of {USES}, not {use!r}")
    verdicts: Dict[str, Dict[str, Any]] = {}
    per_card = []
    for card in cards:
        remains = lost = unknown = 0
        lost_items, unknown_items = [], []
        objects: Dict[str, Dict[str, Any]] = {}
        for item in _items(card):
            if item.get("derived"):
                continue
            answers = {}
            for name in item["sources"]:
                if name not in verdicts:
                    verdicts[name] = labelled_verdict(name, use, today)
                answers[name] = verdicts[name]["verdict"]
            if "allowed" in answers.values():
                outcome = "remains"
                remains += 1
            elif "unknown" in answers.values() or not answers:
                outcome = "unknown"
                unknown += 1
                unknown_items.append({**item, "verdicts": answers})
            else:
                outcome = "lost"
                lost += 1
                lost_items.append({**item, "verdicts": answers})
            if item["kind"] == "relationship" and item.get("object_ref"):
                entry = objects.setdefault(
                    item["object_ref"],
                    {"predicates": set(), "sources": set(), "outcomes": set()},
                )
                entry["predicates"].add(item["predicate"])
                entry["sources"].update(item["sources"])
                entry["outcomes"].add(outcome)
        per_card.append(
            {
                "card_id": card.id,
                "items": remains + lost + unknown,
                "remains": remains,
                "lost": lost_items,
                "unknown": unknown_items,
                "status": "complete"
                if not lost and not unknown
                else "partial"
                if remains
                else "none",
                # Per related entity (a measured molecule, a disease…): whether what the
                # card states about it remains for this use.
                "objects": {
                    ref: {
                        "predicates": sorted(e["predicates"]),
                        "sources": sorted(e["sources"]),
                        "status": "complete"
                        if e["outcomes"] == {"remains"}
                        else "partial"
                        if "remains" in e["outcomes"]
                        else "unknown"
                        if "unknown" in e["outcomes"]
                        else "none",
                    }
                    for ref, e in sorted(objects.items())
                },
            }
        )
    allowed = [v for v in verdicts.values() if v["verdict"] == "allowed"]
    obligations = sorted({o for v in allowed for o in v.get("obligations", [])})
    return {
        "use": use,
        "sources": dict(sorted(verdicts.items())),
        "cards": per_card,
        "obligations": obligations,
        "attribution": sorted(
            {
                v["attribution_text"]
                for v in allowed
                if v.get("attribution_text") and v.get("obligations")
            }
        ),
        "restricted": sorted(
            n for n, v in verdicts.items() if v["verdict"] == "restricted"
        ),
        "unknown": sorted(n for n, v in verdicts.items() if v["verdict"] == "unknown"),
        "rule": RULE,
        "disclaimer": DISCLAIMER,
    }


# --- Terms profiles: build only from sources a project's use allows (#94) --------------

#: Each profile, and the use whose verdicts decide it. Named by use, not by
#: institution: a project that may end in commercial exploitation is ``commercial``
#: from its first day, since knowledge that informed a decision cannot be un-used.
PROFILES = {
    "commercial": "commercial_product",
    "non_commercial": "academic_publication",
}
PROFILE_RULE = "terms_profile@1"


class TermsProfile:
    """Which sources a profile admits, and a record of those it excluded.

    A source is admitted only when its stated terms are ``allowed`` for the profile's
    use. Restricted and unknown terms are both excluded, each with its reason: a wrong
    green light is worse than an exclusion."""

    def __init__(self, profile: str) -> None:
        if profile not in PROFILES:
            raise ValueError(
                f"profile must be one of {sorted(PROFILES)}, not {profile!r}"
            )
        self.profile = profile
        self.use = PROFILES[profile]
        self.excluded: Dict[str, str] = {}
        self.excluded_records: Dict[tuple, int] = {}

    def admits(self, source: str) -> bool:
        """Whether the source may be asked at all. A source whose terms are each
        record's depositor's, and which names the depositors whose terms are known,
        is asked; its records are then judged one by one (``admits_record``)."""
        answer = verdict(source, self.use)
        if answer["verdict"] == "allowed":
            return True
        if answer.get("reason") == "terms_per_record" and (
            source_terms().get(source) or {}
        ).get("depositors"):
            return True
        self.excluded[source] = answer.get("reason") or answer["verdict"]
        return False

    def admits_record(self, source: str, depositor: str | None) -> bool:
        """Whether one record of ``source`` is admitted, by its depositor's terms."""
        answer = labelled_verdict(record_label(source, depositor), self.use)
        if answer["verdict"] == "allowed":
            return True
        key = (source, depositor, answer.get("reason") or answer["verdict"])
        self.excluded_records[key] = self.excluded_records.get(key, 0) + 1
        return False

    def detail(self, source: str) -> str:
        return (
            f"excluded by the terms profile {self.profile!r} "
            f"({self.excluded.get(source)})"
        )

    def record(self) -> Dict[str, Any]:
        """What the card keeps about the profile it was built under."""
        return {
            "profile": self.profile,
            "use": self.use,
            "rule": PROFILE_RULE,
            "excluded": [
                {"source": s, "reason": r} for s, r in sorted(self.excluded.items())
            ],
            **(
                {
                    "excluded_records": [
                        {"source": s, "depositor": d, "reason": r, "count": n}
                        for (s, d, r), n in sorted(
                            self.excluded_records.items(), key=lambda kv: str(kv[0])
                        )
                    ]
                }
                if self.excluded_records
                else {}
            ),
        }
