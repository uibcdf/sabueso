"""Original AlphaFold aliases, conservative range selection and exact history.

All counterexamples are synthetic, including modern-only and conflicting inputs.
The current public P52270 response co-serves agreeing aliases.
"""

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
from sabueso.core.card_exploration_verification_v10 import _verify_links
from sabueso.core.errors import StorageError
from sabueso.core.migration import _has
from sabueso.core.packets import _facts, full_rules
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.alphafold import map_predictions
from sabueso.mappings.alphafold_context_v2 import RULE

SEQUENCE = "ACDEFGHIKLMNPQRSTVWY" * 5
ORIGINAL = (
    Path(__file__).parent / "data/model_range_alias_navigation_original_v1.json.gz"
)


def md5(value):
    return hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()


def forbidden(*args, **kwargs):
    raise AssertionError("No network, current interpretation or Card construction")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def make_card(aliases, *, fragment=False):
    fields = {
        "identifiers.uniprot": "P52270",
        "sequence.primary": SEQUENCE,
        "sequence.length": len(SEQUENCE),
        "sequence.checksums": {"md5": md5(SEQUENCE)},
    }
    inputs = [
        make_source_assertion(key, value, "UniProt", "P52270", "synthetic")
        for key, value in fields.items()
    ]
    model = {
        "modelEntityId": "AF-SYNTHETIC-F1",
        "uniprotAccession": "P52270",
        "sequence": SEQUENCE[4:90] if fragment else SEQUENCE,
        "sequenceChecksum": md5(SEQUENCE[4:90] if fragment else SEQUENCE),
        "latestVersion": 6,
        **deepcopy(aliases),
    }
    mapping = map_predictions(
        {"record": [model]},
        "P52270",
        "synthetic",
        md5(SEQUENCE),
        input_assertions=inputs,
    )
    mapping["source_assertions"] += inputs
    mapping["fields"] = fields
    mapping["field_source_assertions"] = {
        key: [row["id"] for row in inputs if row["field_path"] == key] for key in fields
    }
    return build_card_from_mapping(
        mapping,
        meta={"entity_type": "protein"},
        card_id="sabueso:protein:uniprot:P52270",
    ), model


def question(card):
    return (
        card.explore()
        .answer("predicted_models")
        .items()[0]
        .related()
        .filter("role", equals="question")
        .items()[0]
    )


@pytest.mark.parametrize("mode", ["modern", "agreeing", "legacy"])
def test_complete_ranges_bind_original_fields_without_rewriting_source(mode):
    aliases = {"sequenceStart": 1, "sequenceEnd": 100}
    if mode == "agreeing":
        aliases.update(uniprotStart=1, uniprotEnd=100)
    elif mode == "legacy":
        aliases = {"uniprotStart": 1, "uniprotEnd": 100}
    card, model = make_card(aliases)
    before = card.to_dict()
    rel = card.relationships("has_predicted_structure")[0]
    source = card.source_assertion_store.get(rel["source_assertion_ids"][0])
    assert source["asserted_value"]["model"] == model
    row = card.predicted_structures()["items"][0]
    assert row["range"] == [1, 100] and row["coverage"] == 1.0
    assert row["sequence_matches"] is True
    context = row["sequence_context"]
    assert context["rule"] == (
        "alphafold_sequence_context@1" if mode == "legacy" else RULE
    )
    assert row["rule"] == (
        "predicted_structure_scope@1"
        if mode == "legacy"
        else "predicted_structure_scope@2"
    )
    if mode != "legacy":
        assert context["range_basis"]["state"] == (
            "recorded" if mode == "modern" else "agreeing_aliases"
        )
        assert rel["derivation"]["parameters"]["qualifier_paths"][-1] == "range"
    assert question(card)._entry.value["availability"] == "available"
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "modern",
    [
        {"sequenceStart": 2, "sequenceEnd": 100},
        {"sequenceStart": True, "sequenceEnd": 100},
        {"sequenceStart": 1.0, "sequenceEnd": 100},
        {"sequenceStart": 1, "sequenceEnd": "100"},
        {"sequenceStart": 1, "sequenceEnd": None},
        {"sequenceStart": 0, "sequenceEnd": 100},
        {"sequenceStart": 100, "sequenceEnd": 1},
        {"sequenceStart": 1},
        {"sequenceEnd": 100},
    ],
)
def test_no_valid_legacy_fallback_hides_a_stated_modern_problem(modern):
    card, original = make_card({"uniprotStart": 1, "uniprotEnd": 100, **modern})
    row = card.predicted_structures()["items"][0]
    assert row["range"] == [None, None]
    assert row["coverage"] is None and row["sequence_matches"] is None
    context = row["sequence_context"]
    assert context["checksum_comparison"]["equal"] is True
    declarations = context["range_basis"]["declarations"]
    assert declarations[0]["values"] == [1, 100]
    assert declarations[1]["present"] == [
        k for k in ("sequenceStart", "sequenceEnd") if k in modern
    ]
    assert question(card)._entry.value["availability"] == "unsupported"
    text = str(card.explore().answer("predicted_models"))
    assert any(
        word in text
        for word in (
            "conflicting sequence intervals",
            "interval is incomplete",
            "interval is invalid",
        )
    )
    rel = card.relationships("has_predicted_structure")[0]
    assert (
        card.source_assertion_store.get(rel["source_assertion_ids"][0])[
            "asserted_value"
        ]["model"]
        == original
    )


