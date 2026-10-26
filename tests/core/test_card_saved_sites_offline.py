"""Original comparison science and exact support survive independent saved reading."""

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
from test_card_ligand_site_comparisons_offline import TOPIC, forbidden, protein

import sabueso
from sabueso.core.card import Card
from sabueso.core.card_exploration_history import _require_matches
from sabueso.core.card_exploration_storage import _seal
from sabueso.core.errors import StorageError


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    importlib.import_module("sabueso.core.ligand_explanation")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.mark.parametrize("kind", ["public", "synthetic", "foreign", "empty"])
def test_frozen_original_recipe_matches_actual_native_result_and_context(
    kind, monkeypatch
):
    from sabueso.core.card_ligand_site_history_v1 import expected_links, expected_result

    card = (
        Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
            )
        )
        if kind == "public"
        else protein(molecule="P52270-2")
        if kind == "foreign"
        else protein()
    )
    if kind == "empty":
        card.relationship_store.store.clear()
    explorer = card.explore()
    view = explorer.view(TOPIC)
    actual = explorer.access._objects[view.result_ref]
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_sites"),
        "ligand_sites_view",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_site_scope"),
        "reference",
        forbidden,
    )
    expected = expected_result(explorer.access)
    assert expected.result_ref == view.result_ref
    _require_matches(actual, expected.wire, "original site result")
    for item in view.items():
        _require_matches(
            item.related().native_payload,
            expected_links(explorer.access, expected, item._entry.key),
            "original site links",
        )


def test_missing_comparison_destination_keeps_the_actual_navigation_rule():
    item = protein().explore().view(TOPIC).items()[0]
    link = item.related().filter("role", equals="object").items()[0]
    destination = link.open()
    assert destination.outcome["status"] == "context_not_supplied"
    assert destination.context["adapter"] == link._entry.value["rule"]


@pytest.mark.parametrize("root_kind", ["human", "question", "detail", "machine"])
def test_save_original_comparisons_sources_back_and_exact_agent_request(
    root_kind, tmp_path, monkeypatch
):
    explorer = protein().explore()
    human = explorer.answer(TOPIC) if root_kind == "question" else explorer.view(TOPIC)
    original = human.native_payload
    if root_kind == "machine":
        root = explorer.access.select(
            TOPIC, fields=["site_class"], where={"comparison_status": "computed"}
        )
    else:
        root = human.items()[0].open() if root_kind == "detail" else human
    path = tmp_path / "sites.json"
    root.save(path)
    bundle = json.loads(path.read_text())
    assert bundle["format"] == "sabueso.card_exploration@3"
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for module, names in {
        "ligand_sites": ["ligand_sites_view", "annotated_sites"],
        "ligand_site_scope": ["reference", "annotation", "contact"],
        "card_ligand_site_exploration": [
            "_materialize",
            "view",
            "support",
            "explain",
            "links",
        ],
        "card_ligand_site_access": ["materialize"],
    }.items():
        for name in names:
            monkeypatch.setattr(
                importlib.import_module("sabueso.core." + module), name, forbidden
            )
    saved = sabueso.read_exploration(path)
    assert saved.validation["verifier"] == "site_exploration_binding@1"
    assert saved.capabilities["save"]
    if root_kind == "machine":
        selected = saved.explorer.access.select(
            TOPIC, fields=["site_class"], where={"comparison_status": "computed"}
        )
        assert selected.selection_ref == root.selection_ref
        assert (
            selected.page()["items"][0]["cells"]["site_class"]["value"]
            == original["items"][0]["site_class"]
        )
        assert (
            saved.explorer.access.select(TOPIC, fields=[]).page()["outcome"]["status"]
            == "not_saved"
        )
    else:
        assert saved.view_ref == root.view_ref
        assert saved.native_payload == root.native_payload
    item = saved.items()[0]
    assert item.explain().back().view_ref == saved.view_ref
    links = item.related()
    assert links.back().result_ref == saved.result_ref
    source = links.filter("role", equals="source").items()[0].open()
    assert source.native_payload["id"] in {
        s["id"] for s in item.support[0]["source_assertions"]
    }
    again = tmp_path / "again.json"
    saved.save(again)
    assert sabueso.read_exploration(again).view_ref == saved.view_ref


def test_rehashed_saved_comparison_change_is_refused(tmp_path):
    root = protein().explore().view(TOPIC)
    path = tmp_path / "sites.json"
    root.save(path)
    data = json.loads(path.read_text())
    wire = data["objects"][root.result_ref]
    wire["native_payload"]["items"][0]["comparison"]["status"] = (
        "computed_synthetic_tamper"
    )
    path.write_text(json.dumps(_seal(deepcopy(data))))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.fixture(scope="module")
