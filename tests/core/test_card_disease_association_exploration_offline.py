"""Disease association scope over public sources and labelled synthetic controls."""

import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.snapshot import canonical_json
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.clinicaltrials import FixtureClinicalTrialsClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient

DATA = Path(__file__).resolve().parents[2] / "temp_data"
if not (DATA / "mondo/mondo.obo").is_file():
    DATA = Path.cwd() / "temp_data"
TOPIC = "associations"


def forbidden(*args, **kwargs):
    pytest.fail(
        "Captured disease exploration cannot query sources or build association decks"
    )


@pytest.fixture(scope="module")
def originals():
    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(socket, "create_connection", forbidden)
        guard.setattr(socket.socket, "connect", forbidden)
        mondo = FixtureMONDOClient(DATA)
        disease = resolve_disease_card("MONDO:0014221", mondo_client=mondo)[0]
        chagas = resolve_disease_card("MONDO:0001444", mondo_client=mondo)[0]
        protein = Card.from_dict(
            json.loads((DATA / "frozen_cards/schema_0.3.10__P60174.json").read_text())
        )
        molecule = sabueso.resolve(
            "chembl:CHEMBL110",
            indications=True,
            chembl_client=FixtureChEMBLClient(DATA),
            clinicaltrials_client=FixtureClinicalTrialsClient(DATA),
            ccd_client=FixtureCCDClient(DATA),
            unichem_client=FixtureUniChemClient(DATA),
        )[0]
    return {
        key: value.to_dict()
        for key, value in (
            ("disease", disease),
            ("chagas", chagas),
            ("protein", protein),
            ("molecule", molecule),
        )
    }


@pytest.fixture(autouse=True)
def no_acquisition(originals, monkeypatch):
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    for client in (
        FixtureMONDOClient,
        FixtureChEMBLClient,
        FixtureClinicalTrialsClient,
        FixtureCCDClient,
        FixtureUniChemClient,
    ):
        monkeypatch.setattr(client, "__init__", forbidden)
    for name in ("resolve", "disease_targets", "disease_drugs", "refresh_card"):
        monkeypatch.setattr(sabueso, name, forbidden)
    monkeypatch.setattr(Card, "diseases", forbidden)


def card(originals, name):
    return Card.from_dict(deepcopy(originals[name]))


def explore(originals, *, disease="disease", context="protein"):
    return card(originals, disease).explore(related_cards=[card(originals, context)])


def statements(view):
    return [i for i in view.items() if i.kind != "association_context"]


def frames(selection, *, limit=4, max_bytes=65536):
    cursor, items = None, []
    while True:
        page = selection.page(limit=limit, max_bytes=max_bytes, cursor=cursor)
        assert len(canonical_json(page).encode()) <= max_bytes
        assert page["page"]["blocked"] is None
        items.extend(page["items"])
        cursor = page["page"]["next_cursor"]
        if cursor is None:
            return items


def add_statement(
    protein,
    ref,
    *,
    subject=None,
    source="Synthetic association",
    channel=None,
    missing=False,
):
    subject = subject or protein.id.split(":", 2)[2]
    value = {"disease_ref": ref, "score": 0.25, "note": "Explicit synthetic control"}
    record = make_source_assertion(
        "relationships.associated_with",
        value,
        source,
        "synthetic-control",
        "synthetic fixture",
        subject_ref=subject,
    )
    if not missing:
        protein.source_assertion_store.add(record)
    rel = make_relationship(
        subject,
        "associated_with",
        ref,
        qualifiers={"source": source, "channel": channel},
        source_assertion_ids=[record["id"]],
    )
    protein.relationship_store.add(rel)
    return rel, record


def test_public_human_agent_native_and_original_input_parity(originals):
    from sabueso.core.diseases import _card_statements

    disease, protein = card(originals, "disease"), card(originals, "protein")
    before = [c.to_dict() for c in (disease, protein)]
    native = _card_statements(protein)
    explorer = disease.explore(related_cards=[protein])
    human = explorer.answer("retained_associations")
    machine = explorer.access.select(TOPIC)
    assert human.result_ref == explorer.view(TOPIC).result_ref == machine.result_ref
    assert human.request == {
        "question": "retained_associations",
        "topic": TOPIC,
        "options": {},
    }
    assert len(statements(human)) > 0
    context = next(
        c for c in human.native_payload["contexts"] if c["nature"] == "protein"
    )
    assert context["native_payload"] == native
    assert {i.cells["source"].value for i in statements(human)} >= {
        "UniProt",
        "DISEASES",
        "Open Targets",
        "Orphanet",
        "ClinVar",
    }
    assert [row["item_ref"] for row in frames(machine)] == [
        i.item_ref for i in human.items()
    ]
    assert [c.to_dict() for c in (disease, protein)] == before
    assert TOPIC in explorer.capabilities["scientific_topics"]
    assert TOPIC in explorer.access.capabilities["scientific_topics"]
    assert "retained_associations" in explorer.questions().native_payload
    assert explorer.access.catalog()._entries


