"""Save public sequence/tissue explanations and read their original pins inertly."""

import argparse
from pathlib import Path

import ackredit
from protein_comparison import digest, offline, read_json, require, write_json

import sabueso
from sabueso.core.errors import SabuesoError
from sabueso.core.source_assertion_store import acquisition_of
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.gnomad import FixtureGnomADClient
from sabueso.tools.db.gtex import FixtureGTExClient
from sabueso.tools.db.uniref import FixtureUniRefClient

FORMAT = "sabueso.comparative_support_example@2"
LEGACY_FORMAT = "sabueso.comparative_support_example@1"
ACCESSIONS = {"subject": "P52270", "strain": "Q4DV43", "human": "P60174"}
RULES = {
    "sequence": ("sequence_differences_explanation@1", "equal_length_positions@1"),
    "variants": ("variant_tissue_usage_explanation@1", "pext_at_variant@1"),
    "isoforms": ("isoform_tissue_usage_explanation@1", "isoform_exon_usage@2"),
}
CURRENT_RULES = {
    "sequence": RULES["sequence"],
    "variants": ("variant_tissue_usage_explanation@2", "pext_at_variant@2"),
    "isoforms": ("isoform_tissue_usage_explanation@2", "isoform_exon_usage@3"),
}


def produce(output, fixtures, stage, *, legacy=False):
    selected_format = LEGACY_FORMAT if legacy else FORMAT
    if stage == "original":
        require(
            not output.exists() or not any(output.iterdir()), "Output must be empty"
        )
        output.mkdir(parents=True, exist_ok=True)
    else:
        require(not (output / "later.manifest.json").exists(), "Later stage exists")
        original, _ = read_stage(output, "original")
        selected_format = original["format"]
    rules = RULES if selected_format == LEGACY_FORMAT else CURRENT_RULES
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    timestamp = f"{stage} public fixture read"
    cards = {}
    with offline(), ackredit.session("public comparative support"):
        resolver = EntityResolver(
            FixtureUniProtClient(fixtures, retrieved_at=timestamp)
        )
        for role, accession in ACCESSIONS.items():
            options = {}
            if role == "subject":
                options = {
                    "uniref": True,
                    "uniref_client": FixtureUniRefClient(
                        fixtures, retrieved_at=timestamp
                    ),
                }
            elif role == "human":
                options = {
                    "gnomad": {},
                    "exon_usage": True,
                    "gtex": True,
                    "gnomad_client": FixtureGnomADClient(
                        fixtures, retrieved_at=timestamp
                    ),
                    "gtex_client": FixtureGTExClient(fixtures, retrieved_at=timestamp),
                }
            cards[role] = sabueso.resolve(accession, resolver=resolver, **options)[0]
        pins = {role: store.save(card) for role, card in cards.items()}
        report = {
            "cards": pins,
            "sequence": cards["subject"].explain_sequence_differences(cards["strain"]),
            "variants": cards["human"].explain_variant_tissue_usage(
                usage_rule=rules["variants"][1]
            ),
            "isoforms": cards["human"].explain_isoform_tissue_usage(
                usage_rule=rules["isoforms"][1]
            ),
            "execution_observation": {
                "status": "not_observed",
                "scope": "comparative_operations",
                "reason": "dedicated_comparative_operation_sidecars_are_separate_work",
            },
        }
    filename = f"{stage}.report.json"
    write_json(output / filename, report)
    manifest = {
        "format": selected_format,
        "stage": stage,
        "cards": pins,
        "files": {filename: digest(output / filename)},
        "scope": "public_frozen_responses_not_live_or_installed_artifact_qualification",
    }
    if stage == "later":
        manifest["original_manifest_sha256"] = digest(output / "original.manifest.json")
    write_json(output / f"{stage}.manifest.json", manifest)


def check_support(value, cards):
    """Verify saved locators and complete assertion envelopes without deriving anew."""
    if isinstance(value, list):
        for item in value:
            check_support(item, cards)
    elif isinstance(value, dict):
        if "source_assertion_ref" in value:
            pin, item_id = value["source_assertion_ref"].rsplit("#", 1)
            require(pin in cards, "Assertion belongs to another card")
            assertion = cards[pin].source_assertion_store.get(item_id)
            if not value.get("found"):
                require(
                    assertion is None,
                    "Recorded missing assertion now exists at original pin",
                )
            else:
                require(assertion is not None, "Missing original assertion")
                source = assertion.get("source") or {}
                expected = {
                    "id": item_id,
                    "field_path": assertion.get("field_path"),
                    "subject_ref": assertion.get("subject_ref"),
                    "source": source.get("name"),
                    "record": source.get("record_id"),
                    "version": source.get("version"),
                    "retrieved_at": assertion.get("retrieved_at"),
                    "asserted_value": assertion.get("asserted_value"),
                    "acquisition": acquisition_of(assertion),
                }
                require(
                    all(value.get(k) == v for k, v in expected.items()),
                    "Original assertion differs",
                )
                require(
                    value.get("source_metadata")
                    == (assertion.get("source_metadata") or None),
                    "Assertion metadata differs",
                )
        if "relationship_ref" in value:
            pin, item_id = value["relationship_ref"].rsplit("#", 1)
            require(
                pin in cards
                and cards[pin].relationship_store.get(item_id) == value["relationship"],
                "Original relationship differs",
            )
        if "stored" in value and "field_path" in value and "card_ref" in value:
            require(value["card_ref"] in cards, "Field belongs to another card")
            node = cards[value["card_ref"]].get(value["field_path"])
            require(
                (node is not None) == value["stored"], "Stored field presence differs"
            )
            if node is not None:
                require(node == value["node"], "Original selected field differs")
                require(
                    value["selection_rules"]
                    == cards[value["card_ref"]].selection_rules,
                    "Selection rules differ",
                )
        if "locator" in value:
            locator = value["locator"]
            require(locator["card_ref"] in cards, "Locator belongs to another card")
            card = cards[locator["card_ref"]]
            path = locator["field_path"]
            if path == "quality.enrichments":
                rows = card.quality.get("enrichments") or []
                key = "record"
            else:
                rows = (card.get(path) or {}).get("value") or []
                key = "value"
            require(
                0 <= locator["index"] < len(rows), "Original input locator is absent"
            )
            if key in value:
                require(
                    rows[locator["index"]] == value[key],
                    "Original input locator differs",
                )
        for item in value.values():
            check_support(item, cards)


