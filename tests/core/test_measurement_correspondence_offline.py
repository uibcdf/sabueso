"""Independent copy/correspondence expectations for opt-in measurement @2 (#186)."""

import socket
from copy import deepcopy

import pytest
import pyunitwizard as puw

from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError, SchemaError
from sabueso.core.measurements import measurement_groups as original_groups
from sabueso.core.quantities import normalized_measurement
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion

RULE = "measurement_identity@2"
MOLECULE = "chembl:CHEMBL_SYNTHETIC"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No acquisition during correspondence interpretation")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def card():
    return Card(
        meta={"card_id": "sabueso:protein:uniprot:P52270", "entity_type": "protein"}
    )


def record(
    c,
    activity,
    *,
    source="ChEMBL",
    value=100,
    units="nM",
    relationship_id=None,
    **changes,
):
    q = {
        "source": source,
        "activity_id": activity,
        "measurement": {
            "type": "IC50",
            "value": value,
            "units": units,
            "relation": "=",
            "normalized": normalized_measurement(value, units),
            "stated_value": str(value),
        },
        "assay": {"id": "assay:1", "relationship_type": "D"},
        "document": {"pubmed": "1"},
    }
    q.update(changes)
    sa = make_source_assertion(
        "relationships.has_bioactivity",
        deepcopy(q),
        source,
        str(activity),
        "2026-11-04",
    )
    c.source_assertion_store.add(sa)
    rel = make_relationship(
        "uniprot:P52270", "has_bioactivity", MOLECULE, q, [sa["id"]]
    )
    if relationship_id is not None:
        rel["id"] = (
            relationship_id  # An explicitly synthetic retained duplicate projection.
        )
    c.relationship_store.add(rel)
    return rel["id"]


def result(c):
    return c.bioactivities(measurement_rule=RULE)


@pytest.mark.parametrize(
    "left,right",
    [
        (None, None),
        ("same prose", "same prose"),
        ("Synthetic wild-type, pH7", "Synthetic mutant construct, pH5"),
    ],
)
def test_equal_values_or_prose_do_not_establish_measurement_identity(left, right):
    c = card()
    a = record(
        c, 1, assay={"id": "assay:1", "relationship_type": "D", "description": left}
    )
    b = record(
        c,
        2,
        source="BindingDB",
        assay={"id": "assay:2", "relationship_type": "D", "description": right},
    )
    before = c.to_dict()
    assert len(original_groups(c)["groups"]) == 1
    view = result(c)
    identity = view["measurement_identity"]
    assert identity["rule"]["rule"] == RULE and not identity["groups"]
    assert identity["counting"]["group_count"] == 2
    assert identity["counting"]["independence_status"] == "not_established"
    (possible,) = identity["possible_correspondences"]
    assert set(possible["records"]) == {a, b}
    assert possible["state"] == "possible_correspondence"
    assert possible["measurement_identity"] == "not_established"
    assert possible["independence_status"] == "not_established"
    assert view["items"][0]["measurement_count"] == 2
    assert c.to_dict() == before
    explained = c.explain_measurement(a, measurement_rule=RULE)
    assert explained["rule"]["rule"] == "measurement_group_explanation@2"
    assert explained["group"]["records"] == [a] and not explained["joins"]
    assert explained["diagnostics"]["possible_correspondences"] == [possible]
    assert (
        c.explain_bioactivity(MOLECULE, measurement_rule=RULE)["item"]
        == view["items"][0]
    )


def test_a_declared_activity_copy_retains_discrepancies_but_adds_no_vote():
    c = card()
    original = record(c, 1, value=100)
    copied = record(
        c,
        2,
        source="PubChem",
        value=500000,
        copy_of={"source": "ChEMBL", "activity_id": 1},
    )
    view = result(c)
    item = view["items"][0]
    assert item["record_count"] == 2 and item["measurement_count"] == 1
    assert item["class"] == "active" and item["classes"] == {"active": 1}
    (group,) = view["measurement_identity"]["groups"]
    assert set(group["records"]) == {original, copied}
    assert group["basis"] == ["provenance"]
    assert view["measurement_identity"]["copy_diagnostics"]
    explained = c.explain_bioactivity(MOLECULE, measurement_rule=RULE)
    assert explained["rule"]["rule"] == "bioactivity_explanation@3"
    assert explained["groups"][0]["voters"] == [original]
    assert {
        r["relationship"]["qualifiers"]["measurement"]["value"]
        for r in explained["records"]
    } == {100, 500000}


