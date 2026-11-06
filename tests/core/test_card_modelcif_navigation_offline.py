"""Genuine native/reference questions, selected-source guards and inert history."""

import gzip
import hashlib
import importlib
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
from sabueso.core.card_context_navigation import _link_view
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.card_exploration_verification_v12 import _verify_links
from sabueso.core.card_modelcif_regions_v1 import (
    FORMAT,
    NAVIGATION_RULE,
    RULE,
    VERIFIER,
)
from sabueso.core.errors import StorageError
from sabueso.core.snapshot import canonical_json, digest
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.alphafold import map_predictions
from sabueso.mappings.alphafold_modelcif_reference_v1 import (
    FIELDS,
    map_modelcif_reference_context,
)
from sabueso.mappings.uniprot import map_protein
from sabueso.tools.db.alphafold_modelcif import (
    FixtureAlphaFoldModelCIFClient,
    get_modelcif_metadata,
)

INPUTS = Path("temp_data/alphafold_archive")


def forbidden(*args, **kwargs):
    raise AssertionError("No network, current mapper, parser or Card reconstruction")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module")
def original():
    raw = json.loads((INPUTS / "uniprot/Q8WZ42.json").read_text())
    focal = map_protein(raw, "2026-11-05")
    fields = {*FIELDS, "identifiers.uniprot"}
    sources = [r for r in focal["source_assertions"] if r["field_path"] in fields]
    native = get_modelcif_metadata(
        "Q8WZ42",
        client=FixtureAlphaFoldModelCIFClient(
            INPUTS / "AF-Q8WZ42-F2-model_v6.cif.gz", retrieved_at="2026-11-05"
        ),
    )
    mapping = map_modelcif_reference_context(
        native, "Q8WZ42", "2026-11-05", input_assertions=sources
    )
    mapping["source_assertions"] += deepcopy(sources)
    mapping["fields"] = {r["field_path"]: r["asserted_value"] for r in sources}
    mapping["field_source_assertions"] = {r["field_path"]: [r["id"]] for r in sources}
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:Q8WZ42",
    ).to_dict()


def question(card):
    return (
        card.explore()
        .answer("predicted_models")
        .items()[0]
        .related()
        .filter("role", equals="question")
        .items()[0]
    )


def inert(monkeypatch):
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name in ("alphafold_modelcif_v1", "alphafold_modelcif_reference_v1"):
        module = importlib.import_module("sabueso.mappings." + name)
        for attr in (
            "interpret",
            "declaration",
            "bound_context",
            "crc64",
            "extract_metadata",
        ):
            if hasattr(module, attr):
                monkeypatch.setattr(module, attr, forbidden)
    module = importlib.import_module("sabueso.core.card_protein_exploration")
    monkeypatch.setattr(module, "region_request", forbidden)


