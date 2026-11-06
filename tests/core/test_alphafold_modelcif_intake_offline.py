"""Original public ModelCIF intake, literal navigation and explicit API boundary.

The actual archive member is retained unchanged. Mutated documents below are
labelled counterexamples, never new provider assertions or coordinate evidence.
"""

import gzip
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, ConnectorError, LibraryNotFoundError
from sabueso.mappings.alphafold_modelcif_v1 import (
    KIND,
    RULE,
    bound_declaration,
    declaration,
    extract_metadata,
    map_modelcif_predictions,
)
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.alphafold import get_prediction
from sabueso.tools.db.alphafold_modelcif import (
    FixtureAlphaFoldModelCIFClient,
    SnapshotAlphaFoldModelCIFClient,
    get_modelcif_metadata,
)

INPUTS = Path("temp_data/alphafold_archive")
MODEL = INPUTS / "AF-Q8WZ42-F2-model_v6.cif.gz"
SHA = "74da31b7a0153ef2c90dc8f60fe07edaa83ba50049bf06e6f4eb113ece1963ef"


def forbidden(*args, **kwargs):
    raise AssertionError("No source access, current interpretation or Card rebuilding")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def native():
    return get_modelcif_metadata(
        "Q8WZ42",
        client=FixtureAlphaFoldModelCIFClient(
            MODEL,
            retrieved_at="2026-11-05",
            expected_sha256=SHA,
        ),
    )


def test_original_file_identity_complete_metadata_and_native_scope(native):
    receipt = native["snapshot_receipt"]
    assert receipt["document_sha256"] == SHA
    assert (
        receipt["decoded_sha256"]
        == "206ffc9821eaa76a33f7f3afe1b42f5ffd1eeae5b411c299cf8ae910f9964036"
    )
    assert receipt["encoded_bytes"] == 269404 and receipt["decoded_bytes"] == 1298513
    assert receipt["digest_verification"] == "matched_caller_digest"
    assert receipt["source_access_observed"] is False
    record = native["record"]
    assert len(record["columns"]) == 210
    assert not any(tag.lower().startswith("_atom_site.") for tag in record["columns"])
    assert native["native_extraction"]["excluded_coordinate_tables"][0]["rows"] > 10000
    # The independent older projection decodes CIF quoting; this intake retains
    # the original quoting too. Compare decoded values, preserving unknowns.
    import gemmi

    golden = json.loads((INPUTS / "modelcif_metadata.json").read_text())["native_tags"]
    for tag, values in golden.items():
        assert [
            gemmi.cif.as_string(v) if v.startswith(("'", '"', ";")) else v
            for v in record["columns"][tag]
        ] == values
    projected = declaration(record, "Q8WZ42")
    assert projected["rule"] == RULE
    assert projected["identity_basis"] == "explicit_native_UNP_reference_row"
    assert projected["reference_range"] == [201, 1600]
    assert projected["model_sequence_range"] == [1, 1400]
    assert projected["reference_crc64"] == "DEB216410AD560D9"
    assert projected["reference_sequence_version_date"] == "2012-04-18"
    assert projected["isoform_source_token"] == "?"
    assert projected["model_version"] is None
    assert projected["tool"] == "AlphaFold v2.0"
    assert projected["mean_plddt"] == 54.59
    assert projected["canonical_correspondence"] == "not_evaluated"
    assert projected["state"] == "source_declared"
    (event,) = native["acquisition_trace"]["records"]
    assert event["outcome"] == "received" and event["operation"] == KIND
    assert (
        event["access"] == "supplied_file" and event["source_version"]["value"] is None
    )
    assert (
        "native_citation_columns_not_normalized;referenced_publications_not_queried"
        in event["bibliography_gaps"]
    )
    assert (
        "model_specific_method_and_provider_citations_not_returned"
        not in event["bibliography_gaps"]
    )


@pytest.mark.parametrize("compressed", [False, True])
def test_plain_and_gzip_renamed_files_keep_native_identity(
    tmp_path, native, compressed
):
    raw = gzip.decompress(MODEL.read_bytes())
    # Unknown native columns and quoted null-looking tokens must also survive.
    raw += b"\n_sabueso_counterexample.unknown '?'\n_sabueso_counterexample.absent ?\n"
    path = tmp_path / "AF-WRONG-F99-model_v999.unrelated"
    path.write_bytes(gzip.compress(raw) if compressed else raw)
    result = get_modelcif_metadata(
        "Q8WZ42", client=FixtureAlphaFoldModelCIFClient(path)
    )
    assert declaration(result["record"], "Q8WZ42")["model_id"] == "AF-Q8WZ42-F2"
    assert result["record"]["columns"]["_sabueso_counterexample.unknown"] == [
        "'?' ".strip()
    ]
    assert result["record"]["columns"]["_sabueso_counterexample.absent"] == ["?"]
    assert (
        result["record"]["columns"]["_entity_poly.pdbx_seq_one_letter_code_can"]
        == native["record"]["columns"]["_entity_poly.pdbx_seq_one_letter_code_can"]
    )


