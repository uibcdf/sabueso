"""Review public protein contexts with human, agent and independent saved access."""

import argparse
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import sabueso
from sabueso.core.snapshot import canonical_json

FORMAT = "sabueso.protein_context_review_example@1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def forbidden(*args, **kwargs):
    raise RuntimeError(
        "This walkthrough must not acquire data during exploration or reading"
    )


def pages(selection):
    """Consume the complete bounded agent response, including every page."""
    result, seen, cursor = [], set(), None
    while True:
        page = selection.page(cursor=cursor, limit=3, max_bytes=65536)
        require(
            page["page"]["blocked"] is None, "Agent response exceeded the page budget"
        )
        result.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            break
        require(cursor not in seen, "Agent pagination did not advance")
        seen.add(cursor)
    require(len(result) == selection.count, "Agent response is incomplete")
    return result


def inspect_source(view, item_ref=None):
    """Open one actual retained source; keep its original return selection."""
    item = view.item(item_ref) if item_ref else view.items()[0]
    explanation = item.explain()
    require(explanation.back() is view, "Explanation lost its original view")
    links = item.related().filter("role", equals="source")
    require(len(links.items()) > 0, "The selected public item has no original source")
    source = links.items()[0].open()
    require(source.back() is links, "Source navigation lost its return path")
    return {
        "item_ref": item.item_ref,
        "explanation": digest(explanation.native_payload),
        "source": digest(source.native_payload),
        "source_context": {
            key: value for key, value in source.context.items() if key != "mode"
        },
    }


def observe(explorer, question, topic, options=None, *, source_label=None, fields=None):
    view = explorer.answer(question, options=options)
    # Reuse the effective request, including explicit native defaults.
    fields = list(view.items()[0].cells) if fields is None else fields
    machine = explorer.access.select(
        topic, options=view.request["options"], fields=fields
    )
    frames = pages(machine)
    require(
        view.result_ref == machine.result_ref,
        f"Human and agent results differ for {question}: {view.result_ref} / {machine.result_ref}",
    )
    require(
        [row.item_ref for row in view.items()] == [row["item_ref"] for row in frames],
        "Human and agent membership differs",
    )
    agent_observations = []
    for human, frame in zip(view.items(), frames, strict=True):
        agent_cells = {}
        for key, cell in frame["cells"].items():
            # Compact responses can defer values while retaining exact locations.
            value = (
                cell["value"]
                if cell["value_included"]
                else explorer.inspect(locator=cell["value_location"]).native_payload
            )
            agent_cells[key] = {
                "value": value,
                "state": cell["state"],
                "reason": cell["reason"],
            }
        require(
            digest(
                {
                    key: {
                        "value": cell.value,
                        "state": cell.state,
                        "reason": cell.reason,
                    }
                    for key, cell in human.cells.items()
                }
            )
            == digest(agent_cells),
            "Human and agent values, units or states differ",
        )
        # Some adapters intentionally inline only a compact membership summary.
        support = explorer.inspect(locator=frame["support_location"]).native_payload
        require(human.support == [support], "Human and agent source support differs")
        agent_observations.append(
            {"item_ref": frame["item_ref"], "cells": agent_cells, "support": support}
        )
    require(len(view.items()) > 0, "Expected a positive public example")
    selected = view.filter("label", equals=source_label) if source_label else view
    source = inspect_source(selected)
    empty = view.filter("label", equals="Unmatched walkthrough display filter")
    require(
        not len(empty.items()) and empty.back() is view,
        "Empty recovery lost its origin",
    )
    record = {
        "question": question,
        "topic": topic,
        "options": view.request["options"],
        "fields": fields,
        "result_ref": view.result_ref,
        "view_ref": view.view_ref,
        "native": digest(view.native_payload),
        "rows": digest(view.rows()),
        "agent_items": digest(agent_observations),
        "count": len(view.items()),
        "source_label": source_label,
        "source": source,
    }
    print(f"\n{question}:\n{view}")
    return view, record


def save_session(output, name, explorer, routes):
    records, root = [], None
    for question, topic, options, source_label in routes:
        root, record = observe(
            explorer, question, topic, options, source_label=source_label
        )
        records.append(record)
    receipt = root.save(output / f"{name}.json.gz", compression="gzip")
    return {"bundle_digest": receipt["bundle_digest"], "routes": records}


