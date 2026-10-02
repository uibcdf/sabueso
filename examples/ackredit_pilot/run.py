"""A public offline workflow with two independently attributed knowledge packets."""

import argparse
import json
from pathlib import Path

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    args = parser.parse_args()
    import ackredit

    args.output.mkdir(parents=True, exist_ok=True)
    store = sabueso.KnowledgeStore(args.output / "knowledge.db")
    # Intake is explicit and outside the initial composition adapter. It reads
    # only frozen public UniProt/Europe PMC responses, never private pilot data.
    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient(args.fixtures)),
        europepmc={"article_ids": "PMC:PMC12400196"},
        europepmc_client=FixtureEuropePMCClient(args.fixtures),
    )
    store.save(card)
    with ackredit.session("public Sabueso attribution pilot"):
        with ackredit.capture("knowledge workflow") as workflow:
            with ackredit.scope("application.prepare"):
                with sabueso.attribution() as run:
                    for name, aspects in (
                        ("identity", ["identity"]),
                        ("literature", ["literature"]),
                    ):
                        packet = sabueso.compose_packet(
                            sabueso.KnowledgeQuery("P60174", aspects=aspects), card
                        )
                        store.save_packet(packet, name)
        records = run.records
        assert len(records) == 2
        for name, record in zip(("identity", "literature"), records, strict=True):
            assert record["provider"]["status"] == "available", record["provider"]
            (args.output / f"{name}.attribution.json").write_text(
                json.dumps(record, indent=2), encoding="utf-8"
            )
        (args.output / "workflow.attribution.json").write_text(
            workflow.attribution.to_json(), encoding="utf-8"
        )
        ids = [
            {item["id"] for item in record["provider"]["attribution"]["items"]}
            for record in records
        ]
        assert "doi:10.1093/nar/gkae1010" in ids[0] & ids[1]
        assert {item["id"] for item in workflow.attribution.to_dict()["items"]} == ids[
            0
        ] | ids[1]

    # A new reader session renders original records without registering or
    # crediting a new composition. Original producer/source versions stay intact.
    with ackredit.session("saved reader"):
        with sabueso.attribution() as reader:
            for name in ("identity", "literature"):
                record = json.loads(
                    (args.output / f"{name}.attribution.json").read_text()
                )
                packet = store.load_packet(name)
                assert packet.snapshot_id() == record["packet_snapshot_id"]
                original = ackredit.Attribution.from_dict(
                    record["provider"]["attribution"]
                )
                for format, extension in (("text", "txt"), ("csl-json", "csl.json")):
                    (args.output / f"{name}.references.{extension}").write_text(
                        original.report(format=format), encoding="utf-8"
                    )
        assert not reader.records
        assert not ackredit.get_attribution().to_dict()["items"]
    print(
        f"PASS: two result bibliographies, workflow union and saved readers ({args.output})"
    )


if __name__ == "__main__":
    main()