@pytest.mark.parametrize(
    "change",
    [
        {"source": "Other"},
        {"kind": "prediction"},
        {"query": {"accession": "P52270"}},
        {"version": "v6"},
    ],
)
def test_binding_precedes_file_access(tmp_path, monkeypatch, change):
    client = SnapshotAlphaFoldModelCIFClient(
        tmp_path / "absent",
        source_metadata={
            "source": "AlphaFold DB",
            "kind": KIND,
            "query": {"accession": "Q8WZ42"},
            **change,
        },
    )
    module = importlib.import_module("sabueso.tools.db.alphafold_modelcif")
    monkeypatch.setattr(module, "_load", forbidden)
    with pytest.raises(ConnectorError, match="no file was read"):
        get_modelcif_metadata("Q8WZ42", client=client, skip_digestion=True)


def test_no_native_api_or_implicit_online_fallback(monkeypatch):
    client = FixtureAlphaFoldModelCIFClient(MODEL)
    monkeypatch.setattr(client, "prediction", forbidden)
    with pytest.raises(ArgumentError, match="get_modelcif_metadata"):
        get_prediction("Q8WZ42", client=client, skip_digestion=True)
    with pytest.raises(ArgumentError, match="explicit"):
        get_modelcif_metadata("Q8WZ42", skip_digestion=True)
    with pytest.raises(ArgumentError, match="explicit"):
        get_modelcif_metadata("Q8WZ42", client=object(), skip_digestion=True)


@pytest.mark.parametrize(
    "argument,limit",
    [
        ("max_encoded_bytes", 269403),
        ("max_decoded_bytes", 1298512),
    ],
)
def test_limits_refuse_visibly_and_explicit_overrides_work(argument, limit):
    with pytest.raises(ArgumentError, match="No partial metadata"):
        get_modelcif_metadata(
            "Q8WZ42", client=FixtureAlphaFoldModelCIFClient(MODEL, **{argument: limit})
        )
    result = get_modelcif_metadata(
        "Q8WZ42", client=FixtureAlphaFoldModelCIFClient(MODEL, **{argument: None})
    )
    assert len(result["record"]["columns"]) == 210


@pytest.mark.parametrize(
    "argument,value",
    [
        ("max_encoded_bytes", True),
        ("max_decoded_bytes", 0),
        ("max_decoded_bytes", -1),
        ("expected_sha256", "bad"),
    ],
)
def test_invalid_native_options_are_rejected(argument, value):
    with pytest.raises(ArgumentError):
        FixtureAlphaFoldModelCIFClient(MODEL, **{argument: value})


def test_missing_digest_and_corrupt_native_inputs_are_not_scientific_absence(tmp_path):
    with pytest.raises(ConnectorError, match="unavailable"):
        get_modelcif_metadata(
            "Q8WZ42", client=FixtureAlphaFoldModelCIFClient(tmp_path / "missing")
        )
    with pytest.raises(ConnectorError, match="SHA-256"):
        get_modelcif_metadata(
            "Q8WZ42",
            client=FixtureAlphaFoldModelCIFClient(MODEL, expected_sha256="0" * 64),
        )
    path = tmp_path / "truncated.gz"
    path.write_bytes(MODEL.read_bytes()[:-8])
    with pytest.raises(ConnectorError, match="Unreadable"):
        get_modelcif_metadata("Q8WZ42", client=FixtureAlphaFoldModelCIFClient(path))


@pytest.mark.parametrize(
    "suffix",
    [
        "\ndata_other\n_x.y z\n",
        "\nloop_\n_late.a\n_late.b\none\n",
        "\n_ENTRY.ID repeated\n",
        "\nsave_other\n_x.y z\nsave_\n",
    ],
)
def test_whole_document_is_validated_before_metadata_is_returned(suffix):
    text = gzip.decompress(MODEL.read_bytes()).decode() + suffix
    with pytest.raises(ConnectorError):
        extract_metadata(text)


