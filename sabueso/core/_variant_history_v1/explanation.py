"""SDK230 scoped tissue explanation and exact source-input membership."""

from copy import deepcopy

from .rules import make_derivation
from .source import _Support
from .tissue_usage import (
    EXONS,
    ISOFORMS,
    REGIONS,
    TERMS,
    TISSUE_TEXT,
    TRANSCRIPTS,
    VARIANTS,
)
from .validation import check_arguments


def explain_variant_tissue_usage(card, threshold, usage_rule="pext_at_variant@2"):
    check_arguments(threshold, usage_rule, kind="variant")
    return _scoped_explanation(card, threshold, kind="variant")


def explain_isoform_tissue_usage(card, threshold, usage_rule="isoform_exon_usage@3"):
    check_arguments(threshold, usage_rule, kind="isoform")
    return _scoped_explanation(card, threshold, kind="isoform")


class _ComparativeSupport(_Support):
    def __init__(self, card, paths):
        super().__init__(card, predicates={"same_as", "clustered_with", "isoform_of"})
        self.fields = {path: self.field(path) for path in paths}

    def field(self, path):
        field = super().field(path)
        field["card_ref"] = self.pin
        if not field["stored"]:
            field["alternatives"] = self.assertions(
                [
                    row["id"]
                    for row in self.card.source_assertion_store.find_by_field(path)
                ]
            )
            field["selection_rules"] = self.card.selection_rules
        alternatives = [
            row
            for row in self.card.quality.get("alternatives") or []
            if row.get("field") == path
        ]
        field["selection_alternatives"] = alternatives

        def flatten(values):
            for value in values:
                if isinstance(value, str):
                    yield value
                else:
                    yield from flatten(value)

        field["alternative_source_assertions"] = self.assertions(
            list(flatten([r.get("source_assertion_ids") or [] for r in alternatives]))
        )
        for row in field.get("source_assertions") or []:
            if row["found"] and row.get("field_path") != path:
                self.gaps.append(
                    {
                        "reason": "source_assertion_field_mismatch",
                        "field_path": path,
                        "source_assertion_ref": row["source_assertion_ref"],
                    }
                )
        field["version_basis"] = "stored_source_assertion_labels"
        return field

    def missing(self, path):
        field = self.fields[path]
        if not field["stored"] or not field["node"].get("value"):
            self.gaps.append(
                {"reason": "input_not_stated", "card_ref": self.pin, "field_path": path}
            )

    def input(self, path, index):
        field = self.fields[path]
        value = field["node"]["value"][index]
        exact = [
            row
            for row in field["source_assertions"]
            if row["found"]
            and row.get("field_path") == path
            and row.get("asserted_value") == value
        ]
        aggregate = [
            row
            for row in field["source_assertions"]
            if row["found"]
            and row.get("field_path") == path
            and row.get("asserted_value") == field["node"]["value"]
        ]
        rows = exact or aggregate
        if not rows:
            self.gaps.append(
                {
                    "reason": "no_matching_input_assertion",
                    "card_ref": self.pin,
                    "field_path": path,
                    "index": index,
                }
            )
        return {
            "locator": {"card_ref": self.pin, "field_path": path, "index": index},
            "value": value,
            "source_assertions": rows,
            "support_basis": "exact_asserted_value"
            if exact
            else "selected_field_list"
            if aggregate
            else "not_recorded",
            "mapping_lineage": "not_reconstructed",
        }

    def context(self):
        return {
            "relationships": list(self.links.values()),
            "reports": [
                {
                    "locator": {
                        "card_ref": self.pin,
                        "field_path": "quality.enrichments",
                        "index": i,
                    },
                    "record": row,
                }
                for i, row in enumerate(self.card.quality.get("enrichments") or [])
                if row.get("source") in {"UniProt", "UniRef", "gnomAD", "GTEx"}
            ],
            "report_membership": "source_context_not_per_assertion_membership",
            "absence_basis": "stored_inputs_only_never_external_absence",
            "coverage_basis": "stored_inputs_no_source_completeness_claim",
            "execution_observation": {
                "status": "not_observed",
                "reason": "no_dedicated_comparative_operation_sidecars",
            },
            "runtime_attribution": "not_reconstructed_from_scientific_payload",
            "version_basis": {
                "gnomAD": "stored_dataset_or_client_declared_pext_label",
                "GTEx": "stored_requested_dataset_label",
                "native_release_identity": "not_independently_verified_by_explanation",
            },
        }


def _envelope(support, view, rule, **extra):
    stored = any(field["stored"] for field in support.fields.values())
    return deepcopy(
        {
            "rule": make_derivation(
                rule, inputs=[support.pin], parameters=view["rule"]["parameters"]
            ),
            "card_ref": support.pin,
            "status": "not_on_card"
            if not stored
            else "partial"
            if support.gaps
            else "on_card",
            "view": view,
            "fields": list(support.fields.values()),
            "context": support.context(),
            "gaps": support.gaps,
            **extra,
        }
    )


