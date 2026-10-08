"""AmyPro native entry identity, own-sequence regions and bounded export access."""

import copy
import hashlib
import io
import json
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

import pytest

from sabueso import RetrievalArchive
from sabueso.core.errors import ArgumentError, ConnectorError
from sabueso.mappings.amypro import map_entry, map_regions
from sabueso.tools.db.amypro import FixtureAmyProClient, get_entry

PATH = Path("temp_data/amypro/entries.json")


def native():
    return json.loads(PATH.read_bytes())


def entry(payload, identifier="AP00015"):
    return next(r for r in payload if r["entry_id"] == identifier)


class Client:
    def __init__(self, payload):
        self.payload = payload

    def entry(self, identifier):
        return {"record": self.payload, "retrieved_at": "2026-01-01", "version": None}


def test_native_alpha_synuclein_regions_keep_own_sequence_and_entry_context():
    envelope = get_entry("ap00015", client=FixtureAmyProClient())
    before = copy.deepcopy(envelope)
    (context,) = map_entry(envelope)
    regions = map_regions(envelope)
    row = entry(native())
    assert len(envelope["record"]) == 125 and len(regions) == 3
    assert context["asserted_value"]["uniprot_id"] == "P37840"
    assert context["asserted_value"]["prion_domain"] == "False"
    assert context["asserted_value"]["class_name"] == "pathogenic"
    assert context["asserted_value"]["sequence"] == row["sequence"]
    for assertion in [context, *regions]:
        assert assertion["subject_ref"] == "amypro:AP00015"
        assert assertion["source"]["version"] is None
        assert assertion["acquisition"] == {"method": "database"}
        assert assertion["source_metadata"]["native_entry"] == row
        assert assertion["source_metadata"]["sequence"]["value"] == row["sequence"]
        assert "knowledge_class" not in assertion["asserted_value"]
        assert "evidence_class" not in assertion["asserted_value"]
        assert "experimental_method" not in assertion["asserted_value"]
        assert (
            "region_specific"
            in assertion["source_metadata"]["mapping_scope"]["support"]
        )
    assert [r["asserted_value"]["location"]["sequence"]["start"] for r in regions] == [
        35,
        49,
        86,
    ]
    assert all(
        r["asserted_value"]["location"]["sequence"]["sequence_id"] == "AmyPro:AP00015"
        for r in regions
    )
    (access,) = envelope["acquisition_trace"]["records"]
    assert access["count"] == 1 and access["received_export_count"] == 125
    assert access["selected_region_count"] == 3 and access["network_attempts"] == 0
    assert access["access"] == "supplied_file" and access["retrieved_at"] is None
    assert access["source_version"]["value"] is None
    assert (
        access["snapshot_receipt"]["document_sha256"]
        == hashlib.sha256(PATH.read_bytes()).hexdigest()
    )
    assert "doi:10.1093/nar/gkx950" in json.dumps(access["bibliography"])
    assert any("region_methods" in gap for gap in access["bibliography_gaps"])
    regions[0]["source_metadata"]["native_entry"]["regions"].clear()
    context["asserted_value"]["pubmed_ids"].clear()
    assert envelope == before


def test_native_processed_sequence_offset_is_not_projected_to_parent_uniprot():
    envelope = get_entry("AP00007", client=FixtureAmyProClient())
    (context,), (region,) = map_entry(envelope), map_regions(envelope)
    assert context["asserted_value"]["uniprot_start"] == "20"
    assert context["asserted_value"]["uniprot_end"] == "710"
    assert len(context["asserted_value"]["sequence"]) == 691
    assert region["asserted_value"]["location"]["sequence"]["start"] == 538
    assert region["asserted_value"]["native_region"]["region_sequence"] == "NAGDVAFV"
    assert region["subject_ref"] == "amypro:AP00007"


def test_native_parent_bounds_inconsistent_with_entry_sequence_are_kept_literal():
    envelope = get_entry("AP00012", client=FixtureAmyProClient())
    (assertion,) = map_entry(envelope)
    value = assertion["asserted_value"]
    assert (value["uniprot_start"], value["uniprot_end"]) == ("2", "758")
    assert len(value["sequence"]) == 684
    assert "no_parent" in assertion["source_metadata"]["mapping_scope"]["coordinates"]
    assert map_regions(envelope)