def read_stage(output, stage):
    manifest = read_json(output / f"{stage}.manifest.json")
    require(
        manifest["format"] in (FORMAT, LEGACY_FORMAT) and manifest["stage"] == stage,
        "Wrong manifest",
    )
    require(set(manifest["cards"]) == set(ACCESSIONS), "Wrong card roles")
    filename = f"{stage}.report.json"
    require(set(manifest["files"]) == {filename}, "Wrong report membership")
    require(
        digest(output / filename) == manifest["files"][filename],
        "Changed original report",
    )
    store = sabueso.KnowledgeStore(output / "knowledge.db")
    cards = {}
    for role, ref in manifest["cards"].items():
        card = store.load(ref)
        require(
            card.pinned_ref() == ref
            and card.id == f"sabueso:protein:uniprot:{ACCESSIONS[role]}",
            "Wrong card binding",
        )
        require(card.acquisition_trace is None, "Saved reader has fresh acquisition")
        cards[ref] = card
    report = read_json(output / filename)
    require(report["cards"] == manifest["cards"], "Report roles differ")
    pins = [manifest["cards"][role] for role in ("subject", "strain")]
    rules = RULES if manifest["format"] == LEGACY_FORMAT else CURRENT_RULES
    for key, (explanation_rule, view_rule) in rules.items():
        explanation = report[key]
        require(
            explanation["rule"]["rule"] == explanation_rule
            and explanation["view"]["rule"]["rule"] == view_rule,
            "Unsupported original rules",
        )
        expected = pins if key == "sequence" else [manifest["cards"]["human"]]
        require(explanation["rule"]["inputs"] == expected, "Explanation pins differ")
        actual = (
            explanation["card_refs"] if key == "sequence" else [explanation["card_ref"]]
        )
        require(actual == expected, "Explanation role differs")
        require(
            {f["card_ref"] for f in explanation["fields"]} == set(expected),
            "Input field pins differ",
        )
        if key != "sequence":
            require(
                [r["item"] for r in explanation["items"]]
                == explanation["view"]["items"],
                "Original view items differ",
            )
            require(
                explanation["rule"]["parameters"]
                == explanation["view"]["rule"]["parameters"],
                "Original parameters differ",
            )
        check_support(explanation, cards)
    return manifest, report


def read(output):
    with offline(), ackredit.session("inert comparative reader"):
        before = ackredit.get_attribution().to_dict()
        for stage in ("original", "later"):
            if not (output / f"{stage}.manifest.json").exists():
                require(stage == "later", "Original stage missing")
                continue
            manifest, report = read_stage(output, stage)
            if stage == "later":
                require(
                    manifest["original_manifest_sha256"]
                    == digest(output / "original.manifest.json"),
                    "Original manifest changed",
                )
                old = read_json(output / "original.manifest.json")
                require(
                    old["format"] == manifest["format"],
                    "Reacquisition changed the scientific rule generation",
                )
                require(
                    all(old["cards"][r] != manifest["cards"][r] for r in ACCESSIONS),
                    "Reacquisition did not retain distinct revisions",
                )
            write_json(
                output / f"{stage}.reader.json",
                {
                    "cards": manifest["cards"],
                    "original_report": report,
                    "observed_acquisitions": 0,
                },
            )
        require(
            ackredit.get_attribution().to_dict() == before, "Reader generated credit"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("produce", "read", "reacquire"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Produce the explicit historical @1 report format",
    )
    args = parser.parse_args()
    try:
        if args.action == "read":
            read(args.output)
        else:
            produce(
                args.output,
                args.fixtures,
                "original" if args.action == "produce" else "later",
                legacy=args.legacy,
            )
    except (ValueError, KeyError, OSError, SabuesoError) as exc:
        parser.exit(2, f"FAIL: {exc}\n")


if __name__ == "__main__":
    main()
