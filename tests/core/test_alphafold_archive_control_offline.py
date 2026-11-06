"""Genuine public archive input, original reference and explicit API boundary.

The ModelCIF metadata projection has independent Biopython/Gemmi receiving in
the developer control. This module needs only the existing SDK/standard library;
it does not install a production archive parser or synthesize an API response.
"""

import gzip
import hashlib
import json
import socket
import tarfile
from pathlib import Path

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import RecordNotFoundError
from sabueso.mappings.uniprot import map_protein
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient, get_prediction
from sabueso.tools.db.uniprot import FixtureUniProtClient, get_entry

INPUTS = Path(__file__).resolve().parents[2] / "temp_data/alphafold_archive"
MODEL = "AF-Q8WZ42-F2-model_v6.cif.gz"


def forbidden(*args, **kwargs):
    raise AssertionError("No network, archive fallback or current Card construction")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def test_exact_native_member_and_transport_identity_are_preserved():
    capture = json.loads((INPUTS / "capture.json").read_text("utf-8"))
    raw = (INPUTS / MODEL).read_bytes()
    assert len(raw) == 269404
    assert (
        sha(raw) == "74da31b7a0153ef2c90dc8f60fe07edaa83ba50049bf06e6f4eb113ece1963ef"
    )
    decoded = gzip.decompress(raw)
    assert len(decoded) == 1298513
    assert (
        sha(decoded)
        == "206ffc9821eaa76a33f7f3afe1b42f5ffd1eeae5b411c299cf8ae910f9964036"
    )
    header = (INPUTS / "AF-Q8WZ42-F2-model_v6.tar-header.bin").read_bytes()
    member = tarfile.TarInfo.frombuf(header, encoding="utf-8", errors="strict")
    assert member.isfile() and member.name == MODEL and member.size == len(raw)
    assert (
        sha(header)
        == "952033fd3aeb9a15e0ac7a1815f9db53f8f8b9b4141205b6c71058997e1cd83e"
    )
    assert capture["member_header"]["offset"] == 3628310528
    assert len(capture["requests"]) == 19
    assert sum(row["bytes"] for row in capture["requests"]) == 4595292
    for row in capture["requests"]:
        begin, end = row["range"]
        assert row["status"] == 206
        assert row["headers"]["Content-Range"] == f"bytes {begin}-{end}/5177506304"
        assert row["headers"]["ETag"] == capture["archive"]["etag"]
    for name, item in capture["files"].items():
        source = (INPUTS / name).read_bytes()
        assert len(source) == item["bytes"] and sha(source) == item["sha256"]


def test_native_reference_identity_interval_and_checksum_scope_are_distinct():
    assert (
        sha((INPUTS / "modelcif_metadata.json").read_bytes())
        == "8283e0b66698babc256aa2a8e6b634201d1bbc2167d8887fabb8bffe9e9da1d4"
    )
    projection = json.loads((INPUTS / "modelcif_metadata.json").read_text("utf-8"))
    reference_raw = (INPUTS / "uniprot/Q8WZ42.json").read_bytes()
    assert (
        sha(reference_raw)
        == "28cb420c5f120679947abde3186939a33e07ea232ae4dbc1300268d871c14dec"
    )
    reference = json.loads(reference_raw)
    tags = projection["native_tags"]
    assert tags["_database_2.database_code"] == ["AF-Q8WZ42-F2"]
    assert tags["_ma_target_ref_db_details.db_name"] == ["UNP"]
    assert (
        tags["_ma_target_ref_db_details.db_accession"]
        == [reference["primaryAccession"]]
        == ["Q8WZ42"]
    )
    assert tags["_ma_target_ref_db_details.seq_db_isoform"] == ["?"]
    assert [
        tags["_ma_target_ref_db_details.seq_db_align_begin"],
        tags["_ma_target_ref_db_details.seq_db_align_end"],
    ] == [["201"], ["1600"]]
    assert [
        tags["_struct_ref_seq.seq_align_beg"],
        tags["_struct_ref_seq.seq_align_end"],
    ] == [["1"], ["1400"]]
    fragment = "".join(tags["_entity_poly.pdbx_seq_one_letter_code_can"][0].split())
    assert len(fragment) == 1400
    assert (
        reference["sequence"]["length"] == len(reference["sequence"]["value"]) == 34350
    )
    assert fragment == reference["sequence"]["value"][200:1600]
    assert (
        tags["_ma_target_ref_db_details.seq_db_sequence_checksum"]
        == [reference["sequence"]["crc64"]]
        == ["DEB216410AD560D9"]
    )
    assert (
        tags["_ma_target_ref_db_details.seq_db_sequence_version_date"]
        == [reference["entryAudit"]["lastSequenceUpdateDate"]]
        == ["2012-04-18"]
    )
    assert (
        hashlib.md5(fragment.encode(), usedforsecurity=False).hexdigest()
        == "509b42678e45f12fcf04d77877958e25"
    )
    # This digest is a test-derived check, never a provider-stated API checksum.
    assert "sequenceChecksum" not in projection


