"""Public and explicitly synthetic admission of quaternary interpretation (#165)."""

import gzip
import hashlib
import json
import socket
from copy import deepcopy
from pathlib import Path

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.oligomer import AGREEMENT_RULE, PARTNER_RULE
from sabueso.core.packets import (
    KnowledgeQuery,
    _facts,
    _index,
    compose_packet,
    full_rules,
)
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

SUBJECT = "uniprot:P52270"
FAMILY = "features_positional.family_site"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("No online acquisition")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def assertion(
    card, path, value, *, subject=SUBJECT, source="synthetic", record="SYNTHETIC"
):
    row = make_source_assertion(
        path, deepcopy(value), source, record, "synthetic", subject_ref=subject
    )
    if source == "UniProt":
        row["source_metadata"] = {"sequence_version": 7}
    card.source_assertion_store.add(row)
    return row["id"]


def field(card, path, value, source="UniProt"):
    refs = (
        [assertion(card, path, v, source=source, record="P52270") for v in value]
        if isinstance(value, list)
        else [assertion(card, path, value, source=source, record="P52270")]
    )
    card.set(path, value, refs)


def relation(card, predicate, obj, q, *, subject=SUBJECT, suffix=""):
    ref = assertion(
        card,
        "relationships." + predicate,
        {"object_ref": obj, "qualifiers": q},
        subject=subject,
    )
    row = make_relationship(subject, predicate, obj, deepcopy(q), [ref])
    if suffix:
        row["id"] += "_" + suffix
    card.relationship_store.add(row)
    return card.relationship_store.get(row["id"])


def sample(*, partner=SUBJECT, coverage=1.0, modifier=None, numbering="uniprot"):
    card = Card(
        meta={"entity_type": "protein", "card_id": "sabueso:protein:" + SUBJECT}
    )
    for path, value in [
        ("identifiers.uniprot", "P52270"),
        ("sequence.primary", "M" * 100),
        ("sequence.length", 100),
        ("annotations.subunit", ["Explicit synthetic homodimer"]),
    ]:
        field(card, path, value)
    span = {"start": 12, "end": 14}
    if modifier is not None:
        span["start_modifier"] = modifier
    value = {
        "description": "Synthetic dimer interface",
        "location": {
            "kind": "sequence",
            "sequence": {
                "sequence_id": "UniProt:P52270",
                "indexing": "1-based",
                "fragments": [span],
            },
        },
    }
    field(card, FAMILY, [value], "InterPro")
    q = {"chimeric_with": [], "assemblies": []}
    if coverage is not None:
        q["coverage"] = coverage
    relation(card, "has_structure", "pdb:SYNTHETIC", q)
    relation(
        card,
        "has_interface_with",
        partner,
        {
            "numbering": numbering,
            "structures": ["pdb:SYNTHETIC"],
            "residues": [{"start": 13, "end": 15}],
        },
    )
    return card


def test_positive_canonical_scope_explanation_and_complete_inputs_are_shared():
    card = sample()
    before = deepcopy(card.to_dict())
    view = card.oligomer()
    assert view["interfaces"][0]["class"] == "homomeric"
    assert view["agreement"][0]["both"] == [13, 14]
    assert view["agreement_state"]["status"] == "computed"
    assert (
        view["agreement"][0]["comparison"]["interface_scope"][
            "sequence_revision_agreement"
        ]
        == "not_established"
    )
    explanation = card.explain_oligomer()
    assert explanation["view"] == view
    assert explanation["rule"]["rule"] == "oligomer_explanation@3"
    assert {r["field_path"] for r in explanation["fields"]} >= {
        FAMILY,
        "sequence.primary",
        "sequence.length",
        "identifiers.uniprot",
    }
    assert (
        explanation["agreement"][0]["selection_basis"]
        == "every_focal_self_interface_family_pair"
    )
    assert card.to_dict() == before


