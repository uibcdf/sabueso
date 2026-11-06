"""Original public native/reference agreement and explicit counterfactual refusals."""

import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.mappings.alphafold_modelcif_reference_v1 import (
    FIELDS,
    KEY,
    RULE,
    bound_context,
    crc64,
    interpret,
    map_modelcif_reference_context,
)
from sabueso.mappings.alphafold_modelcif_v1 import (
    RULE as DECLARATION_RULE,
)
from sabueso.mappings.alphafold_modelcif_v1 import (
    bound_declaration,
    map_modelcif_predictions,
)
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.alphafold_modelcif import (
    FixtureAlphaFoldModelCIFClient,
    get_modelcif_metadata,
)

INPUTS = Path("temp_data/alphafold_archive")
MODEL = INPUTS / "AF-Q8WZ42-F2-model_v6.cif.gz"


def forbidden(*args, **kwargs):
    raise AssertionError("No parser, network or current scientific reconstruction")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def native():
    return get_modelcif_metadata(
        "Q8WZ42",
        client=FixtureAlphaFoldModelCIFClient(MODEL, retrieved_at="2026-11-05"),
    )


@pytest.fixture(scope="module")
def focal():
    raw = json.loads((INPUTS / "uniprot/Q8WZ42.json").read_text())
    mapping = map_protein(raw, "2026-11-05")
    return [row for row in mapping["source_assertions"] if row["field_path"] in FIELDS]


def card_with_context(native, focal):
    mapping = map_modelcif_reference_context(
        native, "Q8WZ42", "2026-11-05", input_assertions=focal
    )
    mapping["source_assertions"] += deepcopy(focal)
    mapping["fields"] = {row["field_path"]: row["asserted_value"] for row in focal}
    mapping["fields"]["identifiers.uniprot"] = "Q8WZ42"
    mapping["field_source_assertions"] = {
        row["field_path"]: [row["id"]] for row in focal
    }
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:Q8WZ42",
    )


def test_real_original_interval_and_independent_source_checksums(native, focal):
    before = deepcopy((native, focal))
    result = interpret(native["record"], "Q8WZ42", focal)
    assert result["rule"] == RULE and result["state"] == "comparable_interval"
    assert result["eligible_for_reference_interval"] is True
    assert result["comparison"]["reference_interval"] == [201, 1600]
    assert result["comparison"]["entity_sequence_interval"] == [1, 1400]
    assert result["comparison"]["model_scope"] == "proper_fragment"
    assert result["comparison"]["interval_sequence_equal"] is True
    assert result["comparison"]["reference_crc64_equal"] is True
    reference = result["reference"]
    assert reference["length"] == 34350
    assert reference["entry_version"] == "223" and reference["sequence_version"] == 4
    assert (
        reference["computed_crc64"] == reference["stated_crc64"] == "DEB216410AD560D9"
    )
    assert (
        reference["computed_md5"]
        == reference["stated_md5"].lower()
        == "0d885c1f78642f0ff70c19706e22dcdb"
    )
    assert reference["checksum_integrity"] is True
    # The Card does not retain the original UniProt update date. Do not replace
    # that missing input with the matching date in a developer fixture/control.
    assert reference["sequence_date"] is None
    assert result["comparison"]["native_reference_sequence_date"] == "2012-04-18"
    assert result["comparison"]["reference_date_equal"] is None
    assert result["coordinate_or_assembly_mapping"] == "not_evaluated"
    assert result["experimental_equivalence"] == "not_evaluated"
    assert (native, focal) == before


def test_crc64_iso_has_known_public_reference_and_fragment_controls():
    entry = json.loads((INPUTS / "uniprot/Q8WZ42.json").read_text())
    sequence = entry["sequence"]["value"]
    assert crc64("") == "0000000000000000"
    assert crc64("ACGT") == "71A87EBDB0000000"
    assert crc64(sequence) == entry["sequence"]["crc64"] == "DEB216410AD560D9"
    assert crc64(sequence[200:1600]) == "884CB15CA14DC54F"