def test_sequence_only_reference_control_keeps_human_agent_saved_scope(
    tmp_path, monkeypatch
):
    entry = get_entry("Q8WZ42", client=FixtureUniProtClient(INPUTS / "uniprot"))
    mapping = map_protein(entry["record"], retrieved_at="2026-11-05")
    # Explicit sequence-only reference control. The original source file is
    # complete; full-annotation saving has its own retained #167 failure control
    # and whole-Card regression. This scoped scientific control cannot qualify it.
    fields = (
        "identifiers.uniprot",
        "sequence.primary",
        "sequence.length",
        "sequence.checksums",
    )
    mapping["fields"] = {key: mapping["fields"][key] for key in fields}
    mapping["field_source_assertions"] = {
        key: mapping["field_source_assertions"][key] for key in fields
    }
    refs = {
        ref for values in mapping["field_source_assertions"].values() for ref in values
    }
    mapping["source_assertions"] = [
        row for row in mapping["source_assertions"] if row["id"] in refs
    ]
    mapping["relationships"] = []
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:Q8WZ42",
        entity_subjects={"uniprot:Q8WZ42"},
    )
    assert not card.relationships("has_predicted_structure")
    assert card.get("sequence.checksums")["value"] == {
        key: entry["record"]["sequence"][key] for key in ("crc64", "md5")
    }
    before = card.to_dict()
    explorer = card.explore()
    sequence = explorer.view("sequence")
    length = next(item for item in sequence.items() if item.label == "Sequence length")
    frame = explorer.access.read(length.payload_location).page(limit=8, max_bytes=4096)
    assert (
        next(row for row in frame["items"] if row["key"] == "value")["value"] == 34350
    )
    path = tmp_path / "reference.json.gz"
    sequence.save(path, compression="gzip")
    expected = sequence.native_payload
    assert card.to_dict() == before
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == expected
    assert saved.explorer.view("predicted_structures").outcome["status"] == "not_saved"


def test_complete_public_reference_panel_save_preserves_all_original_content(
    tmp_path, monkeypatch
):
    entry = get_entry("Q8WZ42", client=FixtureUniProtClient(INPUTS / "uniprot"))
    mapping = map_protein(entry["record"], retrieved_at="2026-11-05")
    assert len(mapping["fields"]) == 26
    assert len(mapping["source_assertions"]) == 1489
    assert len(mapping["relationships"]) == 215
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:Q8WZ42",
        entity_subjects={"uniprot:Q8WZ42"},
    )
    before = card.to_dict()
    sequence = card.explore().view("sequence")
    domains = next(
        item
        for item in sequence.items()
        if item._entry.key == "features_positional.domains"
    )
    original_support = domains.support
    expected = sequence.native_payload
    path = tmp_path / "complete-reference.json.gz"
    receipt = sequence.save(path, compression="gzip")
    packet = json.loads(gzip.decompress(path.read_bytes()))
    if packet["format"] == "sabueso.card_exploration@13":
        from sabueso.core.card_exploration_shared_values_v1 import unpack

        packet, report = unpack(packet, receipt["bundle_digest"])
        assert report["logical_format"] == "sabueso.card_exploration@11"
    assert packet["format"] == "sabueso.card_exploration@11"
    assert card.to_dict() == before
    import sabueso.core.card_context_support_v1 as shared

    monkeypatch.setattr(shared, "compact_related", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.native_payload == expected
    exported = tmp_path / "complete-card.json"
    saved.explorer.access.export_card(exported)
    assert json.loads(exported.read_text("utf-8")) == before
    links = saved.item(domains.item_ref).related()
    assert len(links.items()) == len(original_support[0]["statements"])
    member = links.items()[0].support[0]
    full = saved.explorer.inspect(locator=member["support_location"])
    assert full.native_payload["support"] == original_support
    assert saved.explorer.view("predicted_structures").outcome["status"] == "not_saved"


def test_archive_presence_does_not_become_an_api_record_or_global_absence():
    assert (INPUTS / MODEL).is_file()
    with pytest.raises(
        RecordNotFoundError, match="Database availability was not checked"
    ):
        get_prediction("Q8WZ42", client=FixtureAlphaFoldClient(INPUTS))
