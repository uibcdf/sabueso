"""Exact declared fragment questions, original input guards and inert history.

All positive fragment inputs here are explicitly synthetic. They qualify the
contract, not an actual deposited AlphaFold fragment or coordinate correspondence.
"""

import gc
import gzip
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
from sabueso.core.card_context_navigation import _link_view
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.card_exploration_verification_v9 import _verify_links
from sabueso.core.card_model_fragment_regions_v1 import NAVIGATION_RULE, RULE
from sabueso.core.errors import StorageError
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.alphafold import map_predictions

ORIGINAL = Path(__file__).parent / "data/model_fragment_navigation_original_v1.json.gz"
SEQUENCE = "ACDEFGHIKLMNPQRSTVWY" * 5


def md5(value):
    return hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()


def forbidden(*args, **kwargs):
    raise AssertionError("No acquisition, current interpretation or Card recapture")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def synthetic(*, overrides=None, duplicate_model=False):
    fields = {
        "identifiers.uniprot": "P52270",
        "sequence.primary": SEQUENCE,
        "sequence.length": len(SEQUENCE),
        "sequence.checksums": {"md5": md5(SEQUENCE)},
    }
    sources = [
        make_source_assertion(
            path, value, "UniProt", "P52270", "synthetic", subject_ref="uniprot:P52270"
        )
        for path, value in fields.items()
    ]
    model = {
        "entryId": "AF-SYNTHETIC-F1",
        "uniprotAccession": "P52270",
        "sequence": SEQUENCE[4:90],
        "sequenceChecksum": md5(SEQUENCE[4:90]),
        "uniprotStart": 5,
        "uniprotEnd": 90,
        "latestVersion": 6,
        **(overrides or {}),
    }
    models = (
        [model, {**model, "synthetic_note": "another original"}]
        if duplicate_model
        else [model]
    )
    mapping = map_predictions(
        {"record": models},
        "P52270",
        "synthetic",
        md5(SEQUENCE),
        input_assertions=sources,
    )
    mapping["source_assertions"] += sources
    mapping["fields"] = fields
    mapping["field_source_assertions"] = {
        path: [row["id"] for row in sources if row["field_path"] == path]
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
    context = importlib.import_module("sabueso.mappings.alphafold_context_v1")
    predicted = importlib.import_module("sabueso.core.predicted_structures")
    protein = importlib.import_module("sabueso.core.card_protein_exploration")
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(context, "interpret", forbidden)
    monkeypatch.setattr(predicted, "bound_context", forbidden)
    monkeypatch.setattr(predicted, "predicted_structures_view", forbidden)
    monkeypatch.setattr(protein, "region_request", forbidden)


def test_exact_fragment_shares_agent_result_and_keeps_native_whole_scope_unknown():
    card = synthetic()
    before = card.to_dict()
    native = card.predicted_structures()["items"][0]["sequence_context"]
    assert native["sequence_matches"] is None
    explorer = card.explore()
    model = explorer.answer("predicted_models").items()[0]
    links = model.related()
    link = links.filter("role", equals="question").items()[0]
    basis = link._entry.value["model_context"]
    assert basis["rule"] == RULE and basis["state"] == "ready"
    assert basis["original_model_context"] == native
    assert basis["fragment_match"] == {
        "basis": "exact_original_sequence_and_md5",
        "source_assertion_id": card.relationships("has_predicted_structure")[0][
            "source_assertion_ids"
        ][0],
        "sequence_field": "sequence",
        "range_fields": ["uniprotStart", "uniprotEnd"],
        "length": 86,
        "md5": md5(SEQUENCE[4:90]),
        "reference_interval": [5, 90],
        "coordinate_correspondence": "not_established",
    }
    assert basis["request"]["options"] == {
        "sequence_ref": "uniprot:P52270",
        "region": [[5, 90]],
        "include_fragments": True,
    }
    answer = link.open()
    agent = explorer.access.select(
        "structures",
        fields=["structure_ref"],
        options={"region": [[5, 90]], "include_fragments": True},
    )
    assert agent.result_ref == answer.result_ref
    assert answer.back() is link.back()
    assert "sequence correspondence, not observed atoms" in str(answer)
    assert "Retained experimental fragments are included" in answer._repr_html_()
    assert "fragment's reference region" in str(links.table())
    for source in links.filter("role", equals="source").items():
        assert source.open().native_payload["source"]["name"] in (
            "AlphaFold DB",
            "UniProt",
        )
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "overrides",
    [
        {"sequence": None},
        {"sequence": ""},
        {"sequence": SEQUENCE[4:90].lower()},
        {"sequence": SEQUENCE[5:91]},
        {"sequence": " " + SEQUENCE[4:90]},
        {"sequenceChecksum": None},
        {"sequenceChecksum": "0" * 32},
        {"sequenceChecksum": "crc64-is-not-md5"},
        {"uniprotAccession": "P60174"},
        {"uniprotAccession": "P52270-2"},
        {"uniprotStart": 0},
        {"uniprotEnd": 101},
        {"uniprotStart": True},
        {"uniprotStart": 90, "uniprotEnd": 5},
        {"uniprotEnd": 90.0},
    ],
)
def test_incompatible_or_missing_fragment_inputs_do_not_offer_a_ready_question(
    overrides,
):
    link = question(synthetic(overrides=overrides))
    basis = link._entry.value["model_context"]
    assert basis["rule"] == "model_structure_request@1"
    assert basis["state"] != "ready" and basis["request"] is None
    assert link.open().outcome["status"] != "ok"


