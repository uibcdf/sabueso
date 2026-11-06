"""Compact source-bound chemical classification over one captured Card."""

from .card_chemical_history_v1 import ChemicalResult as ChemicalResult
from .card_chemical_history_v1 import defer_frame as defer_frame
from .card_chemical_selection_v1 import COLUMNS, DEFAULT_FIELDS, FLAGS, item_ref
from .chemical_classification_v1 import SCOPE, interpret
from .errors import ArgumentError

TOPIC = "chemical_classification"
ADAPTER = "chemical_classification_exploration@1"
SUPPORT_FORMAT = "chemical_classification_support@1"


def descriptor():
    return {
        "key": TOPIC,
        "label": "Chemical classes and source-stated roles",
        "description": SCOPE,
        "adapter": ADAPTER,
        "scientific_adapter": True,
        "operations": ["select", "explain", "read", "page"],
        "columns": {
            key: {"type": "boolean_or_null" if key in FLAGS else "string"}
            for key in COLUMNS
        },
        "default_fields": list(DEFAULT_FIELDS),
        "options": {},
        "projection": True,
        "machine_filter": True,
        "machine_order": True,
        "machine_membership": True,
        "selection_policy": "chemical_classification_selection@1",
        "mandatory_interpretation": [
            "scope",
            "rule_names",
            "state",
            "assignment",
            "support_reason",
            "support_grain",
        ],
        "source_support": {
            "format": SUPPORT_FORMAT,
            "record_location": "Append Record(id) to source_store_location only for a present member.",
        },
        "save": True,
    }


def options_for_chemical(options):
    if options is not None and (not isinstance(options, dict) or options):
        raise ArgumentError(f"{TOPIC} has no scientific options.")
    return {}


def materialize(access):
    from .card_chemical_history_v1 import expected_result

    key = (ADAPTER, access._focal_key)
    if key not in access._scientific_cache:
        result = expected_result(access, reader=interpret)
        access._objects[result.result_ref] = result.wire
        access._scientific_cache[key] = result
        for entry in result.entries:
            access._scientific_items[item_ref(result, entry)] = (result, entry.key)
    return access._scientific_cache[key]