def test_molecule_indications_keep_native_scope_without_shared_heading_join(originals):
    molecule = card(originals, "molecule")
    native = molecule.clinical()
    explorer = card(originals, "chagas").explore(related_cards=[molecule])
    view = explorer.answer("retained_associations")
    rows = statements(view)
    assert rows and all(row.kind == "indication_statement" for row in rows)
    assert all(row.cells["object_ref"].value == "mondo:MONDO:0001444" for row in rows)
    assert any(
        e["original_item"]["object_ref"] == "efo:EFO:0008559"
        for e in view.native_payload["exclusions"]
    )
    assert (
        next(
            c
            for c in view.native_payload["contexts"]
            if c["nature"] == "small_molecule"
        )["native_payload"]
        == native
    )


def test_source_destinations_and_back_preserve_exact_selected_question(originals):
    view = (
        explore(originals)
        .answer("retained_associations")
        .filter("source", equals="UniProt")
    )
    row = statements(view)[0]
    assert row.open().back() is view
    assert row.explain().back() is view
    links = row.related()
    assert links.back() is view and links.request == view.request
    roles = set()
    for link in links.items():
        roles.add(link._entry.value["role"])
        opened = link.open()
        assert opened.back() is links and opened.request == view.request
        candidate = link._entry.value["candidates"][0]
        assert opened.explorer.access._focal_key == candidate["capture"]
        assert opened.explorer.overview().back() is links
        assert (
            opened.native_payload
            == opened.explorer.access._resolve(candidate["location"])[0]
        )
    assert roles >= {
        "source",
        "original_location",
        "whole_card_context",
        "source_request_context",
    }
    assert all(r["state"] == "present" for r in row.support[0]["source_assertions"])


@pytest.mark.parametrize(
    "ref,reason",
    [
        ("mondo:MONDO:0002908", "not_matched"),
        ("GARD:0005287", "not_matched"),
        ("synthetic:triosephosphate isomerase deficiency", "not_matched"),
    ],
)
def test_names_related_ids_and_parent_terms_never_create_identity(
    originals, ref, reason
):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    rel, _ = add_statement(protein, ref)
    view = disease.explore(related_cards=[protein]).view(TOPIC)
    assert not statements(view)
    assert any(
        e["original_item"]["id"] == rel["id"] and e["reason"] == reason
        for e in view.native_payload["exclusions"]
    )


@pytest.mark.parametrize(
    "defect",
    (
        "missing_equivalence",
        "misbound_equivalence",
        "conflicting_mapping",
        "foreign_subject",
    ),
)
def test_unverified_conflicting_and_foreign_identity_stays_explicit(originals, defect):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    rel, _ = add_statement(
        protein,
        "omim:615512",
        subject="uniprot:FOREIGN" if defect == "foreign_subject" else None,
    )
    data = disease.to_dict()
    field = data["sections"]["identifiers"]["equivalent_ids"]
    if defect == "missing_equivalence":
        data["source_assertion_store"] = [
            r
            for r in data["source_assertion_store"]
            if r["id"] not in field["source_assertion_ids"]
        ]
    elif defect == "misbound_equivalence":
        for r in data["source_assertion_store"]:
            if r["id"] in field["source_assertion_ids"]:
                r["subject_ref"] = "mondo:MONDO:FOREIGN"
    elif defect == "conflicting_mapping":
        from sabueso.mappings.mondo import map_equivalences

        mapped = map_equivalences(
            {
                "OMIM:615512": {
                    "mondo": "MONDO:OTHER",
                    "version": "synthetic",
                    "retrieved_at": "synthetic fixture",
                }
            },
            "SYNTHETIC",
        )
        for r in mapped["source_assertions"]:
            protein.source_assertion_store.add(r)
        for r in mapped["relationships"]:
            protein.relationship_store.add(r)
    view = Card.from_dict(data).explore(related_cards=[protein]).view(TOPIC)
    assert not statements(view)
    excluded = next(
        e
        for e in view.native_payload["exclusions"]
        if e["original_item"]["id"] == rel["id"]
    )
    assert excluded["reason"] == (
        "foreign_or_unverified_subject"
        if defect == "foreign_subject"
        else "conflicting_identity"
        if defect == "conflicting_mapping"
        else "not_matched"
    )


