"""Distinct native molecule labels remain distinct statements (#162).

Every source record here is explicitly synthetic; labels never establish an
isoform identity, a sequence mapping or a shared coordinate axis.
"""

import json
import socket
import subprocess
import sys
from copy import deepcopy
from tempfile import TemporaryDirectory

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import ConnectorError
from sabueso.core.migration import _has
from sabueso.core.source_assertion_store import generate_source_assertion_id
from sabueso.mappings.uniprot import _FEATURES, map_protein
from sabueso.resolver import EntityResolver, FixtureUniProtClient

GAP = "source_assertion_store[].normalized_value"


def forbidden(*args, **kwargs):
    raise AssertionError("No network, reconstruction or scientific execution")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def record(kind="Active site", molecules=("P52270-2", "P52270-3")):
    feature = {
        "type": kind,
        "description": "explicit synthetic feature",
        "location": {
            "start": {"value": 2, "modifier": "EXACT"},
            "end": {"value": 4, "modifier": "EXACT"},
        },
    }
    return {
        "primaryAccession": "P52270",
        "sequence": {"value": "M" * 10, "length": 10},
        "entryAudit": {"sequenceVersion": 7},
        "features": [{**deepcopy(feature), "molecule": m} for m in molecules],
    }


def build(native):
    return build_card_from_mapping(
        map_protein(native, "explicit synthetic input"),
        meta={"entity_type": "protein"},
    )


@pytest.mark.parametrize("kind", sorted(_FEATURES))
def test_each_feature_type_preserves_distinct_native_molecules_and_item_support(kind):
    native = record(kind)
    before = deepcopy(native)
    card = build(native)
    node = card.get(_FEATURES[kind])
    assert len(node["value"]) == len(set(node["source_assertion_ids"])) == 2
    items = card.explore().view("annotated_regions").items()
    assert len(items) == 2
    for item, original in zip(items, native["features"]):
        value = item.open().native_payload
        assert value["molecule"] == original["molecule"]
        assert value["location"]["sequence"]["sequence_id"] is None
        (ref,) = item.support[0]["source_assertion_ids"]
        source = card.source_assertion_store.get(ref)
        assert source["asserted_value"] == original
        assert source["normalized_value"] == value
        assert source["source_metadata"]["uniprot_feature"] == original
        assert source["source_metadata"]["sequence_version"] == 7
        assert item.explain().items()[0].open().native_payload == source
        question = item.related().filter("role", equals="question").items()[0]
        assert question.open().outcome["status"] == "unsupported"
    assert native == before
    assert _has(card.to_dict(), GAP)


def test_ids_do_not_depend_on_feature_order_or_retrieval_and_native_contexts_stay_complete():
    native = record()
    first = build(native)
    native["features"].reverse()
    mapping = map_protein(native, "another synthetic retrieval")
    second = build_card_from_mapping(mapping, meta={"entity_type": "protein"})

    def ids(card):
        return {
            row["asserted_value"]["molecule"]: row["id"]
            for row in card.source_assertion_store.to_list()
            if row["field_path"] == "features_positional.active_site"
        }

    assert ids(first) == ids(second) and len(set(ids(first).values())) == 2
    for missing in (False, True):
        native = record(molecules=(None,))
        if missing:
            native["features"][0].pop("molecule")
        card = build(native)
        node = card.get("features_positional.active_site")
        assert "molecule" not in node["value"][0]
        # Native context, including an explicit null versus an omitted key, remains exact.
        (ref,) = node["source_assertion_ids"]
        assert (
            card.source_assertion_store.get(ref)["asserted_value"]
            == native["features"][0]
        )


def test_literal_labels_do_not_establish_identity_even_on_the_same_canonical_axis():
    card = build(record(molecules=(None, "P52270", "UniProt:P52270", "")))
    node = card.get("features_positional.active_site")
    assert len(node["value"]) == len(set(node["source_assertion_ids"])) == 4
    assert [r["location"]["sequence"]["sequence_id"] for r in node["value"]] == [
        "UniProt:P52270",
        "UniProt:P52270",
        "UniProt:P52270",
        None,
    ]
    assert [r.get("molecule") for r in node["value"]] == [
        None,
        "P52270",
        "UniProt:P52270",
        "",
    ]
    assert not any(
        r["predicate"] in ("same_as", "isoform_of")
        for r in card.relationship_store.to_list()
    )


