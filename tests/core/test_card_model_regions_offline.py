"""Model questions retain original reference scope, support and inert history."""

import hashlib
import importlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import StorageError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.alphafold import map_predictions


def forbidden(*a, **k):
    raise AssertionError("No acquisition, current model interpretation or recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def synthetic(
    *, begin=1, end=100, accession="P52270", checksum=None, entry="AF-SYNTHETIC-F1"
):
    sequence = "M" * 100
    digest = hashlib.md5(sequence.encode(), usedforsecurity=False).hexdigest()
    fields = {
        "identifiers.uniprot": "P52270",
        "sequence.primary": sequence,
        "sequence.length": 100,
        "sequence.checksums": {"md5": digest},
    }
    originals = [
        make_source_assertion(
            path, value, "UniProt", "P52270", "synthetic", subject_ref="uniprot:P52270"
        )
        for path, value in fields.items()
    ]
    model = {
        "entryId": entry,
        "uniprotAccession": accession,
        "sequenceChecksum": digest if checksum is None else checksum,
        "uniprotStart": begin,
        "uniprotEnd": end,
        "latestVersion": 6,
    }
    mapping = map_predictions(
        {"record": [model]}, "P52270", "synthetic", digest, input_assertions=originals
    )
    mapping["source_assertions"] += originals
    mapping["fields"] = fields
    mapping["field_source_assertions"] = {
        path: [row["id"] for row in originals if row["field_path"] == path]
        for path in fields
    }
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    )


def question(card):
    item = card.explore().answer("predicted_models").items()[0]
    return item.related().filter("role", equals="question").items()[0]


def inert(monkeypatch):
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.mappings.alphafold_context_v1"),
        "interpret",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.predicted_structures"),
        "bound_context",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.predicted_structures"),
        "predicted_structures_view",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_protein_exploration"),
        "region_request",
        forbidden,
    )


def test_whole_model_opens_the_shared_reference_question_without_mutation():
    card = synthetic()
    original = card.to_dict()
    explorer = card.explore()
    model = explorer.answer("predicted_models").items()[0]
    links = model.related()
    link = links.filter("role", equals="question").items()[0]
    basis = link._entry.value["model_context"]
    assert basis["state"] == "ready" and basis["rule"] == "model_structure_request@1"
    assert basis["position_scope"] == "original_whole_reference_interval"
    assert "experimental equivalence" in basis["reason"]
    actual = link.open()
    expected = explorer.answer("region_coverage", options=basis["request"]["options"])
    assert actual.result_ref == expected.result_ref
    assert actual.request["options"]["region"] == list(range(1, 101))
    assert actual.back() is link.back()
    refs = {v["id"] for v in link.support[0]["derivation_input_statements"]}
    assert basis["canonical_reference"]["inputs"] and refs.issuperset(
        basis["canonical_reference"]["inputs"]
    )
    for source in links.filter("role", equals="source").items():
        assert source.open().native_payload["source"]["name"] in (
            "AlphaFold DB",
            "UniProt",
        )
    assert card.to_dict() == original


@pytest.mark.parametrize(
    "begin,end,accession,checksum",
    [
        (5, 90, "P52270", None),
        (1, 100, "P60174", None),
        (1, 100, "P52270", "0" * 32),
        (0, 100, "P52270", None),
        (1, 101, "P52270", None),
    ],
)
def test_unconfirmed_models_expose_a_reason_without_inferred_correspondence(
    begin, end, accession, checksum
):
    link = question(
        synthetic(begin=begin, end=end, accession=accession, checksum=checksum)
    )
    basis = link._entry.value["model_context"]
    assert basis["state"] == "unsupported" and basis["request"] is None
    view = link.open()
    assert view.outcome["status"] == "unsupported"
    assert view.native_payload["model_context"] == basis


