"""Initial native LIGYSIS residue rows retain scores, numbering and bounded scope."""

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest
import pyunitwizard as puw

from sabueso.core.errors import ConnectorError
from sabueso.mappings.ligysis import map_displayed_residues, parse_displayed_residues
from sabueso.tools.db.ligysis import FixtureLigysisClient, get_result_page

PATH = Path("temp_data/ligysis/result__P60174__1.html")
RAW = PATH.read_bytes()
NATIVE = RAW.decode("utf-8")


def envelope():
    return get_result_page("P60174", 1, client=FixtureLigysisClient())


def literal(name, value, text=NATIVE):
    return re.sub(
        rf"(?m)^\s*(?:const|let)\s+{name}\s*=.*$",
        lambda _: f"const {name} = {json.dumps(value)};",
        text,
    )


def table():
    return json.loads(re.search(r"let newChartData = ([^\r\n]+)", NATIVE)[1])


def read_table(value):
    result = envelope()
    result["record"] = literal("newChartData", value)
    return result


def test_full_initial_native_rows_retain_provider_support_and_no_canonical_location():
    source = envelope()
    before = copy.deepcopy(source)
    with puw.context(standard_units=["nanometer", "ps", "K", "mole", "dalton"]):
        rows = map_displayed_residues(source)
    assert len(rows) == 20 and source == before
    assert [a["asserted_value"]["native_fields"]["UPResNum"] for a in rows] == [
        12,
        14,
        76,
        96,
        97,
        98,
        166,
        170,
        171,
        172,
        173,
        210,
        211,
        212,
        213,
        231,
        232,
        233,
        234,
        235,
    ]
    assert rows[0]["asserted_value"]["native_fields"] == {
        "UPResNum": 12,
        "MSACol": 17,
        "DS": 0.85,
        "MES": 0.0,
        "p": 1.0,
        "AA": "N",
        "RSA": 1.11,
        "SS": "E",
    }
    assert rows[0]["asserted_value"]["relative_solvent_accessibility"] == {
        "value": 1.11,
        "unit": "percent",
    }
    assert rows[2]["asserted_value"]["relative_solvent_accessibility"] == {
        "value": 0.0,
        "unit": "percent",
    }
    for i, assertion in enumerate(rows):
        meta = assertion["source_metadata"]
        assert assertion["subject_ref"] == "ligysis:displayed_residue_table:P60174:1"
        assert assertion["field_path"] == "annotations.ligysis_residue_records"
        assert assertion["source"]["version"] is None
        assert "location" not in assertion and "evidence_class" not in assertion
        assert meta["native_row_index"] == i and meta["received_row_count"] == 20
        assert meta["native_column_order"] == [
            "UPResNum",
            "MSACol",
            "DS",
            "MES",
            "p",
            "AA",
            "RSA",
            "SS",
        ]
        assert meta["displayed_site_id"] is None
        assert meta["response_sha256"] == hashlib.sha256(RAW).hexdigest()
        assert meta["snapshot_receipt"] == source["snapshot_receipt"]
    rows[0]["source_metadata"]["snapshot_receipt"]["path"] = "changed"
    assert source == before


def test_repeated_positions_unknown_columns_and_conflicts_are_independent_occurrences():
    value = {k: [v[0], v[0]] for k, v in table().items()}
    value["AA"][1] = "X"
    value["SS"][1] = ""
    value["MSACol"][1] = 0  # The provider's alignment index base is not inferred.
    value["native_extra"] = [None, {"unqualified": "kept"}]
    source = read_table(value)
    source["record"] = literal("cc", [*value], source["record"])
    rows = map_displayed_residues(source)
    assert len(rows) == 2 and rows[0]["id"] != rows[1]["id"]
    assert (
        rows[0]["asserted_value"]["native_fields"]["UPResNum"]
        == rows[1]["asserted_value"]["native_fields"]["UPResNum"]
    )
    assert rows[1]["asserted_value"]["native_fields"]["AA"] == "X"
    assert rows[1]["asserted_value"]["native_fields"]["native_extra"] == {
        "unqualified": "kept"
    }
    assert rows[1]["source_metadata"]["displayed_site_id"] is None


