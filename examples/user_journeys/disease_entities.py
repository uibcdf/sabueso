"""Save source-stated disease identities, target/drug lists and their support gaps."""

import argparse
import json
from pathlib import Path

import ackredit
from molecule_target import check_explanation_support
from protein_comparison import digest, offline, read_json, require, write_json

import sabueso
from sabueso.core.errors import SabuesoError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.clinvar import FixtureClinVarClient
from sabueso.tools.db.diseases import FixtureDISEASESClient
from sabueso.tools.db.medgen import FixtureMedGenClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.open_targets import FixtureOpenTargetsClient
from sabueso.tools.db.orphadata import FixtureOrphadataClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

FORMAT = "sabueso.disease_entities_example@5"
ASSOCIATION_FORMAT = "sabueso.disease_entities_example@4"
MONDO_FORMAT = "sabueso.disease_entities_example@3"
SUPPORT_FORMAT = "sabueso.disease_entities_example@2"
LEGACY_FORMAT = "sabueso.disease_entities_example@1"
SCOPE = {
    "target_disease": "ORPHA:868",
    "drug_disease": "mesh:D014355",
    "target_limit": 3,
    "drug_limit": 3,
    "target_context": "P60174",
    "unresolved_query": "efo:EFO:0001360",
    "trials": "not_queried",
    "efficacy": "not_assessed",
    "packet": "not_supported_for_diseases",
}
ANCHORS = {
    "target_disease": "sabueso:disease:mondo:MONDO:0014221",
    "drug_disease": "sabueso:disease:mondo:MONDO:0001444",
    "target": "sabueso:protein:uniprot:P60174",
    "target_context": "sabueso:protein:uniprot:P60174",
    "drug": "sabueso:small_molecule:inchikey:CULUWZNBISUWAS-UHFFFAOYSA-N",
}
LEGACY_GAPS = {
    "observation": [
        "MONDO",
        "Open Targets",
        "Orphanet",
        "DISEASES",
        "ClinVar",
        "MedGen",
    ],
    "deck_operations": "not_observed",
    "membership_source_assertion_pins": "not_recorded_by_disease_deck_builders",
    "indication_references": "metadata_not_declared; cited studies_not_fetched",
    "support": "Card statements are pinned; deck membership remains original metadata.",
}
SUFFIXES = ("report", "traces", "observations", "workflow")
SUPPORT_GAPS = {
    **LEGACY_GAPS,
    "membership_source_assertion_pins": "recorded_by_disease_deck_rules@2",
    "support": "Native membership, disease input and member identity are pinned; source observation remains partial.",
}
MONDO_GAPS = {
    **SUPPORT_GAPS,
    "observation": [
        source for source in LEGACY_GAPS["observation"] if source != "MONDO"
    ],
}
ASSOCIATION_GAPS = {
    **MONDO_GAPS,
    "observation": [
        source
        for source in MONDO_GAPS["observation"]
        if source not in ("Open Targets", "Orphanet")
    ],
    "deck_operations": "observed_disease_builders; custom_source_clients_remain_unobserved",
}
GAPS = {**ASSOCIATION_GAPS, "observation": []}


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
    with offline(), ackredit.session("public disease related entities"):
        with sabueso.attribution() as observed, ackredit.capture(stage) as workflow:
            stamp = f"{stage} fixture read"
            mondo = FixtureMONDOClient(fixtures, retrieved_at=stamp)
            targets = FixtureOpenTargetsClient(fixtures, retrieved_at=stamp)
            orphanet = FixtureOrphadataClient(fixtures, retrieved_at=stamp)
            resolver = EntityResolver(
                FixtureUniProtClient(fixtures, retrieved_at=stamp)
            )
            cards, resolutions = {}, {}
            for role in ("target_disease", "drug_disease"):
                card, resolution = sabueso.resolve(SCOPE[role], mondo_client=mondo)
                require(
                    card is not None and card.id == ANCHORS[role],
                    "Wrong disease identity",
                )
                cards[role] = card
                resolutions[role] = resolution.to_dict()
            unresolved, resolution = sabueso.resolve(
                SCOPE["unresolved_query"], mondo_client=mondo
            )
            require(
                unresolved is None and resolution.status == "not_found",
                "Unstated identity resolved",
            )
            resolutions["unresolved"] = resolution.to_dict()
            target_deck = sabueso.disease_targets(
                cards["target_disease"],
                limit=SCOPE["target_limit"],
                resolver=resolver,
                open_targets_client=targets,
                orphadata_client=orphanet,
            )
            drug_deck = sabueso.disease_drugs(
                cards["drug_disease"],
                limit=SCOPE["drug_limit"],
                chembl_client=FixtureChEMBLClient(fixtures, retrieved_at=stamp),
                ccd_client=FixtureCCDClient(fixtures, retrieved_at=stamp),
                unichem_client=FixtureUniChemClient(fixtures, retrieved_at=stamp),
            )
            require(
                [c.id for c in target_deck.cards] == [ANCHORS["target"]],
                "Unexpected fixture targets",
            )
            require(
                [c.id for c in drug_deck.cards] == [ANCHORS["drug"]],
                "Unexpected fixture drugs",
            )
            cards["target"], cards["drug"] = target_deck.cards[0], drug_deck.cards[0]
            context, resolution = sabueso.resolve(
                SCOPE["target_context"],
                resolver=resolver,
                diseases={"channels": ["knowledge", "experiments", "textmining"]},
                diseases_client=FixtureDISEASESClient(fixtures, retrieved_at=stamp),
                open_targets={},
                open_targets_client=targets,
                orphadata=True,
                orphadata_client=orphanet,
                clinvar={},
                clinvar_client=FixtureClinVarClient(fixtures, retrieved_at=stamp),
                medgen=True,
                medgen_client=FixtureMedGenClient(fixtures, retrieved_at=stamp),
                disease_identity=True,
                mondo_client=mondo,
            )
            require(
                context is not None and context.id == ANCHORS["target_context"],
                "No target context",
            )
            cards["target_context"] = context
            resolutions["target_context"] = resolution.to_dict()
            manifest["cards"] = {role: store.save(card) for role, card in cards.items()}
            decks = {"targets": target_deck, "drugs": drug_deck}
            manifest["decks"] = {
                role: store.save_deck(deck, role) for role, deck in decks.items()
            }
            # These are genuine card items. Do not create statement pins for membership metadata.
            manifest["assertions"] = {
                role: [
                    card.pinned_ref() + "#" + item
                    for item in sorted(card.source_assertion_store.store)
                ]
                for role, card in cards.items()
            }
            manifest["relationships"] = {
                role: [
                    card.pinned_ref() + "#" + item
                    for item in sorted(card.relationship_store.store)
                ]
                for role, card in cards.items()
            }
            report = {
                "scope": SCOPE,
                "cards": manifest["cards"],
                "decks": manifest["decks"],
                "gaps": GAPS,
                "resolutions": resolutions,
                "support": {
                    role: {
                        "assertions": [
                            cards[role].source_assertion_store.get(
                                pin.rsplit("#", 1)[1]
                            )
                            for pin in manifest["assertions"][role]
                        ],
                        "relationships": [
                            cards[role].relationship_store.get(pin.rsplit("#", 1)[1])
                            for pin in manifest["relationships"][role]
                        ],
                    }
                    for role in cards
                },
                "identity": {
                    role: cards[role].get("identifiers.equivalent_ids")
                    for role in ("target_disease", "drug_disease")
                },
                "decks_report": {
                    role: {
                        "snapshot_id": deck.snapshot_id(),
                        "meta": deck.meta,
                        "members": [c.pinned_ref() for c in deck.cards],
                        "explanations": [deck.explain(c.id) for c in deck.cards],
                        "excluded_explanations": [
                            deck.explain(e["candidate"])
                            for e in deck.meta.get("excluded", [])
                        ],
                        "built_count": len(deck.cards),
                    }
                    for role, deck in decks.items()
                },
                "groups": context.diseases(),
                "group_explanation": context.explain_disease("mondo:MONDO:0014221"),
                "terms": {
                    role: card.terms("redistribution") for role, card in cards.items()
                },
                "deck_terms": {
                    role: deck.terms("redistribution") for role, deck in decks.items()
                },
                "limits": [
                    "Target scores and genetic associations do not establish an intervention's efficacy.",
                    "ChEMBL indication phases do not establish approval or efficacy for every population.",
                    "The target disease and drug disease are separate questions, never an inferred link.",
                    "Missing public UniProt fixtures are local unavailability, not absent external proteins.",
                    "Open Targets' returned subset and the deck limit are different scopes.",
                    "Disease deck rules@2 pin membership and identity inputs; original rules@1 keep their recorded support gaps.",
                    "Runtime source credit is partial (#108); unobserved sources are not credited by this example.",
                ],
            }
            write_json(output / f"{stage}.report.json", report)
        write_json(
            output / f"{stage}.traces.json",
            {
                "cards": {role: card.acquisition_trace for role, card in cards.items()},
                "decks": {role: deck.acquisition_trace for role, deck in decks.items()},
            },
        )
        write_json(
            output / f"{stage}.observations.json",
            {
                "acquisitions": observed.acquisitions,
                "packets": observed.records,
            },
        )
        write_json(output / f"{stage}.workflow.json", workflow.attribution.to_dict())
    manifest["files"] = {
        f"{stage}.{suffix}.json": digest(output / f"{stage}.{suffix}.json")
        for suffix in SUFFIXES
    }
    if stage == "later":
        manifest["original_manifest_sha256"] = digest(output / "original.manifest.json")
    write_json(output / f"{stage}.manifest.json", manifest)
    return manifest


