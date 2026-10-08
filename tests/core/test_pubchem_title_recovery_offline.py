"""Native PubChem titles remain descriptions with independent source support."""

import copy
import io
import json
from email.message import Message
from pathlib import Path

import pytest

from sabueso.core.errors import ConnectorError
from sabueso.mappings.pubchem import map_compound
from sabueso.tools.card.small_molecule import build_molecule_cards
from sabueso.tools.db import _http, pubchem

ORIGINAL = Path("temp_data/pubchem/titles__66414_3717450_2244.json").read_bytes()
RECORDS = {
    str(record["CID"]): record
    for record in json.loads(ORIGINAL)["PropertyTable"]["Properties"]
}


def payload(cid="66414"):
    return {"PropertyTable": {"Properties": [copy.deepcopy(RECORDS[cid])]}}


@pytest.mark.parametrize("cid", sorted(RECORDS))
def test_native_title_has_its_own_support_and_preserves_structure_identity(cid):
    record = payload(cid)
    before = copy.deepcopy(record)
    cards, unanchored = build_molecule_cards(
        pubchem={"retrieved_at": "2026-10-08", "compounds": {cid: record}}
    )
    assert not unanchored and set(cards) == {RECORDS[cid]["InChIKey"]}
    card = cards[RECORDS[cid]["InChIKey"]]
    name = card.get("names.canonical_name")
    assert name["value"] == RECORDS[cid]["Title"]
    (support,) = name["source_assertion_ids"]
    assertion = card.source_assertion_store.get(support)
    assert assertion["asserted_value"] == RECORDS[cid]["Title"]
    assert assertion["subject_ref"] == "pubchem:" + cid
    assert assertion["source"]["name"] == "PubChem"
    assert assertion["source"]["record_id"] == cid
    assert assertion["source"].get("version") is None
    assert assertion["retrieved_at"] == "2026-10-08"
    assert assertion["source_metadata"] == {"pubchem_property": "Title"}
    assert "knowledge_class" not in assertion
    assert "evidence_class" not in assertion
    assert support not in card.get("identifiers.inchikey")["source_assertion_ids"]
    assert record == before


@pytest.mark.parametrize("missing", [None, "", "absent"])
def test_missing_title_is_unstated_without_an_iupac_name_fallback(missing):
    record = payload()
    native = record["PropertyTable"]["Properties"][0]
    native["IUPACName"] = "Synthetic systematic name, not a summary title"
    if missing == "absent":
        native.pop("Title")
    else:
        native["Title"] = missing
    mapping = map_compound(record, "fixture")
    assert "names.canonical_name" not in mapping["fields"]
    assert "names.canonical_name" not in mapping["field_source_assertions"]


@pytest.mark.parametrize("invalid", [False, 0, 1.5, [], {}, "   "])
def test_malformed_title_fails_instead_of_becoming_missing_or_coerced(invalid):
    record = payload()
    record["PropertyTable"]["Properties"][0]["Title"] = invalid
    with pytest.raises(ConnectorError, match="Title.*native text"):
        map_compound(record, "fixture")


def test_title_spelling_and_whitespace_are_literal_source_text():
    record = payload()
    title = "  Synthetic \u03b2-name  "
    record["PropertyTable"]["Properties"][0]["Title"] = title
    mapping = map_compound(record, "fixture")
    assert mapping["fields"]["names.canonical_name"] == title
    (support,) = mapping["field_source_assertions"]["names.canonical_name"]
    assertion = next(a for a in mapping["source_assertions"] if a["id"] == support)
    assert assertion["asserted_value"] == title
    assert "normalized_value" not in assertion


@pytest.mark.parametrize("key", [None, "SYNTHETIC-NOT-A-STRUCTURE-KEY"])
def test_title_does_not_anchor_a_compound_without_a_standard_key(key):
    record = payload()
    record["PropertyTable"]["Properties"][0]["InChIKey"] = key
    cards, unanchored = build_molecule_cards(
        pubchem={"retrieved_at": "fixture", "compounds": {"66414": record}}
    )
    assert not cards
    assert unanchored == [{"ref": "pubchem:66414", "reason": "no_standard_inchikey"}]


def test_equal_titles_do_not_merge_native_distinct_structures():
    compounds = {cid: payload(cid) for cid in RECORDS}
    for record in compounds.values():
        record["PropertyTable"]["Properties"][0]["Title"] = "Synthetic shared name"
    cards, unanchored = build_molecule_cards(
        pubchem={"retrieved_at": "fixture", "compounds": compounds}
    )
    assert not unanchored and len(cards) == 3
    assert set(cards) == {r["InChIKey"] for r in RECORDS.values()}


def test_changed_title_conflict_preserves_both_original_assertions():
    first = payload()
    second = payload()
    second["PropertyTable"]["Properties"][0]["Title"] = "Synthetic later title"
    cards, _ = build_molecule_cards(
        pubchem={
            "retrieved_at": "fixture",
            "compounds": {"first": first, "second": second},
        }
    )
    card = next(iter(cards.values()))
    assertions = card.source_assertion_store.find_by_field("names.canonical_name")
    assert {a["asserted_value"] for a in assertions} == {
        RECORDS["66414"]["Title"],
        "Synthetic later title",
    }
    (conflict,) = [
        c for c in card.quality["conflicts"] if c["field"] == "names.canonical_name"
    ]
    assert {a["id"] for a in assertions} == {
        support for group in conflict["source_assertion_ids"] for support in group
    }
    selected = card.get("names.canonical_name")
    assert all(
        card.source_assertion_store.get(support)["asserted_value"] == selected["value"]
        for support in selected["source_assertion_ids"]
    )


def test_online_property_request_includes_title_and_keeps_native_response(monkeypatch):
    calls = []

    class Response(io.BytesIO):
        status = 200

        def __init__(self):
            super().__init__(ORIGINAL)
            self.headers = Message()

    def respond(request, timeout):
        calls.append(request)
        return Response()

    monkeypatch.setattr(_http, "_urlopen", respond)
    monkeypatch.setattr(_http, "_wait", lambda *args: 0)
    result = pubchem.get_compound("66414,3717450,2244")
    assert result["record"] == json.loads(ORIGINAL)
    (request,) = calls
    assert request.get_method() == "GET"
    assert "/property/Title," in request.full_url
