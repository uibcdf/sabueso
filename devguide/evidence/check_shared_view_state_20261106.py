"""Receive the full public Q8WZ42 native-region session without provider queries.

Run under a resource supervisor (one low-priority CPU, 512 MiB owned RSS,
zero owned swap and a host-memory reserve):
    python check_shared_view_state_20261106.py --card ORIGINAL_CARD --output NEW_DIR

The pinned complete public Card is a caller input, not a reduced synthetic fixture.
Writer and cold reader run successively: neither keeps another complete process's
session resident. Original failures and smaller historical controls remain separate.
This engineering control does not establish scientific or researcher acceptance.
"""

import argparse
import builtins
import gc
import hashlib
import importlib.metadata
import json
import socket
import subprocess
import sys
from pathlib import Path

CARD_SHA256 = "995fd68dd95a672af065fc1f6081e0c6e06e088873bdccef6bcdf7e6c1e569e2"
WIRE_SHA256 = "d8f419db3baac1ad5f9a7fcb8da1b91ce1644530b9923386f595aabbe83d9350"
RESULT_REF = "XR_0ce5e2d583b0dbf47570a84416f8f0453018c10eea6fda8a48ad7867ddfdbc63"


def forbidden(*args, **kwargs):
    raise AssertionError("No source query or current reconstruction in cold receiving")


def sdk(expected):
    import sabueso

    assert sabueso.__version__ == importlib.metadata.version("sabueso")
    if expected:
        assert sabueso.__version__ == expected
    return sabueso.__version__


def write(arguments):
    from sabueso.core.card import Card
    from sabueso.core.snapshot import canonical_json

    version = sdk(arguments.expected_sdk)
    raw = arguments.card.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CARD_SHA256
    card = Card.from_dict(json.loads(raw))
    before = card.to_dict()
    explorer = card.explore()
    (item,) = explorer.answer("predicted_models").items()
    links = item.related()
    (question,) = links.filter("role", equals="question").items()
    basis = question._entry.value["model_context"]
    assert basis["state"] == "ready"
    assert basis["request"]["options"] == {
        "sequence_ref": "uniprot:Q8WZ42",
        "region": [[201, 1600]],
        "include_fragments": True,
    }
    assert basis["original_model_context"]["comparison"]["reference_date_equal"] is None
    sources = links.filter("role", equals="source").items()
    assert len(sources) == 5
    for source in sources:
        assert source.open().native_payload["source"]
    answer = question.open()
    agent = explorer.access.select(
        "structures",
        fields=["structure_ref"],
        options={"region": [[201, 1600]], "include_fragments": True},
    )
    assert answer.result_ref == agent.result_ref == RESULT_REF
    assert answer.back() is question.back()
    assert "date agreement remains unknown" in str(answer)
    assert "experimental equivalence" in answer._repr_html_()
    assert len(answer.items()) == 64
    assert (
        hashlib.sha256(
            canonical_json(answer._selection._scientific.wire).encode()
        ).hexdigest()
        == WIRE_SHA256
    )
    path = arguments.output / "native-shared.json.gz"
    receipt = answer.save(path, compression="gzip")
    assert card.to_dict() == before
    result = {
        "owner": "uibcdf/sabueso#167/#148/#112",
        "review_trigger": "final code checkpoint / B3 full-workload acceptance",
        "sdk": version,
        "control_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_card_sha256": CARD_SHA256,
        "captured_card_sha256": hashlib.sha256(
            canonical_json(before).encode()
        ).hexdigest(),
        "source_assertions": len(card.source_assertion_store.store),
        "relationships": len(card.relationship_store.store),
        "retained_inventory_items": 64,
        "reference_interval": [201, 1600],
        "original_source_routes": 5,
        "new_source_queries": 0,
        "card_unchanged": True,
        "result_ref": RESULT_REF,
        "original_native_wire_sha256": WIRE_SHA256,
        "saved_bytes": path.stat().st_size,
        "saved_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "save_transport": receipt["transport"],
        "bundle_digest": receipt["bundle_digest"],
    }
    assert result["source_assertions"] == 1490 and result["relationships"] == 215
    (arguments.output / "writer.json").write_text(json.dumps(result, indent=2) + "\n")


def read(arguments):
    import sabueso
    from sabueso.core.card import Card
    from sabueso.core.snapshot import canonical_json

    version = sdk(arguments.expected_sdk)
    old_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "gemmi" or name.startswith("sabueso.mappings.alphafold_modelcif"):
            forbidden()
        return old_import(name, *args, **kwargs)

    builtins.__import__ = guarded
    Card.from_dict = forbidden
    Card.__init__ = forbidden
    original = json.loads((arguments.output / "writer.json").read_text())
    saved = sabueso.read_exploration(
        arguments.output / "native-shared.json.gz",
        expected_digest=original["bundle_digest"],
    )
    assert saved.validation["storage_format"] == "sabueso.card_exploration@13"
    assert (
        saved.validation["representation_verifier"]
        == "shared_exploration_values_binding@1"
    )
    assert saved.validation["verifier"] == "native_model_navigation_binding@1"
    assert len(saved.items()) == 64
    assert len(saved.explorer.access._focal.data["source_assertion_store"]) == 1490
    assert len(saved.explorer.access._focal.data["relationship_store"]) == 215
    assert (
        hashlib.sha256(
            canonical_json(saved.explorer.access._focal.data).encode()
        ).hexdigest()
        == original["captured_card_sha256"]
    )
    assert saved.result_ref == RESULT_REF
    assert (
        hashlib.sha256(
            canonical_json(saved._selection._scientific.wire).encode()
        ).hexdigest()
        == WIRE_SHA256
    )
    links = saved.explorer.answer("predicted_models").items()[0].related()
    question = links.filter("role", equals="question").items()[0]
    assert question.open().result_ref == saved.result_ref
    assert len(links.filter("role", equals="source").items()) == 5
    path = arguments.output / "resaved.json.gz"
    receipt = saved.save(path, compression="gzip")
    gc.collect()
    restored = sabueso.read_exploration(path, expected_digest=receipt["bundle_digest"])
    assert restored.result_ref == saved.result_ref
    assert len(restored.items()) == 64
    assert (
        hashlib.sha256(
            canonical_json(restored._selection._scientific.wire).encode()
        ).hexdigest()
        == WIRE_SHA256
    )
    result = {
        "sdk": version,
        "validation": saved.validation,
        "result_ref": saved.result_ref,
        "resave_transport": receipt["transport"],
    }
    (arguments.output / "cold.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-sdk")
    parser.add_argument("--phase", choices=["write", "read"], help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    arguments.card = arguments.card.resolve()
    arguments.output = arguments.output.resolve()
    socket.socket.connect = forbidden
    socket.create_connection = forbidden
    if arguments.phase:
        return {"write": write, "read": read}[arguments.phase](arguments)
    arguments.output.mkdir(parents=True, exist_ok=False)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--card",
        str(arguments.card),
        "--output",
        str(arguments.output),
    ]
    if arguments.expected_sdk:
        command.extend(["--expected-sdk", arguments.expected_sdk])
    for phase in ("write", "read"):
        subprocess.run(
            command + ["--phase", phase], cwd=arguments.output, check=True, timeout=480
        )
    result = json.loads((arguments.output / "writer.json").read_text())
    result["cold"] = json.loads((arguments.output / "cold.json").read_text())
    assert result["sdk"] == result["cold"]["sdk"]
    result["process_topology"] = (
        "successive independent writer and cold receiver; supervisor includes orchestrator and each active child"
    )
    (arguments.output / "receiving.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
