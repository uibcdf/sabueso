"""Explicit intake and replay of the bounded literal extraction (#92).

Scientific support belongs on cards. Original runtime records remain detached;
payload-only refresh preserves support but cannot reconstruct original attribution.
"""

import json
from copy import deepcopy

from . import attribution as adapter
from .errors import SchemaError
from .relationship_store import make_relationship
from .snapshot import canonical_json, digest
from .source_assertion_store import make_source_assertion

RULE = "literal_uniprot_mention@1"
INTAKE = "literal_mention_intake@1"


def validate(extraction):
    """Validate support closure for the delivered rule; do not re-execute it."""
    from sabueso._private.argdigest.argument.publication import PUBLICATION
    from sabueso.tools.literature import _ACCESSION

    try:
        data = json.loads(json.dumps(extraction, allow_nan=False))
        trace = data["extraction_trace"]
        assertions = data["source_assertions"]
        relationships = data["relationships"]
        config = trace["configuration"]
        identifier = config["identifier"]
        publication = trace["publication_ref"]
        locator = trace["locator"]
        input_hash = trace["input_sha256"]
        if not (
            trace["format"] == "sabueso.literature_extraction@1"
            and trace["rule"] == RULE
            and _ACCESSION.fullmatch(identifier)
            and PUBLICATION.fullmatch(publication)
            and isinstance(locator, str)
            and locator
            and isinstance(input_hash, str)
            and input_hash.startswith("sha256:")
            and len(input_hash) == 71
            and all(c in "0123456789abcdef" for c in input_hash[7:])
            and isinstance(assertions, list)
            and isinstance(relationships, list)
            and type(trace["count"]) is int
            and trace["count"] == len(assertions)
            and isinstance(trace["started_at"], str)
            and trace["started_at"]
            and trace["terms"]
            == {"state": "unknown", "scope": "supplied_text_fragment"}
            and trace["outcome"] == ("received" if assertions else "empty")
            and config
            == {
                "identifier": identifier,
                "namespaces": ["UniProt", "UniProtKB", "official_uniprot_url"],
                "case_sensitive": True,
                "offset_basis": "unicode_characters_zero_based_end_exclusive",
                "scope": "supplied_text_fragment",
            }
        ):
            raise ValueError("unsupported rule or inconsistent fragment identity")
        literals = {f"UniProt:{identifier}", f"UniProtKB:{identifier}"} | {
            f"{scheme}://www.uniprot.org/{path}/{identifier}{suffix}"
            for scheme in ("http", "https")
            for path in ("uniprot", "uniprotkb")
            for suffix in ("", "/entry")
        }
        ids = []
        for assertion in assertions:
            value = assertion["asserted_value"]
            if not (
                value["locator"] == locator
                and value["input_sha256"] == input_hash
                and type(value["start"]) is int
                and type(value["end"]) is int
                and 0 <= value["start"] < value["end"]
                and isinstance(value["text"], str)
                and value["text"] in literals
                and len(value["text"]) == value["end"] - value["start"]
                and assertion["acquisition"]
                == {
                    "method": "rule_extraction",
                    "tool": "sabueso.literal_uniprot_mention",
                    "version": "1",
                    "configuration": config,
                }
                and assertion
                == make_source_assertion(
                    "relationships.mentioned_in",
                    value,
                    "Literature",
                    publication,
                    trace["started_at"],
                    source_type="literature",
                    subject_ref=f"uniprot:{identifier}",
                    acquisition=assertion["acquisition"],
                )
            ):
                raise ValueError("inconsistent original occurrence support")
            ids.append(assertion["id"])
        if len(set(ids)) != len(ids) or relationships != _relationships(
            f"uniprot:{identifier}", publication, assertions
        ):
            raise ValueError("inconsistent relationship support closure")
        if "article_metadata" in data:
            from .article_metadata import validate as validate_metadata

            binding = validate_metadata(data["article_metadata"], publication)
            if trace.get("article_metadata_support") != {
                "source_assertion_id": binding["source_assertion"]["id"],
                "identity_basis": "source_stated_publication_identifier",
                "fragment_terms": "unknown",
            }:
                raise ValueError("inconsistent article metadata support")
        elif "article_metadata_support" in trace:
            raise ValueError("missing original article metadata support")
        return data
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise SchemaError(f"Invalid literal literature extraction: {error}") from error


