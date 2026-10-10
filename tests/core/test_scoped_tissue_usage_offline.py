"""Genomic scopes, overlap conflicts and per-tissue missingness are scientific contracts."""

from copy import deepcopy

import ackredit
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.core.tissue_usage import EXONS, ISOFORMS, REGIONS, TRANSCRIPTS, VARIANTS
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient


def card():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"}
    )


def put(c, path, rows, metadata=None):
    ids = []
    for i, row in enumerate(rows):
        sa = make_source_assertion(path, row, "synthetic", str(i), "original time")
        if metadata:
            sa["source_metadata"] = deepcopy(metadata)
        c.source_assertion_store.add(sa)
        ids.append(sa["id"])
    c.set(path, rows, ids)
    return ids


def region(start=10, end=19, *, tissues=None, **extra):
    return {
        "assembly": "GRCh38",
        "chromosome": "12",
        "start": start,
        "end": end,
        "tissues": tissues
        if tissues is not None
        else [{"tissue": "liver", "value": 0.5}],
        **extra,
    }


def isoform_card(*, two=False):
    c = card()
    put(
        c,
        ISOFORMS,
        [{"isoform_id": "X-1", "name": "1"}]
        + ([{"isoform_id": "X-2", "name": "2"}] if two else []),
    )
    put(
        c,
        TRANSCRIPTS,
        [{"isoform": "X-1", "transcript": "T1.2"}]
        + ([{"isoform": "X-2", "transcript": "T2.1"}] if two else []),
    )
    put(
        c,
        EXONS,
        [
            {
                "isoform": "X-1",
                "transcript": "T1",
                "transcript_version": "2",
                "assembly": "GRCh38",
                "chromosome": "12",
                "cds": [[10, 29]],
            }
        ],
    )
    put(c, REGIONS, [region(10, 29)])
    return c


def first(c):
    return c.isoform_tissue_usage()["items"][0]["pext"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("assembly", "GRCh37"),
        ("chromosome", "1"),
        ("assembly", None),
        ("chromosome", None),
    ],
)
def test_foreign_and_unknown_region_scopes_never_join_equal_integer_positions(
    field, value
):
    c = isoform_card()
    put(c, REGIONS, [region(10, 29, **{field: value})])
    result = c.isoform_tissue_usage()
    assert first(c)["basis"] == (
        "genomic_scope_missing" if value is None else "incompatible_genomic_scope"
    )
    assert first(c)["by_tissue"] == {}
    assert result["excluded_pext_regions"][0]["reason"] == first(c)["basis"]
    # Historical rule remains reproducible, including its known wrong-scope join.
    legacy = c.isoform_tissue_usage(usage_rule="isoform_exon_usage@2")
    assert legacy["items"][0]["pext"]["by_tissue"] == {"liver": 0.5}
    explanation = c.explain_isoform_tissue_usage()
    assert explanation["view"] == result
    assert explanation["excluded_pext_regions"][0]["input"]["value"][field] == value


@pytest.mark.parametrize("field,value", [("chromosome", "1"), ("assembly", "GRCh37")])
def test_incompatible_coding_exons_cannot_subtract_or_create_variable_regions(
    field, value
):
    c = isoform_card(two=True)
    exons = c.get(EXONS)["value"]
    put(
        c,
        EXONS,
        [
            *exons,
            {
                **exons[0],
                "isoform": "X-2",
                "transcript": "T2",
                "transcript_version": "1",
                field: value,
            },
        ],
    )
    result = c.isoform_tissue_usage()
    assert result["coordinate_scope"]["status"] == "incompatible"
    assert all(
        i["pext"]["basis"] == "incompatible_genomic_scope" for i in result["items"]
    )
    assert (
        result["variable_regions"] == []
        and result["variable_regions_complete"] is False
    )


@pytest.mark.parametrize("defect", ["scope", "link", "version", "interval"])
def test_unsupported_cds_inputs_have_explicit_rejections_and_incomplete_own_bases(
    defect,
):
    c = isoform_card(two=True)
    row = {
        **c.get(EXONS)["value"][0],
        "isoform": "X-2",
        "transcript": "T2",
        "transcript_version": "1",
        "cds": [[20, 29]],
    }
    if defect == "scope":
        row.pop("assembly")
    elif defect == "link":
        row["transcript"] = "UNSTATED"
    elif defect == "version":
        row["transcript_version"] = "99"
    else:
        row["cds"] = [[30, 20]]
    put(c, EXONS, [c.get(EXONS)["value"][0], row])
    result = c.isoform_tissue_usage()
    assert result["items"][0]["own_coding_bases"] == 20
    assert result["items"][0]["own_bases_complete"] is False
    assert result["items"][1]["pext"]["basis"] == "unsupported_coding_exons"
    assert result["isoforms_without_exons"] == ["X-2"]
    assert len(result["excluded_coding_exons"]) == 1