def test_real_native_interval_has_human_agent_source_and_back_parity(original):
    card = Card.from_dict(original)
    before = card.to_dict()
    link = question(card)
    basis = link._entry.value["model_context"]
    assert basis["rule"] == RULE and basis["state"] == "ready"
    assert basis["original_model_context"]["comparison"]["reference_date_equal"] is None
    assert (
        basis["original_model_context"]["comparison"]["reference_crc64_equal"] is True
    )
    assert basis["request"]["options"] == {
        "sequence_ref": "uniprot:Q8WZ42",
        "region": [[201, 1600]],
        "include_fragments": True,
    }
    answer = link.open()
    agent = link._view.explorer.access.select(
        "structures",
        fields=["structure_ref"],
        options={
            key: value
            for key, value in basis["request"]["options"].items()
            if key != "sequence_ref"
        },
    )
    assert answer.result_ref == agent.result_ref
    assert answer.back() is link.back()
    assert "date agreement remains unknown" in str(answer)
    assert "experimental equivalence" in answer._repr_html_()
    assert "native model's reference interval" in str(link.back())
    sources = link.back().back().filter("role", equals="source").items()
    assert len(sources) == 5
    assert {s.open().native_payload["source"]["name"] for s in sources} == {
        "UniProt",
        "AlphaFold DB",
    }
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change",
    [
        "sequence",
        "length",
        "checksums",
        "selection",
        "replacement_sequence",
        "replacement_length",
        "replacement_checksums",
        "foreign_subject",
        "missing_source",
        "missing_application",
        "duplicate_application",
        "conflict",
        "native_metadata",
        "missing_finding",
    ],
)
def test_changed_selected_or_original_context_refuses_a_prepared_question(
    original, change
):
    card = Card.from_dict(original)
    row = card.relationships("has_predicted_structure")[0]
    if change in ("sequence", "length", "checksums"):
        field = {
            "sequence": "sequence.primary",
            "length": "sequence.length",
            "checksums": "sequence.checksums",
        }[change]
        card.get(field)["value"] = (
            "A"
            if change == "sequence"
            else 100
            if change == "length"
            else {"md5": "0" * 32}
        )
    elif change == "selection":
        card.get("sequence.checksums")["source_assertion_ids"] = []
    elif change.startswith("replacement_"):
        field = {
            "replacement_sequence": "sequence.primary",
            "replacement_length": "sequence.length",
            "replacement_checksums": "sequence.checksums",
        }[change]
        node = card.get(field)
        replacement = make_source_assertion(
            field,
            deepcopy(node["value"]),
            "UniProt",
            "Q8WZ42",
            "synthetic-new-selection",
            subject_ref="uniprot:Q8WZ42",
        )
        # Deliberately distinct claimed ID with an equal value: exercise the
        # exact-selection guard, without asserting a genuine provider observation.
        replacement["id"] += "_synthetic_alternative"
        card.source_assertion_store.add(replacement)
        node["source_assertion_ids"] = [replacement["id"]]
    elif change == "foreign_subject":
        row["subject_ref"] = "uniprot:P52270"
    elif change == "missing_source":
        row["source_assertion_ids"] = []
    elif change in ("missing_application", "duplicate_application"):
        apps = row["derivation_applications"]
        target = next(
            a
            for a in apps
            if a["derivation"]["rule"] == "alphafold_modelcif_reference_context@1"
        )
        apps.remove(target) if change == "missing_application" else apps.append(
            deepcopy(target)
        )
    elif change == "conflict":
        row["qualifier_conflicts"] = {
            "native_reference_context": [{"value": "another"}]
        }
    elif change == "native_metadata":
        source = card.source_assertion_store.get(row["source_assertion_ids"][0])
        source["asserted_value"]["modelcif_metadata"]["columns"][
            "_audit_conform.dict_name"
        ] = ["counterfactual"]
    elif change == "missing_finding":
        row["qualifiers"].pop("native_reference_context")
    if change == "foreign_subject":
        explorer = card.explore()
        assert not explorer.answer("predicted_models").items()
        link = (
            explorer._inspect(explorer._location("relationship_store"))
            .items()[0]
            .related()
            .filter("role", equals="question")
            .items()[0]
        )
    else:
        link = question(card)
    basis = link._entry.value["model_context"]
    assert basis["state"] != "ready" and basis["request"] is None
    assert link.open().outcome["status"] != "ok"


@pytest.mark.parametrize("visited", [False, True])
def test_native_saved_reading_is_independent_and_never_runs_unvisited_question(
    original, visited, tmp_path, monkeypatch
):
    link = question(Card.from_dict(original))
    expected = link.open() if visited else None
    path = tmp_path / "native.json.gz"
    link.back().save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == VERIFIER
    opened = saved.filter("role", equals="question").items()[0].open()
    if visited:
        assert opened.native_payload == expected.native_payload
        assert opened.result_ref == expected.result_ref
    else:
        assert opened.outcome["status"] == "not_saved"
    second = tmp_path / "again.json.gz"
    saved.save(second)
    assert sabueso.read_exploration(second).native_payload == saved.native_payload


