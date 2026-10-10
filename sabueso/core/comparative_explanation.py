"""Pinned support for existing comparative rules (#91).

Collectors in the tissue views retain the actual selected region and weighted
intersections. SourceAssertion matching never invents finer mapping lineage.
Scientific pins and stored source labels do not reconstruct execution or credit.
"""

from copy import deepcopy

from .bioactivity_explanation import _Support
from .relationship_store import make_derivation
from .sequences import SEQUENCE, sequence_differences_view
from .tissue_usage import (
    EXONS,
    ISOFORMS,
    REGIONS,
    TERMS,
    TISSUE_TEXT,
    TRANSCRIPTS,
    VARIANTS,
    _merge,
    isoform_tissue_usage_view,
    variant_tissue_usage_view,
)


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


def explain_sequence_differences(card, other):
    from sabueso._private.argdigest.argument.other import digest_other

    digest_other(other, caller="sabueso.core.card.explain_sequence_differences")
    supports = [_ComparativeSupport(c, [SEQUENCE]) for c in (card, other)]
    for support in supports:
        support.missing(SEQUENCE)
        field = support.fields[SEQUENCE]
        if field["stored"] and not any(
            row["found"]
            and row.get("field_path") == SEQUENCE
            and row.get("asserted_value") == field["node"]["value"]
            for row in field.get("source_assertions") or []
        ):
            support.gaps.append(
                {"reason": "no_matching_sequence_assertion", "card_ref": support.pin}
            )
    view = sequence_differences_view(card, other)
    gaps = [gap for support in supports for gap in support.gaps]
    if view.get("basis") == "different_lengths":
        gaps.append({"reason": "different_lengths", "lengths": view["lengths"]})
    pins = [support.pin for support in supports]
    return deepcopy(
        {
            "rule": make_derivation("sequence_differences_explanation@1", inputs=pins),
            "card_refs": pins,
            "status": "partial" if gaps else "on_card",
            "view": view,
            "fields": [s.fields[SEQUENCE] for s in supports],
            "coordinate_scope": {
                "indexing": "1-based",
                "basis": "equal_integer_positions_in_selected_sequences",
                "alignment": "not_performed",
                "residue_correspondence": "not_established",
                "identity": "not_inferred_from_sequence_or_cluster_membership",
            },
            "context": [s.context() for s in supports],
            "gaps": gaps,
        }
    )


def _terms(support, view):
    from sabueso.mappings.gtex import tissue_key

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


def explain_variant_tissue_usage(card, threshold, usage_rule="pext_at_variant@2"):
    from .scoped_tissue_usage import check_arguments

    check_arguments(threshold, usage_rule, kind="variant")
    if usage_rule != "pext_at_variant@1":
        return _scoped_explanation(card, threshold, kind="variant")
    from sabueso._private.argdigest.argument.threshold import digest_threshold

    threshold = digest_threshold(
        threshold, caller="sabueso.core.card.explain_variant_tissue_usage"
    )
    support = _ComparativeSupport(card, [VARIANTS, REGIONS, TERMS])
    for path in (VARIANTS, REGIONS):
        support.missing(path)
    trace = {}
    view = variant_tissue_usage_view(card, threshold, _support=trace)
    items = []
    for item, inputs in zip(view["items"], trace.get("items", []), strict=True):
        position = inputs["position"]
        region = (
            support.input(REGIONS, inputs["region_index"])
            if inputs["region_index"] is not None
            else None
        )
        items.append(
            {
                "item": item,
                "variant_input": support.input(VARIANTS, inputs["variant_index"]),
                "region_input": region,
                "coordinate_scope": {
                    "position": {"chromosome": position[0], "position": position[1]}
                    if position
                    else None,
                    "basis": "first_genomic_base_of_variant_id_not_protein_location",
                    "indexing": "1-based_closed",
                    "assembly": "GRCh38",
                    "assembly_basis": "rule_parameter_and_mapping_scope_not_variant_record_field",
                    "selection_basis": "first_stored_region_on_same_chromosome_containing_position",
                },
            }
        )
        if item["pext"].get("basis"):
            support.gaps.append(
                {
                    "reason": item["pext"]["basis"],
                    "variant_index": inputs["variant_index"],
                    "card_ref": support.pin,
                }
            )
        if region and region["value"].get("assembly") != "GRCh38":
            support.gaps.append(
                {
                    "reason": "region_assembly_not_confirmed",
                    "locator": region["locator"],
                }
            )
    terms = _terms(support, view)
    return _envelope(
        support,
        view,
        "variant_tissue_usage_explanation@1",
        items=items,
        tissue_terms=terms,
        interpretation={
            "threshold": "dimensionless_rule_parameter_not_pathogenicity",
            "outside_region": "not_zero_expression_or_harmlessness",
        },
    )


