"""Disease groups expose exact stored support without acquiring new knowledge."""

from copy import deepcopy

import ackredit
import argdigest
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, StorageError
from sabueso.core.relationship_store import make_relationship
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.mappings.mondo import map_hierarchy
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.clinvar import FixtureClinVarClient
from sabueso.tools.db.diseases import FixtureDISEASESClient
from sabueso.tools.db.medgen import FixtureMedGenClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.open_targets import FixtureOpenTargetsClient
from sabueso.tools.db.orphadata import FixtureOrphadataClient

TERM = "mondo:MONDO:0014221"


@pytest.fixture(scope="module")
def public_card():
    with pytest.warns(Warning):  # declared public ClinVar/Open Targets fixture cuts
        card, _ = sabueso.resolve(
            "P60174",
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            diseases={},
            diseases_client=FixtureDISEASESClient("temp_data"),
            open_targets={},
            open_targets_client=FixtureOpenTargetsClient("temp_data"),
            orphadata=True,
            orphadata_client=FixtureOrphadataClient("temp_data"),
            clinvar={},
            clinvar_client=FixtureClinVarClient("temp_data"),
            medgen=True,
            medgen_client=FixtureMedGenClient("temp_data"),
            disease_identity=True,
            mondo_client=FixtureMONDOClient("temp_data"),
        )
    return card


def relationships(answer):
    for row in answer["statements"] + answer["ungrouped_context"]["statements"]:
        if row["input"]["basis"] == "relationship":
            yield row["input"]
        for path in row["identity"]:
            yield from path["links"]
            yield from path["alternatives"]
        for path in row["hierarchy"]:
            yield from path["links"]


def test_public_group_retains_each_source_and_exact_annotation_members(
    public_card, monkeypatch
):
    from sabueso.tools.db import _http

    monkeypatch.setattr(
        _http, "_urlopen", lambda *a, **k: pytest.fail("no acquisition")
    )
    before = public_card.to_dict()
    with ackredit.session("inert explanation"):
        credited = ackredit.get_attribution().to_dict()
        answer = public_card.explain_disease(TERM)
        assert ackredit.get_attribution().to_dict() == credited
    assert answer["status"] == "on_card" and not answer["gaps"]
    assert answer["rule"]["rule"] == "disease_group_explanation@1"
    assert answer["rule"]["inputs"] == [public_card.pinned_ref()]
    assert answer["grouping_rule"]["rule"] == "disease_grouping@1"
    assert answer["group"] == next(
        g for g in public_card.diseases()["diseases"] if g["mondo"] == "MONDO:0014221"
    )
    assert answer["group"]["sources"] == [
        "ClinVar",
        "DISEASES",
        "Open Targets",
        "Orphanet",
        "UniProt",
    ]
    for row in answer["statements"]:
        basis = row["input"]
        assert basis["source_assertions"] and all(
            a["found"] for a in basis["source_assertions"]
        )
        if basis["basis"] == "selected_annotation_member":
            assert all(
                a["asserted_value"] in basis["members"]
                for a in basis["source_assertions"]
            )
            if row["statement"]["kind"] == "clinvar_condition":
                assert {a["record"] for a in basis["source_assertions"]} == {
                    row["statement"]["variant"]
                }
    chains = [
        path
        for row in answer["statements"]
        for path in row["identity"]
        if len(path["links"]) == 2
    ]
    assert chains and {
        r["relationship"]["qualifiers"]["source"] for r in chains[0]["links"]
    } == {"MedGen", "MONDO"}
    assert {
        row["statement"]["reason"] for row in answer["ungrouped_context"]["statements"]
    } >= {"condition_not_provided", "no_id_stated", "no_stated_equivalence"}
    answer["group"]["names"].clear()
    answer["statements"][0]["input"]["source_assertions"].clear()
    assert public_card.to_dict() == before


def test_historical_explanation_keeps_every_relationship_and_assertion_pin(
    public_card, tmp_path
):
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save(public_card)
    expected = public_card.explain_disease(TERM)
    later = Card.from_dict(public_card.to_dict())
    later.meta["later_observation"] = True
    store.save(later)
    assert store.load(pin).explain_disease(TERM) == expected
    for link in relationships(expected):
        assert store.relationship(link["relationship_ref"]) == link["relationship"]
        for assertion in link["source_assertions"]:
            assert (
                store.source_assertion(assertion["source_assertion_ref"])[
                    "asserted_value"
                ]
                == assertion["asserted_value"]
            )


@pytest.mark.parametrize("route", ["association", "identity", "annotation"])
def test_missing_assertion_support_is_partial(public_card, route):
    subject = Card.from_dict(public_card.to_dict())
    explanation = subject.explain_disease(TERM)
    if route == "annotation":
        row = next(
            r
            for r in explanation["statements"]
            if r["input"]["basis"] == "selected_annotation_member"
        )
        identifier = row["input"]["source_assertions"][0]["id"]
    else:
        row = next(
            r
            for r in relationships(explanation)
            if r["relationship"]["predicate"]
            == ("associated_with" if route == "association" else "same_as")
        )
        identifier = row["source_assertions"][0]["id"]
    subject.source_assertion_store.store.pop(identifier)
    answer = subject.explain_disease(TERM)
    assert answer["status"] == "partial"
    assert any(g["reason"] == "missing_source_assertion" for g in answer["gaps"])