@pytest.mark.parametrize(
    "change",
    [
        "sequence",
        "length",
        "checksum_value",
        "checksum_membership",
        "checksum_shape",
        "checksum_conflict",
        "new_sequence_basis",
        "new_checksum_basis",
        "missing_application",
        "qualifier_alternative",
        "foreign_subject",
    ],
)
def test_changed_or_missing_reference_inputs_do_not_become_another_mapping(change):
    card = synthetic()
    rel = card.relationships("has_predicted_structure")[0]
    if change == "sequence":
        card.get("sequence.primary")["value"] = "A" * 100
    elif change == "length":
        card.get("sequence.length")["value"] = 99
    elif change == "checksum_value":
        card.get("sequence.checksums")["value"] = {"md5": "0" * 32}
    elif change == "checksum_membership":
        card.get("sequence.checksums")["source_assertion_ids"] = []
    elif change == "checksum_shape":
        card.get("sequence.checksums")["source_assertion_ids"] = [{}]
    elif change == "checksum_conflict":
        card.quality.setdefault("conflicts", []).append({"field": "sequence.checksums"})
    elif change in ("new_sequence_basis", "new_checksum_basis"):
        field = (
            "sequence.primary"
            if change == "new_sequence_basis"
            else "sequence.checksums"
        )
        value = (
            "A" * 100
            if change == "new_sequence_basis"
            else deepcopy(card.get(field)["value"])
        )
        if change == "new_checksum_basis":
            value["sha256"] = hashlib.sha256(("M" * 100).encode()).hexdigest()
        source = make_source_assertion(
            field,
            value,
            "UniProt",
            "P52270",
            "synthetic-new",
            subject_ref="uniprot:P52270",
        )
        card.source_assertion_store.add(source)
        card.get(field).update(value=value, source_assertion_ids=[source["id"]])
    elif change == "missing_application":
        rel.pop("derivation_applications")
    elif change == "qualifier_alternative":
        rel["qualifier_conflicts"] = {"range": [[2, 99]]}
    elif change == "foreign_subject":
        rel["subject_ref"] = "uniprot:P60174"
    if change == "foreign_subject":
        assert not card.explore().answer("predicted_models").items()
        return
    link = question(card)
    assert link._entry.value["model_context"]["state"] != "ready"
    assert link._entry.value["model_context"]["request"] is None