def synthetic_bundle(tmp_path_factory):
    card = protein()
    extra = protein(ligand_code="ADP")
    for row in extra.source_assertion_store.to_list():
        card.source_assertion_store.add(row)
    for row in extra.relationships("has_ligand_site"):
        card.relationship_store.add(row)
    explorer = card.explore()
    view = explorer.answer(TOPIC).sort("ligand_ref", descending=True).table()
    explorer.access.select(
        TOPIC, fields=["ligand_ref"], item_refs=[view.items()[0].item_ref]
    ).save(tmp_path_factory.mktemp("synthetic-sites") / "machine.json")
    path = tmp_path_factory.mktemp("site-bundle") / "human.json"
    view.save(path)
    return json.loads(path.read_text())


@pytest.mark.parametrize(
    "mutation",
    [
        "classification",
        "contact_scope",
        "source_members",
        "explanation",
        "row_wording",
        "context_options",
        "cell_type",
        "schema",
        "missing_manifest",
        "downgrade",
        "unknown_adapter",
        "selection_members",
        "source_origin",
        "explanation_origin",
        "unknown_policy",
        "question_options",
    ],
)
def test_coherent_hashes_do_not_admit_changed_original_science_or_navigation(
    synthetic_bundle, mutation, tmp_path
):
    data = deepcopy(synthetic_bundle)
    ref = next(
        r
        for r in data["scientific_results"]
        if data["objects"][r]["context"]["adapter"] == "ligand_site_exploration@1"
    )
    wire = data["objects"][ref]
    key = next(iter(wire["rows"]))
    root = data["views"][data["root_navigation_ref"]]
    if mutation == "classification":
        wire["native_payload"]["items"][0]["site_class"] = "synthetic_changed_class"
    elif mutation == "contact_scope":
        wire["native_payload"]["items"][0]["comparison"]["contact_scope"][
            "sequence_ref"
        ] = "uniprot:FOREIGN"
    elif mutation == "source_members":
        wire["support"][key]["source_assertions"].pop()
    elif mutation == "explanation":
        wire["explanations"][key]["classification_inputs"]["absence_basis"] = (
            "source globally absent"
        )
    elif mutation == "row_wording":
        wire["rows"][key]["outcome"] = "All other sites excluded"
    elif mutation == "context_options":
        wire["context"]["options"] = {"assume_same_numbering": True}
    elif mutation == "cell_type":
        next(iter(root["state"]["items"].values()))["cells"]["comparison_status"][
            "value"
        ] = True
    elif mutation == "schema":
        root["state"]["schema"]["grain"] = "physical molecules"
    elif mutation == "missing_manifest":
        data["scientific_results"].pop(ref)
    elif mutation == "downgrade":
        data["format"] = "sabueso.card_exploration@2"
        data["producer"]["verifier"] = "scientific_exploration_binding@1"
        data["capabilities"]["scientific_saved_adapters"].pop()
    elif mutation == "unknown_adapter":
        wire["context"]["adapter"] = "ligand_site_exploration@99"
    elif mutation == "selection_members":
        root["selected"] = root["selected"][:-1]
    elif mutation in ("source_origin", "explanation_origin"):
        kind = "links" if mutation == "source_origin" else "explanations"
        mappings = data["navigation"][kind]
        names = [k for k in mappings if json.loads(k)[1] in root["state"]["items"]]
        assert len(names) > 1
        mappings[names[0]] = mappings[names[1]]
    elif mutation == "unknown_policy":
        machine = next(
            v
            for v in data["views"].values()
            if v["selection"].get("scientific_result_ref") == ref
            and v["flags"]["_machine_ref"] is not None
        )
        location = data["locations"][
            machine["selection"]["context_location"]["location_ref"]
        ]
        data["objects"][location["result_ref"]]["request"]["selection"]["format"] = (
            "ligand_site_access_selection@99"
        )
    elif mutation == "question_options":
        root["flags"]["_request"]["options"] = {"guess": True}
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(_seal(data)))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


