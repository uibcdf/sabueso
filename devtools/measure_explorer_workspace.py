"""Measure the prepared public mixed-Deck workspace without source acquisition.

Use prepare_explorer_walkthrough.py first and the bounded process observer when
executing this diagnostic. One invocation is one observation, not a benchmark
distribution, speed gate, Qt receiving or an accepted workload budget. Optional
cProfile instrumentation has substantial overhead; compare unprofiled runs only.
"""

from __future__ import annotations

import argparse
import cProfile
import hashlib
import json
import platform
import pstats
import socket
import subprocess
import time
from pathlib import Path
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--profile-save", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    inputs = args.inputs.resolve()
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=False)

    import sabueso
    from sabueso.core.card import Card
    from sabueso.core.deck import Deck
    from sabueso.core.snapshot import canonical_json, digest
    from sabueso.explorer._service import _Service
    from sabueso.explorer._workspace import read_workspace, save_workspace
    from sabueso.tools.db import _http

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def forbidden(*unused_args, **unused_kwargs):
        raise AssertionError("Workspace measurement forbids source acquisition")

    socket.socket.connect = socket.create_connection = _http._urlopen = forbidden
    deck_path = inputs / "public-mixed-deck.jsonl"
    manifest = json.loads((inputs / "inputs.json").read_text())
    before = sha(deck_path)
    if manifest["deck_sha256"] != before:
        raise ValueError("Prepared public Deck differs from its input manifest")
    service = _Service(output)
    service.load_deck(deck_path.read_bytes())

    def act(name, **extra):
        return service.session.dispatch(
            {"name": name, "revision": service.session.revision, **extra}
        )

    def item(panel, predicate, *, related=False):
        row = next(row for row in panel["items"] if predicate(row["label"]))
        return act("related" if related else "open", item_ref=row["ref"])

    def identity(panel):
        # Saved reading deliberately adds its original-reading notice to text.
        # Compare exact nodes/pages and native content, not live/saved captions.
        return {
            key: panel[key]
            for key in ("view_ref", "result_ref", "offset", "count", "full_text")
        }

    def native_digest():
        return digest(
            canonical_json(service.session.card_session.current.native_payload)
        )

    initial = service.session.panel()
    selected = act("search", text="protein")
    assert len(selected["items"]) == 2
    act("open", item_ref=selected["items"][1]["ref"])
    links = item(
        act("search", text="BTS"), lambda x: x == "pdb.ligand:BTS", related=True
    )
    ligand = item(links, lambda x: x == "Entity · pdb.ligand:BTS")
    assert ligand["deck_context"]["entry_position"] == 4
    assert (
        ligand["deck_context"]["current_card"]["card_ref"]
        == manifest["cards"]["ligand"]["pin"]
    )
    groups = item(act("topic", topic="activity_context"), lambda x: True)
    records = item(groups, lambda x: True)
    assert any(
        cell.get("quantity", {}).get("unit") == "nanomolar"
        for cell in records["items"][0]["preview"]["cells"]
        if cell.get("quantity")
    )
    context = item(records, lambda x: True, related=True)
    assay = item(context, lambda x: x == "Retained original target assay context")
    assert "CHEMBL5138431" in assay["text"]
    context = act("back")
    context_digest = native_digest()
    paper = item(
        context,
        lambda x: (
            x.startswith("Full original target publication context") and "35189560" in x
        ),
    )
    assert "35189560" in paper["text"]
    paper_digest = native_digest()
    saved_path = output / "workspace.json.gz"
    profile = cProfile.Profile() if args.profile_save else None
    started = time.perf_counter()
    if profile:
        receipt = profile.runcall(save_workspace, service, saved_path)
    else:
        receipt = save_workspace(service, saved_path)
    save_seconds = time.perf_counter() - started
    timings = {"save_seconds": save_seconds, "save_profiled": args.profile_save}
    timing_path = output / "timings.json"
    timing_path.write_text(json.dumps(timings, indent=2) + "\n")
    if profile:
        profile.dump_stats(str(output / "save.prof"))
        with (output / "save-profile.txt").open("w") as stream:
            pstats.Stats(profile, stream=stream).sort_stats("cumulative").print_stats(
                40
            )

    saved_hash = sha(saved_path)
    with (
        patch.object(Card, "__init__", forbidden),
        patch.object(Deck, "__init__", forbidden),
        patch.object(sabueso, "resolve", forbidden),
        patch.object(sabueso, "resolve_disease_card", forbidden),
    ):
        started = time.perf_counter()
        reopened, resolution, history = read_workspace(
            saved_path, output, receipt["bundle_digest"]
        )
        reopen_seconds = time.perf_counter() - started
        timings["reopen_seconds"] = reopen_seconds
        timing_path.write_text(json.dumps(timings, indent=2) + "\n")
        restored = reopened.panel()
        assert identity(restored) == identity(paper)
        assert restored["mode"] == "saved"
        assert restored["deck_context"]["entry_position"] == 4
        assert resolution is None and history == []
        service.session = reopened
        assert native_digest() == paper_digest
        assert identity(act("back")) == identity(context)
        assert native_digest() == context_digest
        deck = act("deck")
        assert identity(deck) == identity(selected)
        assert deck["items"] == selected["items"]
        assert identity(act("back")) == identity(initial)
    assert sha(deck_path) == before and sha(saved_path) == saved_hash
    report = {
        "format": "sabueso.explorer_workspace_cost_observation@1",
        "owner": "uibcdf/sabueso#154/#153",
        "source_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "code_sha256": {
            str(path.relative_to(root)): sha(path)
            for path in [
                Path(__file__).resolve(),
                root / "sabueso/explorer/_workspace.py",
                root / "sabueso/explorer/_deck_session.py",
                root / "sabueso/core/card_exploration_storage.py",
                root / "sabueso/core/deck_exploration_storage.py",
            ]
        },
        "python": platform.python_version(),
        "input_deck_sha256": before,
        "save_seconds": save_seconds,
        "reopen_seconds": reopen_seconds,
        "save_profiled": args.profile_save,
        "receipt": receipt,
        "saved_sha256": saved_hash,
        "native_publication_digest": paper_digest,
        "native_context_digest": context_digest,
        "checks": {
            "source_bound_ligand_and_repeated_entry": True,
            "native_quantity_assay_and_publication": True,
            "inert_original_reopening_and_exact_trail": True,
            "exact_filtered_deck_and_original_back": True,
            "unchanged_input_and_saved_bytes": True,
        },
        "limits": "One in-process observation; no Qt, fresh-process, installed-artifact, scaling or accepted-budget claim",
    }
    (output / "observation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