def test_native_mutation_strings_and_unknown_category_are_not_interpreted():
    payload = native()
    row = entry(payload, "AP00107")
    row["class_name"], row["prion_domain"] = "future_category", "not stated"
    row["future_context"] = {"literal": None}
    (assertion,) = map_entry(get_entry("AP00107", client=Client(payload)))
    value = assertion["asserted_value"]
    assert value["mutations"] == ["S266SRTVKKNIIEEN"]
    assert (
        value["class_name"] == "future_category"
        and value["prion_domain"] == "not stated"
    )
    assert value["future_context"] == {"literal": None}
    assert "location" not in value and "target_sequence" not in value


def test_shared_parent_and_equal_peptides_do_not_merge_entries_or_regions():
    payload = native()
    first = entry(payload)
    repeated = copy.deepcopy(first)
    repeated["entry_id"] = "AP99998"
    payload.append(repeated)
    first["regions"]["duplicate_declaration"] = copy.deepcopy(
        first["regions"]["region_1"]
    )
    a = map_regions(get_entry("AP00015", client=Client(payload)))
    b = map_regions(get_entry("AP99998", client=Client(payload)))
    assert len(a) == 4 and len({r["id"] for r in a}) == 4
    assert {r["subject_ref"] for r in a} == {"amypro:AP00015"}
    assert {r["subject_ref"] for r in b} == {"amypro:AP99998"}
    assert {r["id"] for r in a}.isdisjoint(r["id"] for r in b)


def test_changed_native_sequence_keeps_distinct_region_support_without_revision_guess():
    original = native()
    changed = copy.deepcopy(original)
    row = entry(changed)
    row["sequence"] = "A" + row["sequence"][1:]
    a = map_regions(get_entry("AP00015", client=Client(original)))
    b = map_regions(get_entry("AP00015", client=Client(changed)))
    assert a[0]["asserted_value"] == b[0]["asserted_value"]
    assert a[0]["id"] != b[0]["id"]
    assert (
        a[0]["source_metadata"]["sequence"]["sha256"]
        != b[0]["source_metadata"]["sequence"]["sha256"]
    )
    assert a[0]["source"]["version"] is b[0]["source"]["version"] is None


def test_native_empty_regions_keep_entry_while_missing_selection_is_export_scoped():
    envelope = get_entry("AP00114", client=FixtureAmyProClient())
    assert map_entry(envelope) and map_regions(envelope) == []
    access = envelope["acquisition_trace"]["records"][0]
    assert access["outcome"] == "received" and access["selected_region_count"] == 0
    absent = get_entry("AP99999", client=FixtureAmyProClient())
    assert len(absent["record"]) == 125
    assert map_entry(absent) == [] and map_regions(absent) == []
    access = absent["acquisition_trace"]["records"][0]
    assert access["outcome"] == "not_found" and access["selected_region_count"] is None
    assert "no_native_total" in access["completeness_scope"]
    empty = get_entry("AP00015", client=Client([]))
    assert empty["record"] == [] and map_regions(empty) == []


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.append(copy.deepcopy(p[0])),
        lambda p: p.append(None),
        lambda p: entry(p).update(entry_id="ap00015"),
        lambda p: entry(p).pop("regions"),
        lambda p: entry(p).update(regions=None),
        lambda p: entry(p).update(prion_domain=False),
        lambda p: entry(p).pop("uniprot_start"),
        lambda p: entry(p).update(sequence="AC D"),
        lambda p: entry(p).update(pubmed_ids="123"),
        lambda p: entry(p).update(pubmed_ids=["PMID:123"]),
        lambda p: entry(p).update(mutations=[None]),
        lambda p: entry(p)["regions"].update(region_1=None),
        lambda p: entry(p)["regions"]["region_1"].update(region_indices="0-44"),
        lambda p: entry(p)["regions"]["region_1"].update(region_indices="44-35"),
        lambda p: entry(p)["regions"]["region_1"].update(region_indices="35-999"),
        lambda p: entry(p)["regions"]["region_1"].update(region_sequence="AAAAAAAAAA"),
        lambda p: entry(p)["regions"]["region_1"].pop("region_sequence"),
        lambda p: p[0].update(sequence=None),  # Unselected rows are validated, too.
        lambda p: p[0].update(future=float("inf")),
    ],
)
def test_invalid_full_export_is_refused_before_selected_mapping(change):
    payload = native()
    change(payload)
    with pytest.raises(ConnectorError):
        get_entry("AP00015", client=Client(payload))