def test_agreeing_duplicate_regions_count_each_base_once_and_preserve_both_inputs():
    c = isoform_card()
    put(c, REGIONS, [region(10, 29), region(10, 29)])
    result = first(c)
    assert result["bases_with_pext"] == 20 and result["overlapping_bases"] == 20
    assert result["by_tissue"] == {"liver": 0.5}
    assert result["coverage_by_tissue"]["liver"]["bases_with_value"] == 20
    explained = c.explain_isoform_tissue_usage()["items"][0]["pext_segments"][0]
    assert [r["locator"]["index"] for r in explained["region_inputs"]] == [0, 1]


def test_conflicting_overlap_excludes_only_disputed_bases_without_average_or_last_wins():
    c = isoform_card()
    put(
        c,
        REGIONS,
        [region(10, 24), region(20, 29, tissues=[{"tissue": "liver", "value": 0.9}])],
    )
    result = first(c)
    assert result["bases_with_pext"] == 20
    assert result["overlapping_bases"] == 5
    assert result["coverage_by_tissue"]["liver"] == {
        "bases_with_value": 15,
        "bases_missing_value": 0,
        "bases_conflicting_value": 5,
        "complete": False,
    }
    assert result["by_tissue"]["liver"] == pytest.approx((10 * 0.5 + 5 * 0.9) / 15)
    answer = c.explain_isoform_tissue_usage()
    assert any(g["reason"] == "pext_tissue_value_conflicting" for g in answer["gaps"])
    assert answer["items"][0]["pext_segments"][1]["intersection"] == [20, 24]


def test_missing_and_null_tissue_values_never_enter_another_tissues_denominator():
    c = isoform_card()
    put(
        c,
        REGIONS,
        [
            region(
                10,
                19,
                tissues=[
                    {"tissue": "liver", "value": 0.8},
                    {"tissue": "brain", "value": None},
                ],
            ),
            region(20, 29, tissues=[{"tissue": "brain", "value": 0.4}]),
        ],
    )
    result = first(c)
    assert result["by_tissue"] == {"brain": 0.4, "liver": 0.8}
    assert all(
        v["bases_with_value"] == 10 and v["bases_missing_value"] == 10
        for v in result["coverage_by_tissue"].values()
    )
    # The historical denominator made liver 0.4 and brain 0.2.
    assert c.isoform_tissue_usage(usage_rule="isoform_exon_usage@2")["items"][0][
        "pext"
    ]["by_tissue"] == {"brain": 0.2, "liver": 0.4}


@pytest.mark.parametrize(
    "values,expected",
    [
        ([None], "missing"),
        ([0.2, 0.7], "conflicting"),
        ([0.2, None], "missing"),
        ([True], "missing"),
        ([1.1], "missing"),
        ([float("nan")], "missing"),
    ],
)
def test_unresolved_tissues_are_unknown_and_cannot_crash_maximum_or_be_called_zero(
    values, expected
):
    c = isoform_card()
    put(
        c,
        REGIONS,
        [region(10, 29, tissues=[{"tissue": "liver", "value": v} for v in values])],
    )
    result = first(c)
    assert result["by_tissue"] == {"liver": None}
    assert result["max"] is None and result["at_or_above_threshold"] == []
    assert result["basis"] == "no_resolved_tissue_values"
    assert result["coverage_by_tissue"]["liver"][f"bases_{expected}_value"] == 20


def test_zero_is_a_stated_value_and_missing_overlap_is_conservatively_unresolved():
    c = isoform_card()
    put(c, REGIONS, [region(10, 29, tissues=[{"tissue": "liver", "value": 0}])])
    assert first(c)["by_tissue"] == {"liver": 0}
    put(c, REGIONS, [*c.get(REGIONS)["value"], region(10, 19, tissues=[])])
    assert first(c)["coverage_by_tissue"]["liver"]["bases_missing_value"] == 10
    assert first(c)["coverage_by_tissue"]["liver"]["bases_with_value"] == 10