def test_native_nan_zero_and_empty_display_do_not_claim_complete_segment_absence():
    value = {k: [v[0], v[1]] for k, v in table().items()}
    for key in ("DS", "MES", "p", "RSA"):
        value[key] = ["NaN", 0]
    rows = map_displayed_residues(read_table(value))
    assert rows[0]["asserted_value"]["relative_solvent_accessibility"] is None
    assert rows[1]["asserted_value"]["relative_solvent_accessibility"] == {
        "value": 0,
        "unit": "percent",
    }
    assert rows[0]["asserted_value"]["native_fields"]["p"] == "NaN"
    assert map_displayed_residues(read_table({k: [] for k in table()})) == []


@pytest.mark.parametrize(
    "key,value",
    [
        ("UPResNum", 1),
        ("UPResNum", True),
        ("UPResNum", "12"),
        ("MSACol", -1),
        ("MSACol", False),
        ("MSACol", 1.5),
        ("AA", None),
        ("AA", "GLY"),
        ("SS", []),
        ("DS", -1),
        ("MES", False),
        ("MES", None),
        ("p", 1.01),
        ("p", "0.01"),
        ("RSA", 100.1),
        ("RSA", -0.1),
    ],
)
def test_malformed_late_row_fails_before_any_annotation_is_returned(key, value):
    data = table()
    data[key][-1] = value
    with pytest.raises(ConnectorError):
        map_displayed_residues(read_table(data))


@pytest.mark.parametrize(
    "change",
    ["missing", "nonlist", "short", "undeclared", "duplicate_header", "missing_header"],
)
def test_changed_native_columns_and_counts_fail_closed(change):
    value = table()
    headers = list(value)
    if change == "missing":
        del value["p"]
    elif change == "nonlist":
        value["p"] = "not an array"
    elif change == "short":
        value["p"].pop()
    elif change == "undeclared":
        value["extra"] = [0] * 20
    elif change == "duplicate_header":
        headers.append("p")
    else:
        headers.remove("p")
    source = read_table(value)
    source["record"] = literal("cc", headers, source["record"])
    with pytest.raises(ConnectorError):
        map_displayed_residues(source)


@pytest.mark.parametrize("name", ["cc", "newChartData"])
@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "expression", "nonfinite", "duplicate_json_key"]
)
def test_literals_cannot_be_ambiguous_or_executed(name, change):
    source = envelope()
    pattern = rf"(?m)^\s*(?:const|let)\s+{name}\s*=.*$"
    if change == "missing":
        source["record"] = re.sub(pattern, "", NATIVE)
    elif change == "duplicate":
        source["record"] += f"\n<script>\nconst {name} = [];\n</script>"
    else:
        content = {
            "expression": "fetch('https://invalid.example/')",
            "nonfinite": "[NaN]",
            "duplicate_json_key": '{"x":1,"x":2}',
        }[change]
        source["record"] = re.sub(
            pattern, lambda _: f"const {name} = {content};", NATIVE
        )
    with pytest.raises(ConnectorError):
        map_displayed_residues(source)


@pytest.mark.parametrize(
    "change",
    [
        {"source": "Other"},
        {"kind": "other"},
        {"version": "guessed"},
        {"truncated": True},
        {"truncated": None},
        {"query": {"accession": "P37840", "segment": 1}},
        {"query": {"accession": "P60174", "segment": 2}},
        {"query": {"accession": "P60174", "segment": 1, "site": 0}},
    ],
)
def test_wrong_identity_revision_cut_or_site_selector_cannot_relabel_the_panel(change):
    source = envelope()
    source.update(change)
    with pytest.raises(ConnectorError):
        map_displayed_residues(source)


def test_original_site_reader_does_not_acquire_the_new_detail_requirement():
    from sabueso.mappings.ligysis import parse_result

    text = re.sub(r"(?m)^\s*let newChartData =.*$", "", NATIVE)
    assert parse_result(text, "P60174", 1)["chartData"]["ID"] == [0, 1]
    with pytest.raises(ConnectorError):
        parse_displayed_residues(text, "P60174", 1)