@pytest.mark.parametrize(
    "change,state",
    [
        ("no_inputs", "missing_prerequisite"),
        ("missing_sequence", "missing_prerequisite"),
        ("foreign_source", "missing_prerequisite"),
        ("foreign_record", "missing_prerequisite"),
        ("curated", "missing_prerequisite"),
        ("missing_revision", "missing_prerequisite"),
        ("malformed_metadata", "unsupported"),
        ("invalid_sequence_revision", "unsupported"),
        ("different_revision", "ambiguous"),
        ("different_sequence_revision", "ambiguous"),
        ("alternative", "ambiguous"),
        ("wrong_md5", "unsupported"),
        ("wrong_crc64", "unsupported"),
        ("no_crc64", "missing_prerequisite"),
        ("ambiguous_sequence", "unsupported"),
        ("wrong_length", "unsupported"),
    ],
)
def test_original_focal_inputs_are_required_without_fallback(
    native, focal, change, state
):
    rows = deepcopy(focal)
    by_path = {row["field_path"]: row for row in rows}
    first = rows[0]
    if change == "no_inputs":
        rows = None
    elif change == "missing_sequence":
        rows.remove(by_path["sequence.primary"])
    elif change == "foreign_source":
        first["source"]["name"] = "Other"
    elif change == "foreign_record":
        first["source"]["record_id"] = "P52270"
    elif change == "curated":
        first["acquisition"]["method"] = "curation"
    elif change == "missing_revision":
        first["source"].pop("version")
    elif change == "malformed_metadata":
        first["source_metadata"] = "not a mapping"
    elif change == "invalid_sequence_revision":
        first["source_metadata"]["sequence_version"] = True
    elif change == "different_revision":
        first["source"]["version"] = "224"
    elif change == "different_sequence_revision":
        first["source_metadata"]["sequence_version"] = 5
    elif change == "alternative":
        extra = deepcopy(first)
        extra["id"] += "_counterexample"
        rows.append(extra)
    elif change == "wrong_md5":
        by_path["sequence.checksums"]["asserted_value"]["md5"] = "0" * 32
    elif change == "wrong_crc64":
        by_path["sequence.checksums"]["asserted_value"]["crc64"] = "0" * 16
    elif change == "no_crc64":
        by_path["sequence.checksums"]["asserted_value"].pop("crc64")
    elif change == "ambiguous_sequence":
        seq = by_path["sequence.primary"]["asserted_value"]
        by_path["sequence.primary"]["asserted_value"] = "X" + seq[1:]
    elif change == "wrong_length":
        by_path["sequence.length"]["asserted_value"] -= 1
    result = interpret(native["record"], "Q8WZ42", rows)
    assert result["state"] == state and result["reasons"]
    assert result["eligible_for_reference_interval"] is False


