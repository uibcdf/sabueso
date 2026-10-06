"""Native disease membership support survives storage, exports and advanced heads."""

from copy import deepcopy

import ackredit
import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.deck import Deck
from sabueso.core.errors import StorageError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.mondo import FixtureMONDOClient
from sabueso.tools.db.open_targets import FixtureOpenTargetsClient
from sabueso.tools.db.orphadata import FixtureOrphadataClient
from sabueso.tools.db.pdb_ccd import FixtureCCDClient
from sabueso.tools.db.unichem import FixtureUniChemClient


@pytest.fixture(scope="module")
def results():
    mondo = FixtureMONDOClient("temp_data", retrieved_at="original source observation")
    disease, _ = sabueso.resolve("ORPHA:868", mondo_client=mondo)
    before = disease.to_dict()
    with pytest.warns(Warning):
        targets = sabueso.disease_targets(
            disease,
            limit=3,
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            open_targets_client=FixtureOpenTargetsClient(
                "temp_data", retrieved_at="original source observation"
            ),
            orphadata_client=FixtureOrphadataClient(
                "temp_data", retrieved_at="original source observation"
            ),
        )
    drugs = sabueso.disease_drugs(
        "mesh:D014355",
        limit=3,
        mondo_client=mondo,
        chembl_client=FixtureChEMBLClient(
            "temp_data", retrieved_at="original source observation"
        ),
        ccd_client=FixtureCCDClient("temp_data"),
        unichem_client=FixtureUniChemClient("temp_data"),
    )
    assert disease.to_dict() == before
    return {"targets": targets, "drugs": drugs}


def entries(answer):
    for row in answer["support"]["statements"]:
        for group in (
            "source_assertion_refs",
            "identity_source_assertion_refs",
            "member_identity_source_assertion_refs",
        ):
            yield from row[group]


@pytest.mark.parametrize("kind", ["targets", "drugs"])
def test_membership_carries_native_rows_original_identity_and_versioned_derivation(
    results, kind
):
    deck = results[kind]
    answer = deck.explain(deck.cards[0].id)
    support = answer["support"]
    assert support["rule"] == "disease_deck_explanation@1"
    assert support["status"] == "recorded" and not support["gaps"]
    assert answer["basis"]["derivation"]["rule"] == f"disease_{kind}@2"
    assert (
        answer["basis"]["derivation"]["parameters"]["identity"] == "source_stated_only"
    )
    assert all(item["found"] for item in entries(answer))
    assert answer["basis"]["member_card_ref"] == deck.cards[0].pinned_ref()
    native = support["statements"][0]["source_assertion_refs"]
    assert all(
        item["assertion"]["retrieved_at"] == "original source observation"
        for item in native
    )
    assert all(
        item["assertion"]["acquisition"] == {"method": "database"} for item in native
    )
    assert all("derivation" not in item["assertion"] for item in native)
    if kind == "targets":
        by_source = {
            item["assertion"]["source"]["name"]: item["assertion"]
            for item in native
            if "rows" not in item["assertion"]["asserted_value"]
        }
        ot = by_source["Open Targets"]
        row = ot["asserted_value"]["row"]
        assert ot["source"]["version"] == "26.09"
        assert row["datatypeScores"] and row["target"]["id"] == "ENSG00000111669"
        response = next(
            item["assertion"]["asserted_value"]
            for item in native
            if "rows" in item["assertion"]["asserted_value"]
        )
        assert response["count"] == 252 and len(response["rows"]) == 20
        assert response["rows"][0] == row
        assert {p["source"] for p in row["target"]["proteinIds"]} >= {
            "uniprot_swissprot",
            "uniprot_trembl",
        }
        assert by_source["Orphanet"]["asserted_value"]["uniprot"] == "P60174"
        assert (
            by_source["Orphanet"]["asserted_value"]
            == FixtureOrphadataClient("temp_data").genes("868")["record"][0]
        )
    else:
        assert len(native) == 2
        assert {item["assertion"]["source"]["version"] for item in native} == {
            "ChEMBL_37"
        }
        assert all(
            item["assertion"]["asserted_value"]["indication_refs"] for item in native
        )