def load_public_cards(fixtures):
    """Explicitly prepare three public inputs before starting a review."""
    from sabueso.resolver import EntityResolver, FixtureUniProtClient
    from sabueso.tools.db.gnomad import FixtureGnomADClient
    from sabueso.tools.db.gtex import FixtureGTExClient
    from sabueso.tools.db.uniref import FixtureUniRefClient

    resolver = EntityResolver(FixtureUniProtClient(fixtures))
    subject = sabueso.resolve(
        "P52270",
        resolver=resolver,
        uniref=True,
        uniref_client=FixtureUniRefClient(fixtures),
    )[0]
    strain = sabueso.resolve("Q4DV43", resolver=resolver)[0]
    human = sabueso.resolve(
        "P60174",
        resolver=resolver,
        gnomad={},
        exon_usage=True,
        gtex=True,
        gnomad_client=FixtureGnomADClient(fixtures),
        gtex_client=FixtureGTExClient(fixtures),
    )[0]
    return subject, strain, human


def produce(fixtures, output):
    require(
        not output.exists() or (output.is_dir() and not any(output.iterdir())),
        "Choose an empty output directory",
    )
    output.mkdir(parents=True, exist_ok=True)
    subject, strain, human = load_public_cards(fixtures)
    originals = [card.to_dict() for card in (subject, strain, human)]
    # Fixture acquisition above is explicit. Browsing below cannot refresh or resolve.
    with patch("sabueso.resolve", forbidden):
        comparison = subject.explore(related_cards=[strain])
        other = comparison.context["inputs"][1]
        print(
            "TcTIM: orient, discover questions and retain supplied context.\n",
            comparison.overview(),
        )
        print(comparison.questions())
        comparisons = save_session(
            output,
            "comparisons",
            comparison,
            [
                ("related_proteins", "comparative_context", None, None),
                (
                    "sequence_differences",
                    "comparative_context",
                    {"other_ref": other},
                    None,
                ),
                (
                    "knowledge_differences",
                    "comparative_context",
                    {"other_ref": other},
                    "features_positional.active_site",
                ),
            ],
        )
        context = human.explore()
        print(
            "HsTIM: inspect its own genomic and tissue context.\n", context.overview()
        )
        print(context.questions())
        human_context = save_session(
            output,
            "human_context",
            context,
            [
                ("variant_tissue_context", "variants", None, None),
                ("isoform_tissue_context", "variants", None, None),
                ("sequence_changes", "sequence_changes", None, None),
                ("protein_associations", "associations", None, None),
            ],
        )
    require(
        originals == [card.to_dict() for card in (subject, strain, human)],
        "Exploration changed a Card",
    )
    write_json(
        output / "review.json",
        {
            "format": FORMAT,
            "sessions": {"comparisons": comparisons, "human_context": human_context},
            "acceptance": "technical_preparation_only",
        },
    )
    print(
        "\nSaved seven public routes. Equal positions do not establish correspondence; associations do not establish causality. Researcher acceptance remains pending."
    )


def read(output):
    manifest = json.loads((output / "review.json").read_text(encoding="utf-8"))
    require(manifest["format"] == FORMAT, "Unknown walkthrough format")
    for name, session in manifest["sessions"].items():
        root = sabueso.read_exploration(
            output / f"{name}.json.gz", expected_digest=session["bundle_digest"]
        )
        require(
            root.explorer.mode == "saved", "Expected an independent saved exploration"
        )
        for original in session["routes"]:
            _, restored = observe(
                root.explorer,
                original["question"],
                original["topic"],
                original["options"],
                source_label=original["source_label"],
                fields=original["fields"],
            )
            require(
                restored == original,
                f"Original route changed: {original['question']}; changed members: {[key for key in original if original[key] != restored.get(key)]}",
            )
    print(
        "\nOriginal human, source and complete agent responses reopened without fixtures or acquisition. Scientific and researcher acceptance remain pending."
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
        stack.enter_context(patch("socket.create_connection", forbidden))
        stack.enter_context(patch("socket.socket.connect", forbidden))
        if args.command == "produce":
            produce(args.fixtures, args.output)
        else:
            stack.enter_context(patch("sabueso.resolve", forbidden))
            read(args.output)


if __name__ == "__main__":
    main()