@pytest.mark.parametrize(
    "change,state",
    [
        ("wrong_accession", "unsupported"),
        ("native_crc64", "mismatch"),
        ("missing_native_crc64", "missing_prerequisite"),
        ("isoform", "unsupported"),
        ("quoted_unknown_isoform", "unsupported"),
        ("range_conflict", "unsupported"),
        ("entity_interval", "unsupported"),
        ("position_duplicate", "unsupported"),
        ("modified_monomer", "unsupported"),
        ("heterogeneity", "unsupported"),
        ("entity_key", "unsupported"),
        ("unknown_sequence", "unsupported"),
        ("invalid_layout_token", "unsupported"),
        ("different_sequence", "mismatch"),
        ("additional_reference_start", "unsupported"),
        ("additional_reference_sequence", "unsupported"),
        ("additional_reference_isoform", "unsupported"),
    ],
)
def test_native_scope_refuses_unsupported_and_mismatching_inputs(
    native, focal, change, state
):
    record = deepcopy(native["record"])
    c = record["columns"]
    if change == "wrong_accession":
        c["_ma_target_ref_db_details.db_accession"] = ["P52270"]
    elif change == "additional_reference_start":
        c["_struct_ref.pdbx_align_begin"] = ["200"]
    elif change == "additional_reference_sequence":
        c["_struct_ref.pdbx_seq_one_letter_code"] = ["ACDEFG"]
    elif change == "additional_reference_isoform":
        c["_struct_ref.pdbx_db_isoform"] = ["Q8WZ42-2"]
    elif change == "native_crc64":
        c["_ma_target_ref_db_details.seq_db_sequence_checksum"] = ["0" * 16]
    elif change == "missing_native_crc64":
        c["_ma_target_ref_db_details.seq_db_sequence_checksum"] = ["?"]
    elif change == "isoform":
        c["_ma_target_ref_db_details.seq_db_isoform"] = ["Q8WZ42-2"]
    elif change == "quoted_unknown_isoform":
        c["_ma_target_ref_db_details.seq_db_isoform"] = ["'?' ".strip()]
    elif change == "range_conflict":
        c["_struct_ref_seq.db_align_end"] = ["1599"]
    elif change == "entity_interval":
        c["_struct_ref_seq.seq_align_beg"] = ["2"]
    elif change == "position_duplicate":
        c["_entity_poly_seq.num"][0] = "2"
    elif change == "modified_monomer":
        c["_entity_poly_seq.mon_id"][0] = "MSE"
    elif change == "heterogeneity":
        c["_entity_poly_seq.hetero"][0] = "y"
    elif change == "entity_key":
        c["_entity_poly_seq.entity_id"][0] = "2"
    elif change == "unknown_sequence":
        c["_entity_poly.pdbx_seq_one_letter_code_can"] = ["?"]
    elif change == "invalid_layout_token":
        c["_entity_poly.pdbx_seq_one_letter_code_can"] = ["AC GT"]
    elif change == "different_sequence":
        for tag in (
            "_entity_poly.pdbx_seq_one_letter_code_can",
            "_entity_poly.pdbx_seq_one_letter_code",
        ):
            assert c[tag][0].startswith(";A")
            c[tag][0] = ";G" + c[tag][0][2:]
        c["_entity_poly_seq.mon_id"][0] = "GLY"
    result = interpret(record, "Q8WZ42", focal)
    assert (
        result["state"] == state and result["eligible_for_reference_interval"] is False
    )
    if change in ("native_crc64", "missing_native_crc64"):
        assert result["comparison"]["interval_sequence_equal"] is True
        assert result["comparison"]["reference_crc64_equal"] is (
            False if change == "native_crc64" else None
        )


def test_explicit_entity_keys_not_loop_order_and_hex_case_define_comparison(
    native, focal
):
    record, rows = deepcopy(native["record"]), deepcopy(focal)
    for tag, values in record["columns"].items():
        if tag.startswith("_entity_poly_seq."):
            record["columns"][tag] = list(reversed(values))
    record["columns"]["_ma_target_ref_db_details.seq_db_sequence_checksum"][0] = (
        "deb216410ad560d9"
    )
    assert interpret(record, "Q8WZ42", rows)["eligible_for_reference_interval"] is True
    # Unrelated confidence does not veto exact source sequence correspondence.
    record["columns"]["_ma_qa_metric_global.metric_value"] = ["999"]
    assert interpret(record, "Q8WZ42", rows)["eligible_for_reference_interval"] is True