@pytest.mark.parametrize(
    "legacy", [{"uniprotStart": 1}, {"uniprotStart": True, "uniprotEnd": 100}]
)
def test_modern_range_does_not_discard_invalid_legacy_declarations(legacy):
    card, _ = make_card({"sequenceStart": 1, "sequenceEnd": 100, **legacy})
    assert card.predicted_structures()["items"][0]["coverage"] is None
    assert question(card)._entry.value["availability"] == "unsupported"


def test_modern_fragment_retains_exact_field_support_agent_and_back_navigation():
    card, _ = make_card({"sequenceStart": 5, "sequenceEnd": 90}, fragment=True)
    native = card.predicted_structures()["items"][0]
    assert native["coverage"] is None and native["sequence_matches"] is None
    link = question(card)
    basis = link._entry.value["model_context"]
    assert basis["fragment_match"]["range_fields"] == [["sequenceStart", "sequenceEnd"]]
    assert basis["fragment_match"]["reference_interval"] == [5, 90]
    assert basis["fragment_match"]["coordinate_correspondence"] == "not_established"
    answer = link.open()
    agent = link._view.explorer.access.select(
        "structures",
        fields=["structure_ref"],
        options={"region": [[5, 90]], "include_fragments": True},
    )
    assert answer.result_ref == agent.result_ref
    assert answer.back() is link.back()
    assert "sequence correspondence, not observed atoms" in str(answer)


@pytest.mark.parametrize("mode", ["whole", "fragment", "conflict"])
def test_modern_session_reopens_inertly_with_its_exact_original_meaning(
    tmp_path, monkeypatch, mode
):
    aliases = {
        "sequenceStart": 5 if mode == "fragment" else 1,
        "sequenceEnd": 90 if mode == "fragment" else 100,
    }
    if mode == "conflict":
        aliases.update(uniprotStart=2, uniprotEnd=100)
    card, _ = make_card(aliases, fragment=mode == "fragment")
    link = question(card)
    expected = deepcopy(link._entry.value)
    answer = link.open()
    path = tmp_path / "modern.json.gz"
    link._view.save(path)
    for name in ("alphafold_context_v1", "alphafold_context_v2"):
        monkeypatch.setattr(
            importlib.import_module("sabueso.mappings." + name), "interpret", forbidden
        )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.predicted_structures"),
        "bound_context",
        forbidden,
    )
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path)
    recovered = saved.filter("role", equals="question").items()[0]
    assert recovered._entry.value == expected
    assert recovered.open().native_payload == answer.native_payload
    assert recovered.open().outcome == answer.outcome
    assert saved.validation["verifier"] == "model_range_navigation_binding@1"


def test_packet16_admits_new_context_without_reinterpreting_old_mapping():
    card, _ = make_card({"sequenceStart": 1, "sequenceEnd": 100})
    assert _facts("structures", card)["predicted"]["items"][0]["coverage"] == 1.0
    old = _facts("structures", card, mapping="packet_aspects@15")["predicted"]["items"][
        0
    ]
    assert (
        old["coverage"] is None
        and old["context_state"] == "original_basis_not_established"
    )
    assert RULE in full_rules()["structures"]
    assert RULE not in full_rules("packet_aspects@15")["structures"]


@pytest.mark.parametrize("change", ["range", "application", "fields", "source"])
def test_native_replay_refuses_changed_original_range_bindings(change):
    card, _ = make_card({"sequenceStart": 1, "sequenceEnd": 100})
    rel = card.relationships("has_predicted_structure")[0]
    if change == "range":
        rel["qualifiers"]["range"] = [2, 100]
    elif change == "application":
        rel["derivation_applications"][0]["derivation"]["parameters"][
            "qualifier_paths"
        ].remove("range")
    elif change == "fields":
        rel["qualifiers"]["sequence_context"]["range_basis"]["supporting_fields"] = [
            ["uniprotStart", "uniprotEnd"]
        ]
    else:
        source = card.source_assertion_store.get(rel["source_assertion_ids"][0])
        source["asserted_value"]["model"]["sequenceStart"] = 2
    row = card.predicted_structures()["items"][0]
    assert row["context_state"] == "original_basis_not_established"
    assert row["coverage"] is None and row["sequence_matches"] is None


