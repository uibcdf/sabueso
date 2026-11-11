"""Review public structure declarations, original contacts and assembly limits."""

import argparse
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import sabueso
from sabueso.core.snapshot import canonical_json

FORMAT = "sabueso.structural_source_review_example@1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def forbidden(*args, **kwargs):
    raise RuntimeError("This public review must not acquire sources while browsing")


def role(view, name):
    items = view.filter("role", equals=name).items()
    require(len(items) == 1, f"Expected one original {name} route")
    return items[0].open()


def original_fields(explorer, location):
    """Compare every finite agent item with the exact original literal node."""
    human = explorer.inspect(locator=location).native_payload
    selection = explorer.access.read(location)
    cursor, seen, observations = None, set(), []
    while True:
        page = selection.page(cursor=cursor, limit=2, max_bytes=16384)
        require(page["page"]["blocked"] is None, "Original read exceeded its budget")
        for item in page["items"]:
            value = (
                item["value"]
                if item["value_included"]
                else explorer.inspect(locator=item["value_location"]).native_payload
            )
            require(
                digest(value) == digest(human[item["key"]]),
                "Agent original field differs from human inspection",
            )
            observations.append(
                {
                    "key": item["key"],
                    "state": item["state"],
                    "support_basis": item["support_basis"],
                    "value": digest(value),
                }
            )
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            break
        require(cursor not in seen, "Original pagination did not advance")
        seen.add(cursor)
    require(
        len(observations) == selection.count == len(human), "Incomplete original read"
    )
    return {"native": digest(human), "items": observations}


def first_annotation(explorer):
    return (
        explorer.view("annotated_regions")
        .filter("feature_type", equals="active_site")
        .items()[0]
    )


def review(explorer):
    annotation = first_annotation(explorer)
    region = role(annotation.related(), "question")
    require(region.request["options"]["region"] == [96], "Different annotation scope")
    selected = region.filter("structure_ref", equals="pdb:1SUX")
    require(len(selected.items()) == 1, "Expected one original 1SUX declaration")
    item = selected.items()[0]
    detail = item.open()
    context = detail.regional_reading
    require(detail.back() is selected, "Lost the selected regional declaration")
    chains = []
    for chain in context["chains"]:
        chains.append(
            {
                "chain": chain["chain"],
                "missing_count": chain["missing_count"],
                "gaps": original_fields(explorer, chain["missing_positions_location"]),
                "numbering": original_fields(explorer, chain["numbering_location"]),
            }
        )
    gaps = explorer.answer(
        "region_coverage", options={"sequence_ref": "uniprot:P52270", "region": [1, 96]}
    ).filter("structure_ref", equals="pdb:1SUX")
    gap_detail = gaps.items()[0].open()
    require(
        gap_detail.regional_reading["complete_chains"] == [],
        "A requested coordinate gap was lost",
    )
    links = item.related()
    sources = []
    for source_item in links.filter("role", equals="source").items():
        source = source_item.open()
        require(source.back() is source_item.back(), "Source lost its original return")
        sources.append(digest(source.native_payload))

    ligands = role(links, "ligand_context")
    ligand_context = ligands.ligand_reading
    components, contacts = [], []
    for entry in ligand_context["entries"]:
        components.append(
            {
                "index": entry["index"],
                "component_id": entry["component_id"]["value"],
                "instance_count": entry["instances"]["count"],
            }
        )
        component = ligands.items()[entry["index"]].open()
        instances = next(i for i in component.items() if i.label == "instances").open()
        for instance_item in instances.items():
            instance = instance_item.open()
            original = instance.ligand_reading["entries"][0]
            require(
                instance.back() is instances, "Instance lost its original selection"
            )
            contacts.append(
                {
                    "component_index": entry["index"],
                    "instance_id": original["instance_id"]["value"],
                    "contacts": original_fields(
                        explorer, original["contacts"]["location"]
                    ),
                }
            )

    assembly = role(links, "question")
    machine = explorer.access.select(
        "assembly_generation",
        fields=["structure_ref", "assembly_id", "declaration_count"],
        options=assembly.request["options"],
    )
    require(machine.result_ref == assembly.result_ref, "Different human/agent assembly")
    page = machine.page(limit=2, max_bytes=16384)
    require(
        page["page"]["complete"] and page["page"]["blocked"] is None,
        "The bounded assembly example needs its complete agent page",
    )
    require(
        [row.item_ref for row in assembly.items()]
        == [row["item_ref"] for row in page["items"]],
        "Different human/agent assembly membership",
    )
    agent_assembly = []
    for human, frame in zip(assembly.items(), page["items"], strict=True):
        cells = {}
        for key, cell in frame["cells"].items():
            value = (
                cell["value"]
                if cell["value_included"]
                else explorer.inspect(locator=cell["value_location"]).native_payload
            )
            observation = {
                "value": value,
                "state": cell["state"],
                "reason": cell["reason"],
            }
            require(
                digest(observation)
                == digest(
                    {
                        "value": human.cells[key].value,
                        "state": human.cells[key].state,
                        "reason": human.cells[key].reason,
                    }
                ),
                "Different human/agent assembly cells",
            )
            cells[key] = observation
        support = explorer.inspect(locator=frame["support_location"]).native_payload
        require(human.support == [support], "Different original assembly support")
        agent_assembly.append(
            {"item_ref": frame["item_ref"], "cells": cells, "support": digest(support)}
        )
    require(
        assembly.native_payload["physical_membership"] == "not_computed",
        "Declaration counts must not become physical membership",
    )
    positions = role(assembly.items()[0].related(), "components")
    original_positions = []
    for position in positions.filter("role", equals="component").items():
        opened = position.open()
        require(opened.back() is position.back(), "Component lost its original return")
        original_positions.append(
            {"label": position.label, "native": digest(opened.native_payload)}
        )
    empty = selected.filter("label", equals="Unmatched structural review selection")
    require(
        not len(empty.items()) and empty.back() is selected,
        "Empty recovery lost origin",
    )
    observation = {
        "card_ref": explorer.context["card_ref"],
        "annotation": digest(annotation.open().native_payload),
        "region_result": region.result_ref,
        "region_request": region.request,
        "relationship_ref": context["relationship_ref"],
        "coordinate_status": context["coordinate_basis"]["status"],
        "reference_revision": context["coordinate_basis"][
            "structure_reference_revision"
        ],
        "complete_chains": context["complete_chains"],
        "chains": chains,
        "gapped_region": digest(
            explorer.inspect(
                locator=gap_detail.regional_reading["item_location"]
            ).native_payload
        ),
        "sources": sources,
        "ligands": components,
        "contacts": contacts,
        "assembly_result": assembly.result_ref,
        "assembly_request": assembly.request,
        "assembly_native": digest(assembly.native_payload),
        "agent_assembly": agent_assembly,
        "positions": original_positions,
        "physical_membership": assembly.native_payload["physical_membership"],
    }
    print("Original region, chain gaps and numbering:\n", detail)
    print("Requested region with a coordinate gap:\n", gap_detail)
    print("Original ligand declarations and contacts:\n", ligands)
    print("Separate assembly declaration positions:\n", positions)
    return assembly, observation


