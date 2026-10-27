"""Stable statements never silently select among different input observations."""

import hashlib
import json
import socket
from copy import deepcopy

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.errors import SchemaError
from sabueso.core.merge import merge_mapping_results
from sabueso.core.source_assertion_store import (
    SourceAssertionStore,
    make_source_assertion,
)
from sabueso.mappings.uniprot import map_protein
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.alphafold import FixtureAlphaFoldClient


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("No source query")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def statement():
    a = make_source_assertion(
        "sequence.checksums", {"md5": "a" * 32}, "UniProt", "P52270", "2026-01-01"
    )
    a["source"]["version"] = "synthetic-first"
    return a


@pytest.mark.parametrize(
    "part",
    [
        "version",
        "retrieved_at",
        "metadata",
        "acquisition",
        "normalized_value",
        "subject",
        "value_type",
    ],
)
@pytest.mark.parametrize("reverse", [False, True])
def test_add_refuses_conflicting_records_under_one_semantic_id_atomically(
    part, reverse
):
    first = statement()
    if part == "value_type":
        first = make_source_assertion(
            "sequence.length", 1, "UniProt", "P52270", "2026-01-01"
        )
    second = deepcopy(first)
    if part == "version":
        second["source"]["version"] = "synthetic-later"
    elif part == "retrieved_at":
        second["retrieved_at"] = "2026-01-02"
    elif part == "metadata":
        first["source_metadata"] = {"sequence_version": 1}
        second["source_metadata"] = {"sequence_version": 2}
    elif part == "acquisition":
        second["acquisition"]["origin"] = "text_mining"
    elif part == "normalized_value":
        second["normalized_value"] = {"md5": "a" * 32}
    elif part == "subject":
        second["subject_ref"] = "uniprot:P60174"
    elif part == "value_type":
        second["asserted_value"] = True
    one, two = (second, first) if reverse else (first, second)
    original = deepcopy(one)
    incoming = deepcopy(two)
    store = SourceAssertionStore([one])
    with pytest.raises(SchemaError, match="observations"):
        store.add(two)
    assert store.to_list() == [original] and two == incoming


def test_exact_duplicate_is_order_independent_and_detached_from_caller():
    first = statement()
    second = dict(reversed(list(deepcopy(first).items())))
    store = SourceAssertionStore([first, second])
    assert len(store.to_list()) == 1
    original = deepcopy(store.to_list())
    first["source"]["version"] = "caller-change"
    second["asserted_value"]["md5"] = "caller-change"
    assert store.to_list() == original


@pytest.mark.parametrize("reverse", [False, True])
def test_compatible_metadata_completion_retains_every_key_without_caller_aliases(
    reverse,
):
    first, second = statement(), statement()
    first["source_metadata"] = {"context": {"sequence_version": 1}}
    second["source_metadata"] = {"context": {"assembly": "synthetic"}}
    store = SourceAssertionStore([second, first] if reverse else [first, second])
    assert store.get(first["id"])["source_metadata"] == {
        "context": {"sequence_version": 1, "assembly": "synthetic"}
    }
    first["source_metadata"]["context"]["sequence_version"] = 2
    assert (
        store.get(second["id"])["source_metadata"]["context"]["sequence_version"] == 1
    )


@pytest.mark.parametrize(
    "old,new", [(None, {}), ([1], [True]), ({"version": 1}, {"version": 2})]
)
def test_metadata_conflicts_never_become_completion_or_list_union(old, new):
    first, second = statement(), statement()
    first["source_metadata"] = {"context": deepcopy(old)}
    second["source_metadata"] = {"context": deepcopy(new), "extra": "must not enter"}
    store = SourceAssertionStore([first])
    with pytest.raises(SchemaError, match="different retained observations"):
        store.add(second)
    assert store.to_list() == [first]