@pytest.mark.parametrize(
    "difference", ["citations", "compound_location", "native_only"]
)
def test_equal_normalized_values_keep_all_complete_original_source_contexts(difference):
    native = record(molecules=("P52270-2", "P52270-2"))
    if difference == "citations":
        for feature, pmid in zip(native["features"], ("1", "2")):
            feature["evidences"] = [
                {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": pmid}
            ]
    elif difference == "compound_location":
        native["features"][1]["location"]["fragments"] = [{"explicit_synthetic": True}]
    else:
        native["features"][1]["explicit_synthetic_source_context"] = "unprojected"
    card = build(native)
    node = card.get("features_positional.active_site")
    assert len(node["value"]) == 1
    assert len(set(node["source_assertion_ids"])) == 2
    originals = [
        card.source_assertion_store.get(ref)["asserted_value"]
        for ref in node["source_assertion_ids"]
    ]
    assert originals == native["features"]
    assert all(
        card.source_assertion_store.get(ref)["normalized_value"] == node["value"][0]
        for ref in node["source_assertion_ids"]
    )
    for item in card.explore().view("annotated_regions").items():
        assert set(item.support[0]["source_assertion_ids"]) == set(
            node["source_assertion_ids"]
        )
        assert len(item.explain().items()) == 2


@pytest.mark.parametrize("compound_first", [False, True])
def test_a_matching_canonical_value_does_not_hide_an_original_compound_scope(
    compound_first,
):
    native = record(molecules=(None, None))
    native["features"][int(not compound_first)]["location"]["fragments"] = [
        {"explicit_synthetic": True}
    ]
    card = build(native)
    (item,) = card.explore().view("annotated_regions").items()
    assert len(item.support[0]["source_assertion_ids"]) == 2
    question = item.related().filter("role", equals="question").items()[0]
    assert question.open().outcome["status"] == "unsupported"


def test_exact_native_duplicates_do_not_invent_distinct_assertions():
    native = record(molecules=("P52270-2", "P52270-2"))
    card = build(native)
    node = card.get("features_positional.active_site")
    assert len(set(node["source_assertion_ids"])) == 1
    (ref,) = set(node["source_assertion_ids"])
    (site,) = card.ligand_sites()["annotated_sites"]
    assert site["source_assertion_id"] == ref
    assert (
        card.source_assertion_store.get(ref)["asserted_value"] == native["features"][0]
    )


def test_ligand_site_reader_keeps_each_matching_original_context_and_its_own_codes():
    native = record(molecules=(None, None))
    for feature, code, pmid in zip(
        native["features"], ("ECO:0000269", "ECO:0000250"), ("1", "2")
    ):
        feature["evidences"] = [{"evidenceCode": code, "source": "PubMed", "id": pmid}]
    card = build(native)
    sites = card.ligand_sites()["annotated_sites"]
    refs = card.get("features_positional.active_site")["source_assertion_ids"]
    assert len(sites) == 2
    assert {site["source_assertion_id"] for site in sites} == set(refs)
    assert [site["evidence"] for site in sites] == [["ECO:0000269"], ["ECO:0000250"]]
    for site in sites:
        source = card.source_assertion_store.get(site["source_assertion_id"])
        assert source["source"]["name"] == site["source"] == "UniProt"
        assert (
            source["normalized_value"]["location"]["sequence"]["start"] == site["start"]
        )


@pytest.mark.parametrize("molecule", [False, 0, 1, [], {}, ["P52270-2"]])
def test_malformed_molecule_labels_fail_instead_of_becoming_unidentified_axes(molecule):
    with pytest.raises(ConnectorError, match="native string or unstated"):
        build(record(molecules=(molecule,)))


def test_card_store_and_saved_exploration_keep_each_original_context(
    tmp_path, monkeypatch
):
    card = build(record())
    original = card.to_dict()
    assert Card.from_dict(json.loads(json.dumps(original))).to_dict() == original
    store = sabueso.KnowledgeStore(tmp_path / "synthetic.db")
    pin = store.save(card)
    assert store.load(pin).to_dict() == original
    view = card.explore().view("annotated_regions")
    path = tmp_path / "contexts.json"
    receipt = view.save(path)
    before = path.read_bytes()
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "structures", forbidden)
    saved = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    for item, molecule in zip(saved.items(), ("P52270-2", "P52270-3")):
        assert item.open().native_payload["molecule"] == molecule
        source = item.explain().items()[0].open().native_payload
        assert source["source_metadata"]["uniprot_feature"]["molecule"] == molecule
        assert source["asserted_value"]["molecule"] == molecule
    assert path.read_bytes() == before


