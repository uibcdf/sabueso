"""Original oligomer support, public systems and clearly synthetic edge cases (#91)."""

from copy import deepcopy

import ackredit
import pytest

import sabueso
from sabueso._private.smonitor.warnings import EnrichmentFailedWarning
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.core.oligomer import AGREEMENT_RULE, LEGACY_AGREEMENT_RULE
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.interpro import FixtureInterProClient
from sabueso.tools.db.pdbe_kb import FixturePDBeKBClient

SUBUNIT = "annotations.subunit"
FAMILY = "features_positional.family_site"


def assertion(card, path, value, source="synthetic", record="synthetic"):
    row = make_source_assertion(path, deepcopy(value), source, record, "2026-01-01")
    row["source"]["version"] = "original-release"
    card.source_assertion_store.add(row)
    return row["id"]


def relationship(card, predicate, obj, qualifiers):
    identifier = assertion(card, f"relationships.{predicate}", qualifiers)
    row = make_relationship("uniprot:P52270", predicate, obj, qualifiers, [identifier])
    card.relationship_store.add(row)
    return card.relationship_store.get(row["id"])


def synthetic(*, partner="uniprot:P52270", structure=True, numbering="uniprot"):
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )
    card.set(
        SUBUNIT,
        ["Synthetic homodimer"],
        [assertion(card, SUBUNIT, "Synthetic homodimer")],
    )
    site = {
        "description": "Synthetic dimer interface",
        "signature": {"accession": "synthetic", "source_database": "synthetic"},
        "location": {
            "sequence": {
                "sequence_id": "UniProt:P52270",
                "indexing": "1-based",
                "fragments": [{"start": 12, "end": 14}],
            }
        },
    }
    card.set(FAMILY, [site], [assertion(card, FAMILY, site)])
    if structure:
        relationship(
            card,
            "has_structure",
            "pdb:1SUX",
            {
                "coverage": 1.0,
                "chimeric_with": [],
                "assemblies": [],
            },
        )
    relationship(
        card,
        "has_interface_with",
        partner,
        {
            "numbering": numbering,
            "structures": ["pdb:1SUX"],
            "residues": [{"start": 13, "end": 15}],
        },
    )
    return card


@pytest.fixture(scope="module", params=["P52270", "P60174"])
def public_card(request):
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    card, _ = sabueso.resolve_protein_card(
        request.param,
        resolver,
        structures="all",
        interfaces=True,
        family_sites=True,
        pdbe_kb_client=FixturePDBeKBClient("temp_data"),
        interpro_client=FixtureInterProClient("temp_data"),
    )
    return card


def test_public_view_rule_parity_and_exact_native_support(public_card):
    before = deepcopy(public_card.to_dict())
    answer = public_card.explain_oligomer()
    assert answer["view"] == public_card.oligomer()
    assert answer["rule"]["rule"] == "oligomer_explanation@2"
    assert answer["card_ref"] == public_card.pinned_ref()
    assert answer["status"] == "on_card" and not answer["gaps"]
    for row in answer["interfaces"]:
        assert row["interface"]["relationship"]["id"] == row["item"]["relationship_id"]
        assert row["interface"]["source_assertions"][0]["source"] == "PDBe-KB"
        assert row["classification_inputs"]["rule"] == "interface_partner_class@1"
        assert row["classification_inputs"]["numbering"] == "uniprot"
    for row in answer["agreement"]:
        assert row["numbering_confirmed"] and row["rule"] == AGREEMENT_RULE
    assert public_card.to_dict() == before


def test_source_assemblies_methods_and_original_versions_survive(public_card):
    answer = public_card.explain_oligomer()
    if public_card.id.endswith("P52270"):
        row = next(
            s
            for s in answer["structures"]
            if s["relationship"]["object_ref"] == "pdb:2V5B"
        )
        assemblies = row["relationship"]["qualifiers"]["assemblies"]
        assert {a["oligomeric_state"] for a in assemblies} == {"Homo 2-mer", "Monomer"}
        assert len({a["defined_by"] for a in assemblies}) == 2
    for row in answer["structures"]:
        assert row["qualifier_lineage"] == "not_recorded"
        for source in row["source_assertions"]:
            original = public_card.source_assertion_store.get(source["id"])
            assert source["version"] == original["source"].get("version")
            assert source["asserted_value"] == original["asserted_value"]
            assert (
                source["source_assertion_ref"] == f"{answer['card_ref']}#{source['id']}"
            )