@pytest.mark.parametrize(
    "defect", ("missing", "wrong_subject", "wrong_field", "qualifier_conflict")
)
def test_association_source_membership_is_not_promoted_when_unverified(
    originals, defect
):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    rel, source = add_statement(
        protein, "mondo:MONDO:0014221", missing=defect == "missing"
    )
    data = protein.to_dict()
    if defect in ("wrong_subject", "wrong_field"):
        record = next(
            r for r in data["source_assertion_store"] if r["id"] == source["id"]
        )
        record["subject_ref" if defect == "wrong_subject" else "field_path"] = (
            "synthetic:foreign"
        )
    elif defect == "qualifier_conflict":
        next(r for r in data["relationship_store"] if r["id"] == rel["id"])[
            "qualifier_conflicts"
        ] = {"score": [0.25, 0.75]}
    row = statements(disease.explore(related_cards=[Card.from_dict(data)]).view(TOPIC))[
        0
    ]
    assert row.cells["support_state"].value == "partial"
    assert row.open().native_payload["id"] == rel["id"]
    assert row.support[0]["basis"] == "support_membership_unverified"


def test_ontology_only_scope_is_missing_context_not_global_absence(originals):
    explorer = card(originals, "disease").explore()
    view = explorer.view(TOPIC)
    assert view.outcome["status"] == "missing_prerequisite"
    assert not statements(view) and view.items()[0].kind == "association_context"
    assert view.coverage["contexts"][0]["knowledge_state"]


def test_equal_occurrences_and_distinct_input_revisions_are_not_merged(originals):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    rel, _ = add_statement(protein, "mondo:MONDO:0014221")
    later = protein.to_dict()
    later["quality"]["synthetic_revision"] = "second explicit synthetic input"
    revision = Card.from_dict(later)
    view = disease.explore(related_cards=[protein, protein, revision]).view(TOPIC)
    rows = statements(view)
    assert len(rows) == 2
    assert len({i.item_ref for i in rows}) == 2
    assert len({i.cells["context_card_ref"].value for i in rows}) == 2
    assert all(i.open().native_payload == rel for i in rows)
    assert len(view.native_payload["input_occurrences"]) == 4
    assert (
        view.native_payload["input_occurrences"][1]
        == view.native_payload["input_occurrences"][2]
    )
    assert len(view.native_payload["contexts"]) == 3


@pytest.mark.parametrize("direction", ("outgoing", "incoming"))
def test_focal_relationship_endpoints_are_separate_entities(originals, direction):
    disease, other = card(originals, "disease"), card(originals, "chagas")
    focal, peer = "mondo:MONDO:0014221", "mondo:MONDO:0001444"
    subject, obj = (focal, peer) if direction == "outgoing" else (peer, focal)
    source = make_source_assertion(
        "relationships.associated_with",
        {"subject": subject, "object": obj},
        "Synthetic association",
        "two-disease-control",
        "synthetic fixture",
        subject_ref=subject,
    )
    disease.source_assertion_store.add(source)
    rel = make_relationship(
        subject,
        "associated_with",
        obj,
        qualifiers={"source": "Synthetic association"},
        source_assertion_ids=[source["id"]],
    )
    disease.relationship_store.add(rel)
    view = disease.explore(related_cards=[other]).view(TOPIC)
    (row,) = statements(view)
    assert (
        row.cells["subject_ref"].value == subject
        and row.cells["object_ref"].value == obj
    )
    assert row.open().native_payload == rel
    assert row.support[0]["identity"]["matching_endpoints"] == (
        [0] if direction == "outgoing" else [1]
    )


