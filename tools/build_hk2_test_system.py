"""Rebuild the public HK2 test card/report from the qualified UniProt fixture."""

import argparse
import hashlib
import json
from pathlib import Path

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "temp_data/P52789.json"
RETRIEVED_AT = "2026-09-23"  # The public acquisition declared in temp_data/NOTICE.md.


def build(output):
    """Generate current documents without importing historical cards or querying sources."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    card, resolution = sabueso.resolve(
        "P52789",
        resolver=EntityResolver(
            FixtureUniProtClient(FIXTURE.parent, retrieved_at=RETRIEVED_AT)
        ),
    )
    report = card.to_notebook(
        output / "HK2_human.ipynb",
        title="Human hexokinase-2 — public offline test system",
        include_card_snapshot=True,
    )
    receipt = {
        "format": "sabueso.hk2_test_system@1",
        "card_ref": card.pinned_ref(),
        "schema_version": card.meta["schema_version"],
        "resolution_status": resolution.status,
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "fixture_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "fixture_retrieved_at": RETRIEVED_AT,
        "source_assertions": len(card.source_assertion_store.to_list()),
        "qualified_scope": ["UniProt entry and its source-supported declarations"],
        "source_requests": 0,
        "historical_cards_imported": False,
        "card_file": report.with_suffix(".card.json").name,
        "notebook_file": report.name,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return card, receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, receipt = build(args.output)
    print(json.dumps(receipt, indent=2))