def test_family_members_and_agreement_locate_actual_stored_inputs(public_card):
    answer = public_card.explain_oligomer()
    for site, agreement in zip(answer["family_interface_sites"], answer["agreement"]):
        assert agreement["family_site_locator"] == site["locator"]
        value = public_card.get(FAMILY)["value"][site["locator"]["index"]]
        assert site["value"] == value
        assert all(a["asserted_value"] == value for a in site["source_assertions"])
        homo = next(
            i for i in answer["interfaces"] if i["item"]["class"] == "homomeric"
        )
        assert (
            agreement["observed_interface_ref"] == homo["interface"]["relationship_ref"]
        )
        assert agreement["item"]["both"] == sorted(
            set(homo["item"]["positions"]) & set(site["item"]["positions"])
        )


@pytest.mark.parametrize(
    "q,expected",
    [
        ({"coverage": 1.0, "chimeric_with": []}, "heteromeric"),
        ({"coverage": 1.0, "chimeric_with": ["OTHER"]}, "chimera"),
        ({"coverage": 0.1, "chimeric_with": []}, "fragment_complex"),
        ({"coverage": 1.0}, "undetermined"),
    ],
)
def test_partner_classification_uses_exact_structural_context(q, expected):
    card = synthetic(partner="uniprot:OTHER")
    card.relationships("has_structure")[0]["qualifiers"] = q
    answer = card.explain_oligomer()
    assert answer["interfaces"][0]["item"]["class"] == expected
    assert answer["structures"][0]["relationship"]["qualifiers"] == q
    assert answer["view"] == card.oligomer()


def test_mixed_chimera_and_fragment_are_not_a_silent_heteromer():
    card = synthetic(partner="uniprot:OTHER")
    card.relationships("has_structure")[0]["qualifiers"].update(chimeric_with=["OTHER"])
    relationship(
        card, "has_structure", "pdb:1TCD", {"coverage": 0.1, "chimeric_with": []}
    )
    card.relationships("has_interface_with")[0]["qualifiers"]["structures"].append(
        "pdb:1TCD"
    )
    answer = card.explain_oligomer()
    assert answer["interfaces"][0]["item"]["class"] == "chimera_or_fragment"
    assert len(answer["interfaces"][0]["classification_inputs"]["structures"]) == 2


def test_missing_structure_support_stays_partial_without_fabricating_a_relationship():
    card = synthetic(partner="uniprot:OTHER", structure=False)
    answer = card.explain_oligomer()
    assert (
        answer["status"] == "partial"
        and answer["interfaces"][0]["item"]["class"] == "undetermined"
    )
    (basis,) = answer["interfaces"][0]["classification_inputs"]["structures"]
    assert (
        basis["relationship_ref"] is None and basis["basis"] == "structure_not_on_card"
    )
    assert answer["structures"] == []


@pytest.mark.parametrize(
    "assemblies,expected",
    [
        (None, "not_stated_on_card"),
        ([], "stated_empty"),
        ([{"assembly_id": "1"}], "stated"),
    ],
)
def test_missing_empty_and_source_stated_assembly_states_stay_distinct(
    assemblies, expected
):
    card = synthetic()
    card.relationships("has_structure")[0]["qualifiers"]["assemblies"] = assemblies
    answer = card.explain_oligomer()
    assert answer["structures"][0]["assembly_state"] == expected
    assert answer["view"]["without_assembly_data"] == (
        ["pdb:1SUX"] if assemblies is None else []
    )


@pytest.mark.parametrize("predicate", ["has_structure", "has_interface_with"])
@pytest.mark.parametrize("missing", [True, False])
def test_missing_relationship_assertions_or_unrecorded_support_are_explicit(
    predicate, missing
):
    card = synthetic()
    card.relationships(predicate)[0]["source_assertion_ids"] = (
        ["SA_missing"] if missing else []
    )
    answer = card.explain_oligomer()
    assert answer["status"] == "partial" and answer["view"] == card.oligomer()
    assert any(
        g["reason"]
        == ("missing_source_assertion" if missing else "no_relationship_support")
        for g in answer["gaps"]
    )