def test_unbuilt_and_capped_candidates_keep_their_original_support(results):
    deck = results["targets"]
    assert {e["reason"] for e in deck.meta["excluded"]} >= {"card_not_built", "limit"}
    for exclusion in deck.meta["excluded"]:
        answer = deck.explain(exclusion["candidate"])
        assert not answer["in_deck"]
        assert answer["support"]["status"] == "recorded"
        assert all(item["found"] for item in entries(answer))
        assert answer["support"]["statements"][0]["basis"]["candidate_refs"] == [
            exclusion["candidate"]
        ]


def test_deck_terms_include_embedded_native_sources_and_original_identity(results):
    targets = results["targets"].terms("redistribution")
    drugs = results["drugs"].terms("redistribution")
    assert targets["rule"] == drugs["rule"] == "disease_deck_terms@1"
    assert {"UniProt", "MONDO", "Open Targets", "Orphanet"} <= set(targets["sources"])
    assert {"MONDO", "ChEMBL"} <= set(drugs["sources"])
    assert targets["scope"] == "members_and_all_embedded_disease_support"
    admitted = results["targets"].admissible("redistribution")
    assert admitted.cards == results["targets"].cards
    assert admitted.meta["admission"]["rule"] == "disease_deck_admission@1"


def test_ordinary_deck_admission_preserves_unrelated_support_metadata(results):
    deck = Deck([results["targets"].cards[0]], meta={"support": ["curator note"]})
    admitted = deck.admissible("redistribution")
    assert admitted.cards == deck.cards
    assert admitted.meta["support"] == ["curator note"]


@pytest.mark.parametrize("kind", ["targets", "drugs"])
def test_save_deck_alone_preserves_every_native_item_and_original_input_after_new_heads(
    results, kind, tmp_path, monkeypatch
):
    original = results[kind]
    store = sabueso.KnowledgeStore(tmp_path / "knowledge.db")
    pin = store.save_deck(original, kind)
    expected = original.explain(original.cards[0].id)
    later = deepcopy(original)
    for role in ("input", "assertions"):
        card = Card.from_dict(later.meta["support"][role]["card"])
        card.meta["later_observation"] = True
        store.save(card)
    for member in later.cards:
        member.meta["later_observation"] = True
        store.save(member)

    def forbidden(*args, **kwargs):
        pytest.fail("saved explanations must not acquire or credit")

    monkeypatch.setattr(sabueso, "resolve", forbidden)
    monkeypatch.setattr(ackredit, "register_item", forbidden)
    monkeypatch.setattr(ackredit, "track_item", forbidden)
    loaded = store.load_deck(pin)
    with ackredit.session("inert disease membership explanation"):
        before = ackredit.get_attribution().to_dict()
        answer = loaded.explain(loaded.cards[0].id)
        assert answer == expected
        assert ackredit.get_attribution().to_dict() == before
    assert (
        store.load(answer["support"]["input_card_ref"]).pinned_ref()
        == answer["basis"]["input_card_ref"]
    )
    for item in entries(answer):
        assert store.source_assertion(item["source_assertion_ref"]) == item["assertion"]


@pytest.mark.parametrize("kind", ["targets", "drugs"])
@pytest.mark.parametrize("format", ["jsonl", "sqlite"])
def test_export_keeps_support_and_can_be_imported_into_an_empty_store(
    results, kind, format, tmp_path
):
    original = results[kind]
    path = tmp_path / f"deck.{format}"
    getattr(original, f"to_{format}")(str(path))
    loaded = getattr(Deck, f"from_{format}")(str(path))
    assert loaded.snapshot_id() == original.snapshot_id()
    store = sabueso.KnowledgeStore(tmp_path / "reimport.db")
    pin = store.save_deck(loaded, "reimport")
    answer = store.load_deck(pin).explain(loaded.cards[0].id)
    assert answer == original.explain(original.cards[0].id)
    assert all(
        store.source_assertion(item["source_assertion_ref"]) == item["assertion"]
        for item in entries(answer)
    )


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "wrong_candidate",
        "wrong_input",
        "wrong_member",
        "identity",
        "rank",
        "score",
    ],
)
def test_incomplete_or_misbound_support_is_explicitly_partial(results, defect):
    deck = deepcopy(results["targets"])
    basis = deck.basis(deck.cards[0].id)
    if defect == "missing":
        basis["source_assertion_refs"][0] = basis["input_card_ref"] + "#SA_missing"
    elif defect == "wrong_candidate":
        basis["candidate_refs"] = ["uniprot:Q00000"]
    elif defect == "wrong_input":
        basis["input_card_ref"] = deck.cards[0].pinned_ref()
    elif defect == "wrong_member":
        basis["member_card_ref"] = basis["input_card_ref"]
    elif defect == "identity":
        basis["identity_source_assertion_refs"] = []
    else:
        basis["statements"][0][defect] = 0
    answer = deck.explain(deck.cards[0].id)
    assert answer["support"]["status"] == "partial" and answer["support"]["gaps"]


