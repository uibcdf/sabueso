"""Public comparison delivery stays economical without losing support membership."""

import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from test_card_ligand_site_comparisons_offline import TOPIC, forbidden, protein

import sabueso
from sabueso.core.card import Card
from sabueso.core.snapshot import canonical_json
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    importlib.import_module("sabueso.core.ligand_explanation")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(params=["historical", "current"])
def explorer(request):
    if request.param == "historical":
        card = Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
            )
        )
    else:
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
    return card.explore()


def size(value):
    return len(canonical_json(value).encode("utf-8"))


def expand_support(access, page):
    expanded = deepcopy(page)
    for item in expanded["items"]:
        support = item.get("support", {})
        store = support.pop("source_store_location", None)
        support.pop("format", None)
        for statement in item.get("support", {}).get("source_assertions", []):
            statement["location"] = (
                {
                    **store,
                    "segments": [
                        *store["segments"],
                        {"type": "Record", "value": statement["id"]},
                    ],
                }
                if store is not None and statement["state"] == "present"
                else statement.get("location")
            )
            if statement["location"] is not None:
                statement["location"] = access._resolve(statement["location"])[1]
    return expanded


def test_public_default_pages_reduce_transport_bytes_and_preserve_all_support(explorer):
    human = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC)
    page = selected.page()
    assert page["page"]["complete"] and page["page"]["values_complete"]
    assert size(page) < size(expand_support(explorer.access, page)) * 0.7
    assert selected.result_ref == human.result_ref
    for item in page["items"]:
        original = explorer.access._resolve(item["support_location"])[0][
            "source_assertions"
        ]
        expanded = expand_support(explorer.access, {"items": [item]})["items"][0][
            "support"
        ]["source_assertions"]
        assert expanded == original
        assert item["support"]["format"] == "ligand_site_support_membership@1"
        for statement in expanded:
            if statement["state"] == "present":
                record, _ = explorer.access._resolve(statement["location"])
                assert record["id"] == statement["id"]
                assert (
                    explorer.access.read(statement["location"]).page(limit=1)["page"][
                        "total"
                    ]
                    > 0
                )


def test_public_small_budget_delivers_values_and_complete_interpretation(
    explorer, monkeypatch
):
    human = explorer.view(TOPIC)
    selected = explorer.access.select(TOPIC)
    original = human.native_payload
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.ligand_sites"),
        "ligand_sites_view",
        forbidden,
    )
    frames, cursor, refs = [], None, []
    while True:
        frame = selected.page(limit=4, max_bytes=8192, cursor=cursor)
        assert size(frame) <= 8192
        assert frame["page"]["values_complete"]
        assert frame["page"]["returned"] > 0
        for row in frame["items"]:
            assert row["value_included"] and not row["inspection_required"]
            assert (
                explorer.access._resolve(row["interpretation_location"])[0]
                == row["interpretation"]
            )
            assert (
                row["cells"]["comparison_status"]["value"]
                == row["interpretation"]["comparison"]["status"]
            )
            refs.append(row["item_ref"])
        frames.append(frame)
        cursor = frame["page"]["next_cursor"]
        if cursor is None:
            break
    assert refs == [row.item_ref for row in human.items()]
    assert human.native_payload == original
    assert selected.page(limit=4, max_bytes=8192) == frames[0]


def test_absent_source_membership_stays_explicit_and_captured_data_is_unmodified():
    card = protein()
    missing = "SA_explicit_synthetic_missing"
    card.relationships("has_ligand_site")[0]["source_assertion_ids"].append(missing)
    before = card.to_dict()
    explorer = card.explore()
    selected = explorer.access.select(TOPIC)
    page = selected.page()
    unknown = next(
        s
        for s in page["items"][0]["support"]["source_assertions"]
        if s["id"] == missing
    )
    assert unknown == {"id": missing, "state": "not_retained"}
    assert (
        expand_support(explorer.access, page)["items"][0]["support"][
            "source_assertions"
        ]
        == explorer.access._resolve(page["items"][0]["support_location"])[0][
            "source_assertions"
        ]
    )
    page["items"][0]["support"]["source_assertions"].clear()
    assert selected.page()["items"][0]["support"]["source_assertions"]
    assert card.to_dict() == before


def test_common_source_path_stays_bound_to_focal_capture_with_related_revision():
    card, other = protein(), protein(position=8)
    explorer = card.explore(related_cards=[other])
    selected = explorer.access.select(TOPIC)
    card.get("sequence.primary")["value"] = "M"
    other.get("sequence.primary")["value"] = "MM"
    item = selected.page()["items"][0]
    store = item["support"]["source_store_location"]
    assert store["card_ref"] == explorer.context["card_ref"]
    assert store["snapshot_id"] == explorer.context["snapshot_id"]
    sources = expand_support(explorer.access, {"items": [item]})["items"][0]["support"][
        "source_assertions"
    ]
    assert (
        sources
        == explorer.access._resolve(item["support_location"])[0]["source_assertions"]
    )
    assert item["interpretation"]["comparison"]["status"] == "computed"
    for source in sources:
        assert source["location"]["card_ref"] == store["card_ref"]