@pytest.mark.parametrize("path", [SUBUNIT, FAMILY])
def test_all_matching_annotation_support_is_retained_alongside_alternatives(path):
    card = synthetic()
    node = card.get(path)
    value = node["value"][0]
    extra = assertion(card, path, value, "second source")
    other = assertion(card, path, "Synthetic competing value", "competing source")
    node["source_assertion_ids"].append(extra)
    answer = card.explain_oligomer()
    members = answer["subunit" if path == SUBUNIT else "family_interface_sites"]
    assert {r["id"] for r in members[0]["source_assertions"]} == set(
        node["source_assertion_ids"]
    )
    field = next(f for f in answer["fields"] if f["field_path"] == path)
    assert field["alternatives"][0]["id"] == other
    assert answer["view"] == card.oligomer()


@pytest.mark.parametrize("path", [SUBUNIT, FAMILY])
def test_selected_annotation_without_matching_original_is_partial(path):
    card = synthetic()
    identifier = card.get(path)["source_assertion_ids"][0]
    card.source_assertion_store.get(identifier)["asserted_value"] = {
        "synthetic": "different"
    }
    answer = card.explain_oligomer()
    assert answer["status"] == "partial"
    assert any(
        g["reason"] == "no_matching_annotation_assertion" and g["field_path"] == path
        for g in answer["gaps"]
    )


def test_field_conflicts_and_qualifier_alternatives_are_not_resolved():
    card = synthetic()
    card.quality["conflicts"] = [
        {"field": SUBUNIT, "source_assertion_ids": [["SA_missing"]]}
    ]
    card.quality["alternatives"] = [
        {"field": FAMILY, "source_assertion_ids": ["SA_alternative_missing"]}
    ]
    card.relationships("has_structure")[0]["qualifier_conflicts"] = {
        "assemblies": [[{"assembly_id": "2"}]]
    }
    answer = card.explain_oligomer()
    assert answer["status"] == "partial"
    assert (
        answer["structures"][0]["relationship"]["qualifier_conflicts"]
        == card.relationships("has_structure")[0]["qualifier_conflicts"]
    )
    assert {
        g.get("source_assertion_ref", "").split("#")[-1] for g in answer["gaps"]
    } == {"SA_missing", "SA_alternative_missing"}


@pytest.mark.parametrize("numbering", ["mixed", "author", None])
def test_agreement_retains_original_result_but_exposes_unconfirmed_numbering(numbering):
    card = synthetic(numbering=numbering)
    answer = card.explain_oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)
    assert answer["view"] == card.oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)
    assert answer["status"] == "partial"
    assert answer["agreement"][0]["item"]["both"] == [13, 14]
    assert not answer["agreement"][0]["numbering_confirmed"]
    assert any(
        g["reason"] == "agreement_numbering_not_confirmed" for g in answer["gaps"]
    )


@pytest.mark.parametrize("status", ["ok", "error", "unavailable", "not_requested"])
def test_empty_failed_unavailable_and_unqueried_report_context_is_original(status):
    card = Card(meta={"card_id": "sabueso:protein:uniprot:P52270"})
    report = {
        "source": "PDBe-KB",
        "data": "interface_residues",
        "status": status,
        "count": 0,
    }
    card.quality["enrichments"] = [{"source": "unrelated"}, report]
    answer = card.explain_oligomer()
    assert answer["status"] == "not_on_card" and answer["interfaces"] == []
    assert answer["context"]["reports"][0]["record"] == report
    assert answer["context"]["reports"][0]["locator"]["index"] == 1
    assert card.source_assertion_store.to_list() == []


def test_unrelated_missing_support_does_not_pollute_oligomer_explanation():
    card = synthetic()
    relationship(card, "has_bioactivity", "chembl:SYNTHETIC", {})[
        "source_assertion_ids"
    ] = ["SA_missing"]
    assert card.explain_oligomer()["status"] == "on_card"


def test_actual_failed_interface_query_is_not_an_empty_success():
    resolver = EntityResolver(FixtureUniProtClient("temp_data"))
    with pytest.warns(EnrichmentFailedWarning):
        card, _ = sabueso.resolve_protein_card(
            "P52270",
            resolver,
            structures=(),
            interfaces=True,
            pdbe_kb_client=FixturePDBeKBClient("temp_data", failing={"P52270"}),
        )
    answer = card.explain_oligomer()
    reports = [
        row
        for row in answer["context"]["reports"]
        if row["record"].get("data") == "interface_residues"
    ]
    assert len(reports) == 1 and reports[0]["record"]["status"] == "error"
    assert answer["view"]["interfaces"] == []
    assert (
        answer["context"]["absence_basis"]
        == "stored_inputs_only_never_external_absence"
    )


