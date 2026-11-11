"""Human-root saves retain finite assembly requests in their actual accesses."""

import gzip
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from test_card_saved_nonpolymer_assembly_offline import inert

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import StorageError

DATA = Path(__file__).parent / "data"
FIELDS = ["structure_ref", "assembly_id", "declaration_count"]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Assembly retention must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def setup(rule):
    capsule = json.loads(
        gzip.decompress((DATA / "assembly_nonpolymer_live_v2.json.gz").read_bytes())
    )
    card = Card.from_dict(deepcopy(capsule["cases"]["2V5B"]["card"]))
    explorer = card.explore()
    structures = explorer.view("structures").filter("structure_ref", equals="pdb:2V5B")
    assembly = explorer.answer(
        "assembly_generation",
        options={"structure_ref": "pdb:2V5B", "generation_rule": rule},
    )
    # Opening a declared source creates a distinct actual access; it does not
    # create a new Card or establish another scientific entity.
    source = assembly.items()[0].related().filter("role", equals="source")
    assembly = (
        source.items()[0]
        .open()
        .explorer.answer("assembly_generation", options=assembly.request["options"])
    )
    assert explorer.access is not assembly.explorer.access
    return card, structures, assembly


def signature(view):
    return (
        view.view_ref,
        None if view._origin is None else view._origin.view_ref,
        None if view.explorer._origin is None else view.explorer._origin.view_ref,
    )


def find_original(saved, original):
    matches = [
        view
        for view in saved.explorer._session["original_nodes"].values()
        if signature(view) == signature(original)
    ]
    assert matches
    return matches[0]


def original_addresses(access, value):
    if isinstance(value, dict):
        if value.get("format") == "card_access_location@1":
            return access._resolve(value)[1]
        return {key: original_addresses(access, child) for key, child in value.items()}
    if isinstance(value, list):
        return [original_addresses(access, child) for child in value]
    return value


@pytest.mark.parametrize(
    "rule", ["rcsb_assembly_generation@4", "rcsb_assembly_generation@5"]
)
@pytest.mark.parametrize("root_kind", ["question", "detail", "filter", "source"])
def test_human_root_retains_exact_observed_projections_and_access_instances(
    rule, root_kind, tmp_path, monkeypatch
):
    card, structures, assembly = setup(rule)
    before = card.to_dict()
    options = assembly.request["options"]
    originals = (structures.explorer.access, assembly.explorer.access)
    expected = []
    for access in originals:
        for fields in (FIELDS, list(reversed(FIELDS))):
            selection = access.select(
                "assembly_generation", options=options, fields=fields
            )
            frame = selection.page(limit=32, max_bytes=65536)
            assert frame["page"]["complete"] and frame["page"]["blocked"] is None
            expected.append((selection, original_addresses(access, frame["items"])))
    root = assembly
    if root_kind == "detail":
        root = assembly.items()[0].open()
    elif root_kind == "filter":
        root = assembly.filter("label", equals="Unmatched assembly retention control")
    elif root_kind == "source":
        root = (
            assembly.items()[0]
            .related()
            .filter("role", equals="source")
            .items()[0]
            .open()
        )
    path = tmp_path / "human.json.gz"
    native, rows = root.native_payload, root.rows()
    root.save(path, compression="gzip")
    assert card.to_dict() == before
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    assert saved.native_payload == native
    assert saved.rows() == rows
    assert saved.explorer._session["format"] == "sabueso.card_exploration@35"
    restored = (
        find_original(saved, structures).explorer.access,
        find_original(saved, assembly).explorer.access,
    )
    assert restored[0] is not restored[1]
    for index, access in enumerate(restored):
        for offset, fields in enumerate((FIELDS, list(reversed(FIELDS)))):
            original, items = expected[index * 2 + offset]
            actual = access.select(
                "assembly_generation", options=options, fields=fields
            )
            assert actual.result_ref == original.result_ref
            assert actual.selection_ref == original.selection_ref
            assert (
                original_addresses(
                    access, actual.page(limit=32, max_bytes=65536)["items"]
                )
                == items
            )
        missing = access.select(
            "assembly_generation", options=options, fields=["reason"]
        )
        assert missing.page()["outcome"]["status"] == "not_saved"
    again = tmp_path / "again.json.gz"
    saved.save(again, compression="gzip")
    reopened = sabueso.read_exploration(again)
    assert reopened.native_payload == saved.native_payload
    assert reopened.explorer._session["format"] == "sabueso.card_exploration@35"


def test_shared_projection_and_typed_filter_survive_without_a_menu(
    tmp_path, monkeypatch
):
    from sabueso.core import card_exploration_storage as storage
    from sabueso.core.card_exploration_shared_values_v12 import pack

    _, structures, root = setup("rcsb_assembly_generation@5")
    options = root.request["options"]
    access = structures.explorer.access
    request = {
        "fields": FIELDS,
        "where": {"declaration_count": 2},
        "order_by": {"column": "label", "descending": True},
    }
    original = access.select("assembly_generation", options=options, **request)
    items = original_addresses(access, original.page()["items"])
    wire = storage._prepare(root)
    packet = storage._seal(pack(wire, threshold=0, min_saving=-(1024**2)))
    assert packet["format"] == "sabueso.card_exploration@36"
    path = tmp_path / "shared.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    inert(monkeypatch)
    saved = sabueso.read_exploration(path)
    restored = find_original(saved, structures).explorer.access
    actual = restored.select("assembly_generation", options=options, **request)
    assert actual.selection_ref == original.selection_ref
    assert original_addresses(restored, actual.page()["items"]) == items


