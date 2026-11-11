"""Prepare three public Card inputs for an independent researcher review.

Run this maintainer helper from a development checkout. It exports inputs, source
notices and an integrity manifest; it does not execute or solve review tasks.
"""

import argparse
import hashlib
import json
import subprocess
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

import sabueso
from sabueso.core.card import Card
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.mondo import FixtureMONDOClient


def forbidden(*args, **kwargs):
    raise RuntimeError("Review preparation must use public local fixtures only")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(fixtures, output):
    """Export verified inputs to a new or empty caller-owned directory."""
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError("Choose a new or empty output directory")
    notice = fixtures / "NOTICE.md"
    if not notice.is_file():
        raise ValueError("The public fixture NOTICE.md is required")
    checkout = Path(__file__).resolve().parents[2]
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=checkout, text=True
        ).strip()
    )
    with ExitStack() as stack:
        for target in (
            "socket.create_connection",
            "socket.socket.connect",
            "socket.socket.connect_ex",
        ):
            stack.enter_context(patch(target, forbidden))
        protein, _ = sabueso.resolve(
            "P52270",
            resolver=EntityResolver(
                FixtureUniProtClient(fixtures),
                rcsb_client=FixtureRCSBClient(fixtures / "rcsb_nonpolymer_instances"),
            ),
            structures=["1SUX"],
        )
        molecule = single_molecule_card(
            chembl=FixtureChEMBLClient(fixtures).molecules(["CHEMBL110"])
        )
        disease = resolve_disease_card(
            "MONDO:0014221", mondo_client=FixtureMONDOClient(fixtures)
        )[0]
        output.mkdir(parents=True, exist_ok=True)
        entries = {}
        for role, card in (
            ("protein", protein),
            ("molecule", molecule),
            ("disease", disease),
        ):
            path = output / f"{role}.json"
            card.to_json(str(path))
            restored = Card.from_json(str(path))
            if restored.pinned_ref() != card.pinned_ref():
                raise ValueError(f"The {role} Card changed during export")
            entries[role] = {
                "file": path.name,
                "sha256": sha256(path),
                "pinned_ref": card.pinned_ref(),
            }
    (output / "SOURCE_NOTICE.md").write_bytes(notice.read_bytes())
    manifest = {
        "format": "sabueso.researcher_review_inputs@1",
        "source_commit": commit,
        "source_tree_dirty": dirty,
        "sabueso_runtime": sabueso.__version__,
        "sabueso_distribution": version("sabueso"),
        "preparation_script_sha256": sha256(Path(__file__).resolve()),
        "fixture_notice_sha256": sha256(notice),
        "cards": entries,
        "scope": "Three public fixture Cards, no solved tasks or exploration sessions",
        "acceptance": "pending_independent_review",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Prepared review inputs: {output / 'manifest.json'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.fixtures, args.output)


if __name__ == "__main__":
    main()
