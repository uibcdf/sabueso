"""Shared live access to original publication roles and their stored support."""

from copy import deepcopy
from dataclasses import dataclass

from .card_access import _Entry, _handle
from .card_literature_selection_v1 import COLUMNS, COUNTS, DEFAULT_FIELDS, item_ref
from .errors import ArgumentError
from .snapshot import canonical_json

TOPIC = "literature"
ADAPTER = "literature_exploration@1"
SUPPORT_FORMAT = "literature_support_membership@1"
SCOPE = (
    "Exact publications linked on the captured Card and the original roles, "
    "relationships, statements and locators that link them; no article acquisition, "
    "reading, curation or project Evidence."
)
DEFAULT_OPTIONS = {"publication_ref": None}


def descriptor():
    return {
        "key": TOPIC,
        "label": "Publications and original source context",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {"type": "integer" if key in COUNTS else "string|null"}
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": deepcopy(DEFAULT_OPTIONS),
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "literature_access_selection@1",
        "mandatory_interpretation": [
            "scope",
            "row_grain",
            "rule_names",
            "effective_options",
            "publication_state",
            "role_counts",
            "counting_scope",
            "citation_support_grain",
            "metadata_scope",
            "query_coverage_scope",
            "qualifier_conflicts",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": False,
        "save_reason": "Original independent literature saved reading is not implemented.",
    }


def options_for_literature(options):
    """Validate the sole exact publication focus before any native reader runs."""
    from sabueso._private.argdigest.argument.publication_ref import (
        digest_publication_ref,
    )

    options = {} if options is None else options
    if not isinstance(options, dict) or set(options) - DEFAULT_OPTIONS.keys():
        raise ArgumentError("literature options require only publication_ref.")
    publication_ref = options.get("publication_ref")
    if publication_ref is not None:
        publication_ref = digest_publication_ref(publication_ref)
    return {"publication_ref": publication_ref}


def _native(access, method, *args):
    key = (ADAPTER, "native", access._focal_key, method, canonical_json(args))
    if key not in access._scientific_cache:
        from .card_scientific_access import _CapturedCard

        card_key = (ADAPTER, "captured_card", access._focal_key)
        if card_key not in access._scientific_cache:
            access._scientific_cache[card_key] = _CapturedCard(access._focal)
        card = access._scientific_cache[card_key]
        access._scientific_cache[key] = deepcopy(getattr(card, method)(*args))
    return access._scientific_cache[key]


@dataclass(frozen=True)
class LiteratureResult:
    result_ref: str
    wire: dict
    entries: tuple
    options: dict

    @property
    def native(self):
        return self.wire["native_payload"]

    def location(self, *keys):
        return {
            "format": "card_access_location@1",
            "kind": "result",
            "result_ref": self.result_ref,
            "segments": [{"type": "Key", "value": key} for key in keys],
        }

    def value(self, key, column):
        return self.wire["rows"][key][column]

    def cell_state(self, key, column):
        if self.value(key, column) is not None:
            return "present"
        return "not_applicable" if column == "reason" else "unknown"

    def cell_reason(self, key, column):
        state = self.cell_state(key, column)
        if state == "present":
            return None
        if state == "not_applicable":
            return "The native publication explanation supplies no diagnostic reason."
        return "The native publication summary does not state a scalar value for this field."

    def frame(self, access, selection, entry):
        row, support = self.wire["rows"][entry.key], self.wire["support"][entry.key]
        interpretation = access._location(
            self.location("rows", entry.key, "interpretation")
        )
        return {
            "adapter": ADAPTER,
            "item_ref": item_ref(self, entry),
            "kind": row["kind"],
            "label": row["label"],
            "subject_ref": access._focal.pin,
            "location": access._location(entry.location),
            "payload_location": access._location(
                self.location("rows", entry.key, "item")
            ),
            "state": row["state"],
            "support_location": access._location(self.location("support", entry.key)),
            "support": {
                "ref": entry.key,
                "format": SUPPORT_FORMAT,
                "basis": support["basis"],
                "source_store_location": access._card_location(
                    segments=[{"type": "Key", "value": "source_assertion_store"}]
                ),
                "source_assertions": [
                    {"id": record["id"], "state": record["state"]}
                    for record in support["source_assertions"]
                ],
            },
            "interpretation": deepcopy(row["interpretation"]),
            "interpretation_location": interpretation,
            "cells": {
                column: {
                    "state": self.cell_state(entry.key, column),
                    "reason": self.cell_reason(entry.key, column),
                    "value": deepcopy(self.value(entry.key, column)),
                    "field": {"adapter": ADAPTER, "column": column},
                    "support_basis": support["basis"],
                    "support_ref": entry.key,
                    "value_included": True,
                    "value_location": access._location(
                        self.location("rows", entry.key, column)
                    ),
                    "interpretation_location": interpretation,
                }
                for column in selection._fields
            },
            "value_included": True,
            "inspection_required": False,
        }


def _record_location(access, store, identifier):
    return access._card_location(
        segments=[
            {"type": "Key", "value": store},
            {"type": "Record", "value": identifier},
        ]
    )


def _index(location, index):
    return {
        **location,
        "segments": [*location["segments"], {"type": "Index", "value": index}],
    }


def _membership(access, store, identifiers):
    available = {record["id"] for record in access._focal.data[store]}
    return [
        {
            "id": identifier,
            "state": "present" if identifier in available else "not_retained",
            "location": _record_location(access, store, identifier)
            if identifier in available
            else None,
        }
        for identifier in sorted(identifiers)
    ]


def _support(access, result, key, summary, explanation):
    assertion_ids, relationship_ids = set(), set()

    def assertions(records):
        assertion_ids.update(record["id"] for record in records)

    def relationship(record):
        relationship_ids.add(record["id"])
        assertion_ids.update(record.get("source_assertion_ids") or [])

    assertions(explanation["source_assertions"])
    for link in explanation["links"]:
        relationship(link["relationship"])
        assertions(link["source_assertions"])
        for context in link["structure_contexts"]:
            assertions(context["source_assertions"])
            assertion_ids.update(context["context"].get("source_assertion_ids") or [])
            relationship_ids.update(context["context"].get("relationship_ids") or [])
            for structural in context["relationships"]:
                if structural["relationship"] is not None:
                    relationship(structural["relationship"])
                assertions(structural["source_assertions"])
    sources = _membership(access, "source_assertion_store", assertion_ids)
    relationships = _membership(access, "relationship_store", relationship_ids)
    locators = []
    for field, label in (
        ("cited_by", "Original source citation"),
        ("primary_citation_of", "Original primary-citation target"),
        ("supports", "Original source-stated support"),
        ("curated", "Original curated statement and locator"),
        ("mentions", "Original text-mined mention and locator"),
        ("structure_mentions", "Original structure mention and both support legs"),
        (
            "article_metadata",
            "Original article metadata and bibliographic alternatives",
        ),
    ):
        locators.extend(
            {
                "role": field,
                "label": f"{label} · {index + 1}",
                "location": _index(result.location("rows", key, "item", field), index),
            }
            for index, _ in enumerate(summary.get(field, []))
        )
    for field, label in (
        ("annotation_requests", "Original annotation request"),
        ("unlinked_pdb_mentions", "Original unlinked structure occurrence"),
    ):
        locators.extend(
            {
                "role": field,
                "label": f"{label} · {index + 1}",
                "location": _index(result.location("explanations", key, field), index),
            }
            for index, _ in enumerate(explanation[field])
        )
    return {
        "format": SUPPORT_FORMAT,
        "basis": "original_native_publication_relationships_and_source_assertions",
        "source_assertion_ids": sorted(assertion_ids),
        "source_assertions": sources,
        "relationship_ids": sorted(relationship_ids),
        "relationships": relationships,
        "relationship_locations": [
            record["location"]
            for record in relationships
            if record["state"] == "present"
        ],
        "summary_location": result.location("rows", key, "item"),
        "explanation_location": result.location("explanations", key),
        "context_location": result.location("context"),
        "quality_location": access._card_location(
            segments=[{"type": "Key", "value": "quality"}]
        ),
        "whole_card_context_location": access._card_location(),
        "unresolved_eco_location": result.location("overview", "unresolved_eco"),
        "locator_locations": locators,
        "citation_support_grain": (
            "Exact native publication roles and original relationship/assertion support; "
            "a citation or mention does not assert article reading or support for every displayed claim."
        ),
    }


def _row(summary, explanation):
    return {
        "label": summary["title"]
        if summary["title"] is not None
        else summary["publication_ref"],
        "kind": "literature_publication",
        **{
            key: deepcopy(summary[key])
            for key in ("publication_ref", "title", "journal", "year", "pubmed", "doi")
        },
        "state": explanation["status"],
        "reason": explanation["reason"],
        "cited_by_count": len(summary["cited_by"]),
        "primary_citation_count": len(summary["primary_citation_of"]),
        "support_count": len(summary["supports"]),
        "curated_count": len(summary["curated"]),
        "mention_count": len(summary["mentions"]),
        "structure_mention_count": len(summary.get("structure_mentions", [])),
        "measurement_count": summary["measurements"],
        "relationship_count": len(explanation["links"]),
        "article_metadata_count": len(summary.get("article_metadata", [])),
        "item": deepcopy(summary),
    }


def _outcome(options, native, explanations, overview, unavailable):
    if unavailable is not None:
        return unavailable
    if options["publication_ref"] is not None:
        status = native["status"]
        return {
            "status": "empty"
            if status == "not_on_card"
            else "partial"
            if status == "partial"
            else "ok",
            "reason": native["reason"],
            "native_status": status,
            "native_reason": native["reason"],
        }
    partial = any(
        explanation["status"] == "partial" for explanation in explanations.values()
    ) or bool(overview["unresolved_eco"])
    return {
        "status": "partial" if partial else "ok" if explanations else "empty",
        "reason": "Some original publication support or ECO references remain unresolved."
        if partial
        else None
        if explanations
        else (
            "No publications are linked on this captured Card; consult the separate "
            "original query/source facts. This does not establish absence from articles or sources."
        ),
        "native_status": None,
        "native_reason": None,
        "native_scope": "Complete original literature catalog and unresolved ECO references on this Card.",
    }


def materialize(access, options=None):
    """Cache an exact request and every original publication explanation once."""
    if access.mode != "live":
        raise ArgumentError("Original literature saved reading is not implemented.")
    options = options_for_literature(options)
    cache_key = (ADAPTER, access._focal_key, canonical_json(options))
    if cache_key in access._scientific_cache:
        return access._scientific_cache[cache_key]
    unavailable = None
    if not access._focal.pin:
        unavailable = {
            "status": "missing_prerequisite",
            "reason": (
                "A captured Card identity is required for exact native publication "
                "and source references; use literal inspection."
            ),
        }
    overview, native, explanations, rows = {}, {}, {}, {}
    quality = access._focal.data.get("quality", {})
    coverage = {
        "basis": "not_evaluated",
        "rows": [],
        "quality_location": access._card_location(
            segments=[{"type": "Key", "value": "quality"}]
        ),
        "quality_source_original": deepcopy(
            {
                key: quality[key]
                for key in ("enrichments", "literature_extractions", "curation")
                if key in quality
            }
        ),
        "scope_note": (
            "Original source/query facts are separate from native on-Card publication "
            "states. Unqueried, failed, partial and empty requests never establish "
            "global article absence."
        ),
    }
    if unavailable is None:
        overview = _native(access, "literature")
        knowledge = _native(access, "knowledge_state")
        coverage.update(
            basis="original_knowledge_state_and_retained_quality",
            rule=deepcopy(knowledge["rule"]),
            rows=deepcopy(knowledge["rows"]),
        )
        focus = options["publication_ref"]
        if focus is None:
            native, publications = overview, overview["publications"]
        else:
            native = _native(access, "explain_literature", focus)
            publications = (
                [native["publication"]] if native["publication"] is not None else []
            )
        for publication in publications:
            key = publication["publication_ref"]
            explanations[key] = _native(access, "explain_literature", key)
            rows[key] = _row(publication, explanations[key])
    ref = _handle(
        "XR_",
        {
            "format": "literature_exploration_result@1",
            "adapter": ADAPTER,
            "focal": access._focal_key,
            "options": options,
            "overview": overview,
            "native": native,
            "explanations": explanations,
            "coverage": coverage,
            "unavailable": unavailable,
        },
    )
    wire = {
        "context": {
            **access.context,
            "adapter": ADAPTER,
            "grain": "publication",
            "options": deepcopy(options),
            "used_captures": [access._focal_key],
            "original_card_location": access._card_location(),
            "quality_location": coverage["quality_location"],
        },
        "native_payload": native,
        "overview": overview,
        "rows": rows,
        "explanations": explanations,
        "support": {},
        "coverage": coverage,
        "exclusions": [],
        "scope": SCOPE,
        "schema": {
            key: value
            for key, value in descriptor().items()
            if key not in ("save", "save_reason")
        },
        "outcome": _outcome(options, native, explanations, overview, unavailable),
    }
    shell = LiteratureResult(ref, wire, (), deepcopy(options))
    for key, row in rows.items():
        support = _support(access, shell, key, row["item"], explanations[key])
        wire["support"][key] = support
        row["interpretation"] = {
            "scope": SCOPE,
            "row_grain": "one exact native publication identity with all retained roles",
            "rule_names": [explanations[key]["rule"]["rule"]],
            "effective_options": deepcopy(options),
            "publication_state": row["state"],
            "role_counts": {column: row[column] for column in COUNTS},
            "counting_scope": (
                "Counts of original role entries and source activity records on this "
                "Card; not independent experiments, articles read or independently "
                "asserted document objects."
            ),
            "citation_support_grain": support["citation_support_grain"],
            "metadata_scope": (
                "Native first-non-null summary metadata is unchanged; original source "
                "values, qualifiers and conflicts remain available through the "
                "complete explanation and original assertions."
            ),
            "query_coverage_scope": coverage["scope_note"],
            "qualifier_conflicts": [
                {
                    "relationship_id": link["relationship"]["id"],
                    "conflicts": deepcopy(link["relationship"]["qualifier_conflicts"]),
                }
                for link in explanations[key]["links"]
                if link["relationship"].get("qualifier_conflicts")
            ],
            "context_location": shell.location("context"),
        }
    result = LiteratureResult(
        ref,
        wire,
        tuple(
            _Entry(shell.location("rows", key), key, row) for key, row in rows.items()
        ),
        deepcopy(options),
    )
    access._objects[ref] = wire
    access._scientific_cache[cache_key] = result
    for entry in result.entries:
        access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return result


def defer_frame(frame):
    """Defer values and interpretation together while retaining exact read paths."""
    deferred = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in ("label", "interpretation", "support", "cells")
    }
    deferred.update(
        cells={
            key: {
                name: deepcopy(value) for name, value in cell.items() if name != "value"
            }
            | {"value_included": False}
            for key, cell in frame["cells"].items()
        },
        value_included=False,
        inspection_required=True,
        value_location=frame["location"],
        reason="value_and_interpretation_exceed_response_budget",
    )
    return deferred
