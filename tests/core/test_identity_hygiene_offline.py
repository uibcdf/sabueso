"""Identity hygiene: redundant entries, strain variants, paralogs, named anchors (#55).

Real UniProt search responses (release 2026_03):

- two Trichomonas vaginalis entries, A2FT29 and A2EGX9, are paralogs: distinct TrichDB
  loci, 4 of 252 positions different;
- human P60174, V9HWK1 and Q53HE2 are one gene, with identical or near-identical
  sequences, and U3KPZ0, U3KPS5 and U3KQF3 are fragments of that gene;
- T. cruzi P52270 and Q4DV43 (strain CL Brener) differ in 4 of 251 positions.
"""

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.identity_audit import IDENTITY_RULE, compare
from sabueso.resolver import (
    EntityQuery,
    EntityResolver,
    FixtureRCSBClient,
    FixtureUniProtClient,
)

TIM = "triosephosphate isomerase"


@pytest.fixture(scope="module")
def resolver():
    return EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )


def _findings(resolution):
    return {
        tuple(f["refs"]): (f["finding"], f["basis"])
        for f in resolution.decision["identity_audit"]
    }


def test_near_identical_paralogs_are_distinct_genes(resolver):
    resolution = resolver.resolve(
        EntityQuery(name=TIM, organism=5722, include_subtaxa=True)
    )
    # Neither is reviewed: the choice is not Sabueso's to make.
    assert resolution.status == "ambiguous"
    ((refs, (finding, basis)),) = _findings(resolution).items()
    assert refs == ("uniprot:A2FT29", "uniprot:A2EGX9")
    assert finding == "distinct_genes"
    assert (basis["sequence"], basis["differences"], basis["length"]) == (
        "near_identical",
        4,
        252,
    )
    assert not resolution.identity_links


def test_redundant_entries_are_flagged_and_fragments_are_one_gene(resolver):
    resolution = resolver.resolve(EntityQuery(name=TIM, organism=9606))
    assert resolution.status == "resolved"
    found = _findings(resolution)
    assert found[("uniprot:P60174", "uniprot:V9HWK1")][0] == "possibly_same_as"
    finding, basis = found[("uniprot:P60174", "uniprot:Q53HE2")]
    assert finding == "possibly_same_as" and basis["differences"] == 1
    finding, basis = found[("uniprot:P60174", "uniprot:U3KPS5")]
    assert finding == "same_gene" and basis["lengths"] == [249, 38]
    # The resolved card links to the flagged alternatives, nothing more; nothing merged.
    assert {link["object_ref"] for link in resolution.identity_links} == {
        "uniprot:V9HWK1",
        "uniprot:Q53HE2",
    }
    assert all(
        link["derivation"]["rule"] == IDENTITY_RULE
        for link in resolution.identity_links
    )


def test_a_strain_entry_is_compared_with_its_species(resolver):
    resolution = resolver.resolve(
        EntityQuery(name=TIM, organism=5693, include_subtaxa=True)
    )
    finding, basis = _findings(resolution)[("uniprot:P52270", "uniprot:Q4DV43")]
    assert finding == "possibly_same_as"
    assert (basis["differences"], basis["length"]) == (4, 251)


def _basis(ref, taxon, organism, loci=(), sequence="MAAA", lineage=()):
    return {
        "ref": ref,
        "taxon_id": taxon,
        "organism": organism,
        "lineage": list(lineage),
        "gene_loci": sorted(loci),
        "sequence": sequence,
        "md5": None,
    }


def test_the_rule_in_isolation():
    # Unrelated organisms: never compared, identical sequences included.
    assert compare(_basis("a", 1, "X"), _basis("b", 2, "Y")) is None
    # Different lengths: not compared (alignment belongs to MolSysMT).
    assert (
        compare(
            _basis("a", 1, "X", sequence="MAAA"), _basis("b", 1, "X", sequence="MAAAA")
        )
        is None
    )
    # Distinct loci of one genome with an identical sequence: still two genes.
    found = compare(
        _basis("a", 1, "X", loci=[("DB", "g1")]),
        _basis("b", 1, "X", loci=[("DB", "g2")]),
    )
    assert (
        found["finding"] == "distinct_genes"
        and found["basis"]["sequence"] == "identical"
    )
    # Distinct loci in two strain genomes: loci decide nothing, the sequence flags.
    found = compare(
        _basis("a", 1, "X", loci=[("DB", "g1")]),
        _basis("b", 2, "X (strain S)", loci=[("DB", "g9")]),
    )
    assert found["finding"] == "possibly_same_as"
    # More than 2% of positions different: no flag.
    assert (
        compare(
            _basis("a", 1, "X", sequence="MAAAAAAAAA"),
            _basis("b", 1, "X", sequence="MAAAAAAACC"),
        )
        is None
    )