@pytest.mark.parametrize("count", [1, 2])
def test_named_assay_copy_requires_a_unique_original_without_numeric_guessing(count):
    c = card()
    originals = [record(c, i + 1, value=100 * (i + 1)) for i in range(count)]
    copied = record(
        c, 3, source="PubChem", copy_of={"source": "ChEMBL", "assay": "assay:1"}
    )
    identity = result(c)["measurement_identity"]
    if count == 1:
        assert identity["groups"][0]["records"] == sorted([originals[0], copied])
    else:
        assert not identity["groups"]
        assert identity["ambiguous"][0]["candidates"] == sorted(originals)
        assert identity["unresolved_copies"][0]["record"] == copied
        assert identity["unresolved_copies"][0]["reason"] == "ambiguous_original"


def test_missing_explicit_original_does_not_fall_back_to_a_similar_assay_row():
    c = card()
    record(c, 1)
    copied = record(
        c,
        2,
        source="PubChem",
        copy_of={"source": "ChEMBL", "activity_id": 999, "assay": "assay:1"},
    )
    view = result(c)
    identity = view["measurement_identity"]
    assert not identity["groups"]
    assert identity["unresolved_copies"][0]["record"] == copied
    assert not identity["possible_correspondences"]
    explained = c.explain_bioactivity(MOLECULE, measurement_rule=RULE)
    copy_group = next(g for g in explained["groups"] if copied in g["records"])
    assert copy_group["class"] == "inconclusive" and not copy_group["voters"]
    assert copy_group["basis"] == "copies_without_original_vote"


def test_copy_cycles_do_not_manufacture_resolved_originals_or_votes():
    c = card()
    a = record(c, 1, copy_of={"source": "BindingDB", "activity_id": 2})
    b = record(c, 2, source="BindingDB", copy_of={"source": "ChEMBL", "activity_id": 1})
    view = result(c)
    assert not view["measurement_identity"]["groups"]
    assert {u["record"] for u in view["measurement_identity"]["unresolved_copies"]} == {
        a,
        b,
    }
    assert {u["reason"] for u in view["measurement_identity"]["unresolved_copies"]} == {
        "copy_cycle"
    }
    assert view["items"][0]["classes"] == {"inconclusive": 2}


def test_a_copy_only_chain_retains_links_but_has_no_original_vote():
    c = card()
    a = record(c, 1, copy_of={"source": "Missing", "activity_id": 99})
    b = record(c, 2, source="PubChem", copy_of={"source": "ChEMBL", "activity_id": 1})
    view = result(c)
    assert set(view["measurement_identity"]["groups"][0]["records"]) == {a, b}
    assert view["items"][0]["class"] == "inconclusive"
    assert view["measurement_identity"]["unresolved_copies"][0]["record"] == a
    assert (
        c.explain_bioactivity(MOLECULE, measurement_rule=RULE)["groups"][0]["voters"]
        == []
    )


def test_rounded_agreement_is_only_a_candidate_and_multiple_candidates_stay_visible():
    c = card()
    a = record(c, 1, value=62)
    b = record(c, 2, value=62.46, source="BindingDB")
    d = record(c, 3, value=62.2, source="Other")
    identity = result(c)["measurement_identity"]
    assert not identity["groups"]
    pairs = {frozenset(p["records"]) for p in identity["possible_correspondences"]}
    assert frozenset({a, b}) in pairs and frozenset({a, d}) in pairs
    assert identity["counting"]["group_count"] == 3


def test_structured_context_is_retained_without_prose_or_transitive_equivalence():
    c = card()
    a = record(
        c, 1, assay={"id": "a", "relationship_type": "D", "variant_mutation": "A1G"}
    )
    record(c, 2, source="BindingDB")
    b = record(
        c,
        3,
        source="Other",
        assay={"id": "b", "relationship_type": "D", "variant_mutation": "A1V"},
    )
    identity = result(c)["measurement_identity"]
    assert not identity["groups"] and identity["counting"]["group_count"] == 3
    row = next(
        p for p in identity["possible_correspondences"] if set(p["records"]) == {a, b}
    )
    field = next(f for f in row["context"] if f["field"] == "assay.variant_mutation")
    assert field["state"] == "different_retained_values"
    assert set((field["left"], field["right"])) == {"A1G", "A1V"}


