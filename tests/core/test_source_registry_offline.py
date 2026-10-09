"""The source registry (devguide/sources/registry.yaml) and its generated page."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "source_registry", "tools/source_registry.py"
)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


@pytest.fixture(scope="module")
def data():
    return registry.load()


def test_the_registry_is_valid(data):
    assert registry.problems(data) == []


def test_shared_source_terms_have_an_explicit_order_independent_owner(data):
    expected = json.loads(registry.terms_export(data))["sources"]["UniProt"]
    reordered = copy.deepcopy(data)
    reordered["resources"].reverse()
    assert (
        json.loads(registry.terms_export(reordered))["sources"]["UniProt"] == expected
    )
    assert expected["registry_id"] == "uniprot"
    assert expected["attribution"] == (
        "UniProt Consortium (https://www.uniprot.org/), CC BY 4.0"
    )


def test_an_undeclared_shared_source_collision_is_refused(data):
    broken = copy.deepcopy(data)
    alias = next(r for r in broken["resources"] if r["id"] == "uniref")
    alias["terms"].pop("shared_with", None)
    assert any("multiple terms owners" in p for p in registry.problems(broken))
    with pytest.raises(ValueError, match="multiple terms owners"):
        registry.terms_export(broken)


@pytest.mark.parametrize(
    "field,value",
    [
        ("licence", "CC0-1.0"),
        ("attribution", "A different provider"),
        ("statement", "https://example.org/terms"),
        ("reviewed", "2026-01-01"),
        ("retention_licence", "CC0-1.0"),
        ("caveats", ["Different restrictions"]),
        ("depositors", {"Another source": "ChEMBL"}),
    ],
)
def test_shared_source_terms_cannot_override_the_owner(data, field, value):
    broken = copy.deepcopy(data)
    alias = next(r for r in broken["resources"] if r["id"] == "uniref")
    alias["terms"][field] = value
    with pytest.raises(ValueError, match="shared terms differ"):
        registry.terms_export(broken)
    assert any("shared terms differ" in p for p in registry.problems(broken))


@pytest.mark.parametrize("owner", ["nowhere", "uniref", "aaindex", [], ""])
def test_shared_source_terms_require_one_direct_matching_owner(data, owner):
    broken = copy.deepcopy(data)
    alias = next(r for r in broken["resources"] if r["id"] == "uniref")
    alias["terms"]["shared_with"] = owner
    with pytest.raises(ValueError, match="shared terms owner"):
        registry.terms_export(broken)


def test_shared_source_terms_refuse_chains_or_cycles(data):
    broken = copy.deepcopy(data)
    owner = next(r for r in broken["resources"] if r["id"] == "uniprot")
    owner["terms"]["shared_with"] = "uniref"
    with pytest.raises(ValueError, match="shared terms owner"):
        registry.terms_export(broken)


@pytest.mark.parametrize("names", ["UniProt", [], [""], ["UniProt", "UniProt"], [{}]])
def test_invalid_owner_source_names_are_refused_even_before_its_row(data, names):
    broken = copy.deepcopy(data)
    owner = next(r for r in broken["resources"] if r["id"] == "uniprot")
    owner["terms"]["source_names"] = names
    broken["resources"].reverse()
    with pytest.raises(ValueError, match="source_names"):
        registry.terms_export(broken)


def test_duplicate_resource_ids_cannot_hide_a_terms_owner(data):
    broken = copy.deepcopy(data)
    owner = next(r for r in broken["resources"] if r["id"] == "uniprot")
    broken["resources"].append(copy.deepcopy(owner))
    with pytest.raises(ValueError, match="Duplicated resource ids"):
        registry.terms_export(broken)


def test_the_page_is_generated_from_the_registry(data):
    page = Path("docs/content/user/data_sources.md").read_text(encoding="utf-8")
    assert page == registry.render(data), "run: python tools/source_registry.py --write"


def test_packaged_catalog_preserves_all_decisions_and_separates_profile_statuses(
    data, monkeypatch
):
    from sabueso.tools.db import _http
    from sabueso.tools.sources import get_catalog

    def forbidden(*args, **kwargs):
        raise AssertionError("Reading source metadata must not acquire data")

    monkeypatch.setattr(_http, "urlopen", forbidden)
    expected = json.loads(registry.catalog_export(data))
    catalog = get_catalog()
    assert catalog == expected
    assert Path("sabueso/resolver/source_catalog.json").read_text(
        encoding="utf-8"
    ) == registry.catalog_export(data)
    by_id = {r["id"]: r for r in catalog["resources"]}
    assert len(by_id) == len(data["resources"])
    assert {r["status"] for r in by_id.values()} >= {
        "in_use",
        "deferred",
        "retired",
        "evaluating",
        "out_of_scope",
    }
    for profile in catalog["profiles"].values():
        assert all(by_id[r]["status"] == "in_use" for r in profile["in_use"])
        assert all(
            by_id[r]["status"] == status
            for status, members in profile["other_statuses"].items()
            for r in members
        )
    assert by_id["alphamissense"]["limit"]["value"] == 10000
    assert by_id["mobidb"]["module"] == [
        "sabueso.tools.db.mobidb",
        "sabueso.mappings.mobidb",
    ]
    assert "verified" not in catalog["profiles"]
    catalog["resources"].clear()
    assert get_catalog() == expected


def test_every_source_module_is_in_use(data):
    in_use = {
        m for r in data["resources"] if r["status"] == "in_use" for m in r["module"]
    }
    assert "sabueso.tools.db.alphafold" in in_use


def test_capabilities_distinguish_native_access_from_declared_card_contribution(data):
    capabilities = registry.capability_inventory(data)
    rows = capabilities["resources"]
    assert rows["mobidb"]["get_functions"]
    assert rows["mobidb"]["mapping_functions"]
    assert rows["mobidb"]["declared_enrichers"] == []
    assert rows["clinvar"]["declared_enrichers"]
    assert rows["asd"]["adoption_status"] == "deferred"
    assert rows["asd"]["get_functions"] == []
    assert all(
        r["live_health"] == "not_assessed_by_offline_inventory" for r in rows.values()
    )
    assert all(
        r["consumer_acceptance"] == "not_assessed_by_offline_inventory"
        for r in rows.values()
    )


def test_capabilities_keep_file_specific_public_local_scope_and_enricher_ownership(
    data,
):
    from sabueso.enrichers import ENRICHERS

    rows = registry.capability_inventory(data)["resources"]
    assert rows["hpo"]["recovery_inputs"]["local_only"]
    assert rows["hpo"]["recovery_inputs"]["repository"] == []
    assert rows["civic"]["recovery_inputs"]["repository"]
    assert rows["civic"]["recovery_inputs"]["local_only"] == []
    assert sum(len(row["declared_enrichers"]) for row in rows.values()) == len(
        ENRICHERS
    )
    for enricher in ENRICHERS:
        assert any(
            e["option"] == enricher.option and e["areas"] == list(enricher.areas)
            for e in rows[enricher.registry_id]["declared_enrichers"]
        )


def test_capability_page_is_current_and_readers_are_detached_without_source_access(
    data, monkeypatch
):
    from sabueso.tools.db import _http
    from sabueso.tools.sources import get_catalog

    def forbidden(*args, **kwargs):
        raise AssertionError("Capability inspection must not acquire a source")

    monkeypatch.setattr(_http, "_urlopen", forbidden)
    assert registry.CAPABILITIES_PAGE.read_text(
        encoding="utf-8"
    ) == registry.render_capabilities(data)
    expected = get_catalog()["capabilities"]
    changed = get_catalog()
    changed["capabilities"]["resources"]["hpo"]["recovery_inputs"]["local_only"].clear()
    assert get_catalog()["capabilities"] == expected
    assert "Code declarations do not establish scientific completeness" in " ".join(
        expected["limits"]
    )


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda r: r.update(status="deferred", revisit_when=None), "revisit_when"),
        (lambda r: r.update(status="rejected", reason=None), "reason"),
        (lambda r: r.update(status="out_of_scope", owner=None), "owner"),
        (lambda r: r.update(status="unknown"), "unknown status"),
        (lambda r: r.update(category="nowhere"), "unknown category"),
        (lambda r: r.update(colour="blue"), "unknown keys"),
        (lambda r: r.update(module=["sabueso.tools.db.nowhere"]), "does not exist"),
        (lambda r: r.update(limit={"constant": "x.Y"}), "what it counts"),
        (lambda r: r.update(requires=["a_wish"]), "requires is a list"),
        (lambda r: r.update(requires=["key"], requires_note=None), "requires_note"),
        (
            lambda r: r.update(limit={"constant": "sabueso.nowhere.LIMIT", "of": "x"}),
            "is not an int",
        ),
    ],
)
def test_a_decision_without_its_basis_is_refused(data, change, message):
    broken = copy.deepcopy(data)
    (entry,) = [r for r in broken["resources"] if r["id"] == "biogrid"]
    change(entry)
    assert any(message in p for p in registry.problems(broken))


def test_an_unregistered_source_module_is_refused(data):
    broken = copy.deepcopy(data)
    broken["resources"] = [r for r in broken["resources"] if r["id"] != "alphafold_db"]
    assert "sabueso.tools.db.alphafold is not registered as an in_use resource" in (
        registry.problems(broken)
    )


def test_the_page_states_each_ceiling_as_the_code_holds_it(data):
    from sabueso.tools.db import open_targets

    page = registry.render(data)
    assert f"| Open Targets Platform | {open_targets.DEFAULT_LIMIT} |" in page
    assert "Blocked: its site did not answer" in page  # an evaluation's state