def test_uncovered_bases_have_union_coverage_and_do_not_change_conditional_mean():
    c = isoform_card()
    put(c, REGIONS, [region(10, 14)])
    result = first(c)
    assert result["bases_without_pext"] == 15
    assert result["by_tissue"] == {"liver": 0.5}
    assert result["coverage_by_tissue"]["liver"]["bases_missing_value"] == 15


@pytest.mark.parametrize("scope", [None, "GRCh37", "GRCh38"])
def test_variant_assembly_is_explicit_and_historical_dataset_label_is_not_scope(scope):
    c = card()
    variant = {"variant_id": "12-15-A-G", "location": {"start": 900, "end": 900}}
    if scope:
        variant["assembly"] = scope
    ids = put(c, VARIANTS, [variant])
    c.source_assertion_store.get(ids[0])["source"]["version"] = "gnomad_r4"
    put(c, REGIONS, [region()])
    result = c.variant_tissue_usage()["items"][0]
    assert result["pext"]["basis"] == (
        "genomic_scope_missing"
        if scope is None
        else "incompatible_genomic_scope"
        if scope == "GRCh37"
        else "resolved_tissue_values"
    )
    if scope == "GRCh38":
        assert result["coordinate_scope"]["position"] == 15
        assert result["pext"]["by_tissue"] == {"liver": 0.5}


def test_variant_selected_coordinate_metadata_is_traced_and_disagreement_is_explicit():
    c = card()
    put(
        c,
        VARIANTS,
        [{"variant_id": "12-15-A-G"}],
        {"coordinate_scope": {"assembly": "GRCh38", "basis": "synthetic"}},
    )
    put(c, REGIONS, [region(), region(mean=99)])
    result = c.explain_variant_tissue_usage()
    assert result["view"]["items"][0]["pext"]["overlapping_bases"] == 1
    assert "mean" not in result["view"]["items"][0]["pext"]
    assert len(result["items"][0]["pext_segments"][0]["region_inputs"]) == 2
    assert (
        result["items"][0]["variant_input"]["source_assertions"][0]["source_metadata"][
            "coordinate_scope"
        ]["assembly"]
        == "GRCh38"
    )
    put(
        c,
        VARIANTS,
        [{"variant_id": "12-15-A-G", "assembly": "GRCh37"}],
        {"coordinate_scope": {"assembly": "GRCh38"}},
    )
    assert (
        c.variant_tissue_usage()["items"][0]["pext"]["basis"]
        == "incompatible_genomic_scope"
    )


def test_variant_overlap_conflict_is_not_first_region_and_all_unknown_is_safe():
    c = card()
    put(
        c,
        VARIANTS,
        [{"variant_id": "12-15-A-G", "assembly": "GRCh38"}, {"hgvs_p": "p.Ala3Thr"}],
    )
    put(c, REGIONS, [region(), region(tissues=[{"tissue": "liver", "value": 0.9}])])
    result = c.variant_tissue_usage()
    assert result["items"][0]["pext"]["by_tissue"] == {"liver": None}
    assert result["items"][1]["pext"]["basis"] == "no_position"
    assert c.variant_tissue_usage(usage_rule="pext_at_variant@1")["items"][0]["pext"][
        "by_tissue"
    ] == {"liver": 0.5}


@pytest.mark.parametrize(
    "method",
    [
        "variant_tissue_usage",
        "isoform_tissue_usage",
        "explain_variant_tissue_usage",
        "explain_isoform_tissue_usage",
    ],
)
def test_rule_and_threshold_guards_apply_even_with_digestion_bypassed(method):
    c = isoform_card()
    for invalid in (True, float("nan"), 10**400):
        for skip in (False, True):
            with pytest.raises(ArgumentError):
                getattr(c, method)(invalid, skip_digestion=skip)
    wrong = "isoform_exon_usage@3" if "variant" in method else "pext_at_variant@2"
    for invalid in (wrong, "unknown@1", None):
        for skip in (False, True):
            with pytest.raises(ArgumentError):
                getattr(c, method)(usage_rule=invalid, skip_digestion=skip)