def explain_isoform_tissue_usage(card, threshold, usage_rule="isoform_exon_usage@3"):
    from .scoped_tissue_usage import check_arguments

    check_arguments(threshold, usage_rule, kind="isoform")
    if usage_rule != "isoform_exon_usage@2":
        return _scoped_explanation(card, threshold, kind="isoform")
    from sabueso._private.argdigest.argument.threshold import digest_threshold

    threshold = digest_threshold(
        threshold, caller="sabueso.core.card.explain_isoform_tissue_usage"
    )
    support = _ComparativeSupport(
        card, [ISOFORMS, EXONS, REGIONS, TRANSCRIPTS, TISSUE_TEXT, TERMS]
    )
    for path in (ISOFORMS, EXONS, REGIONS, TRANSCRIPTS):
        support.missing(path)
    trace = {}
    view = isoform_tissue_usage_view(card, threshold, _support=trace)
    exons = (card.get(EXONS) or {}).get("value") or []
    transcripts = (card.get(TRANSCRIPTS) or {}).get("value") or []
    regions = (card.get(REGIONS) or {}).get("value") or []
    scopes = {
        (row.get("assembly"), str(row.get("chromosome"))) for row in exons + regions
    }
    if len(scopes) > 1 or any(
        assembly != "GRCh38" or chromosome in {"None", ""}
        for assembly, chromosome in scopes
    ):
        support.gaps.append(
            {
                "reason": "genomic_scope_not_confirmed",
                "card_ref": support.pin,
                "basis": "isoform_rule_does_not_check_chromosome_or_assembly",
            }
        )

    def overlaps(rows):
        return [
            {**row, "region_input": support.input(REGIONS, row["region_index"])}
            for row in rows
        ]

    def texts(rows):
        return [
            {
                "item": row,
                "source_assertions": support.assertions([row["source_assertion_id"]]),
            }
            for row in rows
        ]

    items = []
    for item, inputs in zip(view["items"], trace["items"], strict=True):
        own = inputs["own_regions"]
        covered = sum(
            end - start + 1
            for start, end in _merge(
                [row["intersection"] for row in inputs["pext_inputs"]]
            )
        )
        counted = sum(row["bases"] for row in inputs["pext_inputs"])
        if counted != covered:
            support.gaps.append(
                {
                    "reason": "overlapping_pext_regions_counted_multiple_times",
                    "isoform": item["isoform"],
                    "card_ref": support.pin,
                }
            )
        items.append(
            {
                "item": item,
                "isoform_input": support.input(ISOFORMS, inputs["isoform_index"]),
                "transcript_inputs": [
                    support.input(TRANSCRIPTS, i)
                    for i, row in enumerate(transcripts)
                    if row.get("isoform") == item["isoform"]
                ],
                "coding_exon_inputs": [
                    support.input(EXONS, i)
                    for i, row in enumerate(exons)
                    if row.get("isoform") == item["isoform"]
                ],
                "own_regions": own,
                "pext_inputs": overlaps(inputs["pext_inputs"]),
                "bases_without_pext": sum(e - s + 1 for s, e in own) - covered,
                "coverage_basis": "union_of_original_recorded_intersections",
                "tissue_specificity": texts(item["uniprot_tissue_specificity"]),
            }
        )
        if item["pext"].get("basis"):
            support.gaps.append(
                {
                    "reason": item["pext"]["basis"],
                    "isoform": item["isoform"],
                    "card_ref": support.pin,
                }
            )
    if view["isoforms_without_exons"]:
        support.gaps.append(
            {
                "reason": "incomplete_isoform_exon_support",
                "isoforms": view["isoforms_without_exons"],
                "card_ref": support.pin,
            }
        )
    for i, row in enumerate(exons):
        if row.get("assembly") != "GRCh38":
            support.gaps.append(
                {
                    "reason": "exon_assembly_not_confirmed",
                    "locator": {
                        "card_ref": support.pin,
                        "field_path": EXONS,
                        "index": i,
                    },
                }
            )
    terms = _terms(support, view)
    for inputs in trace["variable_regions"]:
        counted = sum(row["bases"] for row in inputs)
        covered = sum(
            end - start + 1
            for start, end in _merge([row["intersection"] for row in inputs])
        )
        if counted != covered:
            support.gaps.append(
                {
                    "reason": "overlapping_pext_regions_in_variable_summary",
                    "card_ref": support.pin,
                }
            )
    return _envelope(
        support,
        view,
        "isoform_tissue_usage_explanation@1",
        items=items,
        tissue_terms=terms,
        variable_regions=[
            {"item": row, "pext_inputs": overlaps(inputs)}
            for row, inputs in zip(
                view["variable_regions"], trace["variable_regions"], strict=True
            )
        ],
        entry_tissue_specificity=texts(view["entry_tissue_specificity"]),
        tissue_specificity_decisions=[
            {
                **row,
                "source_assertions": support.assertions([row["source_assertion_id"]]),
            }
            for row in trace["text_decisions"]
        ],
        coordinate_scope={
            "assembly": "GRCh38",
            "indexing": "1-based_closed_genomic_intervals",
            "basis": "stored_transcripts_and_cds_never_sequence_alignment",
            "chromosome_matching": "not_checked_by_isoform_exon_usage@2",
            "subtraction_inputs": trace["cds_of"],
            "subtraction_scope": "all_stored_coding_exons_including_other_isoforms",
            "denominator": "all_overlapping_pext_bases_including_missing_tissue_values",
            "region_overlap": "each_stored_region_intersection_counted_by_original_rule",
        },
        interpretation={
            "threshold": "dimensionless_rule_parameter_not_pathogenicity",
            "own_bases": "may_be_shared_with_isoforms_without_known_exons",
            "outside_region": "not_zero_expression_or_harmlessness",
        },
    )


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