@pytest.mark.parametrize("defect", ["pin", "format", "payload", "input_rewrite"])
def test_invalid_embedded_support_refuses_an_atomic_save(results, defect, tmp_path):
    deck = deepcopy(results["targets"])
    embedded = deck.meta["support"]
    if defect == "pin":
        embedded["input"]["card_ref"] = deck.cards[0].pinned_ref()
    elif defect == "format":
        embedded["format"] = "unknown@1"
    elif defect == "payload":
        embedded["assertions"].pop("card")
    else:
        card = Card.from_dict(embedded["assertions"]["card"])
        card.meta["changed_original_input"] = True
        embedded["assertions"] = {"card": card.to_dict(), "card_ref": card.pinned_ref()}
    store = sabueso.KnowledgeStore(tmp_path / "invalid.db")
    with pytest.raises(StorageError):
        store.save_deck(deck, "invalid")
    assert not store.card_ids() and not store.deck_names()


def test_legacy_metadata_is_readable_without_invented_support(results, tmp_path):
    current = results["targets"]
    legacy = Deck(
        current.cards,
        meta={
            "kind": "disease_targets",
            "rule": "disease_targets@1",
            "membership": {
                current.cards[0].id: {
                    "rule": "disease_targets@1",
                    "statements": [{"source": "Open Targets", "score": 0.5}],
                }
            },
        },
    )
    store = sabueso.KnowledgeStore(tmp_path / "legacy.db")
    pin = store.save_deck(legacy, "legacy")
    loaded = store.load_deck(pin)
    assert loaded.snapshot_id() == legacy.snapshot_id()
    answer = loaded.explain(loaded.cards[0].id)
    assert answer["basis"] == legacy.basis(legacy.cards[0].id)
    assert answer["support"]["status"] == "not_recorded"


@pytest.mark.parametrize("failed", [False, True])
def test_empty_or_failed_drug_queries_keep_their_input_without_invented_membership(
    tmp_path, failed
):
    deck = sabueso.disease_drugs(
        "ORPHA:868",
        mondo_client=FixtureMONDOClient("temp_data"),
        chembl_client=FixtureChEMBLClient(
            "temp_data", failing={"MONDO:0014221"} if failed else set()
        ),
    )
    assert not deck.cards
    assert deck.meta["sources"][0]["status"] == ("error" if failed else "not_found")
    store = sabueso.KnowledgeStore(tmp_path / "empty.db")
    pin = store.save_deck(deck, "empty")
    loaded = store.load_deck(pin)
    assert (
        store.load(loaded.meta["support"]["input"]["card_ref"]).id
        == deck.meta["disease"]
    )
    assert loaded.explain("chembl:CHEMBL110")["support"]["status"] == "not_in_result"


def test_one_failed_source_preserves_the_other_sources_exact_support():
    with pytest.warns(Warning):
        deck = sabueso.disease_targets(
            "ORPHA:868",
            mondo_client=FixtureMONDOClient("temp_data"),
            resolver=EntityResolver(FixtureUniProtClient("temp_data")),
            open_targets_client=FixtureOpenTargetsClient(
                "temp_data", failing={"MONDO:0014221"}
            ),
            orphadata_client=FixtureOrphadataClient("temp_data"),
        )
    answer = deck.explain(deck.cards[0].id)
    assert answer["support"]["status"] == "recorded"
    assert {
        r["assertion"]["source"]["name"]
        for r in answer["support"]["statements"][0]["source_assertion_refs"]
    } == {"Orphanet"}
    assert {s["source"]: s["status"] for s in deck.meta["sources"]} == {
        "Open Targets": "error",
        "Orphanet": "added",
    }
