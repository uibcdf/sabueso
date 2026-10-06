"""Read two public molecules' measurements against one explicitly declared target."""

import argparse
import json
from pathlib import Path

import ackredit

# These are example-local file/quantity/network helpers, not another SDK contract.
from protein_comparison import digest, offline, read_json, require, write_json

import sabueso
from sabueso.core.deck import Deck
from sabueso.core.errors import SabuesoError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.rcsb import FixtureRCSBClient
from sabueso.tools.db.unichem import FixtureUniChemClient

FORMAT = "sabueso.molecule_target_example@1"
TARGET = "P52270"
MOLECULES = {"bts": "chembl:CHEMBL1161789", "benznidazole": "chembl:CHEMBL110"}
ANCHORS = {
    "bts": "sabueso:small_molecule:inchikey:XBNHRNFODJOFRU-UHFFFAOYSA-N",
    "benznidazole": "sabueso:small_molecule:inchikey:CULUWZNBISUWAS-UHFFFAOYSA-N",
}
SCOPE = {
    "target": "uniprot:" + TARGET,
    "molecules": MOLECULES,
    "activity_sources": ["ChEMBL"],
    "structures": ["pdb:1SUX"],
    "indications": {"bts": "not_queried", "benznidazole": "ChEMBL"},
    "trials": "not_queried",
    "other_targets": "not_queried",
    "packet": "target context; not a molecule-filtered query",
}