def test_optional_alias_context_migration_never_replaces_valid_original_v1():
    legacy, _ = make_card({"uniprotStart": 1, "uniprotEnd": 100})
    modern, _ = make_card({"sequenceStart": 1, "sequenceEnd": 100})
    path = "relationships.has_predicted_structure.sequence_context"
    assert _has(legacy.to_dict(), path) and _has(modern.to_dict(), path)
    assert not _has(legacy.to_dict(), path + ".range_basis")
    assert _has(modern.to_dict(), path + ".range_basis")


@pytest.mark.parametrize("change", ["fields", "state", "range", "request", "support"])
def test_reidentified_alias_link_substitutions_fail_original_source_validation(change):
    card, _ = make_card({"sequenceStart": 5, "sequenceEnd": 90}, fragment=True)
    links = question(card)._view
    forged = deepcopy(links.native_payload["links"])
    target = next(row for row in forged if row["role"] == "question")
    basis = target["model_context"]
    if change == "fields":
        basis["fragment_match"]["range_fields"] = [["uniprotStart", "uniprotEnd"]]
    elif change == "state":
        basis["original_model_context"]["range_basis"]["state"] = "conflicting_aliases"
    elif change == "range":
        basis["original_model_context"]["model_range"] = [1, 100]
    elif change == "request":
        basis["request"]["options"]["region"] = [[1, 100]]
    else:
        target["support"] = []
    view = _link_view(
        links.explorer,
        forged,
        links.back(),
        "Forged alias range",
        source_location=links.native_payload["source_location"],
        rule="retained_context_links@6",
    )
    assert view.result_ref != links.result_ref
    with pytest.raises(StorageError, match="original source/axis basis"):
        _verify_links(view)


def test_resealed_bundle_cannot_replace_the_original_alias_request(tmp_path):
    card, _ = make_card({"sequenceStart": 5, "sequenceEnd": 90}, fragment=True)
    path = tmp_path / "forged.json"
    question(card).open().save(path)
    bundle = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for value in bundle["objects"].values():
        if isinstance(value, dict) and value.get("rule") == "retained_context_links@6":
            for row in value.get("links", []):
                if row["role"] == "question":
                    row["model_context"]["request"]["options"]["region"] = [[1, 100]]
                    changed = True
    assert changed
    path.write_text(json.dumps(_seal(bundle)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_genuine_pre_reader_producer_opens_in_an_independent_inert_process(tmp_path):
    assert (
        hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
        == "197f9bec30fe2179b25967b7667f26b1d4c13282b5fa086a0f4a7b7398b43d44"
    )
    code = r"""
import importlib,socket,sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No current interpretation, source or Card')
socket.socket.connect=forbidden;socket.create_connection=forbidden;Card.from_dict=forbidden
for name in ('alphafold_context_v1','alphafold_context_v2'):
 importlib.import_module('sabueso.mappings.'+name).interpret=forbidden
for name,methods in {'predicted_structures':['bound_context','predicted_structures_view'],'card_protein_exploration':['region_request']}.items():
 module=importlib.import_module('sabueso.core.'+name)
 for method in methods:setattr(module,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and 'temp_data' in args[0].replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1]);question=saved.filter('role',equals='question').items()[0]
basis=question._entry.value['model_context']
assert basis['rule']=='model_fragment_structure_request@2'
assert basis['fragment_match']['range_fields']==[['sequenceStart','sequenceEnd']]
assert basis['fragment_match']['reference_interval']==[5,90]
assert question.open().request['options']['region']==list(range(5,91))
for source in saved.filter('role',equals='source').items():assert source.open().native_payload['source']
assert saved.validation['verifier']=='model_range_navigation_binding@1'
print('PASS independent inert original range-alias reading')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(ORIGINAL.resolve())],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS independent inert original range-alias reading" in result.stdout


@pytest.mark.parametrize("mode,expected", [("modern_only", None), ("disagreeing", 1.0)])
def test_original_sdk177_alias_findings_remain_inert_without_backfill(
    monkeypatch, mode, expected
):
    path = ORIGINAL.parent / f"model_range_alias_{mode}_legacy_v1.json.gz"
    raw = path.read_bytes()
    decoded = gzip.decompress(raw)
    assert (
        hashlib.sha256(decoded).hexdigest()
        == {
            "modern_only": "2784986e792211502e1ffb1e29447ff7a96360af533aa886f059cd9029063522",
            "disagreeing": "ed5e9a4c1fa015c2e11db5fa94e38d0f115737775023e9613c5d22f265041eb1",
        }[mode]
    )
    bundle = json.loads(decoded)
    assert bundle["format"] != "sabueso.card_exploration@10"
    for name in ("alphafold_context_v1", "alphafold_context_v2"):
        monkeypatch.setattr(
            importlib.import_module("sabueso.mappings." + name), "interpret", forbidden
        )
    monkeypatch.setattr(Card, "from_dict", forbidden)
    saved = sabueso.read_exploration(path)
    row = saved.items()[0].open().native_payload
    context = row["qualifiers"]["sequence_context"]
    assert context["rule"] == "alphafold_sequence_context@1"
    assert context["coverage"] == expected and "range_basis" not in context
    assert path.read_bytes() == raw