@pytest.mark.parametrize(
    "partner", ["uniprot:OTHER", "pdbe_kb.partner:TR-alpha light chain"]
)
def test_shared_partner_name_does_not_imply_homomer_identity(partner):
    card = synthetic(partner=partner)
    card.relationships("has_interface_with")[0]["qualifiers"]["partner_name"] = (
        "Synthetic homodimer"
    )
    answer = card.explain_oligomer()
    assert answer["interfaces"][0]["item"]["class"] == "heteromeric"
    assert (
        answer["interfaces"][0]["classification_inputs"]["identity_basis"]
        == "distinct_native_references"
    )


@pytest.mark.parametrize(
    "change", [{"sequence_id": "UniProt:OTHER"}, {"indexing": "0-based"}]
)
def test_family_sequence_context_never_proves_identity_or_numbering_by_equal_positions(
    change,
):
    card = synthetic()
    card.get(FAMILY)["value"][0]["location"]["sequence"].update(change)
    answer = card.explain_oligomer()
    assert not answer["agreement"][0]["numbering_confirmed"]
    assert answer["view"] == card.oligomer() and answer["status"] == "partial"


def test_zero_source_version_and_unknown_version_are_retained():
    card = synthetic()
    for row in card.source_assertion_store.to_list():
        card.source_assertion_store.get(row["id"])["source"]["version"] = 0
    answer = card.explain_oligomer()
    assert answer["interfaces"][0]["interface"]["source_assertions"][0]["version"] == 0
    card.source_assertion_store.get(
        card.relationships("has_interface_with")[0]["source_assertion_ids"][0]
    )["source"].pop("version")
    assert (
        card.explain_oligomer()["interfaces"][0]["interface"]["source_assertions"][0][
            "version"
        ]
        is None
    )


def test_saved_historical_pins_and_item_support_survive_reacquisition(
    public_card, tmp_path
):
    card = Card.from_dict(public_card.to_dict())
    store = sabueso.KnowledgeStore(tmp_path / "oligomer.db")
    pin = store.save(card)
    expected = card.explain_oligomer()
    new_sa = assertion(card, SUBUNIT, "Synthetic later acquisition", "UniProt", "later")
    card.set(SUBUNIT, ["Synthetic later acquisition"], [new_sa])
    assert store.save(card) != pin
    restored = store.load(pin).explain_oligomer()
    assert restored == expected
    for row in restored["structures"] + [
        i["interface"] for i in restored["interfaces"]
    ]:
        assert store.relationship(row["relationship_ref"]) == row["relationship"]
        for sa in row["source_assertions"]:
            assert (
                store.source_assertion(sa["source_assertion_ref"])["source"].get(
                    "version"
                )
                == sa["version"]
            )


def test_reader_acquires_nothing_adds_no_credit_and_returns_detached_records(
    monkeypatch,
):
    from sabueso.core import attribution
    from sabueso.tools.db import _http

    card = synthetic()
    before = deepcopy(card.to_dict())
    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no acquisition")
    )
    monkeypatch.setattr(
        attribution, "_load_backend", lambda *a, **k: pytest.fail("no credit")
    )
    with ackredit.session("inert oligomer explanation"):
        credit = ackredit.get_attribution().to_dict()
        answer = card.explain_oligomer()
        assert ackredit.get_attribution().to_dict() == credit
    answer["structures"][0]["relationship"]["qualifiers"].clear()
    answer["fields"][0]["node"].clear()
    answer["family_interface_sites"][0]["value"].clear()
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "numbering,status,reason",
    [
        ("mixed", "not_comparable", "interface_numbering_not_uniprot"),
        ("author", "not_comparable", "interface_numbering_not_uniprot"),
        (None, "undetermined", "interface_numbering_not_stated"),
    ],
)
def test_current_rule_refuses_equal_integers_without_confirmed_numbering(
    numbering, status, reason
):
    card = synthetic(numbering=numbering)
    before = deepcopy(card.to_dict())
    view = card.oligomer()
    row = view["agreement"][0]
    assert row["comparison"]["status"] == status
    assert row["comparison"]["reasons"] == [reason]
    assert all(row[k] is None for k in ("both", "family_only", "observed_only"))
    assert view["agreement_state"]["status"] == "not_computed"
    explanation = card.explain_oligomer()
    assert explanation["view"] == view and explanation["status"] == "partial"
    assert explanation["agreement"][0]["comparison"] == row["comparison"]
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "change,status,reason",
    [
        ({"sequence_id": None}, "undetermined", "family_sequence_id_not_stated"),
        ({"indexing": None}, "undetermined", "family_indexing_not_stated"),
        (
            {"sequence_id": "UniProt:OTHER"},
            "not_comparable",
            "family_sequence_not_card_subject",
        ),
        (
            {"sequence_id": "uniprot:P52270"},
            "not_comparable",
            "family_sequence_not_card_subject",
        ),
        ({"indexing": "0-based"}, "not_comparable", "family_indexing_not_1_based"),
    ],
)
def test_family_context_is_not_inferred_from_same_positions(change, status, reason):
    card = synthetic()
    card.get(FAMILY)["value"][0]["location"]["sequence"].update(change)
    row = card.oligomer()["agreement"][0]
    assert row["comparison"]["status"] == status
    assert row["comparison"]["reasons"] == [reason]
    assert row["both"] is None
    assert card.oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)["agreement"][0][
        "both"
    ] == [13, 14]


