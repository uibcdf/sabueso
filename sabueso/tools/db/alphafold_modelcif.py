"""Explicit supplied AlphaFold ModelCIF metadata, never an API/archive fallback.

The caller supplies one plain/gzip file. Its complete original byte identity and
all non-atom-site CIF columns survive; the excluded atom tables are named.
No URL, coordinate model, referenced file or molecular calculation is executed.
"""

import gzip
import hashlib
import importlib.metadata
import io
import os
import zlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from smonitor import signal

from sabueso._private.argdigest import arg_digest
from sabueso._private.argdigest.argument.expected_sha256 import digest_expected_sha256
from sabueso._private.argdigest.argument.identifier import digest_identifier
from sabueso._private.argdigest.argument.max_decoded_bytes import (
    digest_max_decoded_bytes,
)
from sabueso._private.argdigest.argument.max_encoded_bytes import (
    digest_max_encoded_bytes,
)
from sabueso._private.argdigest.argument.path import digest_path
from sabueso._private.argdigest.argument.source_metadata import digest_source_metadata
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_acquisition import (
    _terminal,
    acquisition,
    capture_acquisitions,
    missing_fixture,
)
from sabueso.mappings.alphafold_modelcif_v1 import (
    FORMAT,
    KIND,
    SOURCE,
    declaration,
    extract_metadata,
    validate_response,
)
from sabueso.tools.db._record import source_record

BYTE_LIMIT = 64 * 1024**2


def _query(identifier):
    return {"accession": digest_identifier(identifier)}


def _check(name, size, ceiling):
    if ceiling is not None and size > ceiling:
        raise ArgumentError(
            f"Native source file exceeds {name}={ceiling}; increase {name} explicitly or pass {name}=None deliberately. No partial metadata is returned.",
            argument=name,
        )


def _load(path, metadata, expected_sha256, encoded, decoded):
    path = Path(digest_path(path)).expanduser().resolve()
    encoded, decoded = (
        digest_max_encoded_bytes(encoded),
        digest_max_decoded_bytes(decoded),
    )
    try:
        with path.open("rb") as stream:
            _check("max_encoded_bytes", os.fstat(stream.fileno()).st_size, encoded)
            raw = stream.read() if encoded is None else stream.read(encoded + 1)
    except OSError as error:
        raise missing_fixture(
            f"Supplied AlphaFold ModelCIF is unavailable: {path}"
        ) from error
    _check("max_encoded_bytes", len(raw), encoded)
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and sha != expected_sha256:
        raise ConnectorError("SHA-256 mismatch for supplied AlphaFold ModelCIF.")
    compressed = raw.startswith(b"\x1f\x8b")
    try:
        if compressed:
            with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as stream:
                body = stream.read() if decoded is None else stream.read(decoded + 1)
        else:
            body = raw
        _check("max_decoded_bytes", len(body), decoded)
        text = body.decode("utf-8")
    except (OSError, EOFError, zlib.error, UnicodeError) as error:
        raise ConnectorError(
            f"Unreadable supplied AlphaFold ModelCIF: {error}"
        ) from error
    record, excluded = extract_metadata(text)
    result = source_record(
        SOURCE, KIND, metadata["query"], metadata.get("retrieved_at"), None, record
    )
    result["native_format"] = FORMAT
    result["snapshot_receipt"] = {
        "format": "sabueso.supplied_snapshot@1",
        "access": "supplied_file",
        "path": str(path),
        "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "document_sha256": sha,
        "decoded_sha256": hashlib.sha256(body).hexdigest(),
        "encoded_bytes": len(raw),
        "decoded_bytes": len(body),
        "digest_verification": "matched_caller_digest"
        if expected_sha256
        else "not_requested",
        "file_format": "modelcif",
        "compression": "gzip" if compressed else None,
        "source_metadata_basis": "caller_declaration",
        "declared_terms": deepcopy(metadata.get("terms")),
        "source_access_observed": False,
    }
    result["native_extraction"] = {
        "format": FORMAT,
        "metadata_sha256": digest(canonical_json(record)),
        "scope": "all_received_columns_except_atom_site_and_atom_site_anisotrop_tables",
        "excluded_coordinate_tables": excluded,
        "parser": {"name": "gemmi", "version": importlib.metadata.version("gemmi")},
        "database_completeness": "not_established_by_one_supplied_file",
        "coordinate_or_canonical_correspondence": "not_evaluated",
    }
    return result


