"""Merge mapping outputs into a single mapping result."""

from __future__ import annotations

from typing import Any, Dict, List


def merge_mapping_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    source_assertions: List[Dict[str, Any]] = []
    field_source_assertions: Dict[str, List[str]] = {}
    relationships: List[Dict[str, Any]] = []

    for res in results:
        for fp, val in res.get("fields", {}).items():
            fields[fp] = val
        for fp, val in res.get("features", {}).items():
            features[fp] = val
        for assertion in res.get("source_assertions", []):
            source_assertions.append(assertion)
        for fp, sa_ids in res.get("field_source_assertions", {}).items():
            field_source_assertions.setdefault(fp, []).extend(sa_ids)
        relationships.extend(res.get("relationships", []))

    # The located-annotation mapping explicitly retains every alias request/date
    # for identical native content; it never selects away an observation receipt.
    from sabueso.mappings.europepmc import coalesce_annotation_observations

    source_assertions = coalesce_annotation_observations(source_assertions)
    return {
        "fields": fields,
        "features": features,
        "source_assertions": source_assertions,
        "field_source_assertions": field_source_assertions,
        "relationships": relationships,
    }
