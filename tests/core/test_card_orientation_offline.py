"""Current orientation keeps original fields, support declarations and unknowns."""

import json
import os
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.core.source_assertion_store import make_source_assertion
from sabueso.tools.card.disease import resolve_disease_card
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db.chembl import FixtureChEMBLClient
from sabueso.tools.db.mondo import FixtureMONDOClient


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("Orientation must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


@pytest.fixture(scope="module", params=["protein", "small_molecule", "disease"])
def public_original(request):
    if request.param == "protein":
        card = Card.from_dict(
            json.loads(
                Path("temp_data/frozen_cards/schema_0.3.9__P52270.json").read_text()
            )
        )
    elif request.param == "small_molecule":
        card = single_molecule_card(
            chembl=FixtureChEMBLClient("temp_data").molecules(["CHEMBL110"])
        )
    else:
        card = resolve_disease_card(
            "MONDO:0014221", mondo_client=FixtureMONDOClient("temp_data")
        )[0]
    return card.to_dict()


def test_public_orientation_keeps_original_field_values_and_source_versions(
    public_original,
):
    card = Card.from_dict(deepcopy(public_original))
    before = card.to_dict()
    explorer = card.explore()
    overview = explorer.overview()
    original_menu = overview.native_payload
    context = overview.orientation
    assert context["rule"] == "card_orientation@1"
    assert context["card_ref"] == explorer.context["card_ref"]
    assert context["snapshot_id"] == explorer.context["snapshot_id"]
    assert context["fields_complete"] and context["scope"]
    supported = 0
    for field in context["fields"]:
        if field["value_location"] is not None:
            assert (
                explorer.inspect(locator=field["value_location"]).native_payload
                == field["value"]
            )
            raw = explorer.inspect(locator=field["field_location"]).native_payload
            assert raw["value"] == field["value"]
        for source in field["support"]["sources"]:
            if source["state"] == "present":
                record = explorer.inspect(locator=source["location"]).native_payload
                assert record["source"] == source["source"]
                supported += 1
    assert supported > 0
    context["fields"].clear()
    assert overview.orientation["fields"]
    assert overview.native_payload == original_menu
    assert card.to_dict() == before


@pytest.mark.parametrize(
    "field,expected",
    [
        ({"value": None}, "retained_null"),
        ({"value": []}, "retained_empty"),
        ({"value": ""}, "retained_empty"),
        ({"value": False}, "retained"),
        ({"value": 0}, "retained"),
        (None, "unrecognized_shape"),
    ],
)
def test_orientation_keeps_null_empty_false_zero_and_unrecognized_fields_distinct(
    field, expected
):
    card = Card(
        meta={"entity_type": "protein"}, sections={"annotations": {"function": field}}
    )
    view = card.explore().overview()
    row = next(
        row
        for row in view.orientation["fields"]
        if row["path"] == "annotations.function"
    )
    assert row["state"] == expected
    if isinstance(field, dict):
        assert row["value"] == field["value"]
        assert (
            view.explorer.inspect(locator=row["value_location"]).native_payload
            == field["value"]
        )
    assert "Card overview" in repr(view)


def synthetic_support(refs=None):
    records = [
        make_source_assertion(
            "annotations.function", value, "Synthetic source", version, version
        )
        for value, version in (("First claim", "v1"), ("Other claim", "v2"))
    ]
    for record, version in zip(records, ("v1", "v2"), strict=True):
        record["source"]["version"] = version
    references = [record["id"] for record in records] if refs is None else refs
    return Card(
        meta={"entity_type": "protein"},
        sections={
            "annotations": {
                "function": {"value": "First claim", "source_assertion_ids": references}
            }
        },
        source_assertion_store=records,
        quality={
            "conflicts": [
                {
                    "field": "annotations.function",
                    "values": ["First claim", "Other claim"],
                }
            ],
            "alternatives": [
                {
                    "field": "annotations.function",
                    "reason": "synthetic original selection",
                }
            ],
        },
    )


def function_row(view):
    return next(
        row
        for row in view.orientation["fields"]
        if row["path"] == "annotations.function"
    )


def test_versions_conflicts_and_duplicate_support_occurrences_are_not_collapsed():
    card = synthetic_support()
    field = card.sections["annotations"]["function"]
    field["source_assertion_ids"].append(field["source_assertion_ids"][0])
    view = card.explore().overview()
    row = function_row(view)
    assert row["value"] == "First claim"
    assert [source["source"]["version"] for source in row["support"]["sources"]] == [
        "v1",
        "v2",
        "v1",
    ]
    assert row["support"]["references"] == field["source_assertion_ids"]
    assert "Synthetic source [v1]" in repr(view)
    assert "Synthetic source [v2]" in repr(view)
    for key in ("conflicts", "alternatives"):
        original = view.orientation["quality"][key]
        assert original["count"] == 1
        assert (
            view.explorer.inspect(locator=original["location"]).native_payload
            == card.quality[key]
        )
        assert f"Stored {key} are present" in repr(view)


@pytest.mark.parametrize(
    "refs", [None, "SA_UNRECOGNIZED", ["SA_VALID_LOOKALIKE", False]]
)
def test_unrecognized_selected_support_never_attributes_a_valid_looking_prefix(refs):
    card = synthetic_support()
    card.sections["annotations"]["function"]["source_assertion_ids"] = refs
    view = card.explore().overview()
    support = function_row(view)["support"]
    assert support["state"] == "unrecognized_shape"
    assert support["references"] == refs and support["sources"] == []
    assert "unrecognized selection references" in repr(view)
    assert "Synthetic source" not in repr(view)


def test_missing_support_record_and_unstated_version_keep_their_original_states():
    card = synthetic_support()
    first = next(iter(card.source_assertion_store.store.values()))
    first["source"].pop("version")
    card.sections["annotations"]["function"]["source_assertion_ids"] = [
        first["id"],
        "SA_MISSING",
    ]
    view = card.explore().overview()
    sources = function_row(view)["support"]["sources"]
    assert sources[1]["state"] == "not_retained" and sources[1]["location"] is None
    assert "version" not in sources[0]["source"]
    assert "version not retained" in repr(view)
    assert "supporting record not retained" in repr(view)


def test_bounded_preview_never_copies_full_values_or_validates_a_partial_support_list():
    class PrefixOnly(list):
        def __iter__(self):
            raise AssertionError("Preview traversed the entire stored list")

        def __deepcopy__(self, memo):
            raise AssertionError("Preview copied the entire stored list")

    view = synthetic_support().explore().overview()
    field = view.explorer.access._focal.data["sections"]["annotations"]["function"]
    field["value"] = PrefixOnly(["retained claim"] * 10000)
    field["source_assertion_ids"] = PrefixOnly(["SA_UNCHECKED"] * 5 + [False])
    assert "6 declared support references; attribution not evaluated" in repr(view)
    assert (
        "6 declared support references; attribution not evaluated" in view._repr_html_()
    )


@pytest.mark.parametrize("container", [None, []])
def test_unrecognized_parent_is_inspectable_and_differs_from_a_missing_field(container):
    view = (
        Card(meta={"entity_type": "protein"}, sections={"annotations": container})
        .explore()
        .overview()
    )
    row = function_row(view)
    assert row["state"] == "unrecognized_container"
    assert row["field_location"] is None and row["value_location"] is None
    assert (
        view.explorer.inspect(locator=row["container_location"]).native_payload
        == container
    )
    missing = Card(meta={"entity_type": "protein"}).explore().overview()
    assert function_row(missing)["state"] == "not_retained"


def test_only_original_overviews_have_orientation_and_html_stays_escaped():
    card = synthetic_support()
    card.sections["names"] = {"canonical_name": {"value": "<script>name</script>"}}
    card.sections["annotations"]["function"]["value"] = "<script>claim</script>"
    view = card.explore().overview()
    html = view._repr_html_()
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert view.orientation == view.table().orientation
    assert view.explorer.questions().orientation is None
    assert view.explorer.view("function").orientation is None
    assert (
        view.explorer._metadata(
            {"rule": "card_orientation@1"}, "Card overview"
        ).orientation
        is None
    )


def test_null_quality_and_empty_selected_support_are_not_missing_declarations():
    card = synthetic_support([])
    card.quality["conflicts"] = None
    view = card.explore().overview()
    assert function_row(view)["support"]["state"] == "retained_empty"
    assert "selection declares no support references" in repr(view)
    assert view.orientation["quality"]["conflicts"]["state"] == "retained_null"
    assert "Stored conflicts declaration is null; its scope is unknown" in repr(view)


def test_independent_saved_orientation_uses_original_capture_without_current_science(
    public_original, tmp_path
):
    view = Card.from_dict(deepcopy(public_original)).explore().overview()
    expected = view.orientation
    path = tmp_path / "overview.json.gz"
    receipt = view.save(path, compression="gzip")
    expected_path = tmp_path / "expected.json"
    expected_path.write_text(json.dumps(expected), encoding="utf-8")
    code = r"""
import importlib, json, socket, sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card
def forbidden(*a, **k): raise AssertionError('Orientation used current science, fixtures or reconstruction')
targets={'card_scientific_access':['materialize'], 'knowledge_state':['knowledge_state'],
         'source_assertion_store':['make_source_assertion'], 'relationship_store':['make_derivation']}
modules={key:importlib.import_module('sabueso.core.'+key) for key in targets}
for key, names in targets.items():
 for name in names:setattr(modules[key],name,forbidden)
Card.__init__=Card.from_dict=forbidden
sabueso.resolve=forbidden
socket.socket.connect=socket.create_connection=forbidden
def audit(event,args):
 if event=='open' and 'temp_data' in str(args[0]).replace(chr(92),'/').split('/'):forbidden()
sys.addaudithook(audit)
saved=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
assert saved.orientation==json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
for field in saved.orientation['fields']:
 if field['value_location'] is not None:
  assert saved.explorer.inspect(locator=field['value_location']).native_payload==field['value']
 for source in field['support']['sources']:
  if source['state']=='present':
   assert saved.explorer.inspect(locator=source['location']).native_payload['source']==source['source']
assert str(saved) and saved._repr_html_()
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(path.resolve()),
            receipt["bundle_digest"],
            str(expected_path.resolve()),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
