"""Observe one synthetic repeated-position workload; never acquire source data.

Use a fresh process for each produce/read invocation, under an external RSS/swap/
scratch supervisor. Timings are observations, not performance gates. The synthetic
generator is diagnostic material, not a provider response or scientific knowledge.
The output directory must be new. Read consumes only its saved original/receipt.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib
import json
import platform
import socket
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "tests/core/data/assembly_nonpolymer_live_v2.json.gz"
CAPSULE_SHA256 = "b37ef7b9ebe68bbe4d46d6ff65a73522b044b0935f0a2e9128104c30e1e5e57d"


def forbidden(*args, **kwargs):
    raise AssertionError("No source acquisition or current scientific producer")


def digest(value):
    from sabueso.core.snapshot import canonical_json

    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def role(view, name):
    return view.filter("role", equals=name).items()[0]


def metadata():
    import sabueso

    return {
        "source": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runtime_tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD:sabueso"], cwd=ROOT, text=True
        ).strip(),
        "sdk": sabueso.__version__,
        "python": sys.version,
        "platform": platform.platform(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def timed(samples, name, operation):
    wall, cpu = time.perf_counter(), time.process_time()
    result = operation()
    samples[name] = {
        "wall_s": time.perf_counter() - wall,
        "cpu_s": time.process_time() - cpu,
    }
    return result


def stage(directory, name):
    path = directory / "stage.json"
    temporary = directory / "stage.new"
    temporary.write_text(json.dumps({"stage": name}) + "\n")
    temporary.replace(path)


def selection_for(explorer, request, item_ref):
    selected = explorer.access.select(
        "assembly_generation",
        options=request["options"],
        fields=["declaration_count", "component_scope"],
        item_refs=[item_ref],
    )
    return selected


def page_for(explorer, request, item_ref):
    selected = selection_for(explorer, request, item_ref)
    page = selected.page(limit=1, max_bytes=8192)
    assert page["page"]["complete"] and page["page"]["values_complete"]
    assert len(page["items"]) == 1, {
        key: value for key, value in page.items() if key != "items"
    }
    return selected, page


def produce(args):
    from sabueso.core.card import Card
    from sabueso.core.snapshot import canonical_json

    directory = args.output_directory
    directory.mkdir(parents=True, exist_ok=False)
    raw = CAPSULE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CAPSULE_SHA256
    original = json.loads(gzip.decompress(raw))["cases"]["1HTI"]["card"]
    original_digest = digest(original)
    card = Card.from_dict(deepcopy(original))
    source = next(
        value
        for value in card.source_assertion_store.store.values()
        if value["source"]["name"] == "RCSB PDB"
    )
    generator = source["asserted_value"]["assembly_generation_inputs"]["assemblies"][0][
        "pdbx_struct_assembly_gen"
    ][0]
    generator["asym_id_list"] = ["C"] * args.positions
    before = digest(card.to_dict())
    assert digest(original) == original_digest
    samples = {}
    stage(directory, "capture")
    explorer = timed(samples, "capture", card.explore)

    def navigate():
        item = (
            explorer.view("structures")
            .filter("structure_ref", equals="pdb:1HTI")
            .items()[0]
        )
        answer = role(item.related(), "question").open()
        generator_item = answer.filter("kind", equals="assembly_generator").items()[0]
        components = role(generator_item.related(), "components").open()
        positions = components.filter("role", equals="component")
        indices = [
            item._entry.value["component_request"]["component_index"]
            for item in positions.items()
        ]
        assert indices == list(range(args.positions))
        detail = positions.items()[-1].open()
        record = role(detail, "component_record").open()
        support = role(detail, "source").open()
        return answer, generator_item, positions, detail, record, support

    stage(directory, "navigate")
    answer, generator_item, positions, detail, record, support = timed(
        samples, "navigate", navigate
    )
    stage(directory, "preview")
    text, html = timed(
        samples, "preview", lambda: (str(positions), positions._repr_html_())
    )
    assert text and html
    stage(directory, "agent_page")
    selected, page = timed(
        samples,
        "agent_page",
        lambda: page_for(explorer, answer.request, generator_item.item_ref),
    )
    assert selected.result_ref == answer.result_ref
    assert page["items"][0]["cells"]["declaration_count"]["value"] == args.positions
    expected = {
        "root_payload_sha256": digest(detail.native_payload),
        "scientific_wire_sha256": digest(explorer.access._objects[answer.result_ref]),
        "record_payload_sha256": digest(record.native_payload),
        "source_payload_sha256": digest(support.native_payload),
        "result_ref": answer.result_ref,
        "generator_item_ref": generator_item.item_ref,
        "request": answer.request,
    }
    stage(directory, "save")
    saved = timed(samples, "save", lambda: detail.save(directory / "original.json"))
    stage(directory, "save_agent_accumulated")
    saved_agent = timed(
        samples,
        "save_agent_accumulated",
        lambda: selected.save(directory / "agent.json"),
    )
    assert digest(card.to_dict()) == before
    assert digest(original) == original_digest
    assert hashlib.sha256(CAPSULE.read_bytes()).hexdigest() == CAPSULE_SHA256
    report = {
        "format": "component_navigation_workload@1",
        "owner": "#167/#148/#173",
        "producer": metadata(),
        "input": {
            "capsule": CAPSULE.relative_to(ROOT).as_posix(),
            "capsule_sha256": CAPSULE_SHA256,
            "original_card_sha256": original_digest,
            "synthetic_card_sha256": before,
            "basis": "synthetic repeated native C labels in one 1HTI generator; not a provider observation, distinct physical molecules or production knowledge",
            "positions": args.positions,
        },
        "scope": "Fresh native-structure question, full positions, last position and first original record/source visited; human plain JSON save first; explicit agent selection saved afterwards in the accumulated session. The second save is not a fresh agent workload. No timing threshold or researcher acceptance.",
        "operations": samples,
        "expected": expected,
        "sizes": {
            "saved_bytes": (directory / "original.json").stat().st_size,
            "accumulated_agent_saved_bytes": (directory / "agent.json").stat().st_size,
            "complete_agent_page_bytes": len(canonical_json(page).encode()),
            "full_component_list_bytes": len(
                canonical_json(positions.native_payload).encode()
            ),
        },
        "save_receipt": saved,
        "agent_save_receipt": saved_agent,
        "source_queries": 0,
        "originals_and_card_unchanged": True,
        "conditions": "Serial fresh worker, warm/uncontrolled filesystem and host load. Import/loading/setup excluded from operation times; parent sampled RSS separately. No tracemalloc instrumented timing.",
    }
    (directory / "producer.json").write_text(json.dumps(report, indent=2) + "\n")
    stage(directory, "produced")
    print(
        json.dumps(
            {
                "phase": "produce",
                "positions": args.positions,
                "sizes": report["sizes"],
                "operations": samples,
            }
        )
    )


def read(args):
    import sabueso
    from sabueso.core.card import Card

    directory = args.output_directory
    producer = json.loads((directory / "producer.json").read_text())
    expected = producer["expected"]
    # Restore from the original, independently verified wire. No current Card,
    # scientific catalog, native evaluator or navigation producer may help it.
    importlib.import_module("sabueso.core.card_assembly_access_v2")
    Card.__init__ = Card.from_dict = forbidden
    for name, methods in {
        "card_context_navigation": ["related"],
        "card_structure_context_v3": ["related"],
        "card_assembly_exploration_v2": ["_materialize", "options_for_assembly"],
        "card_assembly_component_context_v1": ["assembly_related", "_emit"],
        **{f"assembly_generation_v{i}": ["generation"] for i in range(1, 6)},
    }.items():
        module = importlib.import_module("sabueso.core." + name)
        for method in methods:
            setattr(module, method, forbidden)
    agent = args.phase == "read-agent"
    filename = "agent.json" if agent else "original.json"
    receipt_name = "agent_save_receipt" if agent else "save_receipt"
    stage(directory, "read_agent_verify" if agent else "read_human_verify")
    samples = {}
    view = timed(
        samples,
        "read_verify",
        lambda: sabueso.read_exploration(
            directory / filename,
            expected_digest=producer[receipt_name]["bundle_digest"],
        ),
    )
    stage(directory, "parity")
    assert (
        digest(view.explorer.access._objects[expected["result_ref"]])
        == expected["scientific_wire_sha256"]
    )
    if agent:
        selected, page = page_for(
            view.explorer, expected["request"], expected["generator_item_ref"]
        )
        assert selected.result_ref == expected["result_ref"]
        assert (
            page["items"][0]["cells"]["declaration_count"]["value"]
            == producer["input"]["positions"]
        )
    else:
        assert digest(view.native_payload) == expected["root_payload_sha256"]
        positions = view.back()
        indices = [
            item._entry.value["component_request"]["component_index"]
            for item in positions.items()
        ]
        assert indices == list(range(producer["input"]["positions"]))
        assert positions.items()[-1].open().native_payload == view.native_payload
        assert (
            digest(role(view, "component_record").open().native_payload)
            == expected["record_payload_sha256"]
        )
        assert (
            digest(role(view, "source").open().native_payload)
            == expected["source_payload_sha256"]
        )
        # Paging a live projection does not implicitly save that exact request.
        missing = selection_for(
            view.explorer, expected["request"], expected["generator_item_ref"]
        )
        assert missing.page(limit=1, max_bytes=8192)["outcome"]["status"] == "not_saved"
        assert str(positions) and positions._repr_html_()
    report = {
        "format": "component_navigation_read_receipt@1",
        "consumer": metadata(),
        "phase": args.phase,
        "positions": producer["input"]["positions"],
        "operations": samples,
        "original_binding_parity": True,
        "current_producers_forbidden": True,
        "source_queries": 0,
        "validation": view.validation,
    }
    (directory / f"{args.phase}.json").write_text(json.dumps(report, indent=2) + "\n")
    stage(directory, "verified")
    print(
        json.dumps(
            {
                "phase": args.phase,
                "positions": producer["input"]["positions"],
                "operations": samples,
                "original_binding_parity": True,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="phase", required=True)
    producer = commands.add_parser("produce")
    producer.add_argument("output_directory", type=Path)
    producer.add_argument("--positions", required=True, type=int)
    for name in ("read", "read-agent"):
        commands.add_parser(name).add_argument("output_directory", type=Path)
    args = parser.parse_args()
    if args.phase == "produce" and args.positions < 1:
        parser.error("--positions must be positive")
    socket.create_connection = socket.socket.connect = forbidden
    (produce if args.phase == "produce" else read)(args)


if __name__ == "__main__":
    main()