@pytest.mark.parametrize("structures", [None, []])
def test_interface_table_keeps_unknown_counts_source_names_and_historical_reading(
    structures,
):
    card = sample(numbering="author")
    original = card.relationships("has_interface_with")[0]
    q = deepcopy(original["qualifiers"])
    q["structures"] = structures
    card.relationship_store.store.pop(original["id"])
    relation(card, "has_interface_with", SUBJECT, q)
    before = deepcopy(card.to_dict())
    native = card.oligomer()["interfaces"][0]
    row = card.table("interfaces")[0]
    assert native["sources"] == ["synthetic"]
    assert row["sources"] == "synthetic"
    assert row["n_positions"] is None
    assert row["structures"] == (None if structures is None else 0)
    assert row["coordinate_status"] == "not_computed"
    assert row["coordinate_reason"] == "interface_numbering_not_comparable"
    assert row["classification_status"] == "computed"
    assert row["classification_reason"] is None
    original = card.table("interfaces", agreement_rule="interface_site_agreement@2")[0]
    assert original["n_positions"] == 3
    assert original["sources"] == "synthetic"
    assert original["coordinate_status"] is None
    assert card.to_dict() == before


def test_ligand_table_keeps_uncomputed_positions_as_unknown_instead_of_zero():
    card = sample()
    relation(
        card,
        "has_ligand_site",
        "pdb.ligand:SYNTHETIC",
        {
            "numbering": "author",
            "residues": [{"start": 13, "end": 15}],
            "structures": [],
        },
    )
    before = deepcopy(card.to_dict())
    native = card.ligand_sites()["items"][0]
    assert native["positions"] is None
    row = card.table("ligand_sites")[0]
    assert row["positions"] is None and row["n_positions"] is None
    assert row["site_class"] == "numbering_not_comparable"
    assert card.to_dict() == before


@pytest.mark.parametrize("accession", ["P52270", "P60174"])
def test_current_public_sources_have_qualified_self_interfaces_and_original_support(
    accession,
):
    from test_oligomer_offline import _card

    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card = _card(resolver, accession)
    original = deepcopy(card.to_dict())
    view = card.oligomer()
    assert view["canonical_reference"]["status"] == "comparable"
    own = next(
        row
        for row in view["interfaces"]
        if row["partner_ref"] == "uniprot:" + accession
    )
    assert own["class"] == "homomeric" and own["positions"]
    assert any(row["comparison"]["status"] == "comparable" for row in view["agreement"])
    if accession == "P52270":
        assert (
            next(
                row
                for row in view["interfaces"]
                if row["partner_ref"] == "uniprot:P04789"
            )["class"]
            == "chimera"
        )
    assert card.explain_oligomer()["view"] == view
    assert card.to_dict() == original


@pytest.mark.parametrize(
    "change",
    [
        "canonical_length",
        "identity_conflict",
        "missing_canonical_source",
        "foreign_annotation_source",
        "missing_annotation_source",
        "different_family_axis",
        "unknown_family_indexing",
    ],
)
def test_reference_or_annotation_gaps_do_not_create_exact_comparisons(change):
    card = sample()
    if change == "canonical_length":
        card.get("sequence.length")["value"] = 101
    elif change == "identity_conflict":
        card.quality["conflicts"] = [{"field": "identifiers.uniprot"}]
    elif change == "missing_canonical_source":
        card.source_assertion_store.store.pop(
            card.get("sequence.primary")["source_assertion_ids"][0]
        )
    elif change == "foreign_annotation_source":
        card.source_assertion_store.store[card.get(FAMILY)["source_assertion_ids"][0]][
            "subject_ref"
        ] = "uniprot:P60174"
    elif change == "missing_annotation_source":
        card.get(FAMILY)["source_assertion_ids"] = []
    else:
        value = deepcopy(card.get(FAMILY)["value"])
        value[0]["location"]["sequence"][
            "sequence_id" if change == "different_family_axis" else "indexing"
        ] = "unsupported"
        field(card, FAMILY, value, "InterPro")
    view = card.oligomer()
    assert view["agreement_state"]["status"] == "not_computed"
    assert all(row["both"] is None for row in view["agreement"])


def test_original_annotation_indices_survive_repeated_descriptions_and_positions():
    card = sample()
    value = deepcopy(card.get(FAMILY)["value"])
    value.append(deepcopy(value[0]))
    field(card, FAMILY, value, "InterPro")
    view = card.oligomer()
    assert [row["family_site_index"] for row in view["agreement"]] == [0, 1]
    assert [
        row["family_site_locator"]["index"]
        for row in card.explain_oligomer()["agreement"]
    ] == [0, 1]


