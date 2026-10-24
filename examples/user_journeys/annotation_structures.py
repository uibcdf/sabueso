"""Inspect public annotation-to-structure context and reopen its original reading."""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import sabueso


def first_active(explorer):
    return (
        explorer.view("annotated_regions")
        .filter("feature_type", equals="active_site")
        .items()[0]
    )


def structural_question(item):
    return item.related().filter("role", equals="question").items()[0]


def produce(fixtures, output):
    from sabueso.core.card import Card
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.rcsb import FixtureRCSBClient

    output.mkdir(parents=True, exist_ok=True)
    resolver = EntityResolver(
        FixtureUniProtClient(fixtures), rcsb_client=FixtureRCSBClient(fixtures)
    )
    current, _ = sabueso.resolve("P52270", resolver=resolver, structures=["1SUX"])
    item = first_active(current.explore())
    print("Choose an individual original annotation:\n", item.back())
    print("Inspect its exact source support:\n", item.explain())
    print(
        "Inspect original annotation, identity, sequence and length inputs:\n",
        item.related(),
    )
    view = structural_question(item).open()
    assert view.request["options"]["region"] == [96]
    print("Read the existing structural inventory for the declared positions:\n", view)
    receipts = {"current": view.save(output / "current.json")}

    legacy = Card.from_dict(
        json.loads(
            (fixtures / "frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )
    unavailable = structural_question(first_active(legacy.explore())).open()
    assert unavailable.outcome["status"] == "missing_prerequisite"
    print(
        "A historical recorded position cannot supply missing native scope:\n",
        unavailable,
    )
    receipts["legacy"] = unavailable.save(output / "legacy.json")
    (output / "receipts.json").write_text(
        json.dumps(receipts, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "No source queries or structure recommendation. This is technical preparation, not measured researcher acceptance."
    )


def read(output):
    receipts = json.loads((output / "receipts.json").read_text(encoding="utf-8"))
    for name in ("current", "legacy"):
        saved = sabueso.read_exploration(
            output / f"{name}.json", expected_digest=receipts[name]["bundle_digest"]
        )
        link = saved.back().items()[0]
        assert link.open().outcome["status"] == saved.outcome["status"]
        if name == "current":
            assert saved.request["options"]["region"] == [96]
            assert link.open().result_ref == saved.result_ref
        else:
            assert saved.outcome["status"] == "missing_prerequisite"
        annotations = saved.back().back().back().back()
        source = annotations.items()[0].explain().items()[0].open()
        assert source.native_payload["source"]["name"] == "UniProt"
        print(
            f"{name}: original structural question, source and return path reopened.\n{saved}"
        )


def forbidden(*args, **kwargs):
    raise RuntimeError("This public fixture journey must remain offline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    producer = commands.add_parser("produce")
    producer.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    producer.add_argument("--output", type=Path, required=True)
    reader = commands.add_parser("read")
    reader.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (
        patch("socket.create_connection", forbidden),
        patch("socket.socket.connect", forbidden),
    ):
        if args.command == "produce":
            produce(args.fixtures, args.output)
        else:
            read(args.output)


if __name__ == "__main__":
    main()
