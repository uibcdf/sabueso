"""Chemical context preserves original declarations, units and missing scope."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from sabueso.core.card import Card
from sabueso.tools.card.small_molecule import single_molecule_card
from sabueso.tools.db import pdb_ccd
from sabueso.tools.db.chembl import FixtureChEMBLClient

DATA = Path("temp_data")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*a, **k):
        pytest.fail("Chemical reading must not acquire sources")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def molecule(kind):
    if kind == "chembl":
        return single_molecule_card(
            chembl=FixtureChEMBLClient(DATA).molecules(["CHEMBL110"])
        )
    if kind == "ccd":
        return single_molecule_card(
            ccd=pdb_ccd.FixtureCCDClient(DATA / "pdb_ccd_charge").components(["SO4"])
        )
    return single_molecule_card(
        pubchem={
            "retrieved_at": "fixture",
            "compounds": {
                "3717450": json.loads((DATA / "pubchem/3717450.json").read_text())
            },
        }
    )


def native_fields(context):
    return [
        field
        for rel in context["identity_context"]
        for record in rel["records"]
        for field in record["fields"]
    ]


@pytest.mark.parametrize("kind", ["chembl", "ccd", "pubchem"])
def test_public_context_keeps_exact_original_fields_sources_and_data(kind):
    card = molecule(kind)
    original = card.to_dict()
    explorer = card.explore()
    view = explorer.answer("chemical_identity")
    native, rows = view.native_payload, view.rows()
    context = view.chemical_reading
    assert context["rule"] == "chemical_context_reading@1"
    assert context["card_ref"] == explorer.context["card_ref"]
    assert context["complete"]
    for field in context["representations"]:
        if field["value_location"] is not None:
            assert (
                explorer.inspect(locator=field["value_location"]).native_payload
                == field["value"]
            )
    for field in native_fields(context):
        if field["location"] is not None:
            assert (
                explorer.inspect(locator=field["location"]).native_payload
                == field["value"]
            )
    if kind == "ccd":
        charge = next(
            row
            for row in native_fields(context)
            if row["label"].startswith("Formal charge")
        )
        assert charge["value"] == -2 and type(charge["value"]) is int
        assert charge["state"] == "retained"
        assert "Formal charge number (native integer): -2" in str(view)
    elif kind == "chembl":
        parent = next(
            row
            for row in native_fields(context)
            if row["label"] == "Parent record identifier"
        )
        assert parent["value"] == "CHEMBL110"
        assert "Parent record identifier: CHEMBL110" in str(view)
    else:
        representations = context["representations"]
        assert representations[0]["value"] == representations[1]["value"]
        assert representations[0]["path"] != representations[1]["path"]
        declarations = [
            f["value"]
            for row in representations
            for source in row["metadata"]
            for f in source["fields"]
            if f["label"] == "Source representation label" and f["state"] == "retained"
        ]
        assert "isomeric" in declarations and "connectivity" in declarations
    context["representations"].clear()
    assert view.chemical_reading["representations"]
    assert view.native_payload == native and view.rows() == rows
    assert card.to_dict() == original
    assert view._repr_html_()


def test_property_records_keep_units_and_original_method_without_inferred_origin():
    explorer = molecule("chembl").explore()
    view = explorer.answer("property_context")
    context = view.chemical_reading
    weight = next(
        row for row in context["properties"] if row["label"] == "Molecular weight"
    )
    assert weight["field_record"]["value"] == 260.25
    assert weight["field_record"]["unit"] == "dalton"
    assert (
        explorer.inspect(locator=weight["field_location"]).native_payload
        == weight["field_record"]
    )
    logp = next(row for row in context["properties"] if row["label"] == "logP")
    fields = logp["metadata"][0]["fields"]
    assert (
        next(row for row in fields if row["label"] == "Source method")["value"]
        == "ALogP"
    )
    assert (
        next(
            row for row in fields if row["label"] == "Source determination declaration"
        )["state"]
        == "not_retained"
    )
    assert "Measured/calculated origin is stated only when retained" in str(view)
    weight["field_record"]["value"] = -1
    assert (
        next(
            row
            for row in view.chemical_reading["properties"]
            if row["label"] == "Molecular weight"
        )["field_record"]["value"]
        == 260.25
    )


@pytest.mark.parametrize(
    "declaration,state",
    [
        (None, "retained_null"),
        (0, "retained"),
        (False, "unrecognized_shape"),
        ("-2", "unrecognized_shape"),
        ("missing", "not_retained"),
    ],
)
def test_charge_number_distinguishes_zero_null_missing_and_unrecognized(
    declaration, state
):
    record = json.loads((DATA / "pdb_ccd_charge/pdb_ccd/SO4.json").read_text())
    if declaration == "missing":
        del record["chem_comp"]["pdbx_formal_charge"]
    else:
        record["chem_comp"]["pdbx_formal_charge"] = declaration
    card = single_molecule_card(
        ccd={
            "retrieved_at": "synthetic charge-state control",
            "components": {"SO4": record},
        }
    )
    view = card.explore().view("chemistry")
    row = next(
        row
        for row in native_fields(view.chemical_reading)
        if row["label"].startswith("Formal charge")
    )
    assert row["state"] == state
    if declaration == "missing":
        assert row["value"] is None and row["location"] is None
    else:
        assert type(row["value"]) is type(declaration)
        assert row["value"] == declaration
    if state == "unrecognized_shape":
        assert "Formal charge number (native integer): unrecognized shape" in str(view)


def test_original_ccd_capture_keeps_missing_charge_unknown():
    card = single_molecule_card(ccd=pdb_ccd.FixtureCCDClient(DATA).components(["SO4"]))
    context = card.explore().view("chemistry").chemical_reading
    charge = next(
        row
        for row in native_fields(context)
        if row["label"].startswith("Formal charge")
    )
    assert charge["state"] == "not_retained" and charge["value"] is None


def test_parent_markup_is_escaped_and_source_binding_mismatch_is_visible():
    response = FixtureChEMBLClient(DATA).molecules(["CHEMBL110"])
    response["molecules"]["CHEMBL110"]["molecule_hierarchy"]["parent_chembl_id"] = (
        "<script>& synthetic"
    )
    card = single_molecule_card(chembl=response)
    view = card.explore().view("chemistry")
    rendered = view._repr_html_()
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    relation = card.relationships("same_as")[0]
    card.relationship_store.store[relation["id"]]["object_ref"] = (
        "inchikey:SYNTHETIC_FOREIGN"
    )
    context = card.explore().view("chemistry").chemical_reading
    assert (
        context["identity_context"][0]["records"][0]["state"]
        == "source_binding_mismatch"
    )
    assert context["identity_context"][0]["records"][0]["fields"] == []


def test_bounded_preview_does_not_copy_long_values_or_scan_deferred_support():
    class Guarded(list):
        def __iter__(self):
            raise AssertionError("Scanned an unchecked large value")

        def __deepcopy__(self, memo):
            raise AssertionError("Copied an unchecked large value")

    view = molecule("chembl").explore().view("chemistry")
    capture = view.explorer.access._focal.data
    capture["sections"]["identifiers"]["smiles"]["value"] = Guarded([None] * 10000)
    relation = next(
        entry.value
        for entry in view._selection._entries
        if isinstance(entry.value, dict) and entry.value.get("predicate") == "same_as"
    )
    relation["source_assertion_ids"] = Guarded(["SA_unchecked"] * 10000)
    text, html = str(view), view._repr_html_()
    assert "10000 items" in text and "10000 items" in html
    assert "deferred" in text


@pytest.mark.parametrize(
    "profile,panel",
    [
        ("protein", "function"),
        ("small_molecule", "content"),
        ("small_molecule", "overview"),
    ],
)
def test_unrelated_or_source_owned_lookalikes_do_not_become_chemical_context(
    profile, panel
):
    card = Card(
        meta={"entity_type": profile, "card_id": "sabueso:" + profile + ":synthetic"}
    )
    card.unknown_stored["chemical_reading"] = {
        "rule": "chemical_context_reading@1",
        "charge": 0,
    }
    explorer = card.explore()
    view = explorer.overview() if panel == "overview" else explorer.view(panel)
    assert view.chemical_reading is None


@pytest.mark.parametrize(
    "kind,panel",
    [
        ("chembl", "chemistry"),
        ("chembl", "properties"),
        ("ccd", "chemistry"),
        ("pubchem", "chemistry"),
    ],
)
def test_saved_reading_in_a_fresh_process_uses_only_original_captures(
    kind, panel, tmp_path
):
    view = molecule(kind).explore().view(panel)
    expected = view.chemical_reading
    path = tmp_path / "reading.json"
    view.save(path)
    result_file = tmp_path / "original.json"
    result_file.write_text(json.dumps(expected), encoding="utf-8")
    code = """
