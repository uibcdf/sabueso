"""Compare public protein knowledge, then read its original support independently."""

import argparse
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import ackredit
import pyunitwizard as puw

import sabueso
from sabueso.core.errors import SabuesoError
from sabueso.core.source_assertion_store import assertion_value
from sabueso.resolver import EntityQuery, EntityResolver, FixtureUniProtClient
from sabueso.tools.db.bindingdb import FixtureBindingDBClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.rcsb import FixtureRCSBClient
from sabueso.tools.db.unichem import FixtureUniChemClient

FORMAT = "sabueso.protein_comparison_example@2"
READABLE_FORMATS = {"sabueso.protein_comparison_example@1", FORMAT}
ROLES = {"subject": ("P52270", 5693), "comparator": ("P60174", 9606)}
ASPECTS = ["identity", "structures", "bioactivities", "literature"]
STRUCTURES = {"subject": ["1TCD", "1IIG"], "comparator": ["1HTI", "1KLG"]}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    def physical_quantity(value):
        if puw.is_quantity(value):
            unit = puw.convert(
                str(puw.get_unit(value)), to_form="record", to_type="unit"
            )
            number = puw.get_value(value, to_unit=unit)
            return {
                "value": number.tolist() if hasattr(number, "tolist") else number,
                "unit": unit,
            }
        raise TypeError(f"Cannot serialize {type(value).__name__}")

    path.write_text(
        json.dumps(
            value,
            default=physical_quantity,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def residue_context(card):
    """Read source-active-site positions on their own canonical axis, without alignment."""
    residues = card.get_residues()
    selected = [
        row
        for row in residues
        if any(
            item["field_path"] == "features_positional.active_site"
            and item["support_status"] == "complete"
            for item in row["annotations"]
        )
    ]
    positions = [row["position"] for row in selected]
    assertions = set()
    for row in selected:
        assertions.update(row["sequence_support"]["source_assertion_ids"])
        for item in row["annotations"]:
            assertions.update(item["source_assertion_ids"])
    composition = card.residue_composition(positions)
    assertions.update(composition["sequence_support"]["source_assertion_ids"])
    unplaced = [
        item
        for item in (residues[0]["unmapped"] if residues else [])
        if item["field_path"] == "features_positional.active_site"
    ]
    return {
        "card_ref": card.pinned_ref(),
        "selection": {
            "rule": "source_active_site_selection@1",
            "basis": "caller selects canonical positions with completely supported source active-site annotations",
            "positions": positions,
            "unplaced": unplaced,
        },
        "residues": selected,
        "composition": composition,
        "support_refs": [card.pinned_ref() + "#" + item for item in sorted(assertions)],
        "comparison": {
            "status": "not_compared",
            "reason": "no source-stated residue correspondence",
        },
        "execution_observation": {
            "status": "not_observed",
            "reason": "derived readers provide rules and support without dedicated operation sidecars",
        },
    }


@contextmanager
def offline():
    def forbidden(*args, **kwargs):
        raise RuntimeError("This fixture journey must never reach the network")

    with (
        patch("socket.create_connection", forbidden),
        patch("sabueso.tools.db._http._urlopen", forbidden),
    ):
        yield


def produce(output, fixtures, stage):
    """Acquire frozen public responses and retain each scientific/runtime artifact."""
    require(stage in ("original", "later"), "Unknown stage")
    if stage == "original":
        require(
            not output.exists() or not any(output.iterdir()), "Output must be empty"
        )
        output.mkdir(parents=True, exist_ok=True)
    else:
        require(not (output / "later.manifest.json").exists(), "Later stage exists")
        read_stage(output, "original")
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    with offline(), ackredit.session("public protein comparison"):
        with sabueso.attribution() as observed, ackredit.capture(stage) as workflow:
            timestamp = f"{stage} fixture read"
            resolver = EntityResolver(
                FixtureUniProtClient(fixtures, retrieved_at=timestamp),
                rcsb_client=FixtureRCSBClient(fixtures, retrieved_at=timestamp),
            )
            chembl = FixtureChEMBLClient(fixtures, retrieved_at=timestamp)
            bindingdb = FixtureBindingDBClient(fixtures, retrieved_at=timestamp)
            ccd = FixtureCCDClient(fixtures, retrieved_at=timestamp)
            unichem = FixtureUniChemClient(fixtures, retrieved_at=timestamp)
            cards, decks, traces, resolutions = {}, {}, {}, {}
            manifest = {"format": FORMAT, "stage": stage, "cards": {}, "decks": {}}
            for role, (accession, organism) in ROLES.items():
                card, resolution = sabueso.resolve(
                    EntityQuery(name="triosephosphate isomerase", organism=organism),
                    resolver=resolver,
                    structures=STRUCTURES[role],
                    chembl={},
                    chembl_client=chembl,
                    bindingdb={},
                    bindingdb_client=bindingdb,
                    unichem_client=unichem,
                )
                require(
                    card is not None
                    and resolution.status == "resolved"
                    and card.get("identifiers.uniprot")["value"] == accession,
                    "Expected public protein did not resolve",
                )
                cards[role] = card
                resolutions[role] = resolution.to_dict()
                manifest["cards"][role] = store.save(card)
                traces[role] = card.acquisition_trace
                decks[role] = sabueso.ligand_deck(
                    card, chembl_client=chembl, ccd_client=ccd
                )
                traces[role + "_ligands"] = decks[role].acquisition_trace
                manifest["decks"][role] = store.save_deck(
                    decks[role], role + "-ligands"
                )
            manifest["packets"] = {}
            for detail in ("full", "index"):
                packet = sabueso.compose_packet(
                    sabueso.KnowledgeQuery(
                        "P52270", comparator="P60174", aspects=ASPECTS, detail=detail
                    ),
                    cards["subject"],
                    cards["comparator"],
                )
                filename = f"{stage}.{detail}.attribution.json"
                write_json(output / filename, packet.attribution)
                manifest["packets"][detail] = {
                    "ref": store.save_packet(packet, "comparison-" + detail),
                    "attribution_file": filename,
                }
            # Save the producer's derived results with their rules and pinned inputs.
            # An independent reader inspects these originals rather than recomputing
            # a historical result with whatever rules it has installed today.
            report = {
                "cards": manifest["cards"],
                "decks": manifest["decks"],
                "resolutions": resolutions,
                "knowledge_comparison": cards["subject"].compare_knowledge(
                    cards["comparator"]
                ),
                "ligand_comparison": cards["subject"].compare_ligands(
                    decks["subject"], cards["comparator"], decks["comparator"]
                ),
                "proteins": {},
            }
            manifest["items"] = {}
            manifest["residue_items"] = {}
            for role, card in cards.items():
                node = card.get("annotations.subunit")
                activity = card.bioactivities()["items"][0]
                shared_molecule = report["ligand_comparison"]["shared"][0][
                    "molecule_ref"
                ]
                manifest["items"][role] = [
                    manifest["cards"][role] + "#" + item
                    for item in node["source_assertion_ids"]
                ]
                report["proteins"][role] = {
                    "subunit": node,
                    "support": card.explain(node["source_assertion_ids"]),
                    "mass": card.get("sequence.molecular_weight"),
                    "structures": card.structures(),
                    "bioactivities": card.bioactivities(),
                    "example_activity_explanation": card.explain_bioactivity(
                        activity["molecule_ref"]
                    ),
                    "example_measurement_explanation": card.explain_measurement(
                        activity["measurements"][0]["group"]
                    ),
                    "example_shared_ligand_explanation": card.explain_ligand(
                        shared_molecule, decks[role]
                    ),
                    "knowledge_state": card.knowledge_state(),
                    "conflicts": card.quality.get("conflicts", []),
                    "alternatives": card.quality.get("alternatives", {}),
                    "terms": card.terms("redistribution"),
                    "ligand_sources": decks[role].meta.get("sources", []),
                }
                context = residue_context(card)
                report["proteins"][role]["residue_context"] = context
                manifest["residue_items"][role] = context["support_refs"]
            write_json(output / f"{stage}.report.json", report)
        write_json(output / f"{stage}.traces.json", traces)
        write_json(
            output / f"{stage}.observations.json",
            {"acquisitions": observed.acquisitions, "packets": observed.records},
        )
        write_json(output / f"{stage}.workflow.json", workflow.attribution.to_dict())
    files = {
        f"{stage}.{suffix}.json"
        for suffix in ("report", "traces", "observations", "workflow")
    } | {p["attribution_file"] for p in manifest["packets"].values()}
    manifest["files"] = {name: digest(output / name) for name in sorted(files)}
    if stage == "later":
        manifest["original_manifest_sha256"] = digest(output / "original.manifest.json")
    write_json(output / f"{stage}.manifest.json", manifest)
    return manifest


def read_stage(output, stage):
    """Check original sidecars and exact scientific references before any export."""
    manifest = read_json(output / f"{stage}.manifest.json")
    require(manifest["format"] in READABLE_FORMATS, "Unsupported example manifest")
    require(manifest["stage"] == stage, "Stage differs from manifest")
    require(set(manifest["cards"]) == set(ROLES), "Expected both proteins")
    require(set(manifest["decks"]) == set(ROLES), "Expected both ligand decks")
    require(set(manifest["items"]) == set(ROLES), "Expected support for both proteins")
    require(set(manifest["packets"]) == {"full", "index"}, "Expected both packets")
    required = {
        f"{stage}.{suffix}.json"
        for suffix in ("report", "traces", "observations", "workflow")
    } | {p["attribution_file"] for p in manifest["packets"].values()}
    require(set(manifest["files"]) == required, "Incomplete original file bindings")
    for filename, expected in manifest["files"].items():
        require(Path(filename).name == filename, "Files must be local to the bundle")
        path = output / filename
        require(path.is_file(), f"Missing original file: {filename}")
        require(digest(path) == expected, f"Original file differs: {filename}")
    require((output / "knowledge.db").is_file(), "Missing original knowledge store")
    if stage == "later":
        require(
            digest(output / "original.manifest.json")
            == manifest["original_manifest_sha256"],
            "Original manifest differs from later-stage binding",
        )
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    report = read_json(output / f"{stage}.report.json")
    require(
        report["cards"] == manifest["cards"] and report["decks"] == manifest["decks"],
        "Report belongs to different scientific inputs",
    )
    traces = read_json(output / f"{stage}.traces.json")
    records = []
    for role, ref in manifest["cards"].items():
        card = store.load(ref)
        require(card.pinned_ref() == ref, "Expected an exact card pin")
        require(card.acquisition_trace is None, "Saved card must have no new execution")
        require(traces[role]["card_ref"] == ref, "Source trace belongs to another card")
        deck = store.load_deck(manifest["decks"][role])
        require(deck.acquisition_trace is None, "Saved deck must have no new execution")
        require(
            deck.snapshot_id() == traces[role + "_ligands"]["deck_snapshot_id"],
            "Source trace belongs to another deck",
        )
        require(
            traces[role + "_ligands"]["input_card_refs"] == [ref]
            and traces[role + "_ligands"]["card_refs"]
            == [member.pinned_ref() for member in deck.cards],
            "Ligand trace belongs to different inputs or outputs",
        )
        node = card.get("annotations.subunit")
        expected_items = [ref + "#" + item for item in node["source_assertion_ids"]]
        require(manifest["items"][role] == expected_items, "Support item pins differ")
        require(report["proteins"][role]["subunit"] == node, "Stored subunit differs")
        for item_ref in expected_items:
            item = store.source_assertion(item_ref)
            require(
                item == card.source_assertion_store.get(item_ref.rsplit("#", 1)[1]),
                "Historical item differs from its card",
            )
        if manifest["format"] == FORMAT:
            context = report["proteins"][role]["residue_context"]
            require(
                context["card_ref"] == ref, "Residue context belongs to another card"
            )
            require(
                context["composition"]["card_ref"] == ref,
                "Composition belongs to another card",
            )
            require(
                context["selection"]["rule"] == "source_active_site_selection@1",
                "Unsupported residue selection",
            )
            require(
                context["support_refs"] == manifest["residue_items"][role],
                "Residue support pins differ",
            )
            require(
                context["composition"]["selection"]["requested_positions"]
                == context["selection"]["positions"],
                "Residue selection differs from composition",
            )
            for item_ref in context["support_refs"]:
                require(
                    item_ref.startswith(ref + "#"),
                    "Residue support belongs to another card",
                )
                item = store.source_assertion(item_ref)
                require(
                    item == card.source_assertion_store.get(item_ref.rsplit("#", 1)[1]),
                    "Residue support differs from its pinned card",
                )
            # Validate preserved inputs, not derived results under current rules.
            expected_sequence = card.get("sequence.primary")["value"]
            require(
                context["composition"]["sequence_sha256"]
                == hashlib.sha256(expected_sequence.encode()).hexdigest(),
                "Composition sequence differs from its card",
            )
            for row in context["residues"]:
                require(row["card_ref"] == ref, "Residue row belongs to another card")
                position = row["position"]
                require(
                    1 <= position <= len(expected_sequence),
                    "Residue position outside its sequence",
                )
                require(
                    row["amino_acid"] == expected_sequence[position - 1],
                    "Residue symbol differs from its source sequence",
                )
                for annotation in row["annotations"]:
                    if annotation["support_status"] == "complete":
                        require(
                            annotation["source_assertion_ids"],
                            "Complete annotation has no source support",
                        )
                    for identifier in annotation["source_assertion_ids"]:
                        require(
                            ref + "#" + identifier in context["support_refs"],
                            "Annotation support is absent from the manifest",
                        )
                        assertion = store.source_assertion(ref + "#" + identifier)
                        require(
                            assertion["field_path"] == annotation["field_path"]
                            and assertion_value(assertion) == annotation["annotation"],
                            "Residue annotation differs from its pinned source statement",
                        )
            require(
                [row["position"] for row in context["residues"]]
                == context["selection"]["positions"],
                "Residue rows differ from the selected positions",
            )
            for support in context["composition"]["sequence_support"]["support"]:
                identifier = support["source_assertion_id"]
                require(
                    ref + "#" + identifier in context["support_refs"],
                    "Composition sequence support is absent from the manifest",
                )
                require(
                    support["assertion"]
                    == store.source_assertion(ref + "#" + identifier),
                    "Composition sequence support differs from its pinned statement",
                )
    for detail, binding in manifest["packets"].items():
        packet = store.load_packet(binding["ref"])
        record = read_json(output / binding["attribution_file"])
        require(packet.attribution is None, "Saved packet must have no new credit")
        require(packet.detail == detail, "Packet detail differs from manifest")
        require(record["provider"]["status"] == "available", "Incomplete attribution")
        require(
            record["packet_snapshot_id"] == packet.snapshot_id(),
            "Attribution belongs to another packet",
        )
        for role, ref in manifest["cards"].items():
            require(
                packet.entities[role]["ref"] == ref
                and record["scope"][role]["card_ref"] == ref,
                "Packet or attribution belongs to another protein",
            )
            for item_ref in manifest["items"][role]:
                item_id = item_ref.rsplit("#", 1)[1]
                require(
                    packet.cite(role, item_id) == item_ref, "Packet citation differs"
                )
                require(
                    packet.item(role, item_id, store)
                    == store.source_assertion(item_ref),
                    "Packet historical item differs",
                )
        records.append(record)
    observations = read_json(output / f"{stage}.observations.json")
    require(
        observations["packets"] == records, "Packet sidecars differ from observations"
    )
    workflow = ackredit.Attribution.from_dict(
        read_json(output / f"{stage}.workflow.json")
    )
    for key in ("items", "uses"):
        expected = {
            json.dumps(value, sort_keys=True)
            for group in observations.values()
            for record in group
            for value in (record["provider"].get("attribution") or {}).get(key, [])
        }
        actual = {
            json.dumps(value, sort_keys=True) for value in workflow.to_dict()[key]
        }
        require(expected == actual, f"Workflow {key} differ from observed operations")
    return manifest, report, workflow


def read(output):
    with offline(), ackredit.session("independent comparison reader"):
        before = ackredit.get_attribution().to_dict()
        with sabueso.attribution() as observed:
            for stage in ("original", "later"):
                if stage == "later" and not (output / "later.manifest.json").exists():
                    continue
                manifest, report, workflow = read_stage(output, stage)
                for format, suffix in (("csl-json", "csl.json"), ("bibtex", "bib")):
                    (output / f"{stage}.references.{suffix}").write_text(
                        workflow.report(format=format), encoding="utf-8"
                    )
                write_json(
                    output / f"{stage}.reader.json",
                    {"cards": manifest["cards"], "items": manifest["items"],
                     "original_report": report, "observed_acquisitions": 0},
                )  # fmt: skip
                print(
                    f"{stage}: {len(report['ligand_comparison']['shared'])} shared "
                    "ligands in these source/fixture subsets; no positional alignment"
                )
        require(
            not observed.records
            and not observed.acquisitions
            and not observed.literature,
            "Reading unexpectedly observed an execution",
        )
        require(ackredit.get_attribution().to_dict() == before, "Reading added credit")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("produce", "read", "reacquire"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    args = parser.parse_args()
    try:
        if args.action == "read":
            read(args.output)
        else:
            produce(
                args.output, args.fixtures,
                "original" if args.action == "produce" else "later",
            )  # fmt: skip
    except (ValueError, KeyError, OSError, SabuesoError) as exc:
        parser.exit(2, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