def check_membership_support(explanation, deck, store, disease_ref):
    """Read the original explanation's items without recomputing membership rules."""
    support = explanation["support"]
    require(
        support["status"] == "recorded" and not support["gaps"],
        "Incomplete original membership support",
    )
    require(
        support["rule"] == "disease_deck_explanation@1",
        "Wrong membership explanation rule",
    )
    require(
        support["input_card_ref"]
        == disease_ref
        == deck.meta["support"]["input"]["card_ref"],
        "Wrong original disease input",
    )
    require(
        support["assertion_card_ref"] == deck.meta["support"]["assertions"]["card_ref"],
        "Wrong original membership assertion card",
    )
    for role in ("input", "assertions"):
        embedded = deck.meta["support"][role]
        require(
            store.load(embedded["card_ref"]).to_dict() == embedded["card"],
            "Embedded support differs from its saved card",
        )
    bases = (
        [explanation["basis"]]
        if explanation["in_deck"]
        else [e["basis"] for e in explanation["excluded"]]
    )
    require(
        [r["basis"] for r in support["statements"]] == bases,
        "Support belongs to another candidate",
    )
    for row in support["statements"]:
        for key in (
            "source_assertion_refs",
            "identity_source_assertion_refs",
            "member_identity_source_assertion_refs",
        ):
            require(
                [item["source_assertion_ref"] for item in row[key]]
                == row["basis"].get(key, []),
                "Membership item bindings differ",
            )
            for item in row[key]:
                require(
                    item["found"]
                    and store.source_assertion(item["source_assertion_ref"])
                    == item["assertion"],
                    "Original membership statement differs",
                )