def historical(explorer):
    unavailable = role(first_annotation(explorer).related(), "question")
    require(
        unavailable.outcome["status"] == "missing_prerequisite",
        "Lost historical unknown",
    )
    print("Historical annotation with missing original native scope:\n", unavailable)
    return unavailable, {"outcome": unavailable.outcome, "request": unavailable.request}


def produce(fixtures, output):
    from sabueso.core.card import Card
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

    require(
        not output.exists() or (output.is_dir() and not any(output.iterdir())),
        "Choose an empty output directory",
    )
    output.mkdir(parents=True, exist_ok=True)
    current, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(fixtures),
            rcsb_client=FixtureRCSBClient(fixtures / "rcsb_nonpolymer_instances"),
        ),
        structures=["1SUX"],
    )
    legacy = Card.from_dict(
        json.loads(
            (fixtures / "frozen_cards/schema_0.3.9__P52270.json").read_text(
                encoding="utf-8"
            )
        )
    )
    originals = [c.to_dict() for c in (current, legacy)]
    sessions = {}
    with patch("sabueso.resolve", forbidden):
        for name, card, observe in (
            ("current", current, review),
            ("historical", legacy, historical),
        ):
            root, observation = observe(card.explore())
            receipt = root.save(output / f"{name}.json.gz", compression="gzip")
            sessions[name] = {
                "bundle_digest": receipt["bundle_digest"],
                "observation": observation,
            }
    require(
        originals == [c.to_dict() for c in (current, legacy)], "Review changed a Card"
    )
    (output / "review.json").write_text(
        json.dumps(
            {
                "format": FORMAT,
                "sessions": sessions,
                "acceptance": "technical_preparation_only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def read(output):
    manifest = json.loads((output / "review.json").read_text(encoding="utf-8"))
    require(manifest["format"] == FORMAT, "Unknown structural review format")
    require(
        set(manifest["sessions"]) == {"current", "historical"},
        "Different recorded sessions",
    )
    for name, observe in (("current", review), ("historical", historical)):
        session = manifest["sessions"][name]
        saved = sabueso.read_exploration(
            output / f"{name}.json.gz", expected_digest=session["bundle_digest"]
        )
        # A source-navigation destination owns a distinct actual access. Return
        # through the retained public trail before replaying the initial task;
        # finite requests must stay with the access that actually executed them.
        initial = saved
        seen = set()
        while initial.back() is not initial:
            require(id(initial) not in seen, "Saved return navigation contains a cycle")
            seen.add(id(initial))
            initial = initial.back()
        _, observation = observe(initial.explorer)
        require(
            observation == session["observation"],
            f"Original {name} structural observations changed: "
            f"{[key for key in observation if observation[key] != session['observation'].get(key)]}",
        )
    print(
        "Original sources and finite agent reads reopened. Independent researcher/scientific acceptance remains pending."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("produce")
    prepare.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    prepare.add_argument("--output", type=Path, required=True)
    reopen = commands.add_parser("read")
    reopen.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with ExitStack() as stack:
        stack.enter_context(patch("socket.socket.connect", forbidden))
        stack.enter_context(patch("socket.create_connection", forbidden))
        if args.command == "produce":
            produce(args.fixtures, args.output)
        else:
            stack.enter_context(patch("sabueso.resolve", forbidden))
            read(args.output)


if __name__ == "__main__":
    main()
