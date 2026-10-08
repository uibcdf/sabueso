"""Read explicit supplied source files, separately from observed remote access."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import zlib
from datetime import datetime, timezone
from pathlib import Path

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso.core.errors import ConnectorError
from sabueso.tools.db._record import source_record


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"Repeated JSON key: {key}")
        out[key] = value
    return out


def _json(text):
    value = json.loads(text, object_pairs_hook=_unique_object)
    # Also rejects exponent overflow, NaN and Infinity without converting literals.
    json.dumps(value, allow_nan=False)
    return value


@signal(tags=["api", "source", "local"])
@arg_digest()
def load_source_snapshot(
    path,
    *,
    source_metadata,
    file_format=None,
    expected_sha256=None,
    records_key=None,
    skip_digestion=False,
):
    """Read structured files or literal UTF-8 HTML/text into a source envelope.

    ``source_metadata`` declares source, kind and optional query/retrieved_at/version/
    terms. These are caller declarations, never proof of a source query or permission.
    Hash verification uses the original file bytes, before decompression. CSV/TSV
    values stay strings. ``records_key`` wraps an explicit row list; it does not
    select, overwrite or guess keys inside a JSON object.
    HTML and TXT remain uninterpreted strings, including a UTF-8 BOM and original
    line endings. They are not parsed, rendered or executed; native validation
    remains the consumer's responsibility. All formats optionally support gzip.

    No acquisition credit or card mutation occurs. Native validation and identity
    binding belong to the source client/mapping consuming this envelope.
    """
    path = Path(path).expanduser().resolve()
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and sha256 != expected_sha256:
        raise ConnectorError(f"SHA-256 mismatch for supplied snapshot: {path}")
    compressed = path.suffix.lower() == ".gz"
    suffix = Path(path.stem).suffix if compressed else path.suffix
    selected = file_format or suffix.lstrip(".").lower()
    if selected not in {"json", "jsonl", "ndjson", "csv", "tsv", "html", "txt"}:
        raise ConnectorError(
            "Snapshot format must be json, jsonl, ndjson, csv, tsv, html or txt."
        )
    try:
        literal = selected in {"html", "txt"}
        text = (gzip.decompress(raw) if compressed else raw).decode(
            "utf-8" if literal else "utf-8-sig"
        )
        if literal:
            payload = text
        elif selected == "json":
            payload = _json(text)
        elif selected in {"jsonl", "ndjson"}:
            payload = [_json(line) for line in text.splitlines() if line.strip()]
        else:
            reader = csv.DictReader(
                io.StringIO(text),
                delimiter="\t" if selected == "tsv" else ",",
                strict=True,
            )
            names = reader.fieldnames
            if (
                not names
                or any(not name for name in names)
                or len(names) != len(set(names))
            ):
                raise ValueError(
                    "Delimited snapshot must have unique, non-empty headers."
                )
            payload = list(reader)
            if any(
                None in row or any(value is None for value in row.values())
                for row in payload
            ):
                raise ValueError("Delimited row width differs from its header.")
        if records_key is not None:
            if not isinstance(payload, list):
                raise ValueError(
                    "records_key wraps a row list; it cannot rewrite a JSON object or text."
                )
            payload = {records_key: payload}
    except (
        ValueError,
        UnicodeError,
        OSError,
        EOFError,
        csv.Error,
        zlib.error,
    ) as error:
        raise ConnectorError(f"Unreadable supplied snapshot {path}: {error}") from error
    envelope = source_record(
        source_metadata["source"],
        source_metadata["kind"],
        source_metadata.get("query", {}),
        source_metadata.get("retrieved_at"),
        source_metadata.get("version"),
        payload,
    )
    envelope["snapshot_receipt"] = {
        "format": "sabueso.supplied_snapshot@1",
        "access": "supplied_file",
        "path": str(path),
        "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "document_sha256": sha256,
        "digest_verification": "matched_caller_digest"
        if expected_sha256
        else "not_requested",
        "file_format": selected,
        "compression": "gzip" if compressed else None,
        "records_key": records_key,
        "source_metadata_basis": "caller_declaration",
        "declared_terms": source_metadata.get("terms"),
        "source_access_observed": False,
    }
    return envelope