def _terms(support, view):
    from .terms import tissue_key

    regions = (support.card.get(REGIONS) or {}).get("value") or []
    stated = (support.card.get(TERMS) or {}).get("value") or []
    by_key = {}
    for i, row in enumerate(stated):
        by_key.setdefault(tissue_key(row.get("gtex_id") or ""), []).append(i)
    names = sorted(
        {
            t.get("tissue")
            for r in regions
            for t in r.get("tissues") or []
            if t.get("tissue")
        }
    )
    joins = []
    for name in names:
        candidates = by_key.get(name, [])
        indices = [
            i
            for i, r in enumerate(regions)
            if any(t.get("tissue") == name for t in r.get("tissues") or [])
        ]
        join = {
            "tissue": name,
            "pext_locators": [
                {"card_ref": support.pin, "field_path": REGIONS, "index": i}
                for i in indices
            ],
            "term_input": support.input(TERMS, candidates[-1]) if candidates else None,
            "other_matching_terms": [support.input(TERMS, i) for i in candidates[:-1]],
            "selection_basis": "last_stored_term_with_matching_gtex_key",
        }
        if not candidates:
            support.gaps.append(
                {
                    "reason": "tissue_term_not_stated",
                    "tissue": name,
                    "card_ref": support.pin,
                }
            )
        if len(candidates) > 1:
            support.gaps.append(
                {
                    "reason": "multiple_matching_tissue_terms",
                    "tissue": name,
                    "card_ref": support.pin,
                }
            )
        joins.append(join)
    return {
        "view": view.get("tissue_terms"),
        "joins": joins,
        "identity_basis": "gtex_tissue_key@1_never_shared_ontology_term",
    }


def _scoped_explanation(card, threshold, *, kind):
    from .scoped_tissue_usage import isoform_view, variant_view

    paths = (
        [VARIANTS, REGIONS, TERMS]
        if kind == "variant"
        else [ISOFORMS, EXONS, REGIONS, TRANSCRIPTS, TISSUE_TEXT, TERMS]
    )
    support = _ComparativeSupport(card, paths)
    for path in paths:
        if path not in (TERMS, TISSUE_TEXT):
            support.missing(path)
    trace = {}
    view = (variant_view if kind == "variant" else isoform_view)(
        card, threshold, _support=trace
    )

    def segments(rows):
        result = []
        for row in rows:
            result.append(
                {
                    **row,
                    "region_inputs": [
                        support.input(REGIONS, i) for i in row["region_indices"]
                    ],
                }
            )
            for tissue, decision in row["tissues"].items():
                if decision["status"] != "resolved":
                    support.gaps.append(
                        {
                            "reason": f"pext_tissue_value_{decision['status']}",
                            "tissue": tissue,
                            "intersection": row["intersection"],
                            "card_ref": support.pin,
                        }
                    )
        return result

    def excluded(rows, path, index_key):
        return [{**row, "input": support.input(path, row[index_key])} for row in rows]

    def texts(rows):
        return [
            {
                "item": row,
                "source_assertions": support.assertions([row["source_assertion_id"]]),
            }
            for row in rows
        ]

    items = []
    for item, inputs in zip(view["items"], trace.get("items", []), strict=True):
        row = {"item": item, "pext_segments": segments(inputs["segments"])}
        if kind == "variant":
            row.update(
                variant_input=support.input(VARIANTS, inputs["variant_index"]),
                coordinate_scope=inputs["coordinate_scope"],
                excluded_regions=excluded(
                    inputs["excluded_regions"], REGIONS, "region_index"
                ),
            )
        else:
            row.update(
                isoform_input=support.input(ISOFORMS, inputs["isoform_index"]),
                transcript_inputs=[
                    support.input(TRANSCRIPTS, i)
                    for i, r in enumerate(
                        (card.get(TRANSCRIPTS) or {}).get("value") or []
                    )
                    if r.get("isoform") == item["isoform"]
                ],
                coding_exon_inputs=[
                    support.input(EXONS, i)
                    for i, r in enumerate((card.get(EXONS) or {}).get("value") or [])
                    if r.get("isoform") == item["isoform"]
                ],
                own_regions=inputs["own_regions"],
                tissue_specificity=texts(item["uniprot_tissue_specificity"]),
            )
        basis = item["pext"].get("basis")
        if basis != "resolved_tissue_values":
            support.gaps.append(
                {"reason": basis, "item_index": len(items), "card_ref": support.pin}
            )
        if item["pext"].get("bases_without_pext"):
            support.gaps.append(
                {
                    "reason": "incomplete_pext_region_coverage",
                    "item_index": len(items),
                    "bases": item["pext"]["bases_without_pext"],
                    "card_ref": support.pin,
                }
            )
        items.append(row)
    extra = {}
    if kind == "isoform":
        extra = {
            "coordinate_scope": view["coordinate_scope"],
            "excluded_coding_exons": excluded(
                trace["excluded_exons"], EXONS, "exon_index"
            ),
            "excluded_pext_regions": excluded(
                trace["excluded_regions"], REGIONS, "region_index"
            ),
            "subtraction_inputs": trace["cds_of"],
            "variable_regions": [
                {"item": row, "pext_segments": segments(inputs)}
                for row, inputs in zip(
                    view["variable_regions"], trace["variable_regions"], strict=True
                )
            ],
            "entry_tissue_specificity": texts(view["entry_tissue_specificity"]),
            "tissue_specificity_decisions": [
                {
                    **row,
                    "source_assertions": support.assertions(
                        [row["source_assertion_id"]]
                    ),
                }
                for row in trace["text_decisions"]
            ],
        }
        if not view["variable_regions_complete"]:
            support.gaps.append(
                {"reason": "incomplete_isoform_exon_support", "card_ref": support.pin}
            )
    return _envelope(
        support,
        view,
        f"{kind}_tissue_usage_explanation@2",
        items=items,
        tissue_terms=_terms(support, view),
        interpretation={
            "threshold": "dimensionless_rule_parameter_not_pathogenicity",
            "missing_value": "unknown_never_zero_expression",
            "mean": "resolved_bases_only_read_with_per_tissue_coverage",
            "overlap": "unanimous_stated_values_count_once_otherwise_missing_or_conflicting",
            "coordinate_support": "stored_input_scope_not_native_release_verification_or_alignment",
        },
        **extra,
    )