def test_separate_derivation_preserves_native_assertion_and_declaration(native, focal):
    original = map_modelcif_predictions(native, "Q8WZ42", "2026-11-05")
    mapped = map_modelcif_reference_context(
        native, "Q8WZ42", "2026-11-05", input_assertions=focal
    )
    assert mapped["source_assertions"] == original["source_assertions"]
    (row,) = mapped["relationships"]
    assert (
        row["qualifiers"]["native_modelcif"]
        == original["relationships"][0]["qualifiers"]["native_modelcif"]
    )
    assert row["qualifiers"]["sequence_matches"] is None
    assert {a["derivation"]["rule"] for a in row["derivation_applications"]} == {
        RULE,
        DECLARATION_RULE,
    }
    (native_assertion,) = mapped["source_assertions"]
    assert "model" not in native_assertion["asserted_value"]
    card = card_with_context(native, focal)
    (relationship,) = card.relationships("has_predicted_structure")
    assert (
        bound_declaration(card, relationship)
        == relationship["qualifiers"]["native_modelcif"]
    )
    assert bound_context(card, relationship) == relationship["qualifiers"][KEY]
    assert card.predicted_structures()["items"][0]["coverage"] is None


@pytest.mark.parametrize("full_reference_declaration", [False, True])
def test_explicit_synthetic_whole_reference_and_full_database_sequence(
    native, focal, full_reference_declaration
):
    """Synthetic scope controls; the actual public model remains a fragment."""
    import hashlib

    rows, record = deepcopy(focal), deepcopy(native["record"])
    by_path = {row["field_path"]: row for row in rows}
    original = by_path["sequence.primary"]["asserted_value"]
    fragment = original[200:1600]
    c = record["columns"]
    if full_reference_declaration:
        c["_struct_ref.pdbx_seq_one_letter_code"] = [";" + original + "\n;"]
        result = interpret(record, "Q8WZ42", rows)
        assert result["comparison"]["model_scope"] == "proper_fragment"
    else:
        by_path["sequence.primary"]["asserted_value"] = fragment
        by_path["sequence.length"]["asserted_value"] = len(fragment)
        by_path["sequence.checksums"]["asserted_value"] = {
            "md5": hashlib.md5(fragment.encode(), usedforsecurity=False).hexdigest(),
            "crc64": "884CB15CA14DC54F",
        }
        c["_ma_target_ref_db_details.seq_db_sequence_checksum"] = ["884CB15CA14DC54F"]
        c["_ma_target_ref_db_details.seq_db_align_begin"] = ["1"]
        c["_ma_target_ref_db_details.seq_db_align_end"] = ["1400"]
        c["_struct_ref_seq.db_align_beg"] = ["1"]
        c["_struct_ref_seq.db_align_end"] = ["1400"]
        c["_struct_ref.pdbx_align_begin"] = ["1"]
        c["_struct_ref.pdbx_align_end"] = ["1400"]
        result = interpret(record, "Q8WZ42", rows)
        assert result["comparison"]["model_scope"] == "whole_reference"
    assert result["eligible_for_reference_interval"] is True
    assert (
        result["comparison"]["additional_reference_sequence_scope"] == "whole_reference"
    )


@pytest.mark.parametrize(
    "change",
    [
        "output",
        "source",
        "native_record",
        "revision",
        "missing_source",
        "inputs",
        "application",
        "multiple_models",
        "multiple_applications",
    ],
)
def test_original_binding_refuses_replaced_missing_or_ambiguous_inputs(
    native, focal, change
):
    card = card_with_context(native, focal)
    (relationship,) = card.relationships("has_predicted_structure")
    assert bound_context(card, relationship) is not None
    application = next(
        a
        for a in relationship["derivation_applications"]
        if a["derivation"]["rule"] == RULE
    )
    if change == "output":
        relationship["qualifiers"][KEY]["comparison"]["reference_interval"] = [1, 1400]
    elif change == "source":
        source = card.source_assertion_store.get(focal[0]["id"])
        source["asserted_value"] = "changed"
    elif change == "native_record":
        source = card.source_assertion_store.get(
            relationship["source_assertion_ids"][0]
        )
        record = source["asserted_value"]["modelcif_metadata"]
        record["columns"]["_synthetic_unknown.literal"] = ["changed"]
        record["pairs"].append("_synthetic_unknown.literal")
        assert bound_declaration(card, relationship) is not None
    elif change == "revision":
        card.source_assertion_store.get(focal[0]["id"])["source"]["version"] = "224"
    elif change == "missing_source":
        card.source_assertion_store.store.pop(focal[0]["id"])
    elif change == "inputs":
        application["derivation"]["inputs"] = ["foreign"]
    elif change == "application":
        application["binding"] = "recorded_context"
    elif change == "multiple_models":
        relationship["source_assertion_ids"].append("another_original_model")
    elif change == "multiple_applications":
        relationship["derivation_applications"].append(deepcopy(application))
    assert bound_context(card, relationship) is None


