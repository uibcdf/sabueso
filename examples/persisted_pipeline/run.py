"""Public application exercise: produce, read and reuse in separate processes."""

import argparse
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import ackredit

import sabueso
from sabueso.core.errors import RecordNotFoundError, SchemaError, StorageError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db import europepmc
from sabueso.tools.db.rcsb import FixtureRCSBClient

PUBLICATION = "pubmed:40832834"
ASPECTS = ["identity", "literature", "structures"]
# These files bind this example's outputs, not a shared MOLI ProjectRecord format.
FORMAT = "sabueso.persisted_pipeline_example@1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2),
        encoding="utf-8",
    )


@contextmanager
def offline():
    def forbidden(*args, **kwargs):
        raise RuntimeError("This public exercise must never reach the network")

    with (
        patch("socket.create_connection", forbidden),
        patch("sabueso.tools.db._http._urlopen", forbidden),
    ):
        yield


def save_stage(store, card, name):
    card_ref = store.save(card)
    packets = {}
    for detail in ("full", "index"):
        packet = sabueso.compose_packet(
            sabueso.KnowledgeQuery("P60174", aspects=ASPECTS, detail=detail), card
        )
        packets[detail] = {
            "ref": store.save_packet(packet, "pipeline-" + detail),
            "attribution": packet.attribution,
        }
    assertion = next(
        a
        for a in card.source_assertion_store.to_list()
        if a["field_path"] == "literature.article_metadata"
    )
    # Capture.attribution is final only after its context exits. The caller writes
    # the manifest afterwards; all scientific references already have exact pins.
    return {
        "format": FORMAT,
        "stage": name,
        "card_ref": card_ref,
        "packets": packets,
        "item_id": assertion["id"],
        "item_ref": card_ref + "#" + assertion["id"],
        "item_sha256": hashlib.sha256(
            json.dumps(assertion, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
    }


def finish_stage(output, manifest, observed, workflow):
    name = manifest["stage"]
    observations = {
        "acquisitions": observed.acquisitions,
        "literature": observed.literature,
        "packets": observed.records,
    }
    for kind, records in observations.items():
        for record in records:
            if kind != "acquisitions" or record["outcome"] == "received":
                require(
                    record["provider"]["status"] == "available",
                    "Completed operation has incomplete attribution",
                )
    files = {
        f"{name}.observations.json": observations,
        f"{name}.workflow.json": workflow.attribution.to_dict(),
    }
    for detail, packet in manifest["packets"].items():
        filename = f"{name}.{detail}.attribution.json"
        files[filename] = packet.pop("attribution")
        packet["attribution_file"] = filename
    for filename, value in files.items():
        write_json(output / filename, value)
    manifest["files"] = {filename: sha256(output / filename) for filename in files}
    manifest["files"]["extractions.jsonl"] = sha256(output / "extractions.jsonl")
    write_json(output / f"{name}.manifest.json", manifest)


def produce(output, fixtures):
    require(not output.exists() or not any(output.iterdir()), "Output must be empty")
    output.mkdir(parents=True, exist_ok=True)
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    extractions = sabueso.ExtractionStore(output / "extractions.jsonl")
    with offline(), ackredit.session("public pipeline producer"):
        with sabueso.attribution() as observed, ackredit.capture("produce") as workflow:
            card, _ = sabueso.resolve(
                "P60174",
                resolver=EntityResolver(
                    FixtureUniProtClient(
                        fixtures, retrieved_at="original fixture read"
                    ),
                    rcsb_client=FixtureRCSBClient(fixtures),
                ),
                structures=["1HTI", "1KLG"],
            )
            client = europepmc.FixtureEuropePMCClient(fixtures)
            metadata = europepmc.get_article(PUBLICATION, client=client)
            # Deliberately unavailable fixture: this does not assert that the
            # publication is absent from Europe PMC. Keep its observed outcome.
            try:
                europepmc.get_article("pubmed:9999999999", client=client)
            except RecordNotFoundError:
                pass
            result = sabueso.extract_literature_mentions(
                "Synthetic example: UniProt:P60174",
                "P60174",
                PUBLICATION,
                "Synthetic application fragment, not a quotation or article finding",
                article_metadata=metadata,
            )
            extractions.save(result)
            card.add_literature_extraction(result)
            manifest = save_stage(store, card, "original")
        finish_stage(output, manifest, observed, workflow)
    return manifest


def load_stage(output, name):
    manifest = json.loads((output / f"{name}.manifest.json").read_text("utf-8"))
    require(manifest["format"] == FORMAT, "Unsupported example manifest")
    require(manifest["stage"] == name, "Stage differs from manifest")
    require(set(manifest["packets"]) == {"full", "index"}, "Expected both packets")
    if name == "reused":
        require(
            sha256(output / "original.manifest.json")
            == manifest["original_manifest_sha256"],
            "Original manifest differs from reused workflow binding",
        )
    required = {
        "extractions.jsonl",
        f"{name}.observations.json",
        f"{name}.workflow.json",
        *(packet["attribution_file"] for packet in manifest["packets"].values()),
    }
    require(set(manifest["files"]) == required, "Incomplete original file bindings")
    for filename, expected in manifest["files"].items():
        require(Path(filename).name == filename, "Files must be local to the bundle")
        path = output / filename
        require(path.is_file(), f"Missing original file: {filename}")
        require(sha256(path) == expected, f"Original file differs: {filename}")
    require((output / "knowledge.db").is_file(), "Missing original knowledge store")
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    card = store.load(manifest["card_ref"])
    require(card.acquisition_trace is None, "Saved card must not claim a new execution")
    records = sabueso.ExtractionStore(output / "extractions.jsonl").records()
    require(len(records) == 1, "Expected the single original extraction")
    assertion = records[0]["article_metadata"]["source_assertion"]
    packets, packet_records = {}, []
    for detail, binding in manifest["packets"].items():
        packet = store.load_packet(binding["ref"])
        record = json.loads((output / binding["attribution_file"]).read_text("utf-8"))
        require(packet.attribution is None, "Saved packet must have no runtime credit")
        require(
            record["packet_snapshot_id"] == packet.snapshot_id(),
            "Attribution belongs to a different packet",
        )
        require(
            packet.entities["subject"]["ref"] == manifest["card_ref"]
            and record["scope"]["subject"]["card_ref"] == manifest["card_ref"],
            "Packet or attribution belongs to a different card",
        )
        require(
            packet.cite("subject", manifest["item_id"]) == manifest["item_ref"],
            "Item reference differs from original pin",
        )
        require(
            packet.item("subject", manifest["item_id"], store) == assertion,
            "Historical article support differs from original extraction",
        )
        require(
            hashlib.sha256(
                json.dumps(assertion, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            == manifest["item_sha256"],
            "Historical article support differs from original digest",
        )
        ackredit.Attribution.from_dict(record["provider"]["attribution"])
        packets[detail] = packet
        packet_records.append(record)
    observations = json.loads((output / f"{name}.observations.json").read_text("utf-8"))
    require(
        observations["packets"] == packet_records,
        "Packet sidecars differ from original observed compositions",
    )
    workflow = ackredit.Attribution.from_json(
        (output / f"{name}.workflow.json").read_text("utf-8")
    )
    expected_ids = {
        item["id"]
        for records in observations.values()
        for record in records
        for item in (record["provider"].get("attribution") or {}).get("items", [])
    }
    require(
        expected_ids == {item["id"] for item in workflow.to_dict()["items"]},
        "Workflow bibliography differs from observed operations",
    )
    expected_uses = {
        json.dumps(use, sort_keys=True)
        for records in observations.values()
        for record in records
        for use in (record["provider"].get("attribution") or {}).get("uses", [])
    }
    require(
        expected_uses
        == {json.dumps(use, sort_keys=True) for use in workflow.to_dict()["uses"]},
        "Workflow contextual uses differ from observed operations",
    )
    return manifest, store, packets, observations, workflow


def read(output, name="original"):
    # Readers need no fixture files. Validate all bindings before export.
    with offline(), ackredit.session("independent saved reader"):
        before = ackredit.get_attribution().to_dict()
        with sabueso.attribution() as observed:
            manifest, store, packets, _, workflow = load_stage(output, name)
            for detail, binding in manifest["packets"].items():
                record = json.loads(
                    (output / binding["attribution_file"]).read_text("utf-8")
                )
                saved = ackredit.Attribution.from_dict(
                    record["provider"]["attribution"]
                )
                for format, extension in (("csl-json", "csl.json"), ("bibtex", "bib")):
                    (output / f"{name}.{detail}.references.{extension}").write_text(
                        saved.report(format=format), encoding="utf-8"
                    )
            (output / f"{name}.workflow.references.csl.json").write_text(
                workflow.report(format="csl-json"), encoding="utf-8"
            )
            explanation = store.load(manifest["card_ref"]).explain_literature(
                PUBLICATION
            )
            write_json(
                output / f"{name}.reader.json",
                {
                    "card_ref": manifest["card_ref"],
                    "item_ref": manifest["item_ref"],
                    "explanation": explanation,
                    "terms": packets["index"].terms("redistribution", store=store),
                    "observed_acquisitions": len(observed.acquisitions),
                },
            )
        require(
            not observed.records
            and not observed.acquisitions
            and not observed.literature,
            "Reading unexpectedly observed an execution",
        )
        require(
            ackredit.get_attribution().to_dict() == before, "Reading added new credit"
        )
    return manifest


def reuse(output, fixtures):
    require(
        not (output / "reused.manifest.json").exists(), "Reuse stage already exists"
    )
    with offline(), ackredit.session("independent reusing application"):
        original, store, _, _, _ = load_stage(output, "original")
        with sabueso.attribution() as observed, ackredit.capture("reuse") as workflow:
            # Reacquire the public UniProt/RCSB fixture knowledge while reusing the
            # original fragment and metadata receipt. No extraction or article lookup.
            def forbidden(*args, **kwargs):
                raise RuntimeError("Reuse must not query metadata or rerun extraction")

            with (
                patch.object(europepmc, "get_article", forbidden),
                patch.object(sabueso, "extract_literature_mentions", forbidden),
            ):
                card, _ = sabueso.refresh_card(
                    store.load(original["card_ref"]),
                    resolver=EntityResolver(
                        FixtureUniProtClient(
                            fixtures, retrieved_at="later fixture read"
                        ),
                        rcsb_client=FixtureRCSBClient(fixtures),
                    ),
                    extractions=sabueso.ExtractionStore(output / "extractions.jsonl"),
                    store=store,
                )
            manifest = save_stage(store, card, "reused")
            manifest["original_manifest_sha256"] = sha256(
                output / "original.manifest.json"
            )
            require(
                manifest["card_ref"] != original["card_ref"],
                "Reacquisition did not advance the card",
            )
        finish_stage(output, manifest, observed, workflow)
    # Old pins must still resolve after both unpinned packet heads have advanced.
    read(output, "original")
    read(output, "reused")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("produce", "read", "reuse"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    args = parser.parse_args()
    try:
        if args.action == "read":
            read(args.output)
        else:
            {"produce": produce, "reuse": reuse}[args.action](
                args.output, args.fixtures
            )
    except (ValueError, OSError, KeyError, SchemaError, StorageError) as error:
        parser.exit(2, f"FAIL: {error}\n")
    print(f"PASS: {args.action} ({args.output})")


if __name__ == "__main__":
    main()
