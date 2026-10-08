"""Native directed LIGYSIS dictionaries never assign the queried protein to chains."""

import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

from sabueso.core.errors import ConnectorError
from sabueso.mappings.ligysis import (
    map_residue_correspondences,
    parse_residue_correspondences,
    parse_result,
)
from sabueso.tools.db.ligysis import FixtureLigysisClient, get_result_page

RAW = Path("temp_data/ligysis/result__P60174__1.html").read_bytes()
NATIVE = RAW.decode("utf-8")


def envelope():
    return get_result_page("P60174", 1, client=FixtureLigysisClient())


def literal(document, name, value):
    return re.sub(
        rf"(?m)^\s*(?:const|let)\s+{name}\s*=.*$",
        lambda _: f"const {name} = {json.dumps(value)};",
        document,
    )


def record(forward, reverse):
    source = envelope()
    source["record"] = literal(NATIVE, "Pdb2UpDict", forward)
    source["record"] = literal(source["record"], "Up2PdbDict", reverse)
    return source


def test_native_two_chains_keep_both_directions_and_unknown_protein_identity():
    source = envelope()
    before = copy.deepcopy(source)
    rows = map_residue_correspondences(source)
    assert source == before
    assert len(rows) == 4 and len({row["id"] for row in rows}) == 4
    values = [row["asserted_value"] for row in rows]
    assert [
        (
            v["native_direction"],
            v["native_structure_key"],
            v["native_chain_key"],
            len(v["native_pairs"]),
        )
        for v in values
    ] == [
        ("Pdb2UpDict", "7t0q", "A", 245),
        ("Pdb2UpDict", "7t0q", "B", 246),
        ("Up2PdbDict", "7t0q", "A", 245),
        ("Up2PdbDict", "7t0q", "B", 246),
    ]
    assert values[0]["native_pairs"]["4"] == 5
    assert values[1]["native_pairs"]["3"] == 4
    assert values[2]["native_pairs"]["5"] == 4
    assert sum(len(v["native_pairs"]) for v in values) == 982
    for row in rows:
        meta = row["source_metadata"]
        assert row["subject_ref"].startswith("ligysis:correspondence_table:")
        assert row["field_path"] == "annotations.ligysis_residue_correspondences"
        assert "location" not in row and "evidence_class" not in row
        assert row["source"]["version"] is None and row["retrieved_at"] is None
        assert meta["identity_context"]["protein_accession"] is None
        assert meta["identity_context"]["chain_namespace"] is None
        assert meta["identity_context"]["structure_numbering_scheme"] is None
        assert meta["response_sha256"] == hashlib.sha256(RAW).hexdigest()
        assert meta["native_pair_order"] == list(row["asserted_value"]["native_pairs"])
        assert meta["snapshot_receipt"] == source["snapshot_receipt"]
    rows[0]["asserted_value"]["native_pairs"]["4"] = 99
    rows[0]["source_metadata"]["snapshot_receipt"]["path"] = "changed"
    assert source == before


def test_conflicting_nonbijective_directions_and_missing_opposite_parents_survive():
    forward = {"7t0q": {"A": {"4": 5, "6": 5}, "B": {"3": 4}}}
    reverse = {"7t0q": {"A": {"5": 999}}}
    rows = map_residue_correspondences(record(forward, reverse))
    assert len(rows) == 3
    assert rows[0]["asserted_value"]["native_pairs"] == {"4": 5, "6": 5}
    assert rows[2]["asserted_value"]["native_pairs"] == {"5": 999}
    assert rows[1]["asserted_value"]["native_chain_key"] == "B"
    assert all(
        row["source_metadata"]["identity_context"]["protein_accession"] is None
        for row in rows
    )


def test_chain_case_structure_case_signed_and_equal_numeric_looking_labels_are_literal():
    forward = {"7T0Q": {"a": {"04": 5, "4": 6, "0": -1, "-2": 0}, "A": {}}}
    rows = map_residue_correspondences(record(forward, {}))
    assert len(rows) == 2
    assert rows[0]["asserted_value"]["native_structure_key"] == "7T0Q"
    assert rows[0]["asserted_value"]["native_chain_key"] == "a"
    assert rows[0]["asserted_value"]["native_pairs"] == forward["7T0Q"]["a"]
    assert rows[0]["source_metadata"]["native_pair_order"] == ["04", "4", "0", "-2"]
    assert rows[1]["asserted_value"]["native_chain_key"] == "A"
    assert rows[1]["source_metadata"]["received_pair_count"] == 0
    assert map_residue_correspondences(record({}, {})) == []


@pytest.mark.parametrize("direction", ["Pdb2UpDict", "Up2PdbDict"])
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        [],
        {"custom_model": {}},
        {"7t0q": []},
        {"7t0q": {"": {}}},
        {"7t0q": {"B": []}},
        {"7t0q": {"B": {"4A": 5}}},
        {"7t0q": {"B": {"4": True}}},
        {"7t0q": {"B": {"4": 5.5}}},
        {"7t0q": {"B": {"4": "5"}}},
    ],
)
def test_malformed_direction_or_late_parent_is_refused_before_output(
    direction, invalid
):
    source = envelope()
    source["record"] = literal(NATIVE, direction, invalid)
    with pytest.raises(ConnectorError):
        map_residue_correspondences(source)


@pytest.mark.parametrize("direction", ["Pdb2UpDict", "Up2PdbDict"])
@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "expression", "nonfinite", "duplicate_key"]
)
def test_missing_ambiguous_or_executable_literals_cannot_supply_mapping_support(
    direction, change
):
    source = envelope()
    pattern = rf"(?m)^\s*const {direction}\s*=.*$"
    if change == "missing":
        source["record"] = re.sub(pattern, "", NATIVE)
    elif change == "duplicate":
        source["record"] += f"\n<script>\nconst {direction} = {{}};\n</script>"
    else:
        value = {
            "expression": "fetch('/new_mapping')",
            "nonfinite": '{"7t0q":{"A":{"4":NaN}}}',
            "duplicate_key": '{"7t0q":{"A":{"4":5,"4":6}}}',
        }[change]
        source["record"] = re.sub(
            pattern, lambda _: f"const {direction} = {value};", NATIVE
        )
    with pytest.raises(ConnectorError):
        map_residue_correspondences(source)


@pytest.mark.parametrize(
    "change",
    [
        {"source": "SIFTS"},
        {"kind": "mapping"},
        {"version": "guessed"},
        {"truncated": True},
        {"truncated": None},
        {"query": {"accession": "P37840", "segment": 1}},
        {"query": {"accession": "P60174", "segment": 2}},
        {"query": {"accession": "P60174", "segment": 1, "chain": "A"}},
    ],
)
def test_misbound_scope_cannot_assign_identity_to_received_mapping(change):
    source = envelope()
    source.update(change)
    with pytest.raises(ConnectorError):
        map_residue_correspondences(source)


def test_site_only_parsing_keeps_its_contract_without_correspondence_literals():
    text = re.sub(r"(?m)^\s*const (?:Pdb2UpDict|Up2PdbDict) =.*$", "", NATIVE)
    assert parse_result(text, "P60174", 1)["chartData"]["ID"] == [0, 1]
    with pytest.raises(ConnectorError):
        parse_residue_correspondences(text, "P60174", 1)