@pytest.mark.parametrize(
    "change",
    [
        "sequence",
        "length",
        "checksum",
        "new_checksum_input",
        "new_length_input",
        "missing_application",
        "duplicate_application",
        "qualifier_alternative",
        "missing_model_source",
        "foreign_model_record",
    ],
)
def test_original_reference_and_application_are_not_replaced(change):
    card = synthetic()
    row = card.relationships("has_predicted_structure")[0]
    if change == "sequence":
        card.get("sequence.primary")["value"] = "M" * 100
    elif change == "length":
        card.get("sequence.length")["value"] = 99
    elif change == "checksum":
        card.get("sequence.checksums")["value"] = {"md5": "0" * 32}
    elif change in ("new_checksum_input", "new_length_input"):
        path = (
            "sequence.checksums"
            if change == "new_checksum_input"
            else "sequence.length"
        )
        value = deepcopy(card.get(path)["value"])
        if change == "new_checksum_input":
            value["sha256"] = hashlib.sha256(SEQUENCE.encode()).hexdigest()
        source = make_source_assertion(
            path,
            value,
            "UniProt",
            "P52270" if change == "new_checksum_input" else "ANOTHER-RECORD",
            "synthetic-new",
            subject_ref="uniprot:P52270",
        )
        card.source_assertion_store.add(source)
        card.get(path).update(value=value, source_assertion_ids=[source["id"]])
    elif change == "missing_application":
        row.pop("derivation_applications")
    elif change == "duplicate_application":
        row["derivation_applications"] *= 2
    elif change == "qualifier_alternative":
        row["qualifier_conflicts"] = {"range": [[6, 90]]}
    elif change == "missing_model_source":
        row["source_assertion_ids"] = []
    elif change == "foreign_model_record":
        card.source_assertion_store.get(row["source_assertion_ids"][0])["source"][
            "record_id"
        ] = "AF-OTHER-F1"
    basis = question(card)._entry.value["model_context"]
    assert basis["state"] != "ready" and basis["request"] is None


def test_two_original_model_inputs_are_not_silently_pooled():
    card = synthetic(duplicate_model=True)
    row = card.relationships("has_predicted_structure")[0]
    assert len(row["source_assertion_ids"]) == 2
    assert question(card)._entry.value["model_context"]["state"] != "ready"


def test_whole_reference_retains_its_original_policy():
    link = question(
        synthetic(
            overrides={
                "uniprotStart": 1,
                "uniprotEnd": 100,
                "sequence": SEQUENCE,
                "sequenceChecksum": md5(SEQUENCE),
            }
        )
    )
    basis = link._entry.value["model_context"]
    assert link._entry.value["rule"] == "retained_context_links@4"
    assert basis["rule"] == "model_structure_request@1" and basis["state"] == "ready"
    assert basis["request"]["options"]["include_fragments"] is False