def test_historical_model_flags_do_not_fill_missing_original_context():
    card = Card.from_dict(
        json.loads(
            Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )
    link = question(card)
    assert link._entry.value["model_context"]["state"] == "missing_prerequisite"
    assert link.open().native_payload["model_context"]["original_model_context"] is None


@pytest.mark.parametrize("fragment", [False, True])
def test_original_model_navigation_reopens_without_current_interpretation(
    fragment, tmp_path, monkeypatch
):
    link = question(synthetic(begin=5 if fragment else 1))
    expected = link.open()
    path = tmp_path / "original-model.json"
    receipt = expected.save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert saved.native_payload == expected.native_payload
    assert saved.outcome == expected.outcome
    model = saved.explorer.answer("predicted_models").items()[0]
    original = model.related().filter("role", equals="question").items()[0].open()
    assert original.native_payload == expected.native_payload


def test_unvisited_saved_request_stays_not_saved(tmp_path, monkeypatch):
    model = synthetic().explore().answer("predicted_models").items()[0]
    links = model.related()
    path = tmp_path / "unvisited.json"
    links.save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    result = saved.filter("role", equals="question").items()[0].open()
    assert result.outcome["status"] == "not_saved"


def test_model_lookalike_in_a_literal_value_is_not_a_navigation_contract():
    card = synthetic()
    card.sections["extensions"] = {
        "model": {
            "value": deepcopy(card.relationships("has_predicted_structure")[0]),
            "source_assertion_ids": [],
        }
    }
    item = card.explore().inspect("extensions.model").items()[0]
    assert not item.related().filter("role", equals="question").items()


def test_resealed_model_question_cannot_change_its_original_region(tmp_path):
    view = question(synthetic()).open()
    path = tmp_path / "changed.json"
    view.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for obj in bundle["objects"].values():
        if (
            isinstance(obj, dict)
            and obj.get("rule") == "retained_context_links@4"
            and isinstance(obj.get("links"), list)
        ):
            for link in obj["links"]:
                if link["role"] == "question":
                    link["model_context"]["request"]["options"]["region"] = [[1, 90]]
                    changed = True
    assert changed
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_destination_keeps_its_actual_ready_model_origin(tmp_path):
    card = synthetic()
    other = synthetic(begin=5, entry="AF-SYNTHETIC-F2")
    for source in other.source_assertion_store.to_list():
        card.source_assertion_store.add(source)
    for relation in other.relationships():
        card.relationship_store.add(relation)
    explorer = card.explore()
    items = explorer.answer("predicted_models").items()
    ready = items[0].related().filter("role", equals="question").items()[0].open()
    unavailable_link = items[1].related().filter("role", equals="question")
    unavailable_link.items()[0].open()
    path = tmp_path / "origin.json"
    ready.save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    bad = next(
        key
        for key, record in bundle["views"].items()
        if record["view_ref"] == unavailable_link.view_ref
    )
    root = bundle["views"][bundle["root_navigation_ref"]]
    assert root["origin"] != bad
    root["origin"] = bad
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_public_tctim_model_uses_the_captured_reference_and_existing_inventory():
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.alphafold import FixtureAlphaFoldClient

    card, _ = sabueso.resolve_protein_card(
        "P52270",
        EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
        predicted_structures=True,
        alphafold_client=FixtureAlphaFoldClient("temp_data"),
    )
    original = card.to_dict()
    explorer = card.explore()
    model = explorer.answer("predicted_models").items()[0]
    link = model.related().filter("role", equals="question").items()[0]
    basis = link._entry.value["model_context"]
    assert basis["state"] == "ready"
    assert (
        basis["original_model_context"]
        == card.predicted_structures()["items"][0]["sequence_context"]
    )
    result = link.open()
    assert result.items() and result.request["options"]["region"] == list(range(1, 252))
    selection = explorer.access.select(
        "structures",
        fields=["structure_ref"],
        options={"region": [[1, 251]], "include_fragments": False},
    )
    assert selection.result_ref == result.result_ref
    assert card.to_dict() == original


def test_model_navigation_reads_in_a_clean_inert_process(tmp_path):
    path = tmp_path / "model-original.json"
    question(synthetic()).open().save(path)
    code = r"""
import importlib,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No current science, Card construction or source inputs')
Card.from_dict=forbidden;socket.socket.connect=forbidden;socket.create_connection=forbidden
import sabueso.mappings.alphafold_context_v1 as mapping_context
mapping_context.interpret=forbidden
for name,methods in {'predicted_structures':['bound_context','predicted_structures_view'],'card_protein_exploration':['region_request']}.items():
 module=importlib.import_module('sabueso.core.'+name)
 for method in methods:setattr(module,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1])
model=saved.explorer.answer('predicted_models').items()[0]
links=model.related()
question=links.filter('role',equals='question').items()[0]
assert question._entry.value['model_context']['state']=='ready'
assert question.open().native_payload==saved.native_payload
for source in links.filter('role',equals='source').items():assert source.open().native_payload['source']
print('PASS independent original model question and input navigation')
"""
    with TemporaryDirectory(prefix="sabueso-original-model-") as directory:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path.resolve())],
            cwd=directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS independent original model question" in result.stdout


def test_model_question_keeps_the_detached_original_reference_after_caller_changes():
    card = synthetic()
    explorer = card.explore()
    card.get("sequence.primary")["value"] = "A" * 100
    model = explorer.answer("predicted_models").items()[0]
    link = model.related().filter("role", equals="question").items()[0]
    assert link._entry.value["model_context"]["state"] == "ready"
    assert link.open().request["options"]["region"] == list(range(1, 101))