def _relationships(subject, publication, assertions):
    if not assertions:
        return []
    return [
        make_relationship(
            subject,
            "mentioned_in",
            publication,
            qualifiers={
                "source": "Literature",
                "mention": "uniprot_accession",
                "article": {"publication_ref": publication},
                "locations": [
                    {**a["asserted_value"], "source_assertion_id": a["id"]}
                    for a in assertions
                ],
            },
            source_assertion_ids=[a["id"] for a in assertions],
        )
    ]


def _merge(
    card,
    assertions,
    relationships,
    record,
    preserve_original=False,
    metadata_assertions=(),
):
    if assertions and card.quality.get("terms_profile"):
        raise SchemaError("Unknown fragment terms cannot enter a terms-profile card.")
    # Check the whole incoming support before changing anything. The same occurrence
    # may have been extracted again; its first recorded retrieval time stays intact.
    for assertion in [*assertions, *metadata_assertions]:
        existing = card.source_assertion_store.get(assertion["id"])
        if existing and {k: v for k, v in existing.items() if k != "retrieved_at"} != {
            k: v for k, v in assertion.items() if k != "retrieved_at"
        }:
            raise SchemaError(f"Conflicting extraction support id {assertion['id']}")
    for assertion in [*assertions, *metadata_assertions]:
        if (
            preserve_original
            or card.source_assertion_store.get(assertion["id"]) is None
        ):
            card.source_assertion_store.add(deepcopy(assertion))
    for relationship in relationships:
        card.relationship_store.add(deepcopy(relationship))
    records = card.quality.setdefault("literature_extractions", [])
    if not any(r["id"] == record["id"] for r in records):
        records.append(deepcopy(record))


def add_extraction(card, extraction):
    """Intake copies original support; reuse credit is an independent runtime event."""
    from .card import CARD_SCHEMA_VERSION

    data = validate(extraction)
    trace = data["extraction_trace"]
    subject = "uniprot:" + trace["configuration"]["identifier"]
    if card.id != "sabueso:protein:" + subject:
        raise SchemaError(
            "Literature extraction requires the exact UniProt card subject."
        )
    if card.meta.get("schema_version") != CARD_SCHEMA_VERSION:
        raise SchemaError(
            "Migrate the card explicitly before literature extraction intake."
        )
    record = {
        "rule": INTAKE,
        "extraction_rule": trace["rule"],
        "publication_ref": trace["publication_ref"],
        "locator": trace["locator"],
        "input_sha256": trace["input_sha256"],
        "subject_ref": subject,
        "source_assertion_ids": [a["id"] for a in data["source_assertions"]],
        "relationship_ids": [r["id"] for r in data["relationships"]],
        "terms": deepcopy(trace["terms"]),
    }
    record["id"] = digest(canonical_json(record))
    metadata_assertions = []
    if "article_metadata" in data:
        metadata_assertions = [data["article_metadata"]["source_assertion"]]
        record["article_metadata_source_assertion_ids"] = [
            a["id"] for a in metadata_assertions
        ]
        record["metadata_binding_rule"] = "article_metadata_binding@1"
        record["id"] = digest(
            canonical_json({k: v for k, v in record.items() if k != "id"})
        )
    _merge(
        card,
        data["source_assertions"],
        data["relationships"],
        record,
        metadata_assertions=metadata_assertions,
    )
    event = {
        "format": "sabueso.literature_intake@1",
        "route": "reused_extraction",
        "card_ref": card.pinned_ref(),
        "intake_id": record["id"],
        "original_extraction": deepcopy(trace),
    }
    event["provider"] = _credit(event)
    _observe(card, event)
    return deepcopy(event)