def test_packet_index_keeps_exact_field_scope_instead_of_prefix_lookalikes(tmp_path):
    card = sample()
    extra = (
        "sequence.primary_extra",
        "identifiers.uniprot_notes",
        "features_positional.family_site_notes",
    )
    for path in extra:
        field(card, path, "Explicit unrelated synthetic value")
    index = _index("oligomer", card)
    assert not any(path in index["areas"] for path in extra)
    store = sabueso.KnowledgeStore(tmp_path / "exact-scope.db")
    store.save(card)
    full = compose_packet(KnowledgeQuery("P52270", aspects=["oligomer"]), card)
    reduced = compose_packet(
        KnowledgeQuery("P52270", aspects=["oligomer"], detail="index"), card
    )
    left = full.terms("redistribution", store)["scope"]["subject"]["items"]
    right = reduced.terms("redistribution", store)["scope"]["subject"]["items"]
    assert {row["id"] for row in left} == {row["id"] for row in right}
    assert not any(row.get("path") in extra for row in right)


@pytest.mark.parametrize("coverage", [None, True, -1, 2, "1"])
def test_unknown_invalid_coverage_never_establishes_a_nonfragment_complex(coverage):
    view = sample(partner="uniprot:P60174", coverage=coverage).oligomer()
    assert view["interfaces"][0]["class"] == "undetermined"


def test_foreign_subject_never_becomes_a_focal_homomer():
    card = sample()
    card.relationship_store.store.clear()
    relation(
        card,
        "has_interface_with",
        SUBJECT,
        {
            "numbering": "uniprot",
            "structures": [],
            "residues": [{"start": 13, "end": 15}],
        },
        subject="uniprot:P60174",
    )
    old = card.oligomer(agreement_rule="interface_site_agreement@2")
    assert old["interfaces"][0]["class"] == "homomeric"
    new = card.oligomer()
    assert new["interfaces"][0]["class"] == "undetermined"
    assert (
        new["interfaces"][0]["classification"]["reason"]
        == "declaration_subject_not_focal"
    )
    assert not new["agreement"]


@pytest.mark.parametrize("modifier", ["LESS_THAN", "GREATER_THAN", "UNKNOWN", True])
def test_uncertain_family_endpoints_stay_uncomputed_with_full_original_scope(modifier):
    card = sample(modifier=modifier)
    assert card.oligomer(agreement_rule="interface_site_agreement@2")["agreement"][0][
        "both"
    ] == [13, 14]
    row = card.oligomer()["agreement"][0]
    assert (
        row["both"] is None
        and row["family_only"] is None
        and row["observed_only"] is None
    )
    assert row["comparison"]["status"] == "not_computed"
    assert (
        card.explain_oligomer()["family_interface_sites"][0]["value"]["location"][
            "sequence"
        ]["fragments"][0]["start_modifier"]
        == modifier
    )


def test_all_self_interfaces_and_source_declarations_are_preserved():
    card = sample()
    relation(
        card,
        "has_interface_with",
        SUBJECT,
        {
            "numbering": "uniprot",
            "structures": ["pdb:SYNTHETIC"],
            "residues": [{"start": 50, "end": 51}],
        },
        suffix="SECOND",
    )
    relation(
        card,
        "has_structure",
        "pdb:SYNTHETIC",
        {"coverage": 0.1, "chimeric_with": [], "assemblies": [{"id": "1"}]},
        suffix="SECOND",
    )
    view = card.oligomer()
    assert len(view["assemblies"]) == 2 and len(view["agreement"]) == 2
    assert {tuple(row["both"]) for row in view["agreement"]} == {(13, 14), ()}
    assert len({r["relationship_id"] for r in view["assemblies"]}) == 2
    assert len(card.explain_oligomer()["structures"]) == 2
    assert len(card.explain_oligomer()["agreement"]) == 2


def test_contradictory_declarations_do_not_select_the_last_structure():
    card = sample(partner="uniprot:P60174")
    relation(
        card,
        "has_structure",
        "pdb:SYNTHETIC",
        {"coverage": 0.1, "chimeric_with": [], "assemblies": []},
        suffix="SECOND",
    )
    row = card.oligomer()["interfaces"][0]
    assert row["class"] == "undetermined"
    assert len(row["basis"]["pdb:SYNTHETIC"]) == 2