def test_public_alias_intake_keeps_both_dated_requests_in_its_explanation():
    from sabueso.core.card_exploration_coverage_v1 import _v1_knowledge_state
    from sabueso.tools.db.europepmc import FixtureEuropePMCClient

    class DatedAnswers:
        def annotations(self, requested):
            answer = FixtureEuropePMCClient("temp_data").annotations(
                ["PMC:PMC12400196"]
            )
            answer["retrieved_at"] = (
                "second" if requested[0].startswith("MED:") else "first"
            )
            return answer

    card, _ = sabueso.resolve(
        "P60174",
        resolver=EntityResolver(FixtureUniProtClient("temp_data")),
        europepmc={"article_ids": ["PMC:PMC12400196", "MED:40832834"]},
        europepmc_client=DatedAnswers(),
    )
    explanation = card.explain_literature("pubmed:40832834")
    assert card.knowledge_state()["rows"] == _v1_knowledge_state(card)["rows"]
    assert all(row["status"] == "added" for row in explanation["annotation_requests"])
    assert {
        tuple(row["article_ids"]) for row in explanation["annotation_requests"]
    } == {
        ("PMC:PMC12400196",),
        ("MED:40832834",),
    }
    annotations = [
        row
        for row in card.source_assertion_store.to_list()
        if (row.get("source_metadata") or {}).get("content_kind")
        == "located_accession_annotation"
        and row["subject_ref"] == "uniprot:P60174"
    ]
    assert len(annotations) == 1
    assert {
        tuple(sorted(item.items()))
        for item in annotations[0]["source_metadata"]["annotation_requests"]
    } == {
        (("requested_article", "PMC:PMC12400196"), ("retrieved_at", "first")),
        (("requested_article", "MED:40832834"), ("retrieved_at", "second")),
    }


@pytest.mark.parametrize("restore", [False, True])
def test_extraction_restore_prevalidates_the_entire_batch_with_typed_values(restore):
    from sabueso.core.card import Card
    from sabueso.core.literature_extraction import _merge

    first = statement()
    first["asserted_value"] = {"offset": 1}
    conflicting = deepcopy(first)
    conflicting["asserted_value"]["offset"] = True
    new = make_source_assertion(
        "annotations.function", "new", "synthetic", "new", "time"
    )
    card = Card()
    card.source_assertion_store.add(first)
    before = deepcopy(card.to_dict())
    with pytest.raises(SchemaError, match="Conflicting extraction support"):
        _merge(
            card, [new, conflicting], [], {"id": "synthetic"}, preserve_original=restore
        )
    assert card.to_dict() == before


@pytest.mark.parametrize("reverse", [False, True])
def test_identical_located_annotation_retains_all_alias_request_dates(reverse):
    from sabueso.mappings.europepmc import map_annotations
    from sabueso.tools.db.europepmc import FixtureEuropePMCClient

    record = FixtureEuropePMCClient("temp_data").annotations(["PMC:PMC12400196"])[
        "record"
    ]
    mappings = [
        map_annotations(record, "P60174", date, requested)
        for date, requested in [
            ("2026-01-02", "PMC:PMC12400196"),
            ("2026-01-01", "MED:40832834"),
            ("2026-01-03", "MED:40832834"),
        ]
    ]
    original = deepcopy(mappings)
    result = merge_mapping_results(list(reversed(mappings)) if reverse else mappings)
    store = SourceAssertionStore(result["source_assertions"])
    (row,) = store.to_list()
    assert row["source_metadata"]["annotation_requests"] == [
        {"requested_article": "MED:40832834", "retrieved_at": "2026-01-01"},
        {"requested_article": "MED:40832834", "retrieved_at": "2026-01-03"},
        {"requested_article": "PMC:PMC12400196", "retrieved_at": "2026-01-02"},
    ]
    assert row["retrieved_at"] == "2026-01-01"
    assert mappings == original
    again = merge_mapping_results([result, *mappings])
    assert again["source_assertions"] == result["source_assertions"]


@pytest.mark.parametrize(
    "difference", ["version", "subject_ref", "asserted_value", "identity_basis"]
)
def test_annotation_receipts_never_merge_distinct_source_contexts(difference):
    from sabueso.mappings.europepmc import map_annotations
    from sabueso.tools.db.europepmc import FixtureEuropePMCClient

    record = FixtureEuropePMCClient("temp_data").annotations(["PMC:PMC12400196"])[
        "record"
    ]
    one = map_annotations(record, "P60174", "first", "PMC:PMC12400196")
    two = deepcopy(one)
    row = two["source_assertions"][0]
    if difference == "version":
        row["source"]["version"] = "other"
    elif difference == "identity_basis":
        row["source_metadata"]["identity_basis"]["accession"] = "P52270"
    else:
        row[difference] = "different"
    with pytest.raises(SchemaError):
        SourceAssertionStore(merge_mapping_results([one, two])["source_assertions"])