def test_old_metadata_card_does_not_gain_a_context_when_loaded(native):
    old = build_card_from_mapping(
        map_modelcif_predictions(native, "Q8WZ42", "2026-11-05"),
        meta={"entity_type": "protein"},
    )
    original = old.to_dict()
    restored = Card.from_dict(original)
    (row,) = restored.relationships("has_predicted_structure")
    assert KEY not in row["qualifiers"] and bound_context(restored, row) is None
    assert restored.to_dict() == original


def test_real_card_human_targeted_agent_and_inert_saved_context(tmp_path):
    card, _ = sabueso.resolve(
        "Q8WZ42",
        resolver=EntityResolver(FixtureUniProtClient(INPUTS / "uniprot")),
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldModelCIFClient(
            MODEL, retrieved_at="2026-11-05"
        ),
    )
    before = card.to_dict()
    (row,) = card.relationships("has_predicted_structure")
    finding = bound_context(card, row)
    assert finding["eligible_for_reference_interval"] is True
    explorer = card.explore()
    (model,) = explorer.answer("predicted_models").items()
    details = model.open()
    qualifier_item = next(
        item for item in details.items() if item.label == "qualifiers"
    )
    finding_item = next(
        item for item in qualifier_item.open().items() if item.label == KEY
    )
    finding_view = finding_item.open()
    assert finding_view.native_payload == finding
    agent = explorer.access.read(finding_item.payload_location).page()
    assert (
        next(item["value"] for item in agent["items"] if item["key"] == "state")
        == "comparable_interval"
    )
    sources = model.related().filter("role", equals="source")
    assert len(sources.items()) == 4
    for item in sources.items():
        assert item.open().native_payload["source"]["name"] in (
            "AlphaFold DB",
            "UniProt",
        )
    assert not model.related().filter("role", equals="question").items()
    path = tmp_path / "native-context.json.gz"
    finding_view.save(path, compression="gzip")
    assert card.to_dict() == before
    script = """
import builtins,json,socket,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name == 'gemmi' or name.startswith('gemmi.'): raise AssertionError('parser forbidden')
    return original(name,*args,**kwargs)
builtins.__import__=guarded
import sabueso
from sabueso.core.card import Card
import sabueso.mappings.alphafold_modelcif_reference_v1 as reference
def forbidden(*args,**kwargs): raise AssertionError('current interpretation forbidden')
socket.socket.connect=forbidden
socket.create_connection=forbidden
Card.from_dict=forbidden
reference.interpret=forbidden
reference.crc64=forbidden
saved=sabueso.read_exploration(sys.argv[1])
print(json.dumps(saved.native_payload))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == finding


def test_stored_binding_uses_original_sources_not_current_selected_values(
    native, focal
):
    card = card_with_context(native, focal)
    (relationship,) = card.relationships("has_predicted_structure")
    expected = bound_context(card, relationship)
    card.sections["sequence"]["primary"]["value"] = "another_selected_sequence"
    assert bound_context(card, relationship) == expected
    # A future scientific request must separately bind the current selection;
    # this retained finding makes only an original-input interval claim.