@pytest.mark.parametrize("partner", [SUBJECT, "uniprot:P60174"])
def test_native_partner_binding_is_required_for_classification_and_coordinates(partner):
    card = sample(partner=partner)
    row = card.relationships("has_interface_with")[0]
    native = {
        "object_ref": partner,
        "partner": {
            "accession": "Q4DV43",
            "residues": [
                {
                    "startIndex": 13,
                    "endIndex": 15,
                    "indexType": "UNIPROT",
                    "interactingPDBEntries": [{"pdbId": "SYNTHETIC"}],
                }
            ],
        },
    }
    ref = assertion(
        card,
        "relationships.has_interface_with",
        native,
        source="PDBe-KB",
        record="P52270",
    )
    row["source_assertion_ids"] = [ref]
    item = card.oligomer()["interfaces"][0]
    assert item["class"] == "undetermined"
    assert item["positions"] is None
    assert item["classification"]["reason"] == item["coordinate_scope"]["reason"]
    assert (
        item["classification"]["reason"]
        == "interface_native_partner_binding_unavailable"
    )


def test_native_interface_structure_binding_cannot_use_unobserved_entries():
    card = sample(partner="uniprot:P60174")
    row = card.relationships("has_interface_with")[0]
    native = {
        "object_ref": "uniprot:P60174",
        "partner": {
            "accession": "P60174",
            "residues": [
                {
                    "startIndex": 13,
                    "endIndex": 15,
                    "indexType": "UNIPROT",
                    "interactingPDBEntries": [{"pdbId": "SYNTHETIC"}],
                }
            ],
        },
    }
    ref = assertion(
        card,
        "relationships.has_interface_with",
        native,
        source="PDBe-KB",
        record="P52270",
    )
    row["source_assertion_ids"] = [ref]
    assert card.oligomer()["interfaces"][0]["class"] == "heteromeric"
    relation(
        card,
        "has_structure",
        "pdb:UNOBSERVED",
        {"coverage": 1.0, "chimeric_with": [], "assemblies": []},
    )
    row["qualifiers"]["structures"] = ["pdb:UNOBSERVED"]
    item = card.oligomer()["interfaces"][0]
    assert item["class"] == "undetermined"
    assert (
        item["classification"]["reason"]
        == "interface_native_structure_references_differ"
    )


@pytest.mark.parametrize(
    "change",
    [
        "numbering",
        "missing_source",
        "foreign_source",
        "source_binding",
        "missing_object_binding",
        "boolean",
        "descending",
        "outside",
        "fuzzy",
        "revision",
        "conflict",
        "unknown_axis",
        "extra_axis",
    ],
)
def test_interface_coordinate_admission_cannot_turn_unknown_input_into_negative(change):
    card = sample()
    original = card.relationships("has_interface_with")[0]
    q = deepcopy(original["qualifiers"])
    if change == "numbering":
        q["numbering"] = "author"
    elif change == "boolean":
        q["residues"][0]["start"] = True
    elif change == "descending":
        q["residues"][0].update(start=15, end=13)
    elif change == "outside":
        q["residues"][0]["end"] = 101
    elif change == "fuzzy":
        q["residues"][0]["start_modifier"] = "LESS_THAN"
    elif change == "revision":
        q["sequence_version"] = 8
    elif change == "unknown_axis":
        q["sequence_ref"] = "uniprot:P60174"
    elif change == "extra_axis":
        q["location"] = {"kind": "sequence"}
    card.relationship_store.store.pop(original["id"])
    row = relation(card, "has_interface_with", SUBJECT, q)
    source = card.source_assertion_store.store[row["source_assertion_ids"][0]]
    if change == "missing_source":
        card.source_assertion_store.store.pop(source["id"])
    elif change == "foreign_source":
        source["subject_ref"] = "uniprot:P60174"
    elif change == "source_binding":
        source["asserted_value"]["qualifiers"]["residues"][0]["start"] = 14
    elif change == "missing_object_binding":
        source["asserted_value"].pop("object_ref")
    elif change == "conflict":
        row["qualifier_conflicts"] = {"residues": [[]]}
    view = card.oligomer()
    assert view["interfaces"][0]["positions"] is None
    assert view["agreement"][0]["both"] is None
    assert view["agreement_state"]["status"] == "not_computed"


