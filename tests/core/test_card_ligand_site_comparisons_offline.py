"""Human comparisons retain native science, exact inputs and explicit gaps."""

import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.snapshot import canonical_json
from sabueso.mappings.pdbe_kb import map_ligand_sites
from sabueso.mappings.uniprot import map_protein

TOPIC = "ligand_site_comparisons"


def forbidden(*a, **k):
    raise AssertionError(
        "No source requests, recapture or repeated scientific calculation"
    )


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    # Bind the ordinary native reader before tests temporarily replace its module
    # attribute; a first import under a spy would retain that spy in another module.
    importlib.import_module("sabueso.core.ligand_explanation")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def protein(
    *, position=2, molecule=None, modifier="EXACT", annotation=True, ligand_code="ATP"
):
    native = {
        "primaryAccession": "P52270",
        "sequence": {"value": "M" * 20, "length": 20},
        "entryAudit": {"sequenceVersion": 7},
        "features": [
            {
                "type": "Active site",
                "description": "Explicit synthetic active site",
                "molecule": molecule,
                "location": {
                    "start": {"value": 2, "modifier": modifier},
                    "end": {"value": 4, "modifier": "EXACT"},
                },
            }
        ]
        if annotation
        else [],
    }
    card = build_card_from_mapping(
        map_protein(native, "synthetic"), meta={"entity_type": "protein"}
    )
    mapped = map_ligand_sites(
        {
            "accession": "P52270",
            "record": {
                "data": [
                    {
                        "accession": ligand_code,
                        "name": "Explicit synthetic ligand",
                        "residues": [
                            {
                                "startIndex": position,
                                "endIndex": position,
                                "indexType": "UNIPROT",
                                "startCode": "M",
                                "endCode": "M",
                            }
                        ],
                    }
                ]
            },
        },
        "synthetic",
    )
    for row in mapped["source_assertions"]:
        card.source_assertion_store.add(row)
    for row in mapped["relationships"]:
        card.relationship_store.add(row)
    return card


@pytest.mark.parametrize("card", ["public", "synthetic"])
def test_native_conformance_sources_and_original_inputs_are_preserved(card):
    card = (
        protein()
        if card == "synthetic"
        else Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text(
                    encoding="utf-8"
                )
            )
        )
    )
    before = card.to_dict()
    expected = card.ligand_sites()
    explorer = card.explore()
    question = explorer.answer(TOPIC)
    assert question.native_payload == expected
    assert explorer.view(TOPIC).result_ref == question.result_ref
    assert len(question.items()) == len(expected["items"])
    assert question.context["adapter"] == "ligand_site_exploration@1"
    for item in question.items():
        native = next(
            row
            for row in expected["items"]
            if row["relationship_id"] == item._entry.key
        )
        assert item.kind == "ligand_contact_comparison"
        assert item.open().native_payload == native
        assert item.open().back() is question
        assert item.explain().native_payload == card.explain_ligand_site(
            native["relationship_id"]
        )
        assert item.explain().back() is question
        refs = item.support[0]["source_assertions"]
        assert set(expected["canonical_reference"]["inputs"]) <= {
            row["id"] for row in refs
        }
        for ref in refs:
            if ref["state"] == "present":
                value, _ = explorer.access._resolve(ref["location"])
                assert value == card.source_assertion_store.get(ref["id"])
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "kwargs,status,word",
    [
        ({}, "computed", "Overlap"),
        ({"position": 8}, "computed", "No overlap among retained"),
        ({"molecule": "P52270-2"}, "not_computed", "not computed"),
        ({"modifier": "LESS_THAN"}, "not_computed", "not computed"),
        ({"annotation": False}, "not_computed", "No annotated sites retained"),
    ],
)
def test_readable_outcomes_distinguish_absence_unknown_and_exact_comparisons(
    kwargs, status, word
):
    view = protein(**kwargs).explore().answer(TOPIC)
    item = view.items()[0]
    assert item.cells["comparison_status"].value == status
    assert word in item.cells["outcome"].value
    assert "Unknown comparison is not a negative" in repr(view)
    assert "sequence revision agreement are not established" in view._repr_html_()
    assert "Explicit synthetic ligand" in repr(view)


def test_partial_positive_and_original_annotation_navigation_have_exact_back_context():
    card = protein()
    node = card.get("features_positional.active_site")
    extra = deepcopy(node["value"][0])
    extra["description"] = "Explicit unsupported annotation"
    extra["location"]["sequence"]["sequence_id"] = None
    node["value"].append(extra)
    explorer = card.explore()
    view = explorer.view(TOPIC).filter("comparison_status", equals="partial")
    item = view.items()[0]
    assert "other annotations were not compared" in item.cells["outcome"].value
    links = item.related()
    assert links.back() is view
    annotations = links.filter("role", equals="annotation")
    assert len(annotations.items()) == 2
    values = [a.open().native_payload for a in annotations.items()]
    assert extra in values
    assert node["value"][0] in values
    contact = links.filter("role", equals="contact").items()[0]
    assert contact.open().native_payload == card.relationships("has_ligand_site")[0]
    assert contact.open().back() is contact.back()


