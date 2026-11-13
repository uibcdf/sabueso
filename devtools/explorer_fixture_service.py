"""Receive the actual explorer against declared frozen public source clients.

This is development receiving, not an application offline/source-selection mode.
"""

import argparse
import asyncio
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--fixture-directory", type=Path, required=True)
    args = parser.parse_args()
    import sabueso
    from sabueso.explorer._service import _run
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db import _http
    from sabueso.tools.db.mondo import FixtureMONDOClient
    from sabueso.tools.db.pubchem import FixturePubChemClient

    def refuse(*unused, **also_unused):
        raise AssertionError("The fixture receiving service forbids network access")

    _http._urlopen = refuse
    native = EntityResolver(
        FixtureUniProtClient(args.fixture_directory, failing={"P00000"}),
        rcsb_client=FixtureRCSBClient(args.fixture_directory),
    )
    args.output_directory.mkdir(parents=True, exist_ok=False)
    calls = args.output_directory / "source-calls.jsonl"

    def resolve(query, **options):
        recorded = {"query": query, "options": dict(options)}
        if query.startswith("smiles:"):
            options["pubchem_client"] = FixturePubChemClient(args.fixture_directory)
        elif options.get("entity_type") == "disease":
            options["mondo_client"] = FixtureMONDOClient(args.fixture_directory)
        else:
            options["resolver"] = native
        card, result = sabueso.resolve(query, **options)
        with calls.open("a", encoding="utf-8") as output:
            output.write(json.dumps({**recorded, "status": result.status}) + "\n")
        return card, result

    args.card = args.reading = args.deck = None
    asyncio.run(_run(args, resolver=resolve))


if __name__ == "__main__":
    main()