def test_mixed_pairs_keep_a_valid_positive_and_explicit_uncomputed_members():
    card = sample()
    relation(
        card,
        "has_interface_with",
        SUBJECT,
        {
            "numbering": "author",
            "structures": [],
            "residues": [{"start": 13, "end": 14}],
        },
        suffix="UNCERTAIN",
    )
    view = card.oligomer()
    assert view["agreement_state"] == {
        "status": "partial",
        "computed_pair_count": 1,
        "pair_count": 2,
        "reasons": [],
    }
    assert any(row["both"] == [13, 14] for row in view["agreement"])
    assert any(row["both"] is None for row in view["agreement"])


def normalize_generated(value):
    if isinstance(value, dict):
        generated = (
            isinstance(value.get("rule"), str)
            and {"inputs", "parameters", "sabueso_version"} <= value.keys()
        )
        return {
            key: normalize_generated(v)
            for key, v in value.items()
            if not (generated and key == "sabueso_version")
        }
    if isinstance(value, list):
        return [normalize_generated(v) for v in value]
    return value


def test_genuine_legacy_producer_and_packet_11_interpretation_are_frozen():
    zipped = (Path(__file__).parent / "data/quaternary_legacy_v2.json.gz").read_bytes()
    assert (
        hashlib.sha256(zipped).hexdigest()
        == "df21b5a94494b6d9d3ea87c0c5abc3dac5a4f714b038ac597afddc83af3b6765"
    )
    raw = gzip.decompress(zipped)
    assert (
        hashlib.sha256(raw).hexdigest()
        == "f8fa5fc70bb601124d43ebc40757303bffd764722ecfddc3d3689c9f8377f9e3"
    )
    capsule = json.loads(raw)
    card = Card.from_dict(capsule["card"])
    for rule, expected in capsule["outputs"].items():
        assert normalize_generated(
            card.oligomer(agreement_rule=rule)
        ) == normalize_generated(expected["view"])
        assert normalize_generated(
            card.explain_oligomer(agreement_rule=rule)
        ) == normalize_generated(expected["explanation"])
    assert (
        _facts("oligomer", card, mapping="packet_aspects@11")["interfaces"]
        == card.oligomer(agreement_rule="interface_site_agreement@2")["interfaces"]
    )
    assert set(full_rules("packet_aspects@11")["oligomer"]) >= {
        "interface_partner_class@1",
        "interface_site_agreement@2",
    }


@pytest.mark.parametrize("detail", ["full", "index"])
def test_packet_12_names_actual_rules_and_all_canonical_support(detail, tmp_path):
    card = sample()
    packet = compose_packet(
        KnowledgeQuery(subject="uniprot:P52270", aspects=["oligomer"], detail=detail),
        card,
    )
    data = packet.to_dict()
    assert data["aspect_mapping"] == "packet_aspects@13"
    assert (
        PARTNER_RULE in full_rules()["oligomer"]
        and AGREEMENT_RULE in full_rules()["oligomer"]
    )
    index = _index("oligomer", card)
    assert all(
        path in index["areas"]
        for path in ("sequence.primary", "sequence.length", "identifiers.uniprot")
    )
    assert (
        "sequence.primary"
        not in _index("oligomer", card, mapping="packet_aspects@11")["areas"]
    )
    store = sabueso.KnowledgeStore(tmp_path / "quaternary.db")
    store.save(card)
    report = packet.terms("redistribution", store)
    ids = {item["id"] for item in report["scope"]["subject"]["items"]}
    assert set(card.oligomer()["canonical_reference"]["inputs"]) <= ids
    pin = store.save_packet(packet, "original_quaternary")
    assert store.load_packet(pin).terms("redistribution", store) == report


@pytest.mark.parametrize("method", ["oligomer", "explain_oligomer"])
def test_unknown_rule_fails_with_and_without_digestion(method):
    for skip in [False, True]:
        with pytest.raises(ArgumentError):
            getattr(sample(), method)(
                agreement_rule="interface_site_agreement@999", skip_digestion=skip
            )