@pytest.mark.parametrize(
    "mutation",
    [
        {"relation": ">"},
        {"relation": None},
        {"upper_value": 200},
        {"uncertainty": {"kind": "not_interpreted"}},
        {"value": float("nan"), "normalized": None},
        {"value": 10**500, "normalized": None},
    ],
)
def test_unsupported_numeric_context_is_not_an_exact_scalar_candidate(mutation):
    from sabueso.core.measurement_correspondence import measurement_groups

    c = card()
    a = record(c, 1)
    record(c, 2, source="BindingDB")
    # Explicitly synthetic altered runtime input, not a rewritten public fixture.
    rows = c.relationships("has_bioactivity")
    next(r for r in rows if r["id"] == a)["qualifiers"]["measurement"].update(mutation)
    original = c.relationships
    c.relationships = lambda predicate=None: (
        rows if predicate == "has_bioactivity" else original(predicate)
    )
    identity = measurement_groups(c, measurement_rule=RULE)
    assert not identity["possible_correspondences"] and not identity["groups"]
    assert any(
        row["record"] == a
        and "exact_positive_scalar_context_not_available" in row["reasons"]
        for row in identity["comparison_scope"]["not_compared"]
    )


def test_units_stay_equivalent_under_a_nondefault_quantity_policy():
    c = card()
    record(c, 1, value=100, units="nM")
    record(c, 2, source="BindingDB", value=0.1, units="uM")
    before = c.to_dict()
    with puw.context(
        standard_units=["angstrom", "ns", "K", "mole", "dalton", "micromolar"]
    ):
        view = result(c)
        assert len(view["measurement_identity"]["possible_correspondences"]) == 1
        assert all(
            float(puw.get_value(m["normalized"], to_unit="nanomolar"))
            == pytest.approx(100)
            for m in view["items"][0]["measurements"]
        )
    assert c.to_dict() == before


@pytest.mark.parametrize(
    "counting_rule", ["ligand_measurement_count@1", "ligand_measurement_count@2"]
)
def test_opt_in_crossing_comparison_and_tables_explain_the_same_count_scope(
    counting_rule,
):
    c = card()
    record(c, 1)
    record(c, 2, source="BindingDB")
    molecule = Card(
        meta={
            "card_id": "sabueso:small_molecule:inchikey:SYNTHETIC",
            "entity_type": "small_molecule",
        }
    )
    assertion = make_source_assertion(
        "relationships.same_as",
        {"record": MOLECULE, "anchor": "inchikey:SYNTHETIC"},
        "Synthetic",
        "synthetic-molecule",
        "2026-11-04",
    )
    molecule.source_assertion_store.add(assertion)
    molecule.relationship_store.add(
        make_relationship(
            MOLECULE,
            "same_as",
            "inchikey:SYNTHETIC",
            source_assertion_ids=[assertion["id"]],
        )
    )
    deck = Deck([molecule])
    view = c.ligands(deck, measurement_rule=RULE, counting_rule=counting_rule)
    assert view["items"][0]["bioactivity"]["measurements"] == 2
    assert (
        view["measurement_counting"]["parameters"]["independence_status"]
        == "not_established"
    )
    assert ("source records" if counting_rule.endswith("@1") else "group") in view[
        "measurement_counting"
    ]["parameters"]["measurement_count_scope"]
    explanation = c.explain_ligand(
        molecule.id, deck, measurement_rule=RULE, counting_rule=counting_rule
    )
    assert explanation["rule"]["rule"] == "ligand_deck_explanation@4"
    assert explanation["items"][0]["item"] == view["items"][0]
    compared = c.compare_ligands(
        deck, c, deck, measurement_rule=RULE, counting_rule=counting_rule
    )
    assert compared["shared"][0]["self"] == compared["shared"][0]["other"]
    for name, kwargs in (("bioactivities", {}), ("ligands", {"deck": deck})):
        rows = c.table(
            name,
            measurement_rule=RULE,
            **kwargs,
            **({"counting_rule": counting_rule} if name == "ligands" else {}),
        )
        assert rows and all(
            r["measurement_rule"] == RULE
            and r["independence_status"] == "not_established"
            for r in rows
        )


@pytest.mark.parametrize("bad", [None, True, 2, "measurement_identity@3", [], {}])
@pytest.mark.parametrize(
    "method",
    [
        "bioactivities",
        "explain_measurement",
        "explain_bioactivity",
        "ligands",
        "explain_ligand",
        "compare_ligands",
    ],
)
def test_native_selector_refusal_precedes_pin_capture_even_without_digestion(
    bad, method
):
    c = card()

    def forbidden():
        raise AssertionError("No pin capture for an invalid selector")

    c.pinned_ref = forbidden
    deck = Deck([])
    args = {
        "bioactivities": [],
        "explain_measurement": ["REL_synthetic"],
        "explain_bioactivity": [MOLECULE],
        "ligands": [deck],
        "explain_ligand": ["sabueso:small_molecule:inchikey:SYNTHETIC", deck],
        "compare_ligands": [deck, c, deck],
    }[method]
    with pytest.raises(ArgumentError, match="measurement_rule"):
        getattr(c, method)(*args, measurement_rule=bad, skip_digestion=True)