import json, sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card
from sabueso.core import source_assertion_store
def forbidden(*a,**k):
    raise AssertionError('Chemical reading constructed Cards, acquired data or made assertions')
Card.__init__ = Card.from_dict = sabueso.resolve = forbidden
source_assertion_store.make_source_assertion = forbidden
def audit(event,args):
    if event == 'open' and 'temp_data' in str(args[0]).replace(chr(92),'/').split('/'):
        forbidden()
sys.addaudithook(audit)
saved = sabueso.read_exploration(sys.argv[1])
assert saved.chemical_reading == json.loads(Path(sys.argv[2]).read_text())
assert saved._repr_html_()
print('PASS: original chemical context without Cards, fixtures or acquisition')
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", code, str(path), str(result_file)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_ccd_query_and_frozen_wire_retain_the_real_formal_charge(monkeypatch):
    raw = (DATA / "pdb_ccd_charge/wire/SO4.graphql.json").read_bytes()
    request = json.loads((DATA / "pdb_ccd_charge/wire/SO4.request.json").read_text())
    assert request["query"] == pdb_ccd.COMPONENTS_QUERY
    assert "pdbx_formal_charge" in pdb_ccd.COMPONENTS_QUERY

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return raw

    monkeypatch.setattr(pdb_ccd, "urlopen", lambda *a, **k: Response())
    record = pdb_ccd.OnlineCCDClient().components(["SO4"])
    assert record["components"]["SO4"]["chem_comp"]["pdbx_formal_charge"] == -2