def read_stage(output, stage):
    manifest = read_json(output / f"{stage}.manifest.json")
    require(
        manifest["format"]
        in (FORMAT, ASSOCIATION_FORMAT, MONDO_FORMAT, SUPPORT_FORMAT, LEGACY_FORMAT)
        and manifest["stage"] == stage
        and manifest["scope"] == SCOPE,
        "Wrong manifest or scope",
    )
    require(set(manifest["cards"]) == set(ANCHORS), "Incomplete scientific roles")
    require(set(manifest["decks"]) == {"targets", "drugs"}, "Missing disease deck")
    require(
        set(manifest["files"]) == {f"{stage}.{suffix}.json" for suffix in SUFFIXES},
        "Incomplete original bindings",
    )
    for filename, expected in manifest["files"].items():
        require(
            (output / filename).is_file() and digest(output / filename) == expected,
            f"Missing or changed original: {filename}",
        )
    require((output / "knowledge.db").is_file(), "Missing historical store")
    if stage == "later":
        require(
            digest(output / "original.manifest.json")
            == manifest["original_manifest_sha256"],
            "Changed original manifest",
        )
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    report = read_json(output / f"{stage}.report.json")
    require(
        report["cards"] == manifest["cards"]
        and report["decks"] == manifest["decks"]
        and report["scope"] == SCOPE
        and report["gaps"]
        == {
            FORMAT: GAPS,
            ASSOCIATION_FORMAT: ASSOCIATION_GAPS,
            MONDO_FORMAT: MONDO_GAPS,
            SUPPORT_FORMAT: SUPPORT_GAPS,
            LEGACY_FORMAT: LEGACY_GAPS,
        }[manifest["format"]],
        "Report scope or coverage differs",
    )
    cards = {role: store.load(ref) for role, ref in manifest["cards"].items()}
    traces = read_json(output / f"{stage}.traces.json")
    observations = read_json(output / f"{stage}.observations.json")
    require(not observations["packets"], "Disease packet observation is unsupported")
    operations = {r["id"]: r for r in observations["acquisitions"]}
    require(
        len(operations) == len(observations["acquisitions"]),
        "Duplicate original operation",
    )
    for role, card in cards.items():
        ref = manifest["cards"][role]
        require(
            card.id == ANCHORS[role] and card.pinned_ref() == ref,
            "Wrong card role or pin",
        )
        trace = traces["cards"][role]
        require(
            card.acquisition_trace is None and trace["card_ref"] == ref,
            "Misbound original card trace",
        )
        for record in trace["records"]:
            require(operations.get(record["id"]) == record, "Trace operation differs")
        for key, getter, item_store in (
            ("assertions", store.source_assertion, card.source_assertion_store),
            ("relationships", store.relationship, card.relationship_store),
        ):
            expected_pins = [ref + "#" + item for item in sorted(item_store.store)]
            require(
                manifest[key][role] == expected_pins, "Wrong historical support pins"
            )
            require(
                [item_store.get(pin.rsplit("#", 1)[1]) for pin in expected_pins]
                == report["support"][role][key],
                "Historical support differs",
            )
            # Reuse the verified historical card instead of deserializing it for
            # every item. Also exercise a native store item pin for each role.
            if expected_pins:
                require(
                    getter(expected_pins[0]) == report["support"][role][key][0],
                    "Historical item lookup differs",
                )
    for role in ("target_disease", "drug_disease"):
        require(
            report["identity"][role] == cards[role].get("identifiers.equivalent_ids"),
            "Wrong stated disease identity",
        )
        require(
            all(
                report["resolutions"][role][key] == value
                for key, value in cards[role].quality["entity_resolution"].items()
            ),
            "Wrong disease resolution basis",
        )
    unresolved = report["resolutions"]["unresolved"]
    require(
        unresolved["status"] == "not_found"
        and unresolved["decision"]["query"] == SCOPE["unresolved_query"]
        and unresolved["decision"]["rules"] == ["no_stated_equivalence"],
        "Unstated identity was merged",
    )
    for role, member, disease in (
        ("targets", "target", "target_disease"),
        ("drugs", "drug", "drug_disease"),
    ):
        deck = store.load_deck(manifest["decks"][role])
        original = report["decks_report"][role]
        require(
            deck.snapshot_id() == original["snapshot_id"]
            and deck.meta == original["meta"],
            "Wrong original deck basis",
        )
        require(
            original["members"]
            == [c.pinned_ref() for c in deck.cards]
            == [manifest["cards"][member]],
            "Deck uses another member state",
        )
        require(deck.meta["disease"] == ANCHORS[disease], "Deck uses another disease")
        require(original["built_count"] == len(deck.cards), "Wrong built card count")
        # Compare stored bases, without rerunning Deck.explain or its future rules.
        for explanation, card in zip(original["explanations"], deck.cards, strict=True):
            require(
                explanation["card_id"] == card.id
                and explanation["in_deck"]
                and explanation["basis"] == deck.basis(card.id),
                "Membership explanation differs",
            )
            if manifest["format"] in (
                FORMAT,
                ASSOCIATION_FORMAT,
                MONDO_FORMAT,
                SUPPORT_FORMAT,
            ):
                check_membership_support(
                    explanation, deck, store, manifest["cards"][disease]
                )
        require(
            len(original["excluded_explanations"]) == len(deck.meta["excluded"]),
            "Missing excluded candidate",
        )
        for explanation, excluded in zip(
            original["excluded_explanations"], deck.meta["excluded"], strict=True
        ):
            require(
                explanation["card_id"] == excluded["candidate"]
                and explanation["excluded"] == [excluded]
                and not explanation["in_deck"],
                "Excluded candidate differs",
            )
            if manifest["format"] in (
                FORMAT,
                ASSOCIATION_FORMAT,
                MONDO_FORMAT,
                SUPPORT_FORMAT,
            ):
                check_membership_support(
                    explanation, deck, store, manifest["cards"][disease]
                )
        require(deck.acquisition_trace is None, "Reader created a deck trace")
        trace = traces["decks"][role]
        if manifest["format"] in (FORMAT, ASSOCIATION_FORMAT):
            require(
                trace["deck_snapshot_id"] == deck.snapshot_id()
                and trace["card_refs"] == original["members"]
                and trace["input_card_refs"] == [manifest["cards"][disease]]
                and trace["operation"]["name"] == "disease_" + role
                and trace["operation"]["rule"] == deck.meta["rule"]
                and trace["operation"]["limit"] == deck.meta["limit"]
                and trace["operation"]["support_card_ref"]
                == deck.meta["support"]["assertions"]["card_ref"]
                and trace["operation"]["sources"] == deck.meta["sources"]
                and trace["operation"]["built_count"] == len(deck.cards)
                and trace["operation"]["excluded_count"] == len(deck.meta["excluded"]),
                "Misbound original disease deck trace",
            )
            for record in trace["records"]:
                require(
                    operations.get(record["id"]) == record,
                    "Deck trace operation differs",
                )
        else:
            require(trace is None, "Unsupported historical deck trace")
    explanation = report["group_explanation"]
    require(
        explanation["card_ref"] == manifest["cards"]["target_context"],
        "Group uses another historical card",
    )
    require(
        explanation["group"] in report["groups"]["diseases"], "Group report differs"
    )
    check_explanation_support(explanation, {c.pinned_ref(): c for c in cards.values()})
    workflow = ackredit.Attribution.from_dict(
        read_json(output / f"{stage}.workflow.json")
    )
    for key in ("items", "uses"):
        expected = {
            json.dumps(v, sort_keys=True)
            for r in operations.values()
            for v in (r["provider"].get("attribution") or {}).get(key, [])
        }
        require(
            expected
            == {json.dumps(v, sort_keys=True) for v in workflow.to_dict()[key]},
            f"Workflow {key} differ from observed operations",
        )
    return manifest, report, workflow


def read(output):
    with offline(), ackredit.session("independent disease reader"):
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
                    f"{stage}: disease target/drug metadata retained; support and observation gaps explicit"
                )
        require(
            not observed.acquisitions
            and not observed.records
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