def test_public_native_fixtures_use_original_query_context_and_agree_where_coverage_is_complete(
    monkeypatch,
):
    c = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        gnomad={},
        exon_usage=True,
        gnomad_client=FixtureGnomADClient("temp_data"),
    )[0]
    before = deepcopy(c.to_dict())

    def forbidden(*a, **k):
        pytest.fail("view cannot acquire or generate credit")

    monkeypatch.setattr(ackredit, "register_item", forbidden)
    monkeypatch.setattr(ackredit, "track_item", forbidden)
    modern, old = (
        c.variant_tissue_usage(),
        c.variant_tissue_usage(usage_rule="pext_at_variant@1"),
    )
    assert len(modern["items"]) == len(old["items"]) == 15
    for current, historical in zip(modern["items"], old["items"], strict=True):
        assert current["pext"].get("by_tissue") == historical["pext"].get("by_tissue")
        assert current["coordinate_scope"]["status"] == "confirmed"
    modern_iso, old_iso = (
        c.isoform_tissue_usage(),
        c.isoform_tissue_usage(usage_rule="isoform_exon_usage@2"),
    )
    assert modern_iso["coordinate_scope"] == {
        "status": "confirmed",
        "assembly": "GRCh38",
        "chromosome": "12",
    }
    for current, historical in zip(modern_iso["items"], old_iso["items"], strict=True):
        assert current["pext"].get("by_tissue") == historical["pext"].get("by_tissue")
    assert c.explain_variant_tissue_usage()["view"] == modern
    assert c.explain_isoform_tissue_usage()["view"] == modern_iso
    assert c.to_dict() == before


def test_old_pins_do_not_gain_new_coordinate_context_after_reacquisition(tmp_path):
    c = card()
    put(c, VARIANTS, [{"variant_id": "12-15-A-G"}])
    put(c, REGIONS, [region()])
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    old_pin = store.save(c)
    put(
        c,
        VARIANTS,
        [{"variant_id": "12-15-A-G"}],
        {"coordinate_scope": {"assembly": "GRCh38"}},
    )
    new_pin = store.save(c)
    assert old_pin != new_pin
    assert (
        store.load(old_pin).variant_tissue_usage()["items"][0]["pext"]["basis"]
        == "genomic_scope_missing"
    )
    assert store.load(new_pin).variant_tissue_usage()["items"][0]["pext"][
        "by_tissue"
    ] == {"liver": 0.5}
    assert store.load(old_pin).variant_tissue_usage(usage_rule="pext_at_variant@1")[
        "items"
    ][0]["pext"]["by_tissue"] == {"liver": 0.5}


def test_variable_regions_use_the_same_conflict_and_per_tissue_coverage_policy():
    c = isoform_card(two=True)
    a = c.get(EXONS)["value"][0]
    put(
        c,
        EXONS,
        [
            {**a, "cds": [[10, 19]]},
            {
                **a,
                "isoform": "X-2",
                "transcript": "T2",
                "transcript_version": "1",
                "cds": [[20, 29]],
            },
        ],
    )
    put(
        c,
        REGIONS,
        [region(10, 29), region(15, 24, tissues=[{"tissue": "liver", "value": 0.9}])],
    )
    result = c.isoform_tissue_usage()
    assert result["variable_regions_complete"] is True
    assert len(result["variable_regions"]) == 2
    for run in result["variable_regions"]:
        assert run["pext"]["coverage_by_tissue"]["liver"]["bases_with_value"] == 5
        assert (
            run["pext"]["coverage_by_tissue"]["liver"]["bases_conflicting_value"] == 5
        )
    explanation = c.explain_isoform_tissue_usage()
    assert [r["item"] for r in explanation["variable_regions"]] == result[
        "variable_regions"
    ]
    assert explanation["variable_regions"][0]["pext_segments"][1]["region_indices"] == [
        0,
        1,
    ]


def test_region_order_changes_locators_but_cannot_change_scientific_values():
    c = isoform_card()
    rows = [
        region(10, 24),
        region(20, 29, tissues=[{"tissue": "liver", "value": 0.9}]),
        region(10, 29, chromosome="1"),
    ]
    put(c, REGIONS, rows)
    original = first(c)
    put(c, REGIONS, list(reversed(rows)))
    assert first(c) == original


def test_explicit_matching_nondefault_assembly_is_supported_without_liftover():
    c = isoform_card()
    put(c, EXONS, [{**c.get(EXONS)["value"][0], "assembly": "GRCh37"}])
    put(c, REGIONS, [region(10, 29, assembly="GRCh37")])
    put(c, VARIANTS, [{"variant_id": "12-15-A-G", "assembly": "GRCh37"}])
    assert first(c)["by_tissue"] == {"liver": 0.5}
    assert c.variant_tissue_usage()["items"][0]["pext"]["by_tissue"] == {"liver": 0.5}
    assert c.isoform_tissue_usage()["coordinate_scope"]["assembly"] == "GRCh37"