@pytest.mark.parametrize("residues", [None, []])
def test_missing_observed_residues_and_explicit_empty_contacts_stay_distinct(residues):
    card = synthetic()
    card.relationships("has_interface_with")[0]["qualifiers"]["residues"] = residues
    row = card.oligomer()["agreement"][0]
    if residues is None:
        assert row["both"] is None and row["comparison"]["status"] == "undetermined"
        assert row["comparison"]["reasons"] == ["interface_residues_not_stated"]
    else:
        assert row["both"] == [] and row["comparison"]["status"] == "comparable"
        assert row["family_only"] == [12, 13, 14] and row["observed_only"] == []


@pytest.mark.parametrize(
    "key,alternative",
    [("numbering", "author"), ("residues", [{"start": 99, "end": 99}])],
)
def test_conflicting_numbering_or_positions_are_not_silently_chosen(key, alternative):
    card = synthetic()
    original = card.relationships("has_interface_with")[0]
    q = deepcopy(original["qualifiers"])
    q[key] = alternative
    relationship(card, "has_interface_with", original["object_ref"], q)
    row = card.oligomer()["agreement"][0]
    assert row["comparison"]["reasons"] == [f"interface_{key}_conflicted"]
    assert row["comparison"]["status"] == "undetermined" and row["both"] is None
    assert card.oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)["agreement"][0][
        "both"
    ] == [13, 14]
    answer = card.explain_oligomer()
    assert answer["interfaces"][0]["interface"]["relationship"]["qualifier_conflicts"][
        key
    ] == [original["qualifiers"][key], alternative]


@pytest.mark.parametrize("missing", ["interface", "family", "both"])
def test_no_comparison_inputs_is_not_a_negative_agreement(missing):
    card = (
        synthetic(partner="uniprot:OTHER")
        if missing in {"interface", "both"}
        else synthetic()
    )
    if missing in {"family", "both"}:
        card.sections.pop("features_positional")
    view = card.oligomer()
    assert (
        view["agreement"] == [] and view["agreement_state"]["status"] == "not_computed"
    )
    assert ("no_homomeric_interface_on_card" in view["agreement_state"]["reasons"]) == (
        missing in {"interface", "both"}
    )
    assert (
        "no_family_interface_site_on_card" in view["agreement_state"]["reasons"]
    ) == (missing in {"family", "both"})
    assert "agreement_state" not in card.oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)


def test_comparable_family_members_are_not_hidden_by_an_unconfirmed_member():
    card = synthetic()
    original = deepcopy(card.get(FAMILY)["value"][0])
    other = deepcopy(original)
    other["description"] = "Synthetic second interface"
    other["location"]["sequence"]["sequence_id"] = "UniProt:OTHER"
    card.get(FAMILY)["value"].append(other)
    card.get(FAMILY)["source_assertion_ids"].append(assertion(card, FAMILY, other))
    view = card.oligomer()
    assert view["agreement_state"]["status"] == "partial"
    assert view["agreement"][0]["both"] == [13, 14]
    assert view["agreement"][1]["both"] is None
    explanation = card.explain_oligomer()
    assert [
        row["family_site_locator"]["index"] for row in explanation["agreement"]
    ] == [0, 1]
    assert explanation["view"] == view