def test_default_and_explicit_original_answers_remain_equal():
    c = card()
    record(c, 1)
    record(c, 2, source="BindingDB")
    assert c.bioactivities() == c.bioactivities(
        measurement_rule="measurement_identity@1"
    )
    assert c.bioactivities()["measurement_identity"] == {
        k: original_groups(c)[k] for k in ("rule", "groups", "ambiguous", "review")
    }
    assert (
        c.explain_measurement(c.relationships("has_bioactivity")[0]["id"])["rule"][
            "rule"
        ]
        == "measurement_group_explanation@1"
    )


def test_malformed_context_has_a_controlled_diagnostic_and_retains_original_inspection():
    from sabueso.core.measurement_correspondence import measurement_groups

    c = card()
    record(c, 1)
    rows = c.relationships("has_bioactivity")
    rows[0]["qualifiers"]["assay"] = "malformed synthetic assay"
    original = c.relationships
    c.relationships = lambda predicate=None: (
        rows if predicate == "has_bioactivity" else original(predicate)
    )
    with pytest.raises(SchemaError, match="assay"):
        measurement_groups(c, measurement_rule=RULE)
    assert rows[0]["qualifiers"]["assay"] == "malformed synthetic assay"


@pytest.mark.parametrize(
    "mapping", [f"packet_aspects@{version}" for version in range(6, 16)]
)
def test_existing_packet_mappings_pin_original_measurement_interpretation(
    mapping, monkeypatch
):
    from sabueso.core.packets import _facts

    c = card()
    record(c, 1)
    record(c, 2, source="BindingDB")
    selected = []
    original = c.bioactivities

    def observed(*args, **kwargs):
        selected.append(kwargs.get("measurement_rule"))
        return original(*args, **kwargs)

    monkeypatch.setattr(c, "bioactivities", observed)
    answer = _facts("bioactivities", c, mapping=mapping)
    assert selected == ["measurement_identity@1"]
    assert answer["measurement_identity"]["rule"]["rule"] == "measurement_identity@1"
    assert answer["items"][0]["measurement_count"] == 1