@pytest.mark.parametrize(
    "change",
    ["interval", "fragments", "sequence_ref", "original_date", "original_checksum"],
)
def test_resealed_question_cannot_change_its_original_request_or_finding(
    original, change, tmp_path
):
    path = tmp_path / "native.json"
    question(Card.from_dict(original)).open().save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["format"] == FORMAT
    changed = False
    for obj in bundle["objects"].values():
        if isinstance(obj, dict) and obj.get("rule") == NAVIGATION_RULE:
            for link in obj.get("links", []):
                if link["role"] != "question":
                    continue
                context = link["model_context"]
                if change == "interval":
                    context["request"]["options"]["region"] = [[1, 1600]]
                elif change == "fragments":
                    context["request"]["options"]["include_fragments"] = False
                elif change == "sequence_ref":
                    context["request"]["options"]["sequence_ref"] = "uniprot:P52270"
                elif change == "original_date":
                    context["original_model_context"]["comparison"][
                        "reference_date_equal"
                    ] = True
                else:
                    context["original_model_context"]["reference"]["computed_crc64"] = (
                        "0" * 16
                    )
                changed = True
    assert changed
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize(
    "change", ["interval", "fragments", "date", "atoms", "support"]
)
def test_fresh_metadata_identity_still_requires_original_native_science(
    original, change
):
    links = question(Card.from_dict(original)).back()
    payload = links.native_payload
    forged = deepcopy(payload["links"])
    target = next(row for row in forged if row["role"] == "question")
    if change == "interval":
        target["model_context"]["request"]["options"]["region"] = [[1, 1600]]
    elif change == "fragments":
        target["model_context"]["request"]["options"]["include_fragments"] = False
    elif change == "date":
        target["model_context"]["original_model_context"]["comparison"][
            "reference_date_equal"
        ] = True
    elif change == "atoms":
        target["model_context"]["original_model_context"][
            "coordinate_or_assembly_mapping"
        ] = "established"
    else:
        target["support"] = []
    view = _link_view(
        links.explorer,
        forged,
        links.back(),
        "Forged native context",
        source_location=payload["source_location"],
        rule=NAVIGATION_RULE,
    )
    assert view.result_ref != links.result_ref
    with pytest.raises(StorageError, match="original source/axis basis"):
        _verify_links(view)