def produce(output, fixtures, stage):
    if stage == "original":
        require(
            not output.exists() or not any(output.iterdir()), "Output must be empty"
        )
        output.mkdir(parents=True, exist_ok=True)
    else:
        require(not (output / "later.manifest.json").exists(), "Later stage exists")
        read_stage(output, "original")
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    manifest = {"format": FORMAT, "stage": stage, "scope": SCOPE, "cards": {}}
    with offline(), ackredit.session("public molecule and declared target"):
        with sabueso.attribution() as observed, ackredit.capture(stage) as workflow:
            timestamp = f"{stage} fixture read"
            chembl = FixtureChEMBLClient(fixtures, retrieved_at=timestamp)
            ccd = FixtureCCDClient(fixtures, retrieved_at=timestamp)
            unichem = FixtureUniChemClient(fixtures, retrieved_at=timestamp)
            target, resolution = sabueso.resolve(
                TARGET,
                resolver=EntityResolver(
                    FixtureUniProtClient(fixtures, retrieved_at=timestamp),
                    rcsb_client=FixtureRCSBClient(fixtures, retrieved_at=timestamp),
                ),
                structures=["1SUX"],
                chembl={},
                chembl_client=chembl,
            )
            require(target is not None and resolution.status == "resolved", "No target")
            manifest["cards"]["target"] = store.save(target)
            cards, resolutions = {"target": target}, {"target": resolution.to_dict()}
            deck = Deck()
            for role, identifier in MOLECULES.items():
                card, resolution = sabueso.resolve(
                    identifier,
                    chembl_client=chembl,
                    ccd_client=ccd,
                    unichem_client=unichem,
                    indications=role == "benznidazole",
                )
                require(
                    card is not None and resolution.status == "resolved"
                    and card.id == ANCHORS[role], "Expected molecule did not resolve",
                )  # fmt: skip
                cards[role] = card
                resolutions[role] = resolution.to_dict()
                manifest["cards"][role] = store.save(card)
                deck.add(
                    card,
                    basis={
                        "selection": "explicit identifier",
                        "identifier": identifier,
                    },
                )
            manifest["deck"] = store.save_deck(deck, "declared-molecules")
            packet = sabueso.compose_packet(
                sabueso.KnowledgeQuery(
                    TARGET,
                    aspects=["identity", "structures", "bioactivities"],
                    detail="index",
                ),
                target,
            )
            manifest["packet"] = store.save_packet(packet, "target-context")
            write_json(output / f"{stage}.packet-attribution.json", packet.attribution)
            report = {
                "scope": SCOPE,
                "cards": manifest["cards"],
                "deck": manifest["deck"],
                "deck_snapshot_id": deck.snapshot_id(),
                "resolutions": resolutions,
                "crossing": target.ligands(deck),
                "target_state": target.knowledge_state(),
                "molecules": {},
                "limits": [
                    "Measurements apply to the stated assay and target, not every target or organism.",
                    "A derived inactive class is not universal inactivity or a clinical efficacy claim.",
                    "Unmatched target records are outside this two-molecule deck, not identity failures.",
                    "Clinical indications are ChEMBL statements; cited trials were not fetched.",
                    "knowledge_state@4 may misclassify molecular source-record counts; @5 corrects counts and clinical scopes (#122). Inspect the original named rule and query outcomes.",
                    "Local deck selection and views have no source-acquisition trace; other/custom clients remain outside observed coverage.",
                ],
            }
            # Keep exact relationships and all their original statements as item pins.
            # Do not recompute these named derivations in a future independent reader.
            links = {"target": [], **{role: [] for role in MOLECULES}}
            for role, card in cards.items():
                predicates = (
                    ("has_bioactivity", "has_structure")
                    if role == "target"
                    else ("same_as", "investigated_for")
                )
                for predicate in predicates:
                    for link in card.relationships(predicate):
                        if (
                            predicate == "has_bioactivity"
                            and link["object_ref"] not in MOLECULES.values()
                        ):
                            continue
                        links[role].append(link)
            manifest["relationships"] = {
                role: [manifest["cards"][role] + "#" + link["id"] for link in values]
                for role, values in links.items()
            }
            manifest["assertions"] = {
                role: [
                    manifest["cards"][role] + "#" + item
                    for item in sorted(
                        {
                            item
                            for link in values
                            for item in link["source_assertion_ids"]
                        }
                    )
                ]
                for role, values in links.items()
            }
            report["support"] = {
                role: {
                    "relationships": [
                        store.relationship(ref)
                        for ref in manifest["relationships"][role]
                    ],
                    "assertions": [
                        store.source_assertion(ref)
                        for ref in manifest["assertions"][role]
                    ],
                }
                for role in cards
            }
            for role, identifier in MOLECULES.items():
                card = cards[role]
                activity = target.explain_bioactivity(identifier)
                require(activity["status"] == "on_card", "No supported activity")
                report["molecules"][role] = {
                    "identity": card.get("identifiers.inchikey"),
                    "mass": card.get("properties.physchem.molecular_weight"),
                    "clinical": card.clinical(),
                    "knowledge_state": card.knowledge_state(),
                    "enrichments": card.quality.get("enrichments", []),
                    "conflicts": card.quality.get("conflicts", []),
                    "alternatives": card.quality.get("alternatives", {}),
                    "terms": card.terms("redistribution"),
                    "activity": activity,
                    "measurements": [
                        target.explain_measurement(m["group"])
                        for m in activity["item"]["measurements"]
                    ],
                    "crossing": target.explain_ligand(card.id, deck),
                }
            write_json(output / f"{stage}.report.json", report)
        write_json(
            output / f"{stage}.traces.json",
            {role: card.acquisition_trace for role, card in cards.items()},
        )
        write_json(
            output / f"{stage}.observations.json",
            {"acquisitions": observed.acquisitions, "packets": observed.records},
        )
        write_json(output / f"{stage}.workflow.json", workflow.attribution.to_dict())
    manifest["files"] = {
        f"{stage}.{suffix}.json": digest(output / f"{stage}.{suffix}.json")
        for suffix in (
            "report",
            "traces",
            "observations",
            "workflow",
            "packet-attribution",
        )
    }
    if stage == "later":
        manifest["original_manifest_sha256"] = digest(output / "original.manifest.json")
    write_json(output / f"{stage}.manifest.json", manifest)
    return manifest