@pytest.mark.parametrize(
    "defect", ["projection", "machine_ref", "source_access_boundary"]
)
def test_resealed_request_or_access_changes_are_refused(defect, tmp_path):
    from sabueso.core import card_exploration_storage as storage

    _, structures, root = setup("rcsb_assembly_generation@5")
    machine = structures.explorer.access.select(
        "assembly_generation", options=root.request["options"], fields=FIELDS
    )
    wire = storage._prepare(root)
    key, record = next(
        (key, record)
        for key, record in wire["views"].items()
        if record["flags"]["_machine_ref"] == machine.selection_ref
    )
    if defect == "projection":
        record["selection"]["fields"].reverse()
    elif defect == "machine_ref":
        record["flags"]["_machine_ref"] = "XA_foreign"
    else:
        manifest = wire["knowledge_comparison_access_origins"]
        child, parent = next(
            (node, record["explorer_origin"])
            for node, record in wire["views"].items()
            if record["explorer_origin"] is not None
            and record["origin"] == record["explorer_origin"]
            and wire["views"][record["explorer_origin"]]["flags"]["_link_panel"]
        )
        manifest["views"][child]["explorer"] = manifest["views"][parent]["explorer"]
    path = tmp_path / "resealed.json"
    path.write_text(json.dumps(storage._seal(wire)), encoding="utf-8")
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize(
    "name",
    ["card_assembly_saved_v5.json.gz", "card_structure_assembly_saved_v6.json.gz"],
)
def test_genuine_historical_sessions_keep_their_format(name, tmp_path, monkeypatch):
    inert(monkeypatch)
    original = sabueso.read_exploration(DATA / name)
    expected = original.native_payload
    session_format = original.explorer._session["format"]
    path = tmp_path / "historical.json.gz"
    original.save(path, compression="gzip")
    restored = sabueso.read_exploration(path)
    assert restored.native_payload == expected
    assert restored.explorer._session["format"] == session_format
    assert session_format != "sabueso.card_exploration@35"


@pytest.mark.parametrize(
    "topic", ["structures", "ligand_site_comparisons", "quaternary_interpretation"]
)
@pytest.mark.parametrize("scope", ["public", "empty"])
@pytest.mark.parametrize("root_kind", ["human", "machine"])
def test_earlier_scientific_panels_retain_their_observed_finite_requests(
    topic, scope, root_kind, tmp_path, monkeypatch
):
    card = (
        Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
            )
        )
        if scope == "public"
        else Card(
            meta={
                "entity_type": "protein",
                "card_id": "sabueso:protein:uniprot:SYNTHETIC",
            }
        )
    )
    explorer = card.explore()
    root = explorer.view(topic)
    machine = explorer.access.select(topic, fields=["label"])
    expected = original_addresses(explorer.access, machine.page()["items"])
    outcome = machine.page()["outcome"]
    path = tmp_path / "earlier.json.gz"
    (root if root_kind == "human" else machine).save(path, compression="gzip")
    targets = {
        "structures": ["structures_view", "structure_inventory"],
        "ligand_sites": ["ligand_sites_view"],
        "oligomer": ["oligomer_view"],
        "card_scientific_access": ["materialize"],
        "card_ligand_site_access": ["materialize"],
        "card_quaternary_access": ["materialize"],
    }
    modules = {
        name: importlib.import_module("sabueso.core." + name) for name in targets
    }

    def forbidden(*args, **kwargs):
        pytest.fail("Earlier finite requests must use original frozen science")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name, methods in targets.items():
        for method in methods:
            monkeypatch.setattr(modules[name], method, forbidden)
    saved = sabueso.read_exploration(path)
    actual = saved.explorer.access.select(topic, fields=["label"])
    assert actual.result_ref == machine.result_ref
    assert actual.selection_ref == machine.selection_ref
    assert actual.page()["outcome"] == outcome
    assert original_addresses(saved.explorer.access, actual.page()["items"]) == expected


def test_source_owned_machine_marker_is_only_literal_content(tmp_path):
    from sabueso.core import card_exploration_storage as storage

    card = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    card.unknown_stored["marker"] = {
        "flags": {"_machine_ref": "XA_source_owned"},
        "selection": {
            "operation": "select:structures",
            "scientific_result_ref": "XR_source_owned",
        },
    }
    root = card.explore().inspect()
    wire = storage._prepare(root)
    assert wire["format"] != "sabueso.card_exploration@35"
    path = tmp_path / "literal.json"
    root.save(path)
    assert sabueso.read_exploration(path).native_payload == root.native_payload