@pytest.mark.parametrize(
    "tag,values",
    [
        ("_ma_target_ref_db_details.db_accession", ["P52270"]),
        ("_ma_target_ref_db_details.target_entity_id", ["2"]),
        ("_struct_ref_seq.ref_id", ["nonexistent"]),
        ("_struct_ref_seq.db_align_end", ["not-an-integer"]),
    ],
)
def test_native_identity_and_all_alignment_rows_are_checked(native, tag, values):
    record = deepcopy(native["record"])
    record["columns"][tag] = values
    with pytest.raises(ConnectorError):
        declaration(record, "Q8WZ42")


def test_conflicting_native_declarations_are_retained_without_selecting(native):
    record = deepcopy(native["record"])
    record["columns"]["_struct_ref_seq.db_align_end"] = ["1599"]
    result = declaration(record, "Q8WZ42")
    assert result["state"] == "unresolved_native_declarations"
    assert result["reference_range"] == [None, None]
    assert record["columns"]["_ma_target_ref_db_details.seq_db_align_end"] == ["1600"]
    assert record["columns"]["_struct_ref_seq.db_align_end"] == ["1599"]


def build_native_card():
    card, _ = sabueso.resolve(
        "Q8WZ42",
        resolver=EntityResolver(FixtureUniProtClient(INPUTS / "uniprot")),
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldModelCIFClient(
            MODEL, retrieved_at="2026-11-05", expected_sha256=SHA
        ),
    )
    return card


def test_real_native_card_human_agent_source_and_inert_saved_reading(tmp_path, native):
    card = build_native_card()
    before = card.to_dict()
    (relationship,) = card.relationships("has_predicted_structure")
    projected = bound_declaration(card, relationship)
    assert projected == declaration(native["record"], "Q8WZ42")
    assertion = card.source_assertion_store.get(relationship["source_assertion_ids"][0])
    assert assertion["asserted_value"]["modelcif_metadata"] == native["record"]
    assert "model" not in assertion["asserted_value"]
    assert assertion["source"].get("version") is None
    q = relationship["qualifiers"]
    assert q["sequence_matches"] is None and q["isoform"] is None
    explorer = card.explore()
    (item,) = explorer.answer("predicted_models").items()
    assert "AF-Q8WZ42-F2" in item.label
    links = item.related()
    (question,) = links.filter("role", equals="question").items()
    assert (
        question._entry.value["model_context"]["rule"]
        == "native_model_structure_request@1"
    )
    assert links.filter("role", equals="source").items()
    sources = links.filter("role", equals="source")
    source = sources.items()[0].open()
    assert (
        source.native_payload["asserted_value"]["modelcif_metadata"] == native["record"]
    )
    assert source.back() is sources
    detail = item.open()
    assert detail.native_payload["qualifiers"]["native_modelcif"] == projected
    assert detail.context["adapter"] == "literal_human@1"
    # The agent can address the same exact retained native value without reading
    # the complete Card or any coordinate table.
    (declaration_item,) = [
        entry for entry in detail.items() if entry.label == "qualifiers"
    ]
    qualifier_view = declaration_item.open()
    (native_item,) = [
        entry for entry in qualifier_view.items() if entry.label == "native_modelcif"
    ]
    agent = explorer.access.read(native_item.payload_location).page(max_bytes=65536)
    received = {}
    for entry in agent["items"]:
        key = entry["key"]
        received[key] = (
            [
                child["value"]
                for child in explorer.access.read(entry["location"]).page()["items"]
            ]
            if isinstance(projected[key], list)
            else entry["value"]
        )
    assert received == projected
    (native_row,) = card.predicted_structures()["items"]
    assert native_row["coverage"] is None and native_row["sequence_matches"] is None
    assert native_row["context_state"] == "original_basis_not_established"
    assert card.to_dict() == before
    path = tmp_path / "native.json.gz"
    detail.save(path, compression="gzip")
    expected = detail.native_payload
    # Separate process: neither Gemmi, current native projection, Card factories
    # nor network can participate in reading this original saved capture.
    script = """
import builtins,json,socket,sys
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if name == "gemmi" or name.startswith("gemmi."): raise AssertionError("parser forbidden")
    return original(name,*args,**kwargs)
builtins.__import__=guarded
import sabueso
from sabueso.core.card import Card
import sabueso.mappings.alphafold_modelcif_v1 as native
def forbidden(*args,**kwargs): raise AssertionError("current interpretation forbidden")
socket.socket.connect=forbidden
socket.create_connection=forbidden
Card.from_dict=forbidden
native.declaration=forbidden
native.extract_metadata=forbidden
saved=sabueso.read_exploration(sys.argv[1])
print(json.dumps(saved.native_payload))
"""
    read = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(read.stdout) == expected
    restored = Card.from_dict(before)
    assert restored.to_dict() == before
    assert (
        bound_declaration(
            restored, restored.relationships("has_predicted_structure")[0]
        )
        == projected
    )


