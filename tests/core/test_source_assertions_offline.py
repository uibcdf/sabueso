import importlib
import json
import pkgutil
import re
from pathlib import Path

import yaml

import sabueso
from sabueso.core.card import Card
from sabueso.tools.db.uniprot import create_protein_card_from_file

EVIDENCE = re.compile(r"evidence", re.IGNORECASE)


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for item in node:
            yield from _keys(item)


def test_card_round_trip_keeps_source_assertions(tmp_path: Path):
    card = create_protein_card_from_file("temp_data/P52789.json", retrieved_at="2026-02-01")
    out = tmp_path / "card.json"
    card.to_json(str(out))

    loaded = Card.from_json(str(out))

    node = loaded.get("annotations.organism")
    assert node["source_assertion_ids"]
    for sa_id in node["source_assertion_ids"]:
        assertion = loaded.source_assertion_store.get(sa_id)
        assert assertion is not None
        assert assertion["source"]["name"] == "UniProt"
        assert assertion["value"] == node["value"]
    assert loaded.to_dict() == card.to_dict()


def test_public_api_and_schemas_use_source_assertion_terminology():
    public_names = []
    for info in pkgutil.walk_packages(sabueso.__path__, prefix="sabueso."):
        module = importlib.import_module(info.name)
        public_names.append(info.name)
        public_names.extend(name for name in vars(module) if not name.startswith("_"))
    assert [name for name in public_names if EVIDENCE.search(name)] == []

    for schema in Path("schemas").glob("*.yaml"):
        keys = list(_keys(yaml.safe_load(schema.read_text(encoding="utf-8"))))
        assert [key for key in keys if EVIDENCE.search(str(key))] == [], schema

    card = create_protein_card_from_file("temp_data/P52789.json", retrieved_at="2026-02-01")
    serialized = json.loads(json.dumps(card.to_dict()))
    assert [key for key in _keys(serialized) if EVIDENCE.search(str(key))] == []