def test_partial_machine_request_does_not_become_an_unrestricted_human_topic(tmp_path):
    selection = (
        protein()
        .access()
        .select(TOPIC, fields=["site_class"], where={"comparison_status": "computed"})
    )
    path = tmp_path / "partial.json"
    selection.save(path)
    saved = sabueso.read_exploration(path)
    assert (
        saved.explorer.access.select(
            TOPIC, fields=["site_class"], where={"comparison_status": "computed"}
        ).selection_ref
        == selection.selection_ref
    )
    assert saved.explorer.view(TOPIC).outcome["status"] == "not_saved"
    assert saved.explorer.answer(TOPIC).outcome["status"] == "not_saved"
    assert "structures" not in saved.explorer.access.capabilities["scientific_topics"]


def test_empty_display_still_retains_original_explanation_for_an_underlying_item(
    tmp_path,
):
    access = protein().access()
    complete = access.select(TOPIC)
    ref = complete.page()["items"][0]["item_ref"]
    empty = access.select(TOPIC, fields=[], item_refs=[])
    path = tmp_path / "empty-selection.json"
    empty.save(path)
    saved = sabueso.read_exploration(path)
    assert not saved.items()
    explanation = saved.explorer.access.explain(ref)
    assert saved.explorer.access._resolve(explanation._target["location"])[0][
        "ligand_site_ref"
    ]


@pytest.mark.parametrize("origin", ["fresh", "original_producer"])
def test_independent_original_reader_forbids_live_engines_sources_and_producer_catalog(
    origin, request, tmp_path, monkeypatch
):
    path = tmp_path / "synthetic.json"
    if origin == "original_producer":
        # Historical replay must not even prepare an unused current-writer fixture.
        monkeypatch.setattr(
            importlib.import_module("sabueso.core.card_exploration_storage"),
            "save_exploration",
            forbidden,
        )
        compressed = (
            Path(__file__).parent / "data/card_exploration_sites_v1.json.gz"
        ).read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == (
            "4acb555503c9f1d1e1b26635c11ead3a1423dc5f183cd720e343f96b748d2719"
        )
        original = gzip.decompress(compressed)
        assert hashlib.sha256(original).hexdigest() == (
            "6fc3cfdef13b8bbd1fe1b53dc489dc3cd83fee96dc9bb6a471bc53f436f97c9e"
        )
        path.write_bytes(original)
    else:
        path.write_text(json.dumps(request.getfixturevalue("synthetic_bundle")))
    script = r"""
import importlib, socket, sys
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError("No live science, Card construction, producer catalog or network")
Card.from_dict = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
for name, methods in {
 'ligand_sites':['ligand_sites_view','annotated_sites'],
 'ligand_site_scope':['reference','annotation','contact'],
 'card_ligand_site_exploration':['_materialize','view','links','explain','support','_row'],
 'card_ligand_site_access':['materialize','descriptor','options_for_sites','defer_frame'],
 'card_scientific_access':['materialize','descriptor','equal_values','sorted_entries'],
 'card_context_navigation':['_resolve'],
}.items():
 module=importlib.import_module('sabueso.core.'+name)
 for method in methods: setattr(module,method,forbidden)
def audit(event,args):
 if event=='open' and isinstance(args[0],str) and '/temp_data/' in args[0]: forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1])
assert saved.validation['verifier']=='site_exploration_binding@1'
assert saved.items()[0].explain().back().result_ref==saved.result_ref
assert saved.items()[0].related().filter('role',equals='source').items()[0].open().native_payload['id']
saved.explorer.access.catalog().page()
request=next(s for s in saved.explorer.access._selections.values() if s._operation=='select:ligand_site_comparisons')
assert request.page(max_bytes=8192)['page']['values_complete']
saved.save(sys.argv[2])
assert sabueso.read_exploration(sys.argv[2]).view_ref==saved.view_ref
print('PASS independent original comparison reading')
"""
    with TemporaryDirectory(prefix="sabueso-original-sites-") as cwd:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(path.resolve()),
                str((tmp_path / "again.json").resolve()),
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_mixed_original_structure_coverage_and_site_views_keep_each_historical_adapter(
    tmp_path,
):
    from sabueso.core.relationship_store import make_relationship

    card = protein()
    from sabueso.core.source_assertion_store import make_source_assertion

    qualifiers = {"method": "SYNTHETIC"}
    statement = make_source_assertion(
        "relationships.has_structure",
        qualifiers,
        "Explicit synthetic source",
        "SYNTHETIC",
        "synthetic",
        subject_ref="uniprot:P52270",
    )
    card.source_assertion_store.add(statement)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270",
            "has_structure",
            "pdb:SYNTHETIC",
            qualifiers,
            [statement["id"]],
        )
    )
    explorer = card.explore()
    structures = explorer.view("structures")
    coverage = explorer.view("coverage")
    sites = explorer.view(TOPIC)
    path = tmp_path / "mixed.json"
    sites.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.explorer.view("structures").native_payload == structures.native_payload
    assert saved.explorer.view("coverage").native_payload == coverage.native_payload
    assert saved.explorer.view(TOPIC).native_payload == sites.native_payload