def test_one_scientific_evaluation_and_detached_captured_mutation_isolation(
    monkeypatch,
):
    import sabueso.core.ligand_explanation as explanation
    import sabueso.core.ligand_sites as native

    card = protein()
    explorer = card.explore()
    card.get("sequence.primary")["value"] = "M"
    original = native.ligand_sites_view
    calls = []

    def count(*a, **k):
        calls.append(1)
        return original(*a, **k)

    monkeypatch.setattr(native, "ligand_sites_view", count)
    monkeypatch.setattr(explanation, "ligand_sites_view", forbidden)
    first = explorer.answer(TOPIC)
    assert first.items()[0].cells["comparison_status"].value == "computed"
    assert len(calls) == 1
    monkeypatch.setattr(native, "ligand_sites_view", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for view in [explorer.view(TOPIC), explorer.answer(TOPIC)]:
        item = view.items()[0]
        item.open()
        item.explain()
        item.related()
        view.table()
        view.rows()
    assert len(calls) == 1
    changed = first.native_payload
    changed["items"].clear()
    assert first.native_payload["items"]


def test_bounded_literal_agent_read_can_reach_original_explanation_and_support():
    explorer = protein().explore()
    item = explorer.view(TOPIC).items()[0]
    page = explorer.access.read(item.payload_location).page(limit=2, max_bytes=4096)
    assert len(canonical_json(page).encode("utf-8")) <= 4096
    assert page["page"]["total"] > 2 and not page["page"]["complete"]
    support = explorer.access.read(item._entry.value["support_location"]).page(
        max_bytes=65536
    )
    assert support["page"]["total"] > 0
    assert not explorer.access.catalog().capabilities["scientific_adapter"]
    assert explorer.access.select(TOPIC).count == 1


def test_missing_source_is_a_visible_input_gap_instead_of_a_false_negative():
    card = protein()
    card.get("features_positional.active_site")["source_assertion_ids"].append(
        "SA_EXPLICIT_MISSING"
    )
    item = card.explore().view(TOPIC).items()[0]
    assert item.cells["comparison_status"].value == "not_computed"
    assert any(
        row["id"] == "SA_EXPLICIT_MISSING" and row["state"] != "present"
        for row in item.support[0]["source_assertions"]
    )
    gap = (
        item.related().filter("availability", equals="missing_prerequisite").items()[0]
    )
    assert gap.open().outcome["status"] == "missing_prerequisite"


@pytest.mark.parametrize("nature", ["small_molecule", "disease", "unknown"])
def test_other_natures_do_not_run_a_protein_comparison(nature, monkeypatch):
    import sabueso.core.ligand_sites as native

    monkeypatch.setattr(native, "ligand_sites_view", forbidden)
    explorer = Card(meta={"entity_type": nature}).explore()
    assert explorer.view(TOPIC).outcome["status"] == "not_applicable"
    assert not explorer.view(TOPIC).items()


@pytest.mark.parametrize("operation", ["view", "answer"])
def test_unknown_options_are_rejected_even_with_digestion_skipped(operation):
    with pytest.raises(ArgumentError):
        getattr(protein().explore(), operation)(
            TOPIC, options={"guess_axis": True}, skip_digestion=True
        )


def test_new_science_and_its_origin_are_not_saved_as_unverified_literal_data(tmp_path):
    explorer = protein().explore()
    view = explorer.view(TOPIC)
    for candidate in [
        view,
        view.items()[0].open(),
        view.items()[0].explain(),
        view.items()[0].related(),
    ]:
        assert not candidate.capabilities["save"]
        with pytest.raises(StorageError):
            candidate.save(tmp_path / "not-created.json")
        assert not (tmp_path / "not-created.json").exists()
    assert not explorer.access.read(view.items()[0].payload_location).capabilities[
        "save"
    ]
    source_view = explorer.view("sources")
    receipt = source_view.save(tmp_path / "original-sources.json")
    loaded = sabueso.read_exploration(
        tmp_path / "original-sources.json", expected_digest=receipt["bundle_digest"]
    )
    assert loaded.explorer.view(TOPIC).outcome["status"] == "not_saved"
    assert loaded.explorer.answer(TOPIC).outcome["status"] == "not_saved"


@pytest.mark.parametrize(
    "subject,component,count",
    [("P52270", "ATP", 2), ("P60174", "ATP", 0), ("P52270", "ADP", 0)],
)
@pytest.mark.parametrize("conflict", [False, True])
def test_structure_context_keeps_duplicate_instance_records_and_explicit_component_scope(
    subject, component, count, conflict
):
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    card = protein()
    instance = {
        "asym_id": "SAME_LABEL",
        "chains": ["A"],
        "contacts": [
            {
                "uniprot": "P52270",
                "position": 2,
                "min_distance": {"value": 2.5, "unit": "angstrom"},
            }
        ],
    }
    q = {
        "assemblies": [{"id": "1", "oligomeric_state": "dimeric"}],
        "ligands": [
            {
                "comp_id": component,
                "name": "ATP",
                "instances": [deepcopy(instance), deepcopy(instance)],
            }
        ],
    }
    assertion = make_source_assertion(
        "relationships.has_structure",
        {"explicit_synthetic": deepcopy(q)},
        "RCSB PDB",
        "1ABC",
        "synthetic",
        subject_ref="uniprot:" + subject,
    )
    card.source_assertion_store.add(assertion)
    card.relationship_store.add(
        make_relationship(
            "uniprot:" + subject, "has_structure", "pdb:1ABC", q, [assertion["id"]]
        )
    )
    if conflict:
        card.relationships("has_structure")[0]["qualifier_conflicts"] = {
            "ligands": [{"explicit_synthetic": "unresolved original alternative"}]
        }
    item = card.explore().view(TOPIC).items()[0]
    links = item.related()
    instances = links.filter("role", equals="instance_context")
    assert len(instances.items()) == count
    assert len(links.filter("role", equals="assembly_context").items()) == (
        1 if count else 0
    )
    if count:
        a, b = instances.items()
        assert a.item_ref != b.item_ref
        assert a.open().native_payload == instance == b.open().native_payload
        assert a.open().native_payload["contacts"][0]["min_distance"] == {
            "value": 2.5,
            "unit": "angstrom",
        }
        assert (
            "no aggregate-to-instance correspondence"
            in a._entry.value["component_scope"]["basis"]
        )
        assert ("conflicting qualifiers" in a.label) == conflict
        assert (
            bool(a._entry.value["component_scope"]["qualifier_conflicts"]) == conflict
        )
        assert a.open().back() is instances
        assert {row._entry.value["rule"] for row in links.items()} == {
            "ligand_site_context_links@1"
        }


def test_missing_identity_and_empty_retained_contacts_remain_distinct():
    anonymous = Card(meta={"entity_type": "protein"}).explore().view(TOPIC)
    assert anonymous.outcome["status"] == "missing_prerequisite"
    card = protein()
    card.relationship_store.store.clear()
    empty = card.explore().view(TOPIC)
    assert empty.outcome["status"] == "empty"
    assert "No ligand contact declarations are retained" in empty.outcome["reason"]
    assert empty.native_payload["annotated_sites"]


def test_current_public_fixture_mapping_has_positive_and_negative_supported_comparisons():
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
    from sabueso.tools.db.interpro import FixtureInterProClient
    from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

    card, _ = sabueso.resolve_protein_card(
        "P52270",
        EntityResolver(
            FixtureUniProtClient("temp_data"),
            rcsb_client=FixtureRCSBClient("temp_data"),
        ),
        structures=["1SUX"],
        ligand_sites=True,
        family_sites=True,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    view = card.explore().answer(TOPIC)
    assert len(view.items()) == 6
    assert {item.cells["comparison_status"].value for item in view.items()} == {
        "computed"
    }
    assert {item["site_class"] for item in view.native_payload["items"]} == {
        "overlaps_annotated_site",
        "no_annotated_overlap",
    }
    assert "Partly compared" not in repr(view)
    assert "Family-model site" in repr(view)
    assert view.native_payload == card.ligand_sites()


def test_numeric_component_is_not_identified_with_an_equal_textual_identifier():
    from sabueso.core.relationship_store import make_relationship
    from sabueso.core.source_assertion_store import make_source_assertion

    card = protein(ligand_code="1")
    q = {
        "ligands": [
            {
                "comp_id": "1",
                "instances": [
                    {"asym_id": "EXACT_STRING", "chains": [], "contacts": []}
                ],
            },
            {
                "comp_id": 1,
                "instances": [{"asym_id": "WRONG_TYPE", "chains": [], "contacts": []}],
            },
        ]
    }
    source = make_source_assertion(
        "relationships.has_structure",
        {"explicit_synthetic": deepcopy(q)},
        "RCSB PDB",
        "1ABC",
        "synthetic",
        subject_ref="uniprot:P52270",
    )
    card.source_assertion_store.add(source)
    card.relationship_store.add(
        make_relationship(
            "uniprot:P52270", "has_structure", "pdb:1ABC", q, [source["id"]]
        )
    )
    view = card.explore().view(TOPIC)
    assert len(view.native_payload["items"][0]["instances"]) == 1
    contexts = view.items()[0].related().filter("role", equals="instance_context")
    assert len(contexts.items()) == 1
    assert contexts.items()[0].open().native_payload["asym_id"] == "EXACT_STRING"