def synthetic(conditions, equivalents=(), hierarchy=()):
    card = Card(
        meta={"card_id": "sabueso:protein:uniprot:P60174", "entity_type": "protein"},
        quality={
            "enrichments": [{"source": "MONDO", "status": "added", "ungrouped": []}]
        },
    )
    item = {"accession": "VCV_SYNTHETIC", "conditions": conditions}
    assertion = make_source_assertion(
        "annotations.clinical_variants",
        item,
        "ClinVar",
        item["accession"],
        "2026-01-01",
    )
    card.source_assertion_store.add(assertion)
    card.set("annotations.clinical_variants", [item], [assertion["id"]])
    for subject, obj in equivalents:
        assertion = make_source_assertion(
            "relationships.same_as",
            {"mondo": obj},
            "MONDO",
            obj,
            "2026-01-01",
            subject_ref=subject,
        )
        card.source_assertion_store.add(assertion)
        card.relationship_store.add(
            make_relationship(
                subject,
                "same_as",
                f"mondo:{obj}",
                qualifiers={"source": "MONDO"},
                source_assertion_ids=[assertion["id"]],
            )
        )
    if hierarchy:
        mapped = map_hierarchy(
            [
                [
                    {
                        "term": a,
                        "parent": b,
                        "retrieved_at": "2026-01-01",
                        "version": "synthetic",
                    }
                    for a, b in zip(hierarchy, hierarchy[1:])
                ]
            ]
        )
        for assertion in mapped["source_assertions"]:
            card.source_assertion_store.add(assertion)
        for rel in mapped["relationships"]:
            card.relationship_store.add(rel)
    return card


def test_stated_hierarchy_is_explained_with_every_step_and_rule():
    path = ["MONDO:0000003", "MONDO:0000005", "MONDO:0000009"]
    subject = synthetic(
        [{"name": "synthetic condition", "xrefs": [path[0], "Orphanet:9"]}],
        [("Orphanet:9", path[-1])],
        path,
    )
    answer = subject.explain_disease(f"mondo:{path[-1]}")
    assert answer["status"] == "on_card"
    (step,) = answer["statements"][0]["hierarchy"]
    assert step["path"] == path
    (link,) = step["links"]
    assert link["relationship"]["derivation"]["rule"] == "mondo_hierarchy@1"
    assert len(link["source_assertions"]) == 2


def test_identity_conflicts_are_ungrouped_never_silently_selected():
    subject = synthetic(
        [{"name": "synthetic condition", "xrefs": ["MONDO:0000001", "OMIM:1"]}],
        [("OMIM:1", "MONDO:0000002")],
    )
    answer = subject.explain_disease("MONDO:0000001")
    assert answer["status"] == "not_on_card" and answer["group"] is None
    (row,) = answer["ungrouped_context"]["statements"]
    assert row["statement"]["reason"] == "conflicting_identity"
    assert set(row["statement"]["terms"]) == {"MONDO:0000001", "MONDO:0000002"}
    assert row["input"]["source_assertions"][0]["found"]


def test_lookup_alternatives_and_qualifier_conflicts_remain_visible():
    subject = synthetic(
        [{"name": "synthetic condition", "xrefs": ["OMIM:1"]}],
        [("OMIM:1", "MONDO:0000001"), ("OMIM:1", "MONDO:0000002")],
    )
    rel = subject.relationships("same_as")[-1]
    rel["qualifier_conflicts"] = {
        "mondo_name": ["synthetic name", "synthetic alternative"]
    }
    answer = subject.explain_disease("MONDO:0000002")
    assert answer["status"] == "partial"
    (path,) = answer["statements"][0]["identity"]
    assert len(path["links"]) == len(path["alternatives"]) == 1
    assert (
        path["links"][0]["relationship"]["qualifier_conflicts"]
        == rel["qualifier_conflicts"]
    )
    assert path["alternatives"][0]["selected"] is False
    assert any(g["reason"] == "ambiguous_stored_identity" for g in answer["gaps"])


def test_field_selection_alternatives_are_context_not_selected_members(public_card):
    subject = Card.from_dict(public_card.to_dict())
    node = subject.get("annotations.disease")
    alternative = deepcopy(
        subject.source_assertion_store.get(node["source_assertion_ids"][0])
    )
    alternative["id"] += "_synthetic_alternative"
    alternative["asserted_value"]["name"] = "synthetic competing annotation"
    subject.source_assertion_store.add(alternative)
    subject.quality.setdefault("conflicts", []).append(
        {"field": "annotations.disease", "synthetic_alternative": alternative["id"]}
    )
    answer = subject.explain_disease(TERM)
    field = next(
        f
        for f in answer["field_context"]["fields"]
        if f["field_path"] == "annotations.disease"
    )
    assert field["alternatives"][0]["id"] == alternative["id"]
    assert field["conflicts"][0]["synthetic_alternative"] == alternative["id"]
    assert alternative["id"] not in {
        a["id"] for r in answer["statements"] for a in r["input"]["source_assertions"]
    }


def test_missing_group_unqueried_identity_and_argument_validation(public_card):
    answer = public_card.explain_disease("MONDO:9999999")
    assert (answer["status"], answer["reason"]) == (
        "not_on_card",
        "no_stored_disease_group",
    )
    subject = synthetic([{"name": "synthetic condition", "xrefs": ["OMIM:1"]}])
    subject.quality.clear()
    assert (
        subject.explain_disease("MONDO:0000001")["ungrouped_context"]["statements"][0][
            "statement"
        ]["reason"]
        == "identity_not_queried"
    )
    assert public_card.explain_disease(
        " mondo:mondo:0014221 "
    ) == public_card.explain_disease(TERM)
    for invalid in (None, "doid:DOID:0050884", "MONDO:1", "TPI deficiency", 14221):
        with pytest.raises(ArgumentError):
            public_card.explain_disease(invalid)
    with pytest.raises(argdigest.UnknownArgumentError):
        public_card.explain_disease(TERM, surprise=True)
    with pytest.raises(StorageError):
        Card().explain_disease(TERM)