@pytest.mark.parametrize("visited", [False, True])
def test_saved_fragment_is_inert_and_never_runs_an_unvisited_question(
    visited, tmp_path, monkeypatch
):
    link = question(synthetic())
    expected = link.open() if visited else None
    path = tmp_path / "fragment.json"
    link.back().save(path)
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == "model_fragment_navigation_binding@1"
    opened = saved.filter("role", equals="question").items()[0].open()
    if visited:
        assert opened.native_payload == expected.native_payload
        assert opened.result_ref == expected.result_ref
    else:
        assert opened.outcome["status"] == "not_saved"
    second = tmp_path / "again.json"
    saved.save(second)
    again = sabueso.read_exploration(second)
    assert again.native_payload == saved.native_payload


@pytest.mark.parametrize("case", ["whole", "fragment"])
def test_genuine_original_producer_keeps_its_recorded_decision(
    case, tmp_path, monkeypatch
):
    raw = ORIGINAL.read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9b5ff5c443c879620dfb2f8e1fd5c487b68a9f7578c82d00c904810d7b9df5e8"
    )
    decoded = gzip.decompress(raw)
    assert (
        hashlib.sha256(decoded).hexdigest()
        == "d76878edab397580ac7628a5d3d0219c005fbaa881de0427fc65e54ae19da2e5"
    )
    capsule = json.loads(decoded)
    assert capsule["producer"]["sdk"] == "0.14.0+174.g5c84728"
    original = capsule["cases"][case]
    # The same synthetic input gains a new *live* fragment question, while old
    # saved decisions remain governed by their original predicate and format.
    fresh = question(Card.from_dict(original["card"]))
    assert fresh._entry.value["model_context"]["state"] == "ready"
    path = tmp_path / "original.json"
    path.write_text(json.dumps(original["saved_original"]), encoding="utf-8")
    expected = original["original_model_context"]
    del capsule, decoded, raw, original
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    question_item = saved.filter("role", equals="question").items()[0]
    assert question_item._entry.value["model_context"] == expected
    assert expected["state"] == ("ready" if case == "whole" else "unsupported")
    assert question_item._entry.value["rule"] == "retained_context_links@4"


@pytest.mark.parametrize(
    "change", ["interval", "experimental_fragments", "checksum", "atoms", "support"]
)
def test_fresh_metadata_identity_cannot_forge_fragment_correspondence(change):
    link = question(synthetic())
    links = link.back()
    payload = links.native_payload
    forged = deepcopy(payload["links"])
    target = next(row for row in forged if row["role"] == "question")
    if change == "interval":
        target["model_context"]["request"]["options"]["region"] = [[6, 90]]
    elif change == "experimental_fragments":
        target["model_context"]["request"]["options"]["include_fragments"] = False
    elif change == "checksum":
        target["model_context"]["fragment_match"]["md5"] = "0" * 32
    elif change == "atoms":
        target["model_context"]["fragment_match"]["coordinate_correspondence"] = (
            "established"
        )
    elif change == "support":
        target["support"] = []
    # Rebuild content-addressed metadata, so rejection proves source-semantic
    # validation rather than only detection of a stale object hash.
    view = _link_view(
        links.explorer,
        forged,
        links.back(),
        "Forged fragment",
        source_location=payload["source_location"],
        rule=NAVIGATION_RULE,
    )
    assert view.result_ref != links.result_ref
    with pytest.raises(StorageError, match="original source/axis basis"):
        _verify_links(view)


