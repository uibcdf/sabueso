"""Original extraction results stored independently of cards and human curation (#92)."""

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path

from sabueso._private.argdigest import arg_digest

from .errors import StorageError
from .literature_extraction import validate
from .snapshot import canonical_json, digest

HEADER = {"sabueso_extractions": {"format": 1}}


class ExtractionStore:
    """A JSONL store of original literal-extraction support and runtime sidecars.

    Reading adds no credit. Explicit application reuses original attribution;
    paths never enter card payloads. Records retain unknown publication/fragment
    terms, and are not an authorization to distribute text fragments.
    """

    @arg_digest()
    def __init__(self, path, skip_digestion=False):
        self.path = Path(path)

    def records(self):
        """Read independent original results, validating their content addresses."""
        if not self.path.exists():
            return []
        try:
            rows = [
                json.loads(line)
                for line in self.path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if not rows or rows[0] != HEADER:
                raise ValueError("unsupported extraction-store header")
            results = []
            for row in rows[1:]:
                data = validate(row["extraction"])
                if row["id"] != digest(canonical_json(data)):
                    raise ValueError("extraction content address does not match")
                results.append(data)
            return results
        except (ValueError, KeyError, TypeError) as error:
            raise StorageError(
                f"Invalid extraction store {self.path}: {error}"
            ) from error

    @arg_digest()
    def save(self, extraction, skip_digestion=False):
        """Save an exact original result; repeated saving is byte-idempotent."""
        data = validate(extraction)
        identifier = digest(canonical_json(data))
        records = self.records()
        if any(data == record for record in records):
            return identifier
        records.append(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(HEADER) + "\n")
                for record in records:
                    stream.write(
                        json.dumps(
                            {
                                "id": digest(canonical_json(record)),
                                "extraction": record,
                            },
                            ensure_ascii=False,
                            allow_nan=False,
                        )
                        + "\n"
                    )
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return identifier

    @arg_digest()
    def apply(self, card, skip_digestion=False):
        """Apply only records of this card's exact subject, without re-extraction."""
        events = []
        for data in self.records():
            subject = data["extraction_trace"]["configuration"]["identifier"]
            if card.id == "sabueso:protein:uniprot:" + subject:
                events.append(card.add_literature_extraction(deepcopy(data)))
        return events
