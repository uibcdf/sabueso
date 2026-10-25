"""Original inputs, conservative identity/scope and immutable model history."""

import socket
import subprocess
import sys
from copy import deepcopy
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.migration import _has
from sabueso.core.packets import KnowledgePacket, _facts, full_rules
from sabueso.core.predicted_structures import RULE as VIEW_RULE
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.alphafold import map_predictions
from sabueso.mappings.alphafold_context_v1 import RULE


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("No source acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)


def inputs():
    return [
        make_source_assertion(field, value, "UniProt", "P52270", "synthetic")
        for field, value in [
            ("identifiers.uniprot", "P52270"),
            ("sequence.checksums", {"md5": "A" * 32}),
            ("sequence.length", 100),
            ("annotations.isoforms", {"isoform_id": "P52270-2"}),
        ]
    ]


def model():
    return {
        "entryId": "AF-SYNTHETIC-F1",
        "uniprotAccession": "P52270",
        "sequenceChecksum": "a" * 32,
        "uniprotStart": 1,
        "uniprotEnd": 100,
        "latestVersion": 6,
        "globalMetricValue": 80.0,
    }


def mapping(record=None, originals=None, *, checksum="A" * 32):
    return map_predictions(
        {"record": [record or model()]},
        "P52270",
        "synthetic",
        checksum,
        input_assertions=inputs() if originals is None else originals,
    )


def card(record=None, originals=None):
    originals = inputs() if originals is None else originals
    result = mapping(record, originals)
    result["source_assertions"] += deepcopy(originals)
    result["fields"] = {"identifiers.uniprot": "P52270", "sequence.length": 100}
    result["field_source_assertions"] = {
        field: [r["id"] for r in originals if r["field_path"] == field]
        for field in result["fields"]
    }
    return build_card_from_mapping(
        result,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )


def test_original_context_is_bound_and_replay_never_uses_present_fields():
    result = card()
    (relationship,) = result.relationships("has_predicted_structure")
    derivation = relationship["derivation"]
    assert derivation["rule"] == RULE
    assert derivation["parameters"]["qualifier_paths"] == [
        "isoform",
        "sequence_matches",
        "sequence_context",
    ]
    assert len(relationship["derivation_applications"]) == 1
    source = result.source_assertion_store.get(relationship["source_assertion_ids"][0])
    assert source["asserted_value"]["model"] == model()
    assert "sequence_context" not in source["asserted_value"]
    result.get("sequence.length")["value"] = 200
    (row,) = result.predicted_structures()["items"]
    assert (
        row["coverage"] == 1.0
        and row["coverage_scope"] == "original_whole_sequence_input"
    )
    assert row["sequence_context"]["focal_length"]["value"] == 100
    assert row["sequence_matches"] is True
    assert row["context_state"] == "original_source_inputs_bound"
    row["sequence_context"]["checksum_comparison"]["focal_values"].clear()
    assert result.predicted_structures()["items"][0]["sequence_matches"] is True
    assert Card.from_dict(result.to_dict()).to_dict() == result.to_dict()


@pytest.mark.parametrize(
    "accession,expected",
    [
        ("P52270-2", "source_stated_isoform"),
        ("P60174", "different_accession_unclassified"),
        (None, "model_accession_not_stated"),
        ([], "invalid_model_accession"),
    ],
)
def test_identity_requires_exact_source_context(accession, expected):
    record = model()
    record["uniprotAccession"] = accession
    result = card(record)
    (row,) = result.predicted_structures()["items"]
    assert row["sequence_context"]["identity_state"] == expected
    assert row["isoform"] == (
        "P52270-2" if expected == "source_stated_isoform" else None
    )
    assert row["sequence_matches"] is None and row["coverage"] is None
    if expected == "source_stated_isoform":
        assert row["sequence_context"]["isoform_source_assertion_ids"]


@pytest.mark.parametrize(
    "checksum,match",
    [("B" * 32, False), (None, None), (123, None), ("0" * 16, None), ("bad", None)],
)
def test_checksum_prerequisites_and_mismatch_never_prove_coverage(checksum, match):
    record = model()
    record["sequenceChecksum"] = checksum
    (row,) = card(record).predicted_structures()["items"]
    assert row["sequence_matches"] is match and row["coverage"] is None


@pytest.mark.parametrize(
    "scope", [(1, 50), (2, 100), (0, 100), (1, 101), (True, 100), (1, "100")]
)
def test_fragments_and_invalid_ranges_do_not_compare_to_whole_sequence(scope):
    record = model()
    record["uniprotStart"], record["uniprotEnd"] = scope
    (row,) = card(record).predicted_structures()["items"]
    assert row["sequence_context"]["checksum_comparison"]["equal"] is True
    assert row["sequence_matches"] is None and row["coverage"] is None
    assert (
        "whole_focal_sequence_scope_not_established"
        in row["sequence_context"]["reasons"]
    )


@pytest.mark.parametrize(
    "mode", ["missing", "conflict", "foreign", "supplied_mismatch", "invalid_length"]
)
def test_missing_or_conflicting_original_inputs_remain_unknown(mode):
    originals = inputs()
    checksum = "A" * 32
    if mode == "missing":
        originals = [r for r in originals if r["field_path"] != "sequence.checksums"]
    elif mode == "conflict":
        originals.append(
            make_source_assertion(
                "sequence.checksums", {"md5": "B" * 32}, "UniProt", "P52270", "other"
            )
        )
    elif mode == "foreign":
        next(r for r in originals if r["field_path"] == "sequence.checksums")[
            "subject_ref"
        ] = "uniprot:P60174"
    elif mode == "supplied_mismatch":
        checksum = "C" * 32
    else:
        next(r for r in originals if r["field_path"] == "sequence.length")[
            "asserted_value"
        ] = True
    result = mapping(originals=originals, checksum=checksum)
    context = result["relationships"][0]["qualifiers"]["sequence_context"]
    assert context["sequence_matches"] is None and context["coverage"] is None


def test_standalone_argument_is_retained_without_manufacturing_source_support():
    result = map_predictions({"record": [model()]}, "P52270", "synthetic", "A" * 32)
    assert len(result["source_assertions"]) == 1
    relationship = result["relationships"][0]
    context = relationship["qualifiers"]["sequence_context"]
    assert context["checksum_comparison"]["equal"] is True
    assert context["input_binding"] == "supplied_argument"
    assert context["sequence_matches"] is None and context["coverage"] is None
    assert relationship["derivation"]["parameters"]["sequence_md5_argument"] == "A" * 32


def test_multiple_original_model_contexts_do_not_silently_select_a_finding():
    result = card()
    other_model = model()
    other_model["sequenceChecksum"] = "B" * 32
    second = mapping(other_model)
    for assertion in second["source_assertions"]:
        result.source_assertion_store.add(assertion)
    result.relationship_store.add(second["relationships"][0])
    (row,) = result.predicted_structures()["items"]
    assert row["context_state"] == "multiple_original_contexts"
    assert row["coverage"] is None and row["sequence_matches"] is None
    assert len(row["qualifier_conflicts"]["sequence_context"]) == 2
    assert _has(
        result.to_dict(), "relationships.has_predicted_structure.sequence_context"
    )
    assert "Alternative model values are retained" in repr(
        result.explore().view("predicted_structures")
    )


@pytest.mark.parametrize(
    "mode",
    [
        "missing_source",
        "changed_input",
        "changed_output",
        "wrong_scope",
        "missing_application",
        "invalid_application",
        "null_applications",
        "malformed_conflicts",
    ],
)
def test_incomplete_or_changed_basis_is_not_certified(mode):
    result = card()
    (rel,) = result.relationships("has_predicted_structure")
    if mode in ("missing_source", "changed_input"):
        ref = next(
            ref
            for ref in rel["derivation"]["parameters"]["focal_input_assertion_ids"]
            if result.source_assertion_store.get(ref)["field_path"]
            == "sequence.checksums"
        )
        if mode == "missing_source":
            del result.source_assertion_store.store[ref]
        else:
            result.source_assertion_store.store[ref]["asserted_value"] = None
    elif mode == "changed_output":
        rel["qualifiers"]["sequence_context"]["coverage"] = 0.5
    elif mode == "wrong_scope":
        rel["derivation_applications"][0]["derivation"]["parameters"][
            "qualifier_paths"
        ] = ["unrelated"]
    elif mode == "invalid_application":
        rel["derivation_applications"] = [None, {"derivation": "invalid"}]
    elif mode == "null_applications":
        rel["derivation_applications"] = None
    elif mode == "malformed_conflicts":
        rel["qualifier_conflicts"] = "unrecognized"
    else:
        del rel["derivation_applications"]
    (row,) = result.predicted_structures()["items"]
    assert row["context_state"] == "original_basis_not_established"
    assert row["coverage"] is None and row["sequence_matches"] is None


def test_migration_does_not_manufacture_historical_context():
    result = card()
    (rel,) = result.relationships("has_predicted_structure")
    rel["qualifiers"].pop("sequence_context")
    rel.pop("derivation")
    rel.pop("derivation_applications")
    result.meta["schema_version"] = "0.3.13"
    original = result.to_dict()
    assert not _has(original, "relationships.has_predicted_structure.sequence_context")
    migrated = sabueso.migrate_card(original).to_dict()
    assert migrated["relationship_store"] == original["relationship_store"]
    assert any(
        g["path"] == "relationships.has_predicted_structure.sequence_context"
        for row in migrated["quality"]["migration"]
        for step in row["steps"]
        for g in step["gaps"]
    )
    assert result.to_dict() == original


def test_fixture_refresh_produces_new_basis_and_preserves_original_pin(tmp_path):
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.alphafold import FixtureAlphaFoldClient

    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    original, _ = sabueso.resolve(
        "P52270",
        resolver=resolver,
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldClient("temp_data"),
    )
    (rel,) = original.relationships("has_predicted_structure")
    rel["qualifiers"].pop("sequence_context")
    rel.pop("derivation")
    rel.pop("derivation_applications")
    original.meta["schema_version"] = "0.3.13"
    for enrichment in original.quality.get("enrichments", []):
        enrichment.pop("request_options", None)
    before = original.to_dict()
    store = sabueso.KnowledgeStore(tmp_path / "refresh.db")
    pin = store.save(original)
    refreshed, _ = sabueso.refresh_card(
        original,
        store=store,
        resolver=resolver,
        alphafold_client=FixtureAlphaFoldClient("temp_data"),
    )
    assert refreshed.predicted_structures()["items"][0]["sequence_matches"] is True
    assert refreshed.predicted_structures()["items"][0]["coverage"] == 1.0
    assert store.load(pin).to_dict() == before == original.to_dict()


@pytest.mark.parametrize(
    "mapping_version", ["packet_aspects@6", "packet_aspects@7", "packet_aspects@8"]
)
@pytest.mark.parametrize("detail", ["full", "index"])
def test_old_packets_preserve_original_projection_and_current_terms_are_complete(
    tmp_path, monkeypatch, mapping_version, detail
):
    result = card()
    (rel,) = result.relationships("has_predicted_structure")
    # Deliberately synthetic legacy state: no original context, with a stored flag.
    rel["qualifiers"].pop("sequence_context")
    rel.pop("derivation")
    rel.pop("derivation_applications")
    store = sabueso.KnowledgeStore(tmp_path / "history.db")
    store.save(result)
    packet = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail), result
    )
    assert packet.to_dict()["aspect_mapping"] == "packet_aspects@11"
    assert VIEW_RULE in full_rules()["structures"]
    assert RULE in full_rules()["structures"]
    assert VIEW_RULE not in full_rules(mapping=mapping_version)["structures"]
    assert _facts("structures", result)["predicted"]["items"][0]["coverage"] is None
    assert (
        _facts("structures", result, mapping=mapping_version)["predicted"]["items"][0][
            "coverage"
        ]
        == 1.0
    )
    payload = packet.to_dict()
    payload["aspect_mapping"] = mapping_version
    payload["facts"]["structures"]["subject"] = (
        _facts("structures", result, mapping=mapping_version)
        if detail == "full"
        else {
            **payload["facts"]["structures"]["subject"],
            "full_rules": full_rules(mapping=mapping_version)["structures"],
        }
    )
    historical = KnowledgePacket(payload)
    before = historical.to_dict()
    monkeypatch.setattr(
        Card,
        "predicted_structures",
        lambda *a, **k: pytest.fail("No current predicted scope in historical terms"),
    )
    historical.terms("commercial_product", store=store)
    assert historical.to_dict() == before and packet.same_knowledge(historical) is None