def test_migration_reports_retained_native_scope_missing_from_the_old_value_and_refresh_is_new(
    tmp_path,
):
    # Explicit synthetic legacy shape: only the final original context survived.
    mapping = map_protein(record(molecules=("P52270-3",)), "synthetic legacy")
    value = mapping["features"]["features_positional.active_site"][0]
    value.pop("molecule")
    source_value = deepcopy(value)
    source = next(
        a
        for a in mapping["source_assertions"]
        if a["field_path"] == "features_positional.active_site"
    )
    source["asserted_value"] = source_value
    source.pop("normalized_value")
    source["id"] = generate_source_assertion_id(
        "UniProt", "P52270", "features_positional.active_site", value
    )
    mapping["field_source_assertions"]["features_positional.active_site"] = [
        source["id"]
    ]
    original = build_card_from_mapping(mapping, meta={"entity_type": "protein"})
    original.meta["schema_version"] = "0.3.13"
    before = original.to_dict()
    store = sabueso.KnowledgeStore(tmp_path / "history.db")
    pin = store.save(original)
    assert not _has(before, GAP)
    migrated = sabueso.migrate_card(before)
    gaps = [
        g for step in migrated.quality["migration"][-1]["steps"] for g in step["gaps"]
    ]
    assert any(g["path"] == GAP and g["kind"] == "missing" for g in gaps)
    assert migrated.get("features_positional.active_site")["value"] == [value]
    assert not _has(migrated.to_dict(), GAP)
    (tmp_path / "P52270.json").write_text(json.dumps(record()), encoding="utf-8")
    resolver = EntityResolver(FixtureUniProtClient(tmp_path))
    refreshed, _ = sabueso.refresh_card(original, resolver=resolver, store=store)
    assert _has(refreshed.to_dict(), GAP)
    assert len(refreshed.get("features_positional.active_site")["value"]) == 2
    assert store.load(pin).to_dict() == before == original.to_dict()


def test_molecule_gap_applies_only_to_retained_source_declarations():
    assert _has(Card(meta={"entity_type": "protein"}).to_dict(), GAP)
    card = build(record(molecules=(None,)))
    assert _has(card.to_dict(), GAP)
    data = build(record(molecules=("P52270-2",))).to_dict()
    source = next(
        a
        for a in data["source_assertion_store"]
        if a["field_path"].startswith("features_positional.")
    )
    source["normalized_value"]["molecule"] = "P52270-3"
    assert not _has(data, GAP)
    source["source"]["name"] = "Explicit other synthetic source"
    assert _has(data, GAP)


def test_independent_reader_keeps_both_contexts_without_current_science(tmp_path):
    path = tmp_path / "original-contexts.json"
    build(record()).explore().view("annotated_regions").save(path)
    script = """
import sys,socket,sabueso
from sabueso.core.card import Card
def forbidden(*a,**k):raise AssertionError('No reconstruction or current science')
Card.from_dict=forbidden
Card.structures=forbidden
socket.socket.connect=forbidden
socket.create_connection=forbidden
saved=sabueso.read_exploration(sys.argv[1])
items=saved.items()
assert len(items)==2
for item,molecule in zip(items,('P52270-2','P52270-3')):
 assert item.open().native_payload['molecule']==molecule
 assert item.explain().items()[0].open().native_payload['source_metadata']['uniprot_feature']['molecule']==molecule
 assert item.related().filter('role',equals='question').items()[0].open().outcome['status']=='unsupported'
print('PASS independent retained native molecule contexts')
"""
    with TemporaryDirectory() as cwd:
        result = subprocess.run(
            [sys.executable, "-c", script, str(path.resolve())],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS independent" in result.stdout


@pytest.mark.parametrize("mapping", ["packet_aspects@8", "packet_aspects@9"])
def test_historical_packet_source_projection_remains_frozen(
    mapping, tmp_path, monkeypatch
):
    from sabueso.core.packets import KnowledgePacket, _facts, full_rules

    native = record(molecules=(None, None))
    for feature, pmid in zip(native["features"], ("1", "2")):
        feature["evidences"] = [
            {"evidenceCode": "ECO:0000269", "source": "PubMed", "id": pmid}
        ]
    data = build(native).to_dict()
    refs = []
    for source in data["source_assertion_store"]:
        if source["field_path"] == "features_positional.active_site":
            # Explicit synthetic old normalized-only statements with distinct
            # opaque imported IDs; both were valid inputs to the original reader.
            source["asserted_value"] = source.pop("normalized_value")
            source["id"] = f"SA_EXPLICIT_SYNTHETIC_LEGACY_{len(refs)}"
            refs.append(source["id"])
    data["sections"]["features_positional"]["active_site"]["source_assertion_ids"] = (
        refs
    )
    card = Card.from_dict(data)
    current = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["ligand_sites"]), card
    )
    assert current.to_dict()["aspect_mapping"] == "packet_aspects@13"
    assert len(_facts("ligand_sites", card)["annotated_sites"]) == 2
    historical = _facts("ligand_sites", card, mapping=mapping)
    assert len(historical["annotated_sites"]) == 1
    assert historical["annotated_sites"][0]["source_assertion_id"] == refs[-1]
    assert "annotated_site_source_support@1" not in full_rules(mapping)["ligand_sites"]
    payload = current.to_dict()
    payload["aspect_mapping"] = mapping
    payload["facts"]["ligand_sites"]["subject"] = historical
    old = KnowledgePacket(payload)
    store = sabueso.KnowledgeStore(tmp_path / "packets.db")
    store.save(card)
    before = old.to_dict()
    pin = store.save_packet(old, "explicit_synthetic_history")
    monkeypatch.setattr(Card, "ligand_sites", forbidden)
    restored = store.load_packet(pin)
    assert (
        restored.terms("commercial_product", store=store)["packet_rule"]
        == "packet_terms@1"
    )
    assert restored.to_dict() == before