def test_equal_uniprot_text_for_distinct_products_keeps_both_original_comments():
    comments = [
        {
            "commentType": "FUNCTION",
            "molecule": label,
            "texts": [{"value": "Same synthetic text"}],
        }
        for label in ["synthetic product 1", "synthetic product 2"]
    ]
    mapped = map_protein(
        {"primaryAccession": "SYNTHETIC", "comments": comments}, "synthetic"
    )
    store = SourceAssertionStore(mapped["source_assertions"])
    rows = store.find_by_field("annotations.function")
    assert len(rows) == 2 and rows[0]["id"] != rows[1]["id"]
    assert [row["asserted_value"]["comment"] for row in rows] == comments
    assert all(row["normalized_value"] == "Same synthetic text" for row in rows)


def entry(version):
    seq = "M" * 100
    return {
        "primaryAccession": "P52270",
        "entryType": "UniProtKB reviewed (Swiss-Prot)",
        "sequence": {
            "value": seq,
            "length": 100,
            "md5": hashlib.md5(seq.encode(), usedforsecurity=False).hexdigest(),
        },
        "entryAudit": {"entryVersion": version, "sequenceVersion": 1},
        "proteinDescription": {
            "recommendedName": {"fullName": {"value": "Synthetic protein"}}
        },
    }


@pytest.mark.parametrize("reverse", [False, True])
def test_mapping_merge_refuses_silent_observation_selection(reverse):
    mappings = [
        map_protein(entry(1), "2026-01-01"),
        map_protein(entry(2), "2026-01-02"),
    ]
    if reverse:
        mappings.reverse()
    original = deepcopy(mappings)
    combined = merge_mapping_results(mappings)
    assert len(combined["source_assertions"]) == sum(
        len(m["source_assertions"]) for m in mappings
    )
    with pytest.raises(SchemaError, match="observations"):
        build_card_from_mapping(combined, meta={"entity_type": "protein"})
    assert mappings == original


def test_public_refresh_rebuilds_a_new_observation_and_preserves_original_pins(
    tmp_path,
):
    digest = entry(1)["sequence"]["md5"]
    model = {
        "entryId": "AF-SYNTHETIC-F1",
        "uniprotAccession": "P52270",
        "sequenceChecksum": digest,
        "uniprotStart": 1,
        "uniprotEnd": 100,
        "latestVersion": 6,
    }
    dirs = []
    for version in (1, 2):
        directory = tmp_path / str(version)
        directory.mkdir()
        dirs.append(directory)
        (directory / "P52270.json").write_text(
            json.dumps(entry(version)), encoding="utf-8"
        )
        (directory / "alphafold").mkdir()
        (directory / "alphafold/P52270.json").write_text(
            json.dumps([model]), encoding="utf-8"
        )

    def options(index):
        return {
            "resolver": EntityResolver(
                FixtureUniProtClient(dirs[index], retrieved_at=f"2026-01-0{index + 1}")
            ),
            "alphafold_client": FixtureAlphaFoldClient(
                dirs[index], retrieved_at=f"2026-01-0{index + 1}"
            ),
        }

    original, _ = sabueso.resolve("P52270", predicted_structures=True, **options(0))
    before = deepcopy(original.to_dict())
    store = sabueso.KnowledgeStore(tmp_path / "observations.db")
    old_pin = store.save(original)
    refreshed, _ = sabueso.refresh_card(original, store=store, **options(1))
    new_pin = store.save(refreshed)
    old = original.get("sequence.checksums")["source_assertion_ids"][0]
    new = refreshed.get("sequence.checksums")["source_assertion_ids"][0]
    assert old == new and old_pin != new_pin
    assert original.source_assertion_store.get(old)["source"]["version"] == "1"
    assert refreshed.source_assertion_store.get(new)["source"]["version"] == "2"
    assert original.predicted_structures()["items"][0]["sequence_matches"] is True
    assert refreshed.predicted_structures()["items"][0]["sequence_matches"] is True
    assert store.load(old_pin).to_dict() == before == original.to_dict()
    assert store.load(new_pin).to_dict() == refreshed.to_dict()