def test_resealed_bundle_cannot_replace_a_fragment_request(tmp_path):
    path = tmp_path / "forged.json"
    question(synthetic()).open().save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for obj in bundle["objects"].values():
        if (
            isinstance(obj, dict)
            and obj.get("rule") == NAVIGATION_RULE
            and isinstance(obj.get("links"), list)
        ):
            for link in obj["links"]:
                if link["role"] == "question":
                    link["model_context"]["request"]["options"]["region"] = [[1, 100]]
                    changed = True
    assert changed
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_fragment_and_declared_component_journey_share_one_saved_session(
    tmp_path, monkeypatch
):
    # Original public 1HTI Card plus an explicitly synthetic model declaration.
    # This is mixed-format receiving, not a deposited model of that protein.
    original = json.loads(
        gzip.decompress(
            (
                Path(__file__).parent / "data/assembly_nonpolymer_live_v2.json.gz"
            ).read_bytes()
        )
    )["cases"]["1HTI"]["card"]
    card = Card.from_dict(original)
    sequence = card.get("sequence.primary")["value"]
    accession = card.get("identifiers.uniprot")["value"]
    inputs = {
        ref
        for path in ("sequence.length", "sequence.checksums")
        for ref in card.get(path)["source_assertion_ids"]
    }
    mapping = map_predictions(
        {
            "record": [
                {
                    "entryId": "AF-SYNTHETIC-F1",
                    "uniprotAccession": accession,
                    "sequence": sequence[4:90],
                    "sequenceChecksum": md5(sequence[4:90]),
                    "uniprotStart": 5,
                    "uniprotEnd": 90,
                    "latestVersion": 6,
                }
            ]
        },
        accession,
        "synthetic",
        md5(sequence),
        input_assertions=[
            card.source_assertion_store.get(ref) for ref in sorted(inputs)
        ],
    )
    for source in mapping["source_assertions"]:
        card.source_assertion_store.add(source)
    for row in mapping["relationships"]:
        card.relationship_store.add(row)
    explorer = card.explore()
    model = explorer.answer("predicted_models").items()[0]
    fragment = model.related().filter("role", equals="question").items()[0].open()
    assert fragment.request["options"]["region"] == list(range(5, 91))
    structure = next(
        row
        for row in card.relationships("has_structure")
        if row["object_ref"] == "pdb:1HTI"
    )
    location = {
        **explorer._location("relationship_store"),
        "segments": [
            {"type": "Key", "value": "relationship_store"},
            {"type": "Record", "value": structure["id"]},
        ],
    }
    qualifiers = next(
        item
        for item in explorer.inspect(locator=location).items()
        if item.label == "qualifiers"
    )
    answer = qualifiers.related().filter("role", equals="question").items()[0].open()
    components = (
        answer.items()[0]
        .related()
        .filter("role", equals="components")
        .items()[0]
        .open()
    )
    position = components.filter("role", equals="component").items()[2].open()
    # This complete mixed session deliberately exceeds the default 64 MiB
    # decoded-file budget. Keep a finite explicit budget for this receiving case.
    path = tmp_path / "mixed.json.gz"
    position.save(path, compression="gzip", max_decoded_bytes=128 * 1024**2)
    expected_position, expected_fragment = (
        position.native_payload,
        fragment.native_payload,
    )
    del card, explorer, model, fragment, qualifiers, answer, components, position
    gc.collect()
    inert(monkeypatch)
    restored = sabueso.read_exploration(path, max_decoded_bytes=128 * 1024**2)
    assert restored.native_payload == expected_position
    reopened = (
        restored.explorer.answer("predicted_models")
        .items()[0]
        .related()
        .filter("role", equals="question")
        .items()[0]
        .open()
    )
    assert reopened.native_payload == expected_fragment
    assert restored.validation["verifier"] == "model_fragment_navigation_binding@1"


def test_fragment_reopens_in_an_independent_inert_process(tmp_path):
    path = tmp_path / "fragment.json"
    question(synthetic()).open().save(path)
    code = r"""
import importlib,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No live science, acquisition or Card construction')
import sabueso.mappings.alphafold_context_v1 as mapping
mapping.interpret=forbidden;Card.from_dict=forbidden
socket.socket.connect=forbidden;socket.create_connection=forbidden
for name,methods in {'predicted_structures':['bound_context','predicted_structures_view'],'card_protein_exploration':['region_request']}.items():
 module=importlib.import_module('sabueso.core.'+name)
 for method in methods:setattr(module,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1])
links=saved.explorer.answer('predicted_models').items()[0].related()
link=links.filter('role',equals='question').items()[0]
assert link._entry.value['model_context']['rule']=='model_fragment_structure_request@1'
assert link.open().native_payload==saved.native_payload
assert saved.validation['verifier']=='model_fragment_navigation_binding@1'
for source in links.filter('role',equals='source').items():assert source.open().native_payload['source']
print('PASS independent inert fragment reading')
"""
    with TemporaryDirectory(prefix="sabueso-inert-fragment-") as directory:
        result = subprocess.run(
            [sys.executable, "-c", code, str(path.resolve())],
            cwd=directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS independent inert fragment reading" in result.stdout
