"""SMonitor catalog for Sabueso (uibcdf/sabueso#31).

Diagnostics tell users what they need to see: a source that could not be consulted, a
result that was truncated, records that could not be identified. The same outcomes stay
recorded as data on cards and decks (``quality.enrichments``, ``deck.meta``); SMonitor is
the user-facing channel, not a replacement for them.

Exceptions keep the message written at each raise site (template ``{message}``), and gain
a stable code.
"""

from __future__ import annotations

from pathlib import Path

from .meta import API_URL, DOC_URL, ISSUES_URL

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

META = {
    "doc_url": DOC_URL,
    "issues_url": ISSUES_URL,
    "api_url": API_URL,
}


def _exception(code: str, name: str, category: str) -> dict:
    return {
        "code": code,
        "source": f"sabueso.error.{name}",
        "category": category,
        "level": "ERROR",
    }


CATALOG = {
    "exceptions": {
        "SabuesoError": _exception("SABUESO-E-GENERIC-001", "generic", "sabueso"),
        "ResolverError": _exception("SABUESO-E-RESOLVE-001", "resolver", "resolution"),
        "SchemaError": _exception("SABUESO-E-SCHEMA-001", "schema", "schema"),
        "StorageError": _exception("SABUESO-E-STORAGE-001", "storage", "storage"),
        "ConnectorError": _exception("SABUESO-E-SOURCE-001", "connector", "source"),
        "RecordNotFoundError": _exception(
            "SABUESO-E-SOURCE-002", "record_not_found", "source"
        ),
        "ArgumentError": _exception("SABUESO-E-ARG-001", "argument", "argument"),
    },
    "warnings": {
        "EnrichmentFailedWarning": {
            "code": "SABUESO-W-ENRICH-001",
            "source": "sabueso.warning.enrichment_failed",
            "category": "source",
            "level": "WARNING",
        },
        "EnrichmentTruncatedWarning": {
            "code": "SABUESO-W-ENRICH-002",
            "source": "sabueso.warning.enrichment_truncated",
            "category": "source",
            "level": "WARNING",
        },
        "UnanchoredRecordsWarning": {
            "code": "SABUESO-W-IDENTITY-001",
            "source": "sabueso.warning.unanchored_records",
            "category": "identity",
            "level": "WARNING",
        },
        "DeprecatedUsageWarning": {
            "code": "SABUESO-W-DEPRECATED-001",
            "source": "sabueso.warning.deprecated_usage",
            "category": "api",
            "level": "WARNING",
        },
        "CuratedDisagreementWarning": {
            "code": "SABUESO-W-CURATION-001",
            "source": "sabueso.warning.curated_disagreement",
            "category": "curation",
            "level": "WARNING",
        },
    },
}

_RAISE_SITE = {"title": "Sabueso error", "user_message": "{message}"}

CODES = {
    "SABUESO-E-GENERIC-001": {**_RAISE_SITE, "title": "Sabueso error"},
    "SABUESO-E-RESOLVE-001": {**_RAISE_SITE, "title": "Resolution failed"},
    "SABUESO-E-SCHEMA-001": {**_RAISE_SITE, "title": "Schema error"},
    "SABUESO-E-STORAGE-001": {**_RAISE_SITE, "title": "Storage error"},
    "SABUESO-E-SOURCE-001": {**_RAISE_SITE, "title": "Source unavailable"},
    "SABUESO-E-SOURCE-002": {**_RAISE_SITE, "title": "Record not found"},
    "SABUESO-E-ARG-001": {
        **_RAISE_SITE,
        "title": "Invalid argument",
        "user_hint": "Check the documented values of this argument.",
    },
    "SABUESO-W-ENRICH-001": {
        "title": "Source not consulted",
        "user_message": "{source} could not be consulted for {subject}; the result was "
        "built without it.",
        "user_hint": "The failure is recorded with the result. Retry later, or check "
        "the source's availability.",
        "dev_message": "{source} failed for {subject}: {detail}",
        "dev_hint": "See the enrichment record for the full outcome.",
    },
    "SABUESO-W-ENRICH-002": {
        "title": "Result truncated",
        "user_message": "{source} returned {count} of {total} records for {subject}; "
        "the result is incomplete.",
        "user_hint": "Raise the limit to retrieve all of them.",
    },
    "SABUESO-W-IDENTITY-001": {
        "title": "Records without identity",
        "user_message": "{count} records could not be anchored at a standard InChIKey "
        "and were left out of the deck (for {subject}).",
        "user_hint": "They are listed in deck.meta['unanchored'].",
        "dev_message": "Unanchored records for {subject}: {examples}",
    },
    "SABUESO-W-DEPRECATED-001": {
        "title": "Deprecated function",
        "user_message": "{function} is deprecated and will be removed before Sabueso 1.0.",
        "user_hint": "Use {replacement} instead.",
    },
    "SABUESO-W-CURATION-001": {
        "title": "Curated assertion differs",
        "user_message": "The literature assertion from {publication} on {field} of "
        "{subject} differs from what other sources state about the same item. Both are "
        "kept; neither takes priority.",
        "user_hint": "Whether they contradict needs a reader: see "
        "card.quality['conflicts'] and card.literature().",
    },
}

SIGNALS = {
    "sabueso.warning.enrichment_failed": {
        "extra_required": ["source", "subject", "detail"]
    },
    "sabueso.warning.enrichment_truncated": {
        "extra_required": ["source", "subject", "count", "total"]
    },
    "sabueso.warning.unanchored_records": {
        "extra_required": ["subject", "count", "examples"]
    },
    "sabueso.warning.deprecated_usage": {"extra_required": ["function", "replacement"]},
    "sabueso.warning.curated_disagreement": {
        "extra_required": ["subject", "field", "publication"]
    },
}
