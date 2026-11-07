"""Read exact public publication links and original source context, offline."""

import argparse
import socket
from pathlib import Path
from unittest.mock import patch

import sabueso
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.europepmc import FixtureEuropePMCClient

ACTIVITY_PUBLICATION = "pubmed:20889239"
LOCATED_PUBLICATION = "pubmed:40832834"
LOCATED_ARTICLE = "PMC:PMC12400196"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def forbidden(*args, **kwargs):
    raise RuntimeError("This public fixture walkthrough forbids network access")


def show(question, view):
    print(f"\n{question}\n{view}")
    return view


def choose(view, column, value):
    selected = view.filter(column, equals=value)
    require(len(selected.items()) == 1, f"Expected one retained {column}={value!r}")
    return selected


def protein(identifier, fixtures, **kwargs):
    card, resolution = sabueso.resolve(
        identifier,
        resolver=EntityResolver(FixtureUniProtClient(fixtures)),
        **kwargs,
    )
    require(resolution.status == "resolved", "The public protein was not resolved")
    return card


def compact_value(explorer, row, column):
    cell = row["cells"][column]
    if cell["value_included"]:
        return cell["value"]
    return explorer.inspect(locator=cell["value_location"]).native_payload


def activity_publication(fixtures):
    card = protein(
        "P52270", fixtures, chembl={}, chembl_client=FixtureChEMBLClient(fixtures)
    )
    explorer = card.explore()
    catalog = show(
        "TcTIM: which publications are linked in this captured source scope?",
        explorer.answer("publications"),
    )
    require(
        catalog.result_ref == explorer.view("literature").result_ref,
        "The question and topic did not retain the same original result",
    )
    selected = choose(catalog, "publication_ref", ACTIVITY_PUBLICATION)
    publication = selected.items()[0]
    detail = show("Open PMID 20889239's complete retained context:", publication.open())
    native = detail.native_payload
    require(detail.back() is selected, "The publication lost its return path")
    require(len(native["links"]) == 459, "The frozen publication context differs")
    print(
        f"The complete native_payload retains all {len(native['links'])} original "
        "relationship links. Its source activity records are not independent experiments."
    )

    compact = explorer.access.select(
        "literature",
        fields=["publication_ref", "year", "measurement_count"],
        where={"publication_ref": ACTIVITY_PUBLICATION},
        item_refs=[publication.item_ref],
    )
    page = compact.page(limit=1, max_bytes=16384)
    require(page["page"]["blocked"] is None, "The compact page cannot fit its budget")
    require(len(page["items"]) == 1, "The exact compact selection is missing")
    require(
        compact.result_ref == catalog.result_ref,
        "Compact projection changed the original publication result",
    )
    row = page["items"][0]
    print(
        "\nThe agent projection selects the same original member:",
        {
            key: compact_value(explorer, row, key)
            for key in ("publication_ref", "year", "measurement_count")
        },
    )
    print(
        "The year retains its source text type; absent bibliography values stay null."
    )

    missing = show(
        "What does an exact publication reference without a stored link return?",
        explorer.view("literature", options={"publication_ref": "pubmed:999999999"}),
    )
    require(
        missing.native_payload["status"] == "not_on_card"
        and missing.native_payload["reason"] == "no_stored_publication_link",
        "The missing-publication outcome changed",
    )
    print("not_on_card describes this capture; it does not establish article absence.")
    require(catalog.capabilities["save"] is False, "Review the example's saved scope")
    print(
        "Publication-profile saving is explicitly unavailable in this live increment."
    )


def follow(links, role, question):
    selected = links.filter("role", equals=role)
    require(len(selected.items()) > 0, f"No original {role} destination was retained")
    opened = show(question, selected.items()[0].open())
    require(opened.back() is selected, "The original destination lost its return path")
    return opened


def located_publication(fixtures):
    card = protein(
        "P60174",
        fixtures,
        europepmc={"article_ids": LOCATED_ARTICLE},
        europepmc_client=FixtureEuropePMCClient(fixtures),
    )
    explorer = card.explore()
    focused = show(
        "HsTIM: what original context links PMID 40832834 to this protein?",
        explorer.view("literature", options={"publication_ref": LOCATED_PUBLICATION}),
    )
    publication = focused.items()[0]
    native = publication.open().native_payload
    structural = next(
        link
        for link in native["links"]
        if link["relationship"]["predicate"] == "structure_mentioned_in"
    )
    context = structural["structure_contexts"][0]
    require(
        structural["source_assertions"] and context["source_assertions"],
        "Both original source-support legs are required",
    )
    structure = context["relationships"][0]["relationship"]["object_ref"]
    print(
        f"The structure occurrence links through {structure}, with original mention "
        f"and protein/structure support; its scope is {context['context']['scope']}."
    )

    links = publication.related()
    follow(links, "source", "Follow an original SourceAssertion:")
    follow(links, "original_relationship", "Follow an original relationship:")
    follow(links, "structure_mentions", "Open a retained structure-mention locator:")
    require(links.back() is focused, "The context links lost the publication selection")
    unlinked = native["unlinked_pdb_mentions"]
    require(
        len(unlinked) == 3
        and {row["structure_ref"] for row in unlinked} == {"pdb:7QON"},
        "The frozen unlinked structure occurrences differ",
    )
    print(
        "Three 7QON occurrences remain unlinked to HsTIM. A located mention records "
        "naming; it does not establish support for an arbitrary scientific claim."
    )


def empty_annotation_scope(fixtures):
    card = protein(
        "P60174",
        fixtures,
        europepmc={"article_ids": "MED:18562316"},
        europepmc_client=FixtureEuropePMCClient(fixtures),
    )
    explorer = card.explore()
    selected = explorer.access.select("literature", fields=[])
    page = selected.page(limit=1, max_bytes=8192)
    coverage = explorer.inspect(locator=page["coverage"]["location"]).native_payload
    rows = [
        row
        for row in coverage["rows"]
        if row["source"] == "Europe PMC"
        and row["area"]
        in ("relationships.mentioned_in", "relationships.structure_mentioned_in")
    ]
    require(
        len(rows) == 2 and {row["state"] for row in rows} == {"not_stated"},
        "The frozen empty annotation request changed",
    )
    print("\nWhat does an empty annotation request say about the whole catalog?")
    for row in rows:
        print(f"{row['source']} / {row['area']}: {row['state']}")
    print(
        f"This captured Card still retains {selected.count} linked publications. "
        "The empty MED:18562316 annotation response supplies no article-absence claim."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "temp_data",
    )
    args = parser.parse_args()
    with (
        patch.object(socket.socket, "connect", forbidden),
        patch.object(socket, "create_connection", forbidden),
    ):
        activity_publication(args.fixtures)
        located_publication(args.fixtures)
        empty_annotation_scope(args.fixtures)
    print(
        "\nOnly declared public fixture responses were read. Exploration acquires "
        "no articles or new metadata, creates no project Evidence and establishes "
        "no efficacy conclusion. Independent original saved reading and researcher "
        "acceptance remain separate work."
    )


if __name__ == "__main__":
    main()