def _observe(card, event):
    card._literature_intake_traces.append(deepcopy(event))
    adapter._observe_literature(event)


def _credit(event):
    original = event["original_extraction"]
    attribution = (original.get("provider") or {}).get("attribution")
    if attribution is None:
        return {
            "status": "unavailable",
            "reason": "original_attribution_not_available",
            "attribution": None,
        }
    backend = None
    try:
        from .attribution_bibliography import software

        backend = adapter._load_backend()
        saved = backend.Attribution.from_dict(attribution).to_dict()
        context = {
            "route": event["route"],
            "card_ref": event["card_ref"],
            "intake_id": event["intake_id"],
            "original_producer": original["producer"],
        }
        with backend.capture(
            "sabueso.add_literature_extraction", context=context
        ) as capture:
            with backend.scope("sabueso.add_literature_extraction"):
                for item in saved["items"]:
                    backend.register_item(**item)
                for use in saved["uses"]:
                    backend.track_item(
                        use["item_id"],
                        roles=["reused_reference"],
                        context={**context, "original_use": deepcopy(use)},
                    )
                current = software()
                backend.register_item(**current)
                backend.track_item(
                    current["id"], roles=["executed_software"], context=context
                )
        return {
            "status": "available",
            "version": backend.__version__,
            "attribution": capture.attribution.to_dict(),
        }
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        adapter._warning("literature extraction intake", reason)
        return {
            "status": "failed",
            "version": getattr(backend, "__version__", None),
            "reason": reason,
            "attribution": None,
        }


def preserve_extractions(previous, refreshed):
    """Preserve stored scientific support; never manufacture an original runtime trace."""
    records = previous.quality.get("literature_extractions") or []
    if not records:
        return
    if previous.id != refreshed.id:
        raise SchemaError(
            "Refreshing extraction support requires the same stated subject."
        )
    for record in records:
        assertions = [
            previous.source_assertion_store.get(i)
            for i in record["source_assertion_ids"]
        ]
        if any(a is None for a in assertions):
            raise SchemaError(
                "Cannot refresh literature extraction with missing original support."
            )
        metadata_assertions = [
            previous.source_assertion_store.get(i)
            for i in record.get("article_metadata_source_assertion_ids", [])
        ]
        if any(
            a is None
            or a.get("field_path") != "literature.article_metadata"
            or a.get("subject_ref") != record["publication_ref"]
            for a in metadata_assertions
        ):
            raise SchemaError(
                "Cannot refresh literature metadata with missing or inconsistent original support."
            )
        if any(
            previous.relationship_store.get(i) is None
            for i in record["relationship_ids"]
        ):
            raise SchemaError(
                "Cannot refresh literature extraction with missing original relationship."
            )
        relationships = _relationships(
            record["subject_ref"], record["publication_ref"], assertions
        )
        if [r["id"] for r in relationships] != record["relationship_ids"]:
            raise SchemaError(
                "Cannot refresh inconsistent literature extraction relationships."
            )
        _merge(
            refreshed,
            assertions,
            relationships,
            record,
            preserve_original=True,
            metadata_assertions=metadata_assertions,
        )
        if not any(
            t["intake_id"] == record["id"] for t in refreshed._literature_intake_traces
        ):
            _observe(
                refreshed,
                {
                    "format": "sabueso.literature_intake@1",
                    "route": "stored_support",
                    "card_ref": refreshed.pinned_ref(),
                    "intake_id": record["id"],
                    "original_extraction": None,
                    "provider": {
                        "status": "not_recorded",
                        "attribution": None,
                        "reason": "original_runtime_sidecar_not_supplied",
                    },
                },
            )