def test_wrong_or_unselected_assertion_metadata_cannot_supply_variant_scope():
    c = card()
    put(c, VARIANTS, [{"variant_id": "12-15-A-G"}])
    put(c, REGIONS, [region()])
    for field, value in [
        (VARIANTS, {"variant_id": "12-16-A-G"}),
        (REGIONS, {"variant_id": "12-15-A-G"}),
    ]:
        sa = make_source_assertion(field, value, "synthetic", field, "old")
        sa["source_metadata"] = {"coordinate_scope": {"assembly": "GRCh38"}}
        c.source_assertion_store.add(sa)
        if field == REGIONS:
            c.sections["annotations"]["population_variants"][
                "source_assertion_ids"
            ].append(sa["id"])
    assert (
        c.variant_tissue_usage()["items"][0]["pext"]["basis"] == "genomic_scope_missing"
    )


def test_empty_region_and_tissue_inputs_remain_unknown_with_safe_maximum():
    c = isoform_card()
    put(c, REGIONS, [region(10, 29, tissues=[])])
    assert first(c)["basis"] == "no_resolved_tissue_values"
    assert first(c)["max"] is None
    put(c, REGIONS, [])
    assert first(c)["basis"] == "outside_pext_regions"
    assert first(c)["bases_without_pext"] == 20


def test_one_known_transcript_does_not_make_an_isoforms_other_unanswered_transcript_complete():
    c = isoform_card()
    put(
        c,
        TRANSCRIPTS,
        [*c.get(TRANSCRIPTS)["value"], {"isoform": "X-1", "transcript": "OTHER.1"}],
    )
    result = c.isoform_tissue_usage()
    assert result["items"][0]["own_bases_complete"] is False
    assert result["variable_regions_complete"] is False
    assert result["transcripts_without_coding_exons"] == {"X-1": ["OTHER.1"]}
    assert result["items"][0]["pext"]["by_tissue"] == {"liver": 0.5}


def test_invalid_region_interval_and_zero_variant_position_are_explicit():
    c = isoform_card()
    put(c, REGIONS, [region(30, 10)])
    assert first(c)["basis"] == "invalid_genomic_interval"
    put(c, VARIANTS, [{"variant_id": "12-0-A-G", "assembly": "GRCh38"}])
    assert c.variant_tissue_usage()["items"][0]["pext"]["basis"] == "no_position"


def test_coordinate_context_migration_reports_gap_without_inventing_old_assembly_and_refresh_fills_it():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    client = FixtureGnomADClient("temp_data")
    c = sabueso.resolve(
        "P60174", resolver=resolver, gnomad={}, exon_usage=True, gnomad_client=client
    )[0]
    old = c.to_dict()
    old["meta"]["schema_version"] = "0.3.13"
    for sa in old["source_assertion_store"]:
        if sa["field_path"] == VARIANTS and sa["source"]["name"] == "gnomAD":
            sa.pop("source_metadata", None)
    before = deepcopy(old)
    migrated = sabueso.migrate_card(old)
    assert old == before
    step = migrated.quality["migration"][-1]["steps"][-1]
    assert step["gaps"] == [
        {
            "introduced_in": "0.3.14",
            "path": "source_assertion_store[].source_metadata.coordinate_scope",
            "kind": "missing",
            "filled_by": "gnomad",
        }
    ]
    assert (
        migrated.variant_tissue_usage()["items"][0]["pext"]["basis"]
        == "genomic_scope_missing"
    )
    refreshed, _ = sabueso.refresh_card(
        migrated, resolver=resolver, gnomad_client=client
    )
    assert (
        refreshed.variant_tissue_usage()["items"][0]["coordinate_scope"]["status"]
        == "confirmed"
    )
    record = refreshed.quality["migration"][-1]
    assert (
        "source_assertion_store[].source_metadata.coordinate_scope"
        in record["completed"]
    )
    assert (
        "source_assertion_store[].source_metadata.coordinate_scope"
        not in record["not_stated"]
    )


def test_refresh_restores_only_recorded_gnomad_requests_and_keeps_original_limit():
    from sabueso.core.migration import rebuild_options

    c = card()
    c.quality["enrichments"] = [
        {"source": "gnomAD", "identifier": "G1", "status": "error", "limit": 7},
        {"source": "gnomAD", "data": "pext", "status": "not_queried"},
        {"source": "gnomAD", "data": "unknown", "limit": 99},
    ]
    assert rebuild_options(c) == {"gnomad": {"limit": 7}, "exon_usage": True}
    c.quality["enrichments"] = []
    assert rebuild_options(c) == {}