@pytest.mark.parametrize("change", ["range", "native", "original", "version"])
def test_native_binding_refuses_changed_original_or_output(native, change):
    from sabueso.core.aggregator import build_card_from_mapping

    mapping = map_modelcif_predictions(native, "Q8WZ42", "2026-11-05")
    card = build_card_from_mapping(mapping, meta={"entity_type": "protein"})
    (row,) = card.relationships("has_predicted_structure")
    assert bound_declaration(card, row) is not None
    if change == "range":
        row["qualifiers"]["range"] = [1, 1400]
    elif change == "native":
        row["qualifiers"]["native_modelcif"] = None
    elif change == "version":
        row["qualifiers"]["model_version"] = 6
    else:
        statement = card.source_assertion_store.get(row["source_assertion_ids"][0])
        statement["asserted_value"]["modelcif_metadata"]["columns"][
            "_struct_ref_seq.db_align_end"
        ] = ["1599"]
    assert bound_declaration(card, row) is None


def test_gemmi_is_requested_only_for_explicit_file_parsing(monkeypatch, native):
    mapping = importlib.import_module("sabueso.mappings.alphafold_modelcif_v1")
    monkeypatch.setattr(mapping, "_gemmi", forbidden)
    assert map_modelcif_predictions(native, "Q8WZ42", "2026-11-05")["relationships"]
    assert get_prediction(
        "P52270",
        client=importlib.import_module(
            "sabueso.tools.db.alphafold"
        ).FixtureAlphaFoldClient("temp_data"),
    )["record"]
    with pytest.raises(AssertionError, match="No source"):
        get_modelcif_metadata("Q8WZ42", client=FixtureAlphaFoldModelCIFClient(MODEL))


def test_missing_gemmi_uses_the_depdigest_diagnostic(monkeypatch):
    from depdigest.core import checker

    real = checker.is_installed
    monkeypatch.setattr(
        checker, "is_installed", lambda name: False if name == "gemmi" else real(name)
    )
    with pytest.raises(LibraryNotFoundError) as error:
        get_modelcif_metadata("Q8WZ42", client=FixtureAlphaFoldModelCIFClient(MODEL))
    assert error.value.code == "SABUESO-E-LIBRARY-001"
    assert "gemmi" in str(error.value)


@pytest.mark.parametrize(
    "category,reason",
    [
        ("_ma_target_ref_db_details.", "multiple_native_reference_rows_unselected"),
        ("_software.", "multiple_native_software_rows_unselected"),
        ("_ma_qa_metric_global.", "multiple_native_global_plddt_rows_unselected"),
    ],
)
def test_multiple_source_rows_remain_literal_and_unselected(native, category, reason):
    record = deepcopy(native["record"])
    columns = record["columns"]
    tags = [tag for tag in columns if tag.startswith(category)]
    # Explicit synthetic additional row; convert an original scalar category to
    # a loop rather than creating an impossible literal membership description.
    if all(tag in record["pairs"] for tag in tags):
        record["pairs"] = [tag for tag in record["pairs"] if tag not in tags]
        record["loops"].append(tags)
    for tag in tags:
        columns[tag].append(columns[tag][0])
    result = declaration(record, "Q8WZ42")
    assert result["state"] == "unresolved_native_declarations"
    assert reason in result["reasons"]
    if category == "_ma_target_ref_db_details.":
        assert result["reference_range"] == [None, None]
    elif category == "_software.":
        assert result["tool"] is None
    else:
        assert result["mean_plddt"] is None


def test_independent_native_loops_are_not_joined_by_row_number(native):
    record = deepcopy(native["record"])
    software = next(tags for tags in record["loops"] if "_software.name" in tags)
    record["loops"].remove(software)
    record["loops"].extend([software[:1], software[1:]])
    with pytest.raises(ConnectorError, match="independent loops"):
        declaration(record, "Q8WZ42")


def test_missing_native_file_keeps_card_knowledge_unavailable(tmp_path):
    from sabueso._private.smonitor.warnings import EnrichmentFailedWarning

    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve(
            "Q8WZ42",
            resolver=EntityResolver(FixtureUniProtClient(INPUTS / "uniprot")),
            predicted_structures=True,
            alphafold_client=FixtureAlphaFoldModelCIFClient(
                tmp_path / "unavailable.cif"
            ),
        )
    assert not card.relationships("has_predicted_structure")
    row = next(
        row for row in card.knowledge_state()["rows"] if row["source"] == "AlphaFold DB"
    )
    assert row["state"] == "unavailable" and row["count"] is None
