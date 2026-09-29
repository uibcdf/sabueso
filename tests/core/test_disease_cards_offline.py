"""Disease cards: one disease across terminologies, joined only through MONDO's stated
equivalences (#90). Frozen MONDO terms of release v2026-09-01."""

import json

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.tools.db.mondo import (
    FixtureMONDOClient,
    get_term,
    normalize,
    parse_release,
)

TPI_DEFICIENCY = "sabueso:disease:mondo:MONDO:0014221"


@pytest.fixture(scope="module")
def mondo():
    return FixtureMONDOClient("temp_data")


def _resolve(query, mondo, **options):
    return sabueso.resolve(query, mondo_client=mondo, **options)


@pytest.mark.parametrize(
    "query",
    [
        "mondo:MONDO:0014221",
        "MONDO:0014221",
        "MONDO_0014221",
        "doid:DOID:0050884",
        "DOID:0050884",
        "orphanet:868",
        "ORPHA:868",
        "omim:615512",
        "mesh:C566029",
    ],
)
def test_every_stated_equivalent_resolves_to_one_disease(query, mondo):
    card, resolution = _resolve(query, mondo)
    assert resolution.status == "resolved"
    assert card.id == TPI_DEFICIENCY
    assert resolution.decision["route"]["entity_type"] == "disease"
    if not query.upper().startswith("MONDO"):
        identity = resolution.decision["identity"]
        assert identity["rule"] == "mondo_equivalence@1"
        assert (identity["stated_by"], identity["release"]) == ("MONDO", "2026-09-01")
        assert identity["mondo"] == "MONDO:0014221"


def test_the_card_holds_what_mondo_states(mondo):
    card, _ = _resolve("ORPHA:868", mondo)
    assert card.meta["entity_type"] == "disease"
    assert card.get("names.canonical_name")["value"] == (
        "triosephosphate isomerase deficiency"
    )
    equivalent = card.get("identifiers.equivalent_ids")["value"]
    assert {"DOID:0050884", "Orphanet:868", "OMIM:615512"} <= set(equivalent)
    related = card.get("identifiers.related_ids") or {"value": []}
    assert not set(related["value"]) & set(equivalent)
    parents = {r["object_ref"] for r in card.relationships("subclass_of")}
    assert "mondo:MONDO:0002908" in parents
    assert all(r["source_assertion_ids"] for r in card.relationships("subclass_of"))
    assert card.get("annotations.definition")["value"]["text"]


def test_a_related_xref_is_never_identity(mondo):
    # MONDO lists EFO:0001360 for type 2 diabetes only as the source of other xrefs,
    # not as an equivalent: it does not resolve.
    card, resolution = _resolve("efo:EFO:0001360", mondo)
    assert card is None
    assert resolution.status == "not_found"
    assert resolution.decision["rules"] == ["no_stated_equivalence"]


def test_an_obsolete_term_names_its_replacement_but_is_not_followed(mondo):
    card, resolution = _resolve("MONDO:0000002", mondo)
    assert card is None and resolution.status == "obsolete"
    assert [c["entity_ref"] for c in resolution.candidates] == [
        "sabueso:disease:mondo:MONDO:0009299"
    ]
    assert resolution.candidates[0]["basis"] == {
        "stated_by": "MONDO",
        "replaced_by": "MONDO:0009299",
    }


def test_ids_of_other_entities_in_shared_namespaces_are_not_found(mondo):
    # OMIM also numbers genes (190450 is TPI1): no MONDO equivalence, never a disease.
    card, resolution = _resolve("omim:190450", mondo)
    assert card is None and resolution.status == "not_found"


def test_proteins_and_molecules_keep_their_routes():
    from sabueso.tools.resolve import _route

    assert _route("P60174", None)[0] == "protein"
    assert _route("pdb:1HTI", None)[0] == "protein"
    assert _route("TPIS_HUMAN", None)[0] == "protein"
    assert _route("chembl:CHEMBL25", None)[0] == "small_molecule"
    assert _route("doid:9352", None)[0] == "disease"


def test_a_failing_source_is_an_error_not_an_absence():
    card, resolution = _resolve(
        "ORPHA:868", FixtureMONDOClient("temp_data", failing={"Orphanet:868"})
    )
    assert card is None and resolution.status == "error"


def test_the_card_survives_storage_and_migration(mondo, tmp_path):
    card, _ = _resolve("ORPHA:868", mondo)
    data = json.loads(json.dumps(card.to_dict()))
    assert Card.from_dict(data).id == TPI_DEFICIENCY
    store = sabueso.KnowledgeStore(tmp_path / "k.db")
    ref = store.save(card)
    assert store.load(ref).get("identifiers.mondo")["value"] == "MONDO:0014221"
    report = sabueso.migrate_card(data)
    assert report.quality["migration"][-1]["steps"] == []


def test_normalization_of_the_forms_sources_write():
    assert normalize("efo:EFO:0008559") == "EFO:0008559"
    assert normalize("EFO_0008559") == "EFO:0008559"
    assert normalize("mondo:MONDO:0001444") == "MONDO:0001444"
    assert normalize("ORPHA:868") == "Orphanet:868"
    assert normalize("mesh:D003924") == "MESH:D003924"
    assert normalize("uniprot:P60174") is None
    assert normalize("P60174") is None


def test_only_equivalent_xrefs_enter_the_index():
    text = (
        "format-version: 1.2\ndata-version: releases/2026-01-01\n\n[Term]\n"
        "id: MONDO:1\nname: a disease\n"
        'xref: DOID:1 {source="MONDO:equivalentTo"}\n'
        'xref: GARD:1 {source="MONDO:GARD"}\n'
    )
    version, terms, equivalents = parse_release(text)
    assert version == "2026-01-01"
    assert equivalents == {"DOID:1": "MONDO:1"}
    assert [x["equivalent"] for x in terms["MONDO:1"]["xrefs"]] == [True, False]


def test_the_public_function_and_the_entity_type(mondo):
    result = get_term("MONDO:0001444", client=mondo)
    assert result["source"] == "MONDO" and result["version"] == "2026-09-01"
    assert result["record"]["name"] == "Chagas disease"
    card, _ = sabueso.resolve(
        "MONDO:0001444", entity_type="disease", mondo_client=mondo
    )
    assert card.get("names.canonical_name")["value"] == "Chagas disease"
    with pytest.raises(ArgumentError):
        sabueso.resolve("MONDO:0001444", entity_type="illness")
