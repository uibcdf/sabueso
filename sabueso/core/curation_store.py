"""Curated assertions that survive rebuilds: the curation store (uibcdf/sabueso#48).

Cards are rebuilt from their sources, for example to get a newer UniProt release; a
curated literature assertion (``sabueso.core.curation``) lives on the card it was added
to. The ``CurationStore`` keeps what was curated, apart from any card, and applies it
again when a card of the same entity is built:

- one JSON line per curated assertion: what was stated, where (publication, locator),
  who curated it and when, and the outcome last seen. Never a card;
- records are keyed by SourceAssertion id. Curated ids are derived from the statement
  itself (publication, field, value as stored, locator), so re-applying a record
  recreates the same SourceAssertion: a reference to it keeps meaning the same thing;
- applying recomputes each outcome against the fresh sources, and reports an outcome
  that changed since it was last recorded (a database may start to state the same
  value, or to state something else);
- a retracted record is kept, with its reason, curator and date, and is not applied.

The file holds a header line ``{"sabueso_curations": {"format": 1}}`` and then one
record per line. Pinning and the reference syntax shared with Nextia are decided in
uibcdf/moli#3; these ids are Sabueso's provisional internal identities.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .errors import StorageError

HEADER = "sabueso_curations"
FORMAT = 1


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _records_of(card: Any) -> List[Dict[str, Any]]:
    """The curated assertions on a card, as store records."""
    outcomes = {
        r["source_assertion_id"]: r["outcome"] for r in card.quality.get("curation", [])
    }
    records = []
    for assertion in card.source_assertion_store.to_list():
        source = assertion.get("source") or {}
        if source.get("type") != "literature":
            continue
        metadata = assertion.get("source_metadata") or {}
        curation = metadata.get("curation") or {}
        record: Dict[str, Any] = {
            "source_assertion_id": assertion["id"],
            "entity": assertion["subject_ref"],
            "publication": source.get("record_id"),
            "curator": curation.get("curator"),
            "curated_at": curation.get("curated_at"),
            "locator": curation.get("locator"),
            "quote": curation.get("quote"),
            "eco_code": ((metadata.get("eco") or [{}])[0]).get("code"),
            "outcome": outcomes.get(assertion["id"]),
        }
        field_path = assertion["field_path"]
        if field_path == "relationships.has_bioactivity":
            stated = assertion["asserted_value"]
            measurement = stated["measurement"]
            anchor = f"inchikey:{stated['molecule']['inchikey']}"
            known = card.entity_identities.get(anchor) or {}
            record.update(
                kind="bioactivity",
                molecule={
                    **stated["molecule"],
                    "records": sorted(known.get("records") or []),
                },
                measurement_type=measurement["type"],
                value={"value": measurement["value"], "unit": measurement["unit"]},
                relation=measurement["relation"],
                target_assignment=stated["target_assignment"],
                assay_description=stated.get("assay_description"),
            )
        elif field_path.startswith("relationships."):
            record.update(
                kind="relationship",
                predicate=field_path.split(".", 1)[1],
                object_ref=assertion["asserted_value"]["object_ref"],
                qualifiers=assertion["asserted_value"]["qualifiers"],
            )
        else:
            record.update(
                kind="field",
                field_path=field_path,
                value=assertion["asserted_value"],
                method=metadata.get("method"),
            )
        records.append(record)
    return records


class CurationStore:
    """A JSONL file of curated literature assertions, applied when cards are built."""

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = Path(path)

    # --- reading and writing -------------------------------------------------------------

    def records(self) -> List[Dict[str, Any]]:
        """Every record, retracted ones included; empty if the file does not exist."""
        if not self.path.exists():
            return []
        out: List[Dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if number == 1 and set(data) == {HEADER}:
                    version = (data[HEADER] or {}).get("format")
                    if version != FORMAT:
                        raise StorageError(
                            f"{self.path}: curation store format {version!r} is not "
                            f"supported (expected {FORMAT})."
                        )
                    continue
                if number == 1:
                    raise StorageError(f"{self.path} is not a Sabueso curation store.")
                out.append(data)
        return out

    def _write(self, records: List[Dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Written to a temporary file and moved into place: a failure never leaves a
        # half-written store.
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps({HEADER: {"format": FORMAT}}) + "\n")
            for record in records:
                f.write(json.dumps(record, sort_keys=True, default=str) + "\n")
        os.replace(tmp, self.path)

    # --- operations ----------------------------------------------------------------------

    def save(self, card: Any) -> Dict[str, int]:
        """Record the card's curated assertions. Saving twice changes nothing but the
        outcome last seen; a retracted record stays retracted."""
        stored = {r["source_assertion_id"]: r for r in self.records()}
        added = updated = 0
        for record in _records_of(card):
            previous = stored.get(record["source_assertion_id"])
            if previous is None:
                record["outcome_checked_at"] = _today()
                stored[record["source_assertion_id"]] = record
                added += 1
            elif previous.get("outcome") != record["outcome"]:
                previous["outcome"] = record["outcome"]
                previous["outcome_checked_at"] = _today()
                updated += 1
        self._write(list(stored.values()))
        return {"added": added, "updated": updated, "total": len(stored)}

    def retract(self, source_assertion_id: str, reason: str, curator: str) -> None:
        """Mark a record as retracted. It is kept, and never applied again."""
        records = self.records()
        for record in records:
            if record["source_assertion_id"] == source_assertion_id:
                record["retracted"] = {
                    "reason": reason,
                    "curator": curator,
                    "at": _today(),
                }
                self._write(records)
                return
        raise StorageError(
            f"No curated assertion {source_assertion_id} in {self.path}."
        )

    def apply(self, card: Any) -> Dict[str, Any]:
        """Apply the records about the card's entity; returns what happened.

        ``{"applied", "skipped_retracted", "changed": [{source_assertion_id,
        previous_outcome, outcome}]}``. The same summary is kept in
        ``card.quality["curation_store"]``.
        """
        from .curation import _subject

        subject = _subject(card)
        applied, retracted, changed = 0, 0, []
        for record in self.records():
            if record.get("entity") != subject:
                continue
            if record.get("retracted"):
                retracted += 1
                continue
            common = dict(
                publication=record["publication"],
                curator=record["curator"],
                locator=record.get("locator"),
                quote=record.get("quote"),
                eco_code=record.get("eco_code"),
                curated_at=record.get("curated_at"),
            )
            if record["kind"] == "bioactivity":
                result = card.add_literature_bioactivity(
                    record["molecule"],
                    record["measurement_type"],
                    record["value"],
                    target_assignment=record["target_assignment"],
                    relation=record["relation"],
                    assay_description=record.get("assay_description"),
                    **common,
                )
            elif record["kind"] == "relationship":
                result = card.add_literature_relationship(
                    record["predicate"],
                    record["object_ref"],
                    record.get("qualifiers"),
                    **common,
                )
            else:
                result = card.add_literature_assertion(
                    record["field_path"],
                    record["value"],
                    method=record.get("method"),
                    **common,
                )
            if result["source_assertion_id"] != record["source_assertion_id"]:
                raise StorageError(
                    f"Re-applying {record['source_assertion_id']} produced "
                    f"{result['source_assertion_id']}: the record no longer states the "
                    "same thing."
                )
            applied += 1
            if record.get("outcome") and result["outcome"] != record["outcome"]:
                changed.append(
                    {
                        "source_assertion_id": record["source_assertion_id"],
                        "previous_outcome": record["outcome"],
                        "previously_checked": record.get("outcome_checked_at"),
                        "outcome": result["outcome"],
                    }
                )
        summary = {
            "applied": applied,
            "skipped_retracted": retracted,
            "changed": changed,
        }
        card.quality["curation_store"] = summary
        return summary
