"""A public offline workflow with source traces and three attributed knowledge packets."""

import argparse
import json
from pathlib import Path

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient
from sabueso.tools.db.rcsb import FixtureRCSBClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    args = parser.parse_args()
    import ackredit

    args.output.mkdir(parents=True, exist_ok=True)
    store = sabueso.KnowledgeStore(args.output / "knowledge.db")
    records = []
    with ackredit.session("public Sabueso attribution pilot"):
        with ackredit.capture("knowledge workflow") as workflow:
            # Intake reads only declared frozen public responses. Its runtime
            # trace is saved separately from the scientific card and packets.
            card, resolution = sabueso.resolve(
                "P60174",
                resolver=EntityResolver(
                    FixtureUniProtClient(args.fixtures),
                    rcsb_client=FixtureRCSBClient(args.fixtures),
                ),
                structures=["1HTI", "1KLG"],
                europepmc={"article_ids": "PMC:PMC12400196"},
                europepmc_client=FixtureEuropePMCClient(args.fixtures),
            )
            trace = card.acquisition_trace
            assert trace == resolution.acquisition_trace
            assert trace["card_ref"] == card.pinned_ref()
            assert len(trace["records"]) == 3
            assert all(r["access"] == "fixture" for r in trace["records"])
            assert all(r["network_attempts"] == 0 for r in trace["records"])
            assert all(r["provider"]["status"] == "available" for r in trace["records"])
            store.save(card)
            (args.output / "acquisition.trace.json").write_text(
                json.dumps(trace, indent=2), encoding="utf-8"
            )
            with ackredit.scope("application.prepare"):
                for name, aspects in (
                    ("identity", ["identity"]),
                    ("literature", ["literature"]),
                    ("structures", ["structures"]),
                ):
                    packet = sabueso.compose_packet(
                        sabueso.KnowledgeQuery("P60174", aspects=aspects), card
                    )
                    store.save_packet(packet, name)
                    records.append(packet.attribution)
        assert len(records) == 3
        for name, record in zip(
            ("identity", "literature", "structures"), records, strict=True
        ):
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
        assert "doi:10.1093/nar/gkae1091" in ids[2]
        intake_ids = {
            item["id"]
            for record in trace["records"]
            for item in record["provider"]["attribution"]["items"]
        }
        assert {item["id"] for item in workflow.attribution.to_dict()["items"]} == (
            intake_ids | set().union(*ids)
        )
        assert any(
            item.get("url") == "https://pubmed.ncbi.nlm.nih.gov/8061610/"
            for record in trace["records"]
            for item in record["bibliography"]
        )

    # A new reader session renders original records without registering or
    # crediting a new composition. Original producer/source versions stay intact.
    with ackredit.session("saved reader"):
        with sabueso.attribution() as reader:
            saved_trace = json.loads(
                (args.output / "acquisition.trace.json").read_text()
            )
            assert saved_trace == trace
            assert store.load(card.id).acquisition_trace is None
            for record in saved_trace["records"]:
                original = ackredit.Attribution.from_dict(
                    record["provider"]["attribution"]
                )
                for format, extension in (("csl-json", "csl.json"), ("bibtex", "bib")):
                    (
                        args.output
                        / f"intake.{record['source'].replace(' ', '_')}.{extension}"
                    ).write_text(original.report(format=format), encoding="utf-8")
            original_workflow = ackredit.Attribution.from_dict(
                json.loads((args.output / "workflow.attribution.json").read_text())
            )
            for format, extension in (("csl-json", "csl.json"), ("bibtex", "bib")):
                (args.output / f"workflow.references.{extension}").write_text(
                    original_workflow.report(format=format), encoding="utf-8"
                )
            for name in ("identity", "literature", "structures"):
                record = json.loads(
                    (args.output / f"{name}.attribution.json").read_text()
                )
                packet = store.load_packet(name)
                assert packet.snapshot_id() == record["packet_snapshot_id"]
                original = ackredit.Attribution.from_dict(
                    record["provider"]["attribution"]
                )
                for format, extension in (
                    ("text", "txt"),
                    ("csl-json", "csl.json"),
                    ("bibtex", "bib"),
                ):
                    (args.output / f"{name}.references.{extension}").write_text(
                        original.report(format=format), encoding="utf-8"
                    )
        assert not reader.records
        assert not reader.acquisitions
        assert not ackredit.get_attribution().to_dict()["items"]
    print(
        f"PASS: source traces, three result bibliographies, workflow union and saved readers ({args.output})"
    )


if __name__ == "__main__":
    main()