@pytest.mark.parametrize("detail", ["full", "index"])
def test_current_packet_keeps_original_model_and_uniprot_input_support(
    tmp_path, detail
):
    result = card()
    (rel,) = result.relationships("has_predicted_structure")
    store = sabueso.KnowledgeStore(tmp_path / "current.db")
    store.save(result)
    packet = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["structures"], detail=detail), result
    )
    items = packet.terms("commercial_product", store=store)["scope"]["subject"]["items"]
    assert any(item["id"] == rel["id"] for item in items)
    assert set(rel["derivation"]["inputs"]) <= {item["id"] for item in items}


def test_human_saved_source_context_reads_without_live_rule_or_card(tmp_path):
    result = card()
    view = result.explore().view("predicted_structures")
    assert "Recorded mapping context: the declared focal accession" in repr(view)
    assert "Coverage of original reference input: 1.0" in repr(view)
    (relationship,) = result.relationships("has_predicted_structure")
    source_links = view.items()[0].related().filter("role", equals="source")
    assert any(
        "reference sequence checksums" in item.label for item in source_links.items()
    )
    assert any(
        "reference sequence length" in item.label for item in source_links.items()
    )
    assert {item.open().native_payload["id"] for item in source_links.items()} == set(
        relationship["derivation"]["inputs"]
    )
    target = tmp_path / "model.json"
    receipt = view.save(target)
    script = """
import sys, socket
import sabueso
from sabueso.core.card import Card
from sabueso.core.relationship_store import RelationshipStore
import sabueso.mappings.alphafold_context_v1 as context
def forbidden(*a, **k): raise AssertionError('No live reconstruction/rule')
Card.from_dict = forbidden
Card.predicted_structures = forbidden
RelationshipStore.add = forbidden
context.interpret = forbidden
socket.socket.connect = forbidden
view = sabueso.read_exploration(sys.argv[1], expected_digest=sys.argv[2])
row = view.items()[0].open().native_payload
assert row['qualifiers']['sequence_context']['coverage'] == 1.0
assert row['derivation']['rule'] == 'alphafold_sequence_context@1'
assert 'Coverage of original reference input: 1.0' in repr(view)
print('PASS original context')
"""
    with TemporaryDirectory(prefix="sabueso-model-reader-") as cwd:
        read = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(target.resolve()),
                receipt["bundle_digest"],
            ],
            cwd=cwd,
            text=True,
            capture_output=True,
        )
    assert read.returncode == 0, read.stdout + read.stderr
    assert "PASS original context" in read.stdout