def test_equal_variant_conditions_keep_their_original_occurrence_locations(originals):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    condition = {
        "name": "Explicit synthetic repeated condition",
        "xrefs": ["OMIM:615512"],
    }
    variant = {
        "accession": "synthetic-variant",
        "conditions": [condition, deepcopy(condition)],
    }
    source = make_source_assertion(
        "annotations.clinical_variants",
        variant,
        "ClinVar",
        "synthetic-variant",
        "synthetic fixture",
        subject_ref="uniprot:SYNTHETIC",
    )
    protein.source_assertion_store.add(source)
    protein.sections.setdefault("annotations", {})["clinical_variants"] = {
        "value": [variant],
        "source_assertion_ids": [source["id"]],
    }
    view = disease.explore(related_cards=[protein]).view(TOPIC)
    rows = statements(view)
    assert len(rows) == 2 and len({row.item_ref for row in rows}) == 2
    assert [
        row.support[0]["original_location"]["segments"][-1]["value"] for row in rows
    ] == [0, 1]
    assert all(row.open().native_payload == condition for row in rows)
    assert all(row.support[0]["state"] == "retained" for row in rows)


@pytest.mark.parametrize(
    "state", ("complete", "missing", "misbound", "conflicting", "unfinished")
)
def test_medgen_uses_only_the_supported_concept_uid_mondo_contract(originals, state):
    from sabueso.mappings.medgen import map_concepts
    from sabueso.mappings.mondo import map_equivalences

    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    add_statement(protein, "medgen:C1860808")
    mapping = map_concepts({"C1860808": "349893"}, "synthetic fixture", "synthetic")
    for row in mapping["source_assertions"]:
        if state == "misbound":
            row["asserted_value"]["uid"] = "999"
        if state != "missing":
            protein.source_assertion_store.add(row)
    for row in mapping["relationships"]:
        protein.relationship_store.add(row)
    if state in ("conflicting", "unfinished"):
        extra = map_concepts({"C1860808": "999"}, "synthetic fixture", "synthetic")
        if state == "conflicting":
            terminal = map_equivalences(
                {
                    "MEDGEN:999": {
                        "mondo": "MONDO:OTHER",
                        "version": "synthetic",
                        "retrieved_at": "synthetic fixture",
                    }
                },
                "SYNTHETIC",
            )
            for key in ("source_assertions", "relationships"):
                extra[key].extend(terminal[key])
        for row in extra["source_assertions"]:
            protein.source_assertion_store.add(row)
        for row in extra["relationships"]:
            protein.relationship_store.add(row)
    view = disease.explore(related_cards=[protein]).view(TOPIC)
    if state == "complete":
        (row,) = statements(view)
        assert row.cells["identity_basis"].value == "medgen_mondo_equivalence"
        assert {r["role"] for r in row.support[0]["source_assertions"]} >= {
            "association_statement",
            "medgen_identity",
            "disease_equivalence",
        }
        assert row.support[0]["state"] == "retained"
    else:
        assert not statements(view)
        assert any(
            e["reason"]
            == (
                "conflicting_identity"
                if state == "conflicting"
                else "incomplete_identity"
            )
            for e in view.native_payload["exclusions"]
        )


@pytest.mark.parametrize(
    "shape", (False, {"value": "MONDO:OTHER", "source_assertion_ids": []})
)
def test_incoherent_primary_disease_field_is_explicitly_unavailable(originals, shape):
    disease = card(originals, "disease").to_dict()
    disease["sections"]["identifiers"]["mondo"] = shape
    view = (
        Card.from_dict(disease)
        .explore(related_cards=[card(originals, "protein")])
        .view(TOPIC)
    )
    assert view.outcome["status"] == "missing_prerequisite"
    assert not statements(view) and view.native_payload["identity"]["coherent"] is False


def test_unrecognized_source_channel_shape_preserves_original_value(originals):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    rel, _ = add_statement(protein, "mondo:MONDO:0014221", channel=False)
    (row,) = statements(disease.explore(related_cards=[protein]).view(TOPIC))
    assert row.cells["channel"].value is None
    assert row.cells["channel"].state == "unrecognized_shape"
    assert row.open().native_payload == rel
    assert row.open().native_payload["qualifiers"]["channel"] is False


@pytest.mark.parametrize("placeholder", ("MEDGEN:C3661900", "MEDGEN:CN169374"))
def test_unspecified_conditions_never_become_positive_disease_associations(
    originals, placeholder
):
    disease = card(originals, "disease").to_dict()
    value = disease["sections"]["identifiers"]["equivalent_ids"]
    value["value"].append(placeholder)
    for source in disease["source_assertion_store"]:
        if source["id"] in value["source_assertion_ids"]:
            source["asserted_value"] = deepcopy(value["value"])
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    add_statement(protein, placeholder)
    view = Card.from_dict(disease).explore(related_cards=[protein]).view(TOPIC)
    assert not statements(view)
    assert any(
        e["reason"] == "condition_not_provided"
        for e in view.native_payload["exclusions"]
    )