def test_new_process_reads_native_question_without_parser_or_current_mappers(
    original, tmp_path
):
    path = tmp_path / "native.json.gz"
    expected = question(Card.from_dict(original)).open()
    expected.save(path)
    script = """
import builtins, socket, sys
import sabueso
def forbidden(*a, **k): raise AssertionError('No current parser, source or reconstruction')
socket.socket.connect = forbidden
socket.create_connection = forbidden
original_import = builtins.__import__
def guarded(name, *a, **k):
    if name == 'gemmi' or name.startswith('sabueso.mappings.alphafold_modelcif'):
        forbidden()
    return original_import(name, *a, **k)
builtins.__import__ = guarded
from sabueso.core.card import Card
Card.from_dict = forbidden
saved = sabueso.read_exploration(sys.argv[1])
assert saved.validation['verifier'] == 'native_model_navigation_binding@1'
links = saved.explorer.answer('predicted_models').items()[0].related()
question = links.filter('role', equals='question').items()[0]
assert question.open().result_ref == saved.result_ref
print(saved.result_ref)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(path.resolve())],
        text=True,
        capture_output=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert expected.result_ref in result.stdout


def test_explicit_synthetic_whole_native_scope_excludes_experimental_fragments(
    original,
):
    """Counterfactual native/reference scope; the genuine public model is partial."""
    sources = deepcopy(original["source_assertion_store"])
    focal = [
        row for row in sources if row["field_path"] in {*FIELDS, "identifiers.uniprot"}
    ]
    by_path = {row["field_path"]: row for row in focal}
    fragment = by_path["sequence.primary"]["asserted_value"][200:1600]
    by_path["sequence.primary"]["asserted_value"] = fragment
    by_path["sequence.length"]["asserted_value"] = 1400
    by_path["sequence.checksums"]["asserted_value"] = {
        "md5": hashlib.md5(fragment.encode(), usedforsecurity=False).hexdigest(),
        "crc64": "884CB15CA14DC54F",
    }
    source = next(
        row
        for row in sources
        if row["field_path"] == "relationships.has_predicted_structure"
    )
    record = deepcopy(source["asserted_value"]["modelcif_metadata"])
    columns = record["columns"]
    columns["_ma_target_ref_db_details.seq_db_sequence_checksum"] = ["884CB15CA14DC54F"]
    for key in (
        "_ma_target_ref_db_details.seq_db_align_begin",
        "_struct_ref_seq.db_align_beg",
        "_struct_ref.pdbx_align_begin",
    ):
        columns[key] = ["1"]
    for key in (
        "_ma_target_ref_db_details.seq_db_align_end",
        "_struct_ref_seq.db_align_end",
        "_struct_ref.pdbx_align_end",
    ):
        columns[key] = ["1400"]
    response = {
        "source": "AlphaFold DB",
        "kind": "modelcif_prediction",
        "query": {"accession": "Q8WZ42"},
        "version": None,
        "native_format": "alphafold_modelcif_metadata@1",
        "record": record,
        "native_extraction": {
            "format": "alphafold_modelcif_metadata@1",
            "metadata_sha256": digest(canonical_json(record)),
        },
    }
    mapping = map_modelcif_reference_context(
        response, "Q8WZ42", "synthetic-whole-scope", input_assertions=focal
    )
    mapping["source_assertions"] += focal
    mapping["fields"] = {r["field_path"]: r["asserted_value"] for r in focal}
    mapping["field_source_assertions"] = {r["field_path"]: [r["id"]] for r in focal}
    card = build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:Q8WZ42",
    )
    basis = question(card)._entry.value["model_context"]
    assert basis["state"] == "ready"
    assert (
        basis["original_model_context"]["comparison"]["model_scope"]
        == "whole_reference"
    )
    assert basis["request"]["options"] == {
        "sequence_ref": "uniprot:Q8WZ42",
        "region": [[1, 1400]],
        "include_fragments": False,
    }


def test_mixed_native_and_synthetic_api_questions_keep_separate_original_policies(
    original, tmp_path, monkeypatch
):
    """An explicitly synthetic API whole model coexists with genuine native metadata."""
    card = Card.from_dict(original)
    mapping = map_predictions(
        {
            "record": [
                {
                    "entryId": "AF-SYNTHETIC-Q8WZ42-F1",
                    "uniprotAccession": "Q8WZ42",
                    "uniprotStart": 1,
                    "uniprotEnd": 34350,
                    "sequenceChecksum": card.get("sequence.checksums")["value"]["md5"],
                }
            ]
        },
        "Q8WZ42",
        "synthetic-api-whole",
        input_assertions=card.source_assertion_store.to_list(),
    )
    for row in mapping["source_assertions"]:
        card.source_assertion_store.add(row)
    for row in mapping["relationships"]:
        card.relationship_store.add(row)
    explorer = card.explore()
    items = explorer.answer("predicted_models").items()
    assert len(items) == 2
    questions = [
        item.related().filter("role", equals="question").items()[0] for item in items
    ]
    expected = [item.open().result_ref for item in questions]
    assert {item._entry.value["model_context"]["rule"] for item in questions} == {
        RULE,
        "model_structure_request@1",
    }
    path = tmp_path / "mixed.json.gz"
    questions[0].open().save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == VERIFIER
    actual = [
        item.related().filter("role", equals="question").items()[0].open().result_ref
        for item in saved.explorer.answer("predicted_models").items()
    ]
    assert actual == expected


def test_mixed_nonpolymer_assembly_and_foreign_native_context_keep_their_scopes(
    original, tmp_path, monkeypatch
):
    """Synthetic session composition; no correspondence between the two proteins."""
    capsule = Path(__file__).parent / "data/assembly_nonpolymer_live_v2.json.gz"
    existing = json.loads(gzip.decompress(capsule.read_bytes()))
    card = Card.from_dict(existing["cases"]["2V5B"]["card"])
    for source in original["source_assertion_store"]:
        card.source_assertion_store.add(deepcopy(source))
    (native,) = original["relationship_store"]
    card.relationship_store.add(deepcopy(native))
    explorer = card.explore()
    literal = explorer._inspect(explorer._location("relationship_store"))
    item = next(
        row for row in literal.items() if row._entry.value["id"] == native["id"]
    )
    link = item.related().filter("role", equals="question").items()[0]
    assert link._entry.value["model_context"]["state"] != "ready"
    assert link.open().outcome["status"] != "ok"
    options = {
        "structure_ref": "pdb:2V5B",
        "generation_rule": "rcsb_assembly_generation@5",
    }
    assembly = explorer.answer("assembly_generation", options=options)
    assert assembly.items()
    path = tmp_path / "mixed-assembly.json.gz"
    assembly.save(path)
    inert(monkeypatch)
    for name in ("assembly_generation_v4", "assembly_generation_v5"):
        monkeypatch.setattr(
            importlib.import_module("sabueso.core." + name), "generation", forbidden
        )
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == VERIFIER
    assert saved.native_payload == assembly.native_payload
    assert (
        saved.explorer.answer("assembly_generation", options=options).result_ref
        == assembly.result_ref
    )