def test_duplicate_activity_selectors_are_ambiguous_and_same_source_copies_remain_declared():
    c = card()
    record(c, 1)
    record(c, 1, value=200, relationship_id="REL_synthetic_duplicate")
    copied = record(
        c, 2, source="PubChem", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    identity = result(c)["measurement_identity"]
    assert not identity["groups"]
    assert identity["ambiguous"][0]["record"] == copied
    assert len(identity["ambiguous"][0]["candidates"]) == 2
    c = card()
    original = record(c, 1)
    record(c, 2, source="PubChem", copy_of={"source": "ChEMBL", "activity_id": 1})
    record(c, 3, source="PubChem", copy_of={"source": "ChEMBL", "activity_id": 1})
    identity = result(c)["measurement_identity"]
    assert len(identity["groups"]) == 1 and len(identity["groups"][0]["records"]) == 3
    assert identity["review"][0]["reason"] == "same_source_copy_family"
    assert c.explain_bioactivity(MOLECULE, measurement_rule=RULE)["groups"][0][
        "voters"
    ] == [original]


def test_distinct_target_and_molecule_references_are_never_joined_by_value():
    from sabueso.core.measurement_correspondence import measurement_groups

    for changed in ("target", "molecule"):
        c = card()
        a = record(c, 1)
        record(c, 2, source="BindingDB")
        rows = c.relationships("has_bioactivity")
        row = next(r for r in rows if r["id"] == a)
        row["subject_ref" if changed == "target" else "object_ref"] = (
            "uniprot:P60174" if changed == "target" else "chembl:OTHER"
        )
        original = c.relationships
        c.relationships = lambda predicate=None: (
            rows if predicate == "has_bioactivity" else original(predicate)
        )
        identity = measurement_groups(c, measurement_rule=RULE)
        assert not identity["groups"] and not identity["possible_correspondences"]


def test_public_digest_and_original_support_remain_available():
    c = card()
    a = record(c, 1)
    b = record(c, 2, source="BindingDB")
    with pytest.raises(ArgumentError, match="measurement_rule"):
        c.bioactivities(measurement_rule="latest")
    explanation = c.explain_measurement(a, measurement_rule=RULE)
    pair = explanation["diagnostics"]["possible_correspondences"][0]
    assert set(pair["source_assertion_ids"]) == {a, b}
    links = explanation["records"] + explanation["context"]["relationships"]
    for rid in (a, b):
        link = next(row for row in links if row["relationship"]["id"] == rid)
        assert link["relationship_ref"] == c.pinned_ref() + "#" + rid
        assert all(row["found"] for row in link["source_assertions"])
        assert set(link["relationship"]["source_assertion_ids"]) == set(
            pair["source_assertion_ids"][rid]
        )
    assert pair["precision"]["left"]["half_last_digit"]["unit"] == "nanomolar"


def test_empty_and_excluded_original_scope_never_supply_independent_copy_votes():
    c = card()
    empty = result(c)
    assert (
        not empty["items"]
        and empty["measurement_identity"]["counting"]["record_count"] == 0
    )
    assert (
        "does not establish absence"
        in empty["measurement_identity"]["comparison_scope"]["interpretation"]
    )
    original = record(c, 1, assay={"id": "assay:1", "relationship_type": "H"})
    copied = record(
        c, 2, source="PubChem", copy_of={"source": "ChEMBL", "activity_id": 1}
    )
    current = result(c)
    assert current["items"][0]["class"] == "inconclusive"
    assert current["items"][0]["measurements"][0]["relationship_id"] == copied
    assert current["items"][0]["measurements"][0]["class"] == "active"
    assert (
        c.bioactivities()["items"][0]["class"] == "active"
    )  # Original explicit copy-only fallback.
    explanation = c.explain_bioactivity(MOLECULE, measurement_rule=RULE)
    assert explanation["groups"][0]["voters"] == []
    included = c.explain_bioactivity(
        MOLECULE, include_indirect=True, measurement_rule=RULE
    )
    assert included["groups"][0]["voters"] == [original]


@pytest.mark.parametrize("count", [1, 2])
def test_named_assay_copy_without_an_endpoint_still_needs_one_unique_original(count):
    c = card()
    originals = [record(c, i + 1) for i in range(count)]
    copied = record(
        c,
        3,
        source="PubChem",
        copy_of={"source": "ChEMBL", "assay": "assay:1"},
        measurement={
            "type": None,
            "relation": None,
            "value": 0.1,
            "units": "uM",
            "normalized": normalized_measurement(0.1, "uM"),
        },
    )
    view = result(c)
    identity = view["measurement_identity"]
    if count == 1:
        assert identity["groups"][0]["records"] == sorted([originals[0], copied])
        assert view["items"][0]["class"] == "active"
        assert (
            next(
                m
                for m in view["items"][0]["measurements"]
                if m["relationship_id"] == copied
            )["type"]
            is None
        )
    else:
        assert not identity["groups"] and identity["ambiguous"][0][
            "candidates"
        ] == sorted(originals)


@pytest.mark.parametrize("rule", ["measurement_identity@1", RULE])
def test_explanation_context_uses_the_actual_pinned_glossary_not_registration_keys(
    rule,
):
    c = card()
    rid = record(c, 1)
    a = "inchikey:AAAAAAAAAAAAAA-AAAAAAAAAA-N"
    b = "inchikey:BBBBBBBBBBBBBB-BBBBBBBBBB-N"
    for key in (a, b):
        c.entity_identities[key] = {
            "entity_type": "small_molecule",
            "records": [MOLECULE],
            "resolved": {"by": "Synthetic"},
        }
    before = c.to_dict()
    assert b not in c.entities() and b in c.entities()[a]["records"]
    answer = c.explain_measurement(rid, measurement_rule=rule)
    assert answer["status"] == "on_card"
    stored = answer["context"]["stored_identities"]
    assert [entry["locator"]["key"] for entry in stored] == [a]
    assert stored[0]["record"] == before["entities"][a]
    assert b in answer["context"]["entities"][a]["records"]
    restored = Card.from_dict(before)
    assert restored.pinned_ref() == c.pinned_ref()
    assert restored.explain_measurement(rid, measurement_rule=rule) == answer
    assert c.to_dict() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("assay", []),
        ("measurement", []),
        ("document", []),
        ("molecule_ref", []),
        ("source", False),
        ("source", ""),
        ("copy_of", []),
        ("copy_of", {"source": "ChEMBL", "activity_id": []}),
    ],
)
def test_malformed_candidate_context_is_refused_before_glossary_work(field, value):
    from sabueso.core.measurement_correspondence import measurement_groups

    c = card()
    record(c, 1)
    rows = c.relationships("has_bioactivity")
    rows[0]["qualifiers"][field] = value
    original = c.relationships
    c.relationships = lambda predicate=None: (
        rows if predicate == "has_bioactivity" else original(predicate)
    )
    with pytest.raises(SchemaError):
        measurement_groups(c, measurement_rule=RULE)