@pytest.mark.parametrize("value", ["measured", "calculated", None, ""])
def test_method_origin_declarations_are_literal_and_keep_their_source_scope(value):
    card = molecule("chembl")
    field = card.get("properties.physchem.logp")
    record = card.source_assertion_store.store[field["source_assertion_ids"][0]]
    record.setdefault("source_metadata", {})["determination"] = value
    view = card.explore().view("properties")
    row = next(
        row
        for row in view.chemical_reading["properties"]
        if row["path"].endswith(".logp")
    )
    declaration = next(
        field
        for field in row["metadata"][0]["fields"]
        if field["label"] == "Source determination declaration"
    )
    assert declaration["value"] == value
    assert (
        view.explorer.inspect(locator=declaration["location"]).native_payload == value
    )


def test_a_source_owned_relationship_lookalike_inside_a_field_is_not_native_context():
    view = molecule("ccd").explore().view("chemistry")
    relation = next(
        entry.value
        for entry in view._selection._entries
        if entry.value.get("predicate") == "same_as"
    )
    field = next(
        entry.value for entry in view._selection._entries if "value" in entry.value
    )
    field.update(relation)
    assert len(view.chemical_reading["identity_context"]) == 1


def test_another_propertys_method_is_not_attributed_to_molecular_weight():
    card = molecule("chembl")
    wrong = card.get("properties.physchem.logp")["source_assertion_ids"]
    card.get("properties.physchem.molecular_weight")["source_assertion_ids"] = list(
        wrong
    )
    view = card.explore().view("properties")
    weight = next(
        row
        for row in view.chemical_reading["properties"]
        if row["label"] == "Molecular weight"
    )
    assert weight["metadata"][0]["state"] == "field_scope_mismatch"
    assert weight["metadata"][0]["fields"] == []
    selected = view.filter("label", equals="Molecular weight")
    assert "declared support has another field scope" in str(selected)