@pytest.mark.parametrize(
    "nature,pinned,status",
    [
        ("small_molecule", False, "not_applicable"),
        ("protein", False, "missing_prerequisite"),
        ("protein", True, "empty"),
    ],
)
def test_saved_unavailable_and_empty_comparisons_keep_original_outcomes(
    nature, pinned, status, tmp_path
):
    card = protein() if pinned else Card(meta={"entity_type": nature})
    if pinned:
        card.relationship_store.store.clear()
    view = card.explore().view(TOPIC)
    path = tmp_path / "empty.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.outcome["status"] == status
    assert not saved.items()


def test_current_public_mapping_comparisons_keep_positive_and_negative_originals(
    tmp_path,
):
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.interpro import FixtureInterProClient
    from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

    card, _ = sabueso.resolve_protein_card(
        "P52270",
        EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
        ligand_sites=True,
        family_sites=True,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    view = card.explore().answer(TOPIC)
    assert {i["site_class"] for i in view.native_payload["items"]} == {
        "overlaps_annotated_site",
        "no_annotated_overlap",
    }
    path = tmp_path / "current.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == view.native_payload
    assert saved.explorer.answer(TOPIC).native_payload == view.native_payload


def test_changed_typed_policy_with_rebuilt_selection_identity_is_refused(tmp_path):
    from dataclasses import replace

    from sabueso.core.card_exploration import CardView
    from sabueso.core.card_exploration_storage import _explorer, _prepare, _restore
    from sabueso.core.card_ligand_site_selection_v1 import selection_ref

    selected = protein().access().select(TOPIC, where={"comparison_status": "computed"})
    access = selected._access
    context = deepcopy(access._resolve(selected._context_location)[0])
    spec = context["request"]["selection"]
    spec["selected_count"] = True
    ref = selection_ref(selected._scientific, selected._fields, spec)
    forged = replace(
        selected, _selection_ref=ref, _context_location=access._object_location(context)
    )
    explorer = _explorer(access, {"views": {}, "links": {}, "explanations": {}})
    root = CardView(
        explorer,
        forged,
        forged._entries,
        "Synthetic coherent selector tamper",
        _record_panel=TOPIC,
        _machine_ref=ref,
        _context_override=selected._scientific.wire["context"],
        _native_override=selected._scientific.wire["native_payload"],
    )
    bundle = _seal(_prepare(root))
    with pytest.raises(StorageError, match="selection decisions"):
        _restore(bundle, bundle["bundle_digest"])


@pytest.mark.parametrize("topic", [TOPIC, "sources", "structures"])
def test_repeated_save_does_not_expand_an_automatic_support_tree(topic, tmp_path):
    view = (
        protein().explore().answer(TOPIC)
        if topic == TOPIC
        else protein().explore().view(topic)
    )
    before = view.native_payload
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    one = view.save(first)
    two = view.save(second)
    assert one["bundle_digest"] == two["bundle_digest"]
    assert first.read_bytes() == second.read_bytes()
    assert view.native_payload == before
    if topic == TOPIC:
        assert len(json.loads(first.read_text())["views"]) < 20


def test_saved_comparison_supplied_molecule_transition_preserves_focal_owner(tmp_path):
    from test_card_context_navigation_offline import card, edge

    target = card("inchikey:synthetic-target", "small_molecule")
    edge(target, "pdb.ligand:ATP", "same_as")
    explorer = protein().explore(related_cards=[target])
    view = explorer.view(TOPIC)
    destination = (
        view.items()[0].related().filter("role", equals="object").items()[0].open()
    )
    assert destination.explorer.profile == "small_molecule"
    path = tmp_path / "supplied.json"
    view.save(path)
    saved = sabueso.read_exploration(path)
    links = saved.items()[0].related()
    chosen = links.filter("role", equals="object")
    opened = chosen.items()[0].open()
    assert opened.context["card_ref"] == destination.context["card_ref"]
    assert opened.back().view_ref == chosen.view_ref
    assert chosen.back().view_ref == links.view_ref
    assert links.back().view_ref == saved.view_ref
    data = json.loads(path.read_text())
    root = data["views"][data["root_navigation_ref"]]
    root["focal"] = next(key for key in data["cards"] if key != root["focal"])
    path.write_text(json.dumps(_seal(data)))
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)