def _summarize(result, query, fixture, requests):
    if isinstance(result, Exception):
        return {"outcome": _terminal(result, fixture, requests)}
    native = result["native_extraction"]
    return {
        "outcome": "received",
        "count": 1,
        "truncated": False,
        "retrieved_at": result.get("retrieved_at"),
        "source_version": {
            "value": None,
            "basis": "native_model_revision_not_stated;_filename_and_distribution_not_model_version",
        },
        "response_identity": {
            "basis": "complete_original_supplied_ModelCIF_bytes",
            "hash": "sha256:" + result["snapshot_receipt"]["document_sha256"],
        },
        "access": "supplied_file",
        "snapshot_receipt": deepcopy(result["snapshot_receipt"]),
        "native_metadata_identity": native["metadata_sha256"],
        "coverage": "one_explicit_model_file_only;other_models_and_distributions_not_asked",
        "native_citations": "literal_columns_retained_if_stated;publication_metadata_not_queried",
    }


class SnapshotAlphaFoldModelCIFClient:
    native_format = FORMAT

    def __init__(
        self,
        path,
        *,
        source_metadata,
        expected_sha256=None,
        max_encoded_bytes=BYTE_LIMIT,
        max_decoded_bytes=BYTE_LIMIT,
    ):
        self.path = digest_path(path)
        self.source_metadata = digest_source_metadata(source_metadata)
        self.expected_sha256 = digest_expected_sha256(expected_sha256)
        self.max_encoded_bytes = digest_max_encoded_bytes(max_encoded_bytes)
        self.max_decoded_bytes = digest_max_decoded_bytes(max_decoded_bytes)

    @acquisition(SOURCE, KIND, fixture=True, summarize=_summarize)
    def prediction(self, accession):
        query = _query(accession)
        metadata = digest_source_metadata(self.source_metadata)
        if (
            metadata["source"] != SOURCE
            or metadata["kind"] != KIND
            or metadata.get("query") != query
            or metadata.get("version") is not None
        ):
            raise ConnectorError(
                "Supplied AlphaFold ModelCIF source/kind/query/revision differ from the request; no file was read."
            )
        result = _load(
            self.path,
            metadata,
            digest_expected_sha256(self.expected_sha256),
            self.max_encoded_bytes,
            self.max_decoded_bytes,
        )
        declaration(result["record"], query["accession"])
        return result


class FixtureAlphaFoldModelCIFClient:
    """One explicitly named public fixture file; its name never establishes identity."""

    native_format = FORMAT

    def __init__(
        self,
        path,
        *,
        retrieved_at=None,
        expected_sha256=None,
        max_encoded_bytes=BYTE_LIMIT,
        max_decoded_bytes=BYTE_LIMIT,
    ):
        self.path = digest_path(path)
        self.retrieved_at = retrieved_at
        self.expected_sha256 = digest_expected_sha256(expected_sha256)
        self.max_encoded_bytes = digest_max_encoded_bytes(max_encoded_bytes)
        self.max_decoded_bytes = digest_max_decoded_bytes(max_decoded_bytes)

    def prediction(self, accession):
        return SnapshotAlphaFoldModelCIFClient(
            self.path,
            source_metadata={
                "source": SOURCE,
                "kind": KIND,
                "query": _query(accession),
                "retrieved_at": self.retrieved_at,
            },
            expected_sha256=self.expected_sha256,
            max_encoded_bytes=self.max_encoded_bytes,
            max_decoded_bytes=self.max_decoded_bytes,
        ).prediction(accession)


@signal(tags=["api", "source", "local"])
@arg_digest()
@capture_acquisitions
def get_modelcif_metadata(identifier, client=None, skip_digestion=False):
    """Read original native metadata from an explicit single-model file client.

    Gemmi is optional and needed only for requested file parsing. Defaults bound
    encoded and decoded file bytes at 64 MiB; positive/None constructor overrides
    are explicit. These limits do not bound all parser/Python-object memory.
    Source/model identity is read from native columns, not the file name. This is
    not the prediction API, a proteome download or a canonical/atom mapping.
    """
    query = _query(identifier)
    if (
        client is None
        or getattr(client, "native_format", None) != FORMAT
        or not callable(getattr(client, "prediction", None))
    ):
        raise ArgumentError(
            "Supply an explicit AlphaFold ModelCIF file client; no online, archive or API fallback is performed.",
            argument="client",
        )
    response = client.prediction(query["accession"])
    validate_response(response, query["accession"])
    return response