def check_explanation_support(value, cards):
    """Inspect original pinned links, including nested identity/assay/group inputs."""
    if isinstance(value, list):
        for item in value:
            check_explanation_support(item, cards)
    elif isinstance(value, dict):
        for key, store_name, payload in (
            ("relationship_ref", "relationship_store", "relationship"),
            ("source_assertion_ref", "source_assertion_store", None),
        ):
            if key not in value:
                continue
            ref = value[key]
            card_ref, item_id = ref.rsplit("#", 1)
            require(card_ref in cards, "Explanation uses another card")
            # Each card pin was verified on load. Inspect its in-memory item stores
            # once loaded, rather than deserialize the same card for every link.
            stored = getattr(cards[card_ref], store_name).get(item_id)
            if payload:
                require(stored == value[payload], "Explanation relationship differs")
            else:
                require(
                    stored["id"] == value["id"] and value["found"],
                    "Explanation statement differs",
                )
                require(
                    stored["asserted_value"] == value["asserted_value"],
                    "Explanation assertion value differs",
                )
                require(
                    stored["source"].get("version") == value.get("version"),
                    "Explanation source version differs",
                )
        for item in value.values():
            check_explanation_support(item, cards)


def read_stage(output, stage):
    manifest = read_json(output / f"{stage}.manifest.json")
    require(
        manifest["format"] == FORMAT and manifest["stage"] == stage, "Wrong manifest"
    )
    require(manifest["scope"] == SCOPE, "Different declared query")
    roles = {"target", *MOLECULES}
    require(set(manifest["cards"]) == roles, "Missing target or molecule")
    require(
        set(manifest["relationships"]) == set(manifest["assertions"]) == roles,
        "Missing support roles",
    )
    files = {
        f"{stage}.{suffix}.json"
        for suffix in (
            "report",
            "traces",
            "observations",
            "workflow",
            "packet-attribution",
        )
    }
    require(set(manifest["files"]) == files, "Incomplete original file bindings")
    for filename, expected in manifest["files"].items():
        path = output / filename
        require(
            path.is_file() and digest(path) == expected,
            f"Missing or changed original file: {filename}",
        )
    require((output / "knowledge.db").is_file(), "Missing historical store")
    if stage == "later":
        require(
            digest(output / "original.manifest.json")
            == manifest["original_manifest_sha256"],
            "Original manifest differs",
        )
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    report = read_json(output / f"{stage}.report.json")
    require(
        report["cards"] == manifest["cards"]
        and report["deck"] == manifest["deck"]
        and report["scope"] == SCOPE,
        "Report belongs to different scientific inputs",
    )
    traces = read_json(output / f"{stage}.traces.json")
    cards = {role: store.load(ref) for role, ref in manifest["cards"].items()}
    for role, card in cards.items():
        ref = manifest["cards"][role]
        expected_id = (
            "sabueso:protein:uniprot:" + TARGET if role == "target" else ANCHORS[role]
        )
        require(
            card.id == expected_id and card.pinned_ref() == ref,
            "Wrong entity or card pin",
        )
        require(
            card.acquisition_trace is None and traces[role]["card_ref"] == ref,
            "Wrong original card trace",
        )
        require(
            traces[role]["result_status"] == "resolved",
            "Incomplete original resolution",
        )
        for key, getter, payload in (
            ("relationships", store.relationship, "relationships"),
            ("assertions", store.source_assertion, "assertions"),
        ):
            pins = manifest[key][role]
            require(
                pins and all(pin.rsplit("#", 1)[0] == ref for pin in pins),
                "Misbound historical item pins",
            )
            require(
                [getter(pin) for pin in pins] == report["support"][role][payload],
                "Historical support differs",
            )
        for link in report["support"][role]["relationships"]:
            expected = {ref + "#" + item for item in link["source_assertion_ids"]}
            require(
                expected <= set(manifest["assertions"][role]),
                "Missing relationship statements",
            )
    deck = store.load_deck(manifest["deck"])
    require(deck.snapshot_id() == report["deck_snapshot_id"], "Wrong deck snapshot")
    require(
        [card.pinned_ref() for card in deck.cards]
        == [manifest["cards"][role] for role in MOLECULES],
        "Deck belongs to different molecules",
    )
    require(deck.acquisition_trace is None, "Saved selection must not create execution")
    for role, identifier in MOLECULES.items():
        original = report["molecules"][role]
        require(
            deck.basis(ANCHORS[role])
            == {"selection": "explicit identifier", "identifier": identifier},
            "Wrong selection basis",
        )
        require(
            original["identity"] == cards[role].get("identifiers.inchikey"),
            "Wrong molecule identity",
        )
        activity, crossing = original["activity"], original["crossing"]
        require(
            activity["card_ref"] == manifest["cards"]["target"]
            and activity["molecule_ref"] == identifier,
            "Activity belongs to another target or molecule",
        )
        require(
            crossing["card_ref"] == manifest["cards"]["target"]
            and crossing["molecule_ref"] == ANCHORS[role],
            "Crossing belongs to another target or molecule",
        )
        require(
            crossing["deck"]["snapshot_id"] == deck.snapshot_id(),
            "Crossing uses another deck",
        )
        require(
            len(crossing["items"]) == 1
            and crossing["items"][0]["molecule_card_ref"] == manifest["cards"][role],
            "Crossing uses another molecular state",
        )
        require(
            [m["group"]["id"] for m in original["measurements"]]
            == [m["group"] for m in activity["item"]["measurements"]],
            "Measurement groups differ from the reported activity",
        )
        for measurement in original["measurements"]:
            require(
                measurement["card_ref"] == manifest["cards"]["target"],
                "Measurement belongs to another target",
            )
        check_explanation_support(
            original, {card.pinned_ref(): card for card in cards.values()}
        )
    packet = store.load_packet(manifest["packet"])
    record = read_json(output / f"{stage}.packet-attribution.json")
    require(
        packet.attribution is None and packet.detail == "index",
        "Unexpected saved packet",
    )
    require(
        packet.entities["subject"]["ref"] == manifest["cards"]["target"],
        "Wrong packet target",
    )
    require(
        record["scope"]["subject"]["card_ref"] == manifest["cards"]["target"]
        and record["packet_snapshot_id"] == packet.snapshot_id(),
        "Wrong packet attribution",
    )
    require(
        record["provider"]["status"] == "available", "Incomplete packet attribution"
    )
    for pin in manifest["assertions"]["target"]:
        item_id = pin.rsplit("#", 1)[1]
        require(
            packet.cite("subject", item_id) == pin
            and packet.item("subject", item_id, store) == store.source_assertion(pin),
            "Packet historical support differs",
        )
    observations = read_json(output / f"{stage}.observations.json")
    require(
        observations["packets"] == [record], "Packet sidecar differs from observations"
    )
    require(
        observations["acquisitions"]
        == [record for role in cards for record in traces[role]["records"]],
        "Intake traces differ from observed operations",
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
        require(
            expected
            == {json.dumps(value, sort_keys=True) for value in workflow.to_dict()[key]},
            f"Workflow {key} differ from observed operations",
        )
    return manifest, report, workflow


def read(output):
    with offline(), ackredit.session("independent molecule target reader"):
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
                    {
                        "cards": manifest["cards"],
                        "original_report": report,
                        "observed_acquisitions": 0,
                    },
                )
                print(
                    f"{stage}: BTS and benznidazole against {TARGET}; other targets and trials not queried"
                )
        require(
            not observed.records
            and not observed.acquisitions
            and not observed.literature,
            "Reader observed an execution",
        )
        require(ackredit.get_attribution().to_dict() == before, "Reader added credit")


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
                args.output,
                args.fixtures,
                "original" if args.action == "produce" else "later",
            )
    except (ValueError, KeyError, OSError, SabuesoError) as exc:
        parser.exit(2, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