@pytest.mark.parametrize(
    "payload", [None, {}, {"regions": []}, "", "{u'entry_id': u'AP00015'}"]
)
def test_missing_or_non_native_export_is_not_an_empty_result(payload):
    with pytest.raises(ConnectorError):
        get_entry("AP00015", client=Client(payload))


@pytest.mark.parametrize(
    "identifier",
    ["AP0001", "AP00000", "P37840", "../AP00015", "AP00015?x", "AP00015/", 15, True],
)
def test_invalid_identifier_never_reaches_client_even_with_skip(identifier):
    class NoAccess:
        def entry(self, identifier):
            pytest.fail("Invalid identifier reached the client")

    with pytest.raises((ArgumentError, ConnectorError)):
        get_entry(identifier, client=NoAccess(), skip_digestion=True)


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(source="UniProt"),
        lambda e: e.update(kind="regions"),
        lambda e: e.update(version="2023-08-25"),
        lambda e: e.update(truncated=True),
        lambda e: e.update(query={"accession": "P37840"}),
        lambda e: e["query"].update(page=1),
    ],
)
def test_mapper_refuses_unsupported_envelope_scope(change):
    envelope = get_entry("AP00015", client=FixtureAmyProClient())
    change(envelope)
    with pytest.raises(ConnectorError):
        map_regions(envelope)
    with pytest.raises(ConnectorError):
        map_entry(envelope)


def test_missing_fixture_is_unavailable(tmp_path):
    with pytest.raises(ConnectorError) as error:
        get_entry("AP00015", client=FixtureAmyProClient(tmp_path))
    assert error.value.acquisition_trace["records"][0]["outcome"] == "unavailable"


@pytest.mark.parametrize("status", [404, 500])
def test_failed_http_is_not_export_absence(status, monkeypatch):
    import sabueso.tools.db._http as http

    monkeypatch.setattr(http, "RETRIES", 0)

    def fail(request, timeout):
        raise HTTPError(request.full_url, status, "failed", {}, None)

    monkeypatch.setattr(http, "_urlopen", fail)
    with pytest.raises(ConnectorError) as error:
        get_entry("AP00015")
    access = error.value.acquisition_trace["records"][0]
    assert access["outcome"] == "failed" and access["network_attempts"] == 1


@pytest.mark.parametrize(
    "body",
    [
        b"{u'entry_id': u'AP00015'}",
        b'[{"entry_id":"AP00015","entry_id":"AP00007"}]',
        b"[NaN]",
    ],
)
def test_malformed_wire_json_is_never_repaired_or_evaluated(body, monkeypatch):
    import sabueso.tools.db._http as http

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    monkeypatch.setattr(http, "_urlopen", lambda request, timeout: Answer(body))
    with pytest.raises(ConnectorError) as error:
        get_entry("AP00015")
    assert error.value.acquisition_trace["records"][0]["outcome"] == "failed"


def test_shared_archive_replay_preserves_export_and_original_time_without_link_access(
    tmp_path, monkeypatch
):
    import sabueso.tools.db._http as http

    calls = []

    class Answer(io.BytesIO):
        status = 200
        headers = Message()
        headers["Content-Type"] = "application/json"

    def wire(request, timeout):
        calls.append(request.full_url)
        return Answer(PATH.read_bytes())

    monkeypatch.setattr(http, "_urlopen", wire)
    archive = RetrievalArchive(tmp_path / "amypro.db")
    with archive.recording():
        first = get_entry("AP00015")

    def fail(*args, **kwargs):
        pytest.fail("Replay or mapping reached a linked resource")

    monkeypatch.setattr(http, "_urlopen", fail)
    with archive.replaying():
        second = get_entry("AP00015")
    assert calls == ["https://amypro.net/data/amypro.json"]
    assert first["record"] == second["record"] == native()
    assert first["retrieved_at"] == second["retrieved_at"]
    assert map_regions(first) == map_regions(second) and map_entry(first) == map_entry(
        second
    )
    a, b = (
        first["acquisition_trace"]["records"][0],
        second["acquisition_trace"]["records"][0],
    )
    assert a["received_responses"] == a["network_attempts"] == 1
    assert b["access"] == "replay" and b["network_attempts"] == 0
    assert a["response_identity"] == b["response_identity"]