def test_display_filter_keeps_original_partial_support_state(originals):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    add_statement(protein, "mondo:MONDO:0014221", missing=True)
    original = disease.explore(related_cards=[protein]).view(TOPIC)
    selected = original.filter("kind", equals="association_statement")
    assert original.outcome["status"] == selected.outcome["status"] == "partial"
    assert len(selected.items()) == 1 and selected.back() is original


@pytest.mark.parametrize("nature", ("protein", "small_molecule", "generic"))
def test_other_card_profiles_refuse_disease_association_materialization(nature):
    from sabueso.core.card_disease_association_access import materialize

    access = Card(meta={"entity_type": nature}).access()
    with pytest.raises(ArgumentError):
        materialize(access)
    if nature == "protein":
        selected = access.select(TOPIC)
        assert (
            selected._scientific.wire["context"]["adapter"]
            == "protein_context_exploration@1"
        )
        assert selected.count == 0
    else:
        with pytest.raises(ArgumentError):
            access.select(TOPIC)


def test_typed_projection_membership_order_and_foreign_session_refusal(originals):
    explorer = explore(originals)
    all_rows = explorer.access.select(TOPIC)
    one = frames(all_rows)[0]["item_ref"]
    selected = explorer.access.select(
        TOPIC,
        fields=["source", "predicate"],
        item_refs=[one],
        order_by={"column": "source", "descending": True},
    )
    rows = frames(selected)
    assert len(rows) == 1 and set(rows[0]["cells"]) == {"source", "predicate"}
    assert rows[0]["interpretation"]["rule"] == "disease_association_context@1"
    assert selected.selection_ref != all_rows.selection_ref
    other = card(originals, "disease").access()
    with pytest.raises(ArgumentError):
        other.select(TOPIC, item_refs=[one])
    with pytest.raises(ArgumentError):
        all_rows.page(cursor="foreign")
    assert not explorer.access.select(TOPIC, where={"source": "synthetic absent"}).count


@pytest.mark.parametrize(
    "options",
    [
        {"where": {"source": 1}},
        {"where": {"source": False}},
        {"where": {"unknown": "x"}},
        {"fields": ["source", "source"]},
        {"options": {"fetch": True}},
        {"order_by": {"column": "source", "unit": "nm"}},
    ],
)
def test_invalid_scientific_selection_refuses_before_materialization(
    originals, monkeypatch, options
):
    from sabueso.core import card_disease_association_access

    monkeypatch.setattr(card_disease_association_access, "materialize", forbidden)
    with pytest.raises(ArgumentError):
        explore(originals).access.select(TOPIC, **options)


def test_complete_raw_values_and_source_roles_are_deferred_together(originals):
    explorer = explore(originals)
    selected = explorer.access.select(TOPIC)
    rows = frames(selected, limit=1, max_bytes=7000)
    assert any(not row["value_included"] for row in rows)
    for row in rows:
        if not row["value_included"]:
            assert "interpretation" not in row
            native = explorer.inspect(locator=row["value_location"]).native_payload
            assert native["interpretation"]["rule"] == "disease_association_context@1"


def test_public_view_machine_and_detail_saving_use_production_limits(
    originals, tmp_path
):
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    add_statement(protein, "mondo:MONDO:0014221", missing=True)
    explorer = card(originals, "disease").explore(related_cards=[protein])
    view = explorer.view(TOPIC)
    selection = explorer.access.select(TOPIC)
    for name, item in (
        ("view", view),
        ("machine", selection),
        ("detail", view.items()[0].open()),
    ):
        assert item.capabilities["save"]
        path = tmp_path / (name + ".json")
        item.save(path)
        saved = sabueso.read_exploration(path)
        assert (
            saved.validation["verifier"] == "disease_association_exploration_binding@1"
        )
        assert saved.native_payload == (
            item._scientific.native if name == "machine" else item.native_payload
        )


def test_bounded_escaped_display_preserves_full_original_values(originals):
    disease = card(originals, "disease")
    protein = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:uniprot:SYNTHETIC"}
    )
    add_statement(
        protein, "mondo:MONDO:0014221", source="<script>synthetic</script>" + "x" * 1000
    )
    view = disease.explore(related_cards=[protein]).answer("retained_associations")
    assert "<script>" not in view._repr_html_()
    assert "&lt;script&gt;" in view._repr_html_()
    assert "not establish mechanism" in repr(view)
    assert len(repr(view)) < 15000
    assert len(statements(view)[0].cells["source"].value) > 1000
