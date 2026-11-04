"""Genuine earlier structure questions never acquire new navigation or science."""

import gzip
import hashlib
import importlib
import socket
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card

ORIGINALS = {
    6: (
        "card_structure_assembly_saved_v6.json.gz",
        "c7e8d06671a2e5e9ca2d2bb40861081d00f50ab218bf434d0c17645d637d24c1",
        "sha256:02baf95fe229cbc4d1e4966457f6246c801d6b3ecd637bbe3bb200c3f0d9fad3",
    ),
    7: (
        "card_nonpolymer_navigation_saved_v7.json.gz",
        "dee76cc4eca064aa743dcded62728462870ad6cae85f9c4ed0a13378ea8e4705",
        "sha256:4d297792fc40c323a278316f2e4b0e333c4c0b7422e2049f1350d1c65fccdede",
    ),
}


def forbidden(*a, **k):
    raise AssertionError(
        "No current science, navigation producer, Card or source acquisition"
    )


@pytest.mark.parametrize("version", [6, 7])
def test_genuine_original_structure_questions_keep_original_destinations(
    version, tmp_path, monkeypatch
):
    name, digest, bundle_digest = ORIGINALS[version]
    original = Path(__file__).parent / "data" / name
    assert hashlib.sha256(original.read_bytes()).hexdigest() == digest
    path = tmp_path / "original.json"
    with gzip.open(original, "rb") as source, path.open("wb") as destination:
        import shutil

        shutil.copyfileobj(source, destination)
    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    for module, functions in {
        "card_context_navigation": ["related"],
        "card_assembly_exploration": ["_materialize", "links"],
        "card_assembly_exploration_v2": ["_materialize", "links"],
        **{f"assembly_generation_v{i}": ["generation"] for i in range(1, 6)},
    }.items():
        for function in functions:
            monkeypatch.setattr(
                importlib.import_module("sabueso.core." + module), function, forbidden
            )
    view = sabueso.read_exploration(path, expected_digest=bundle_digest)
    related = view.explorer.view("structures").items()[0].related()
    assert related.native_payload["rule"] == "structure_declaration_context_links@2"
    answer = related.filter("role", equals="question").items()[0].open()
    assert answer.native_payload["rule"] == "rcsb_assembly_generation@4"
    assert "generation_rule" not in answer.request["options"]
    if version == 7:
        assert view.native_payload["rule"] == "rcsb_assembly_generation@5"
        original_links = view.items()[0].related()
        assert original_links.native_payload["rule"] == "assembly_generation_links@2"
        assert not any(
            item._entry.value["role"] == "components" for item in original_links.items()
        )
    else:
        assert (
            view.explorer.answer(
                "assembly_generation",
                options={"generation_rule": "rcsb_assembly_generation@5"},
            ).outcome["status"]
            == "not_saved"
        )