def test_a_deck_audit_compares_its_protein_cards():
    def card(accession, taxon, organism, loci, sequence):
        return Card(
            meta={
                "card_id": f"sabueso:protein:uniprot:{accession}",
                "entity_type": "protein",
            },
            sections={
                "annotations": {
                    "taxon_id": {"value": taxon, "source_assertion_ids": []},
                    "organism": {"value": organism, "source_assertion_ids": []},
                },
                "identifiers": {
                    "gene_loci": {
                        "value": [{"database": d, "id": i} for d, i in loci],
                        "source_assertion_ids": [],
                    }
                },
                "sequence": {
                    "primary": {"value": sequence, "source_assertion_ids": []}
                },
            },
        )

    deck = Deck(
        [
            card("Q1", 5, "X", [("DB", "g1")], "MKTA"),
            card("Q2", 5, "X", [("DB", "g2")], "MKTA"),
            card("Q3", 6, "Y", [], "MKTA"),
        ]
    )
    report = deck.identity_audit()
    assert report["derivation"]["rule"] == IDENTITY_RULE
    ((finding),) = report["findings"]
    assert finding["finding"] == "distinct_genes"


def test_a_curated_name_anchors_resolution(resolver, tmp_path):
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.add_literature_assertion(
        "names.synonyms",
        {"name": "TcTIM"},
        "pubmed:8061610",
        "curator-a",
        locator="Title",
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)

    anchored, resolution = sabueso.resolve(
        EntityQuery(name="tctim", organism=5693), resolver=resolver, curations=store
    )
    assert anchored.id == "sabueso:protein:uniprot:P52270"
    assert resolution.decision["rules"][0] == "curated_name"
    (support,) = resolution.decision["curated_name"]["designates"]["uniprot:P52270"]
    assert support["publication"] == "pubmed:8061610"
    # The curated name designates a T. cruzi entry: it does not answer a human query.
    other, resolution = sabueso.resolve(
        EntityQuery(name="TcTIM", organism=9606), resolver=resolver, curations=store
    )
    assert resolution.decision["rules"][0] == "curated_name_other_organism"

    # Once retracted, the name is no longer an anchor.
    (record,) = store.records()
    store.retract(record["source_assertion_id"], "wrong paper", "curator-b")
    assert store.entities_named("TcTIM") == {}


def test_a_name_curated_for_two_entries_is_ambiguous(resolver, tmp_path):
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    for accession in ("P52270", "P60174"):
        card, _ = sabueso.resolve(accession, resolver=resolver)
        card.add_literature_assertion(
            "names.synonyms", {"name": "TIM"}, "pubmed:1", "curator-a"
        )
        store.save(card)
    card, resolution = sabueso.resolve(
        EntityQuery(name="TIM"), resolver=resolver, curations=store
    )
    assert card is None and resolution.status == "ambiguous"
    assert resolution.decision["rules"] == ["curated_name_ambiguous"]
    assert {c["entity_ref"] for c in resolution.candidates} == {
        "uniprot:P52270",
        "uniprot:P60174",
    }


def test_the_same_statement_about_two_entities_is_two_records(resolver, tmp_path):
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    ids = []
    for accession in ("P52270", "P60174"):
        card, _ = sabueso.resolve(accession, resolver=resolver)
        record = card.add_literature_assertion(
            "annotations.subunit", "Homodimer", "pubmed:1", "curator-a"
        )
        ids.append(record["source_assertion_id"])
        assert store.save(card)["added"] == 1
    assert ids[0] != ids[1]
    assert {r["entity"] for r in store.records()} == {
        "uniprot:P52270",
        "uniprot:P60174",
    }


def _legacy_store(resolver, tmp_path):
    """A store as releases up to 0.2.0 wrote it: curated ids without the subject."""
    import json

    from sabueso.core.curation import legacy_curated_id

    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.add_literature_assertion(
        "annotations.subunit", "Homodimer", "pubmed:1", "curator-a", locator="Fig. 2"
    )
    store = sabueso.CurationStore(tmp_path / "curation.jsonl")
    store.save(card)
    (record,) = store.records()
    assertion = card.source_assertion_store.get(record["source_assertion_id"])
    record["source_assertion_id"] = legacy_curated_id(assertion)
    del record["id_scheme"]
    store._write([record])
    return store, record["source_assertion_id"]


def test_a_legacy_record_is_reidentified_when_applied(resolver, tmp_path):
    store, old_id = _legacy_store(resolver, tmp_path)
    card, _ = sabueso.resolve("P52270", resolver=resolver, curations=store)
    assert card.quality["curation_store"]["migrated"] == 1
    (record,) = store.records()
    assert record["previous_ids"] == [old_id]
    assert record["source_assertion_id"] != old_id
    assert card.source_assertion_store.get(record["source_assertion_id"]) is not None
    # Applying again finds nothing left to migrate; the old id still retracts it.
    again, _ = sabueso.resolve("P52270", resolver=resolver, curations=store)
    assert "migrated" not in again.quality["curation_store"]
    store.retract(old_id, "test", "curator-b")
    assert store.records()[0]["retracted"]["reason"] == "test"


def test_a_legacy_record_is_reidentified_when_the_card_is_saved(resolver, tmp_path):
    store, old_id = _legacy_store(resolver, tmp_path)
    card, _ = sabueso.resolve("P52270", resolver=resolver)
    card.add_literature_assertion(
        "annotations.subunit", "Homodimer", "pubmed:1", "curator-a", locator="Fig. 2"
    )
    summary = store.save(card)
    assert (summary["added"], summary["migrated"], summary["total"]) == (0, 1, 1)
    assert store.records()[0]["previous_ids"] == [old_id]