@pytest.mark.parametrize(
    "value",
    [None, "@1", "interface_site_agreement@3", "interface_site_agreement@2 ", 2, []],
)
@pytest.mark.parametrize("method", ["oligomer", "explain_oligomer"])
def test_agreement_selector_is_digested_without_alias_or_version_guessing(
    value, method
):
    with pytest.raises(ArgumentError):
        getattr(synthetic(), method)(agreement_rule=value)


@pytest.mark.parametrize("rule", [AGREEMENT_RULE, LEGACY_AGREEMENT_RULE])
def test_both_rules_preserve_historical_card_pins_and_source_support(rule, tmp_path):
    card = synthetic(numbering="mixed")
    store = sabueso.KnowledgeStore(tmp_path / "agreement.db")
    pin = store.save(card)
    expected = card.explain_oligomer(agreement_rule=rule)
    card.relationships("has_interface_with")[0]["qualifiers"]["numbering"] = "uniprot"
    assert store.save(card) != pin
    restored = store.load(pin).explain_oligomer(agreement_rule=rule)
    assert restored == expected and restored["card_ref"] == pin
    assert restored["agreement"][0]["item"]["both"] == (
        None if rule == AGREEMENT_RULE else [13, 14]
    )
    for row in restored["interfaces"][0]["interface"]["source_assertions"]:
        assert (
            store.source_assertion(row["source_assertion_ref"])["source"]["version"]
            == "original-release"
        )


def test_full_and_index_packets_declare_current_rule_and_preserve_saved_results(
    tmp_path,
):
    card = synthetic(numbering="mixed")
    card.set(
        "identifiers.uniprot",
        "P52270",
        [assertion(card, "identifiers.uniprot", "P52270")],
    )
    full = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["oligomer"]), card
    )
    index = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["oligomer"], detail="index"), card
    )
    facts = full.facts["oligomer"]["subject"]
    assert facts["agreement"][0]["both"] is None
    assert facts["agreement"][0]["comparison"]["status"] == "not_comparable"
    assert AGREEMENT_RULE in {rule["rule"] for rule in facts["rules"]}
    assert AGREEMENT_RULE in index.facts["oligomer"]["subject"]["full_rules"]
    assert LEGACY_AGREEMENT_RULE not in index.facts["oligomer"]["subject"]["full_rules"]
    store = sabueso.KnowledgeStore(tmp_path / "packets.db")
    store.save(card)
    store.save_packet(full, "original")
    pin = full.ref
    card.relationships("has_interface_with")[0]["qualifiers"]["numbering"] = "uniprot"
    store.save(card)
    current = sabueso.compose_packet(
        sabueso.KnowledgeQuery("P52270", aspects=["oligomer"]), card
    )
    assert current.facts["oligomer"]["subject"]["agreement"][0]["both"] == [13, 14]
    assert store.load_packet(pin).facts == full.facts


@pytest.mark.parametrize(
    "area,reason",
    [
        ("interface_zero", "interface_positions_not_1_based"),
        ("family_zero", "family_positions_not_1_based"),
        ("missing_position", "interface_residue_positions_not_stated"),
        ("different_subject", "interface_subject_not_card_subject"),
        ("missing_subject", "interface_subject_not_stated"),
    ],
)
def test_declared_numbering_requires_native_subject_and_actual_located_positive_positions(
    area, reason
):
    card = synthetic()
    interface = card.relationships("has_interface_with")[0]
    if area == "interface_zero":
        interface["qualifiers"]["residues"] = [{"start": 0, "end": 14}]
    elif area == "family_zero":
        card.get(FAMILY)["value"][0]["location"]["sequence"]["fragments"][0][
            "start"
        ] = 0
    elif area == "missing_position":
        interface["qualifiers"]["residues"].append({"start": None, "end": None})
    else:
        interface["subject_ref"] = (
            "uniprot:OTHER" if area == "different_subject" else None
        )
    row = card.oligomer()["agreement"][0]
    assert row["both"] is None and row["comparison"]["reasons"] == [reason]
    assert card.oligomer(agreement_rule=LEGACY_AGREEMENT_RULE)["agreement"][0][
        "both"
    ] == ([12, 13, 14] if area == "interface_zero" else [13, 14])
