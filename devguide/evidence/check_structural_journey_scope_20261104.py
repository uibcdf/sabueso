"""Reproduce the bounded B3 source-scope review; never acquire provider data.

Run from any directory with the shared editable checkout:
    python check_structural_journey_scope_20261105.py --output NEW_DIRECTORY

The expected public declarations below were transcribed from the original source
inputs before exercising current readers. Synthetic perturbations are explicitly
separate from public observations. This is technical/source-contract review, not
independent scientist or researcher acceptance. Caller output is never overwritten.
"""

import argparse
import gzip
import hashlib
import json
import socket
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

import sabueso
from sabueso.core.card import Card
from sabueso.core.source_assertion_store import make_source_assertion

ROOT = Path(__file__).resolve().parents[2]
CAPSULE = ROOT / "tests/core/data/assembly_nonpolymer_live_v2.json.gz"
CAPSULE_SHA256 = "b37ef7b9ebe68bbe4d46d6ff65a73522b044b0935f0a2e9128104c30e1e5e57d"
RULE = "rcsb_assembly_generation@5"
EXPECTED = {
    "1HTI": [("1", [(x, ["1"]) for x in "ABC"])],
    "1SUX": [("1", [(x, ["1"]) for x in "ABCDEFGHIJKL"])],
    "2V5B": [
        ("2", [("A", ["1"]), ("B", ["1"])]),
        ("1", [("A", ["1"]), ("A", ["2"]), ("B", ["1"]), ("B", ["2"])]),
    ],
}
READER = r"""
import importlib, json, socket, sys
from pathlib import Path
import sabueso
from sabueso.core.card import Card

def forbidden(*a, **k):
    raise AssertionError('No current Card/science, source requests or fixtures')

Card.from_dict = forbidden
Card.__init__ = forbidden
socket.socket.connect = forbidden
socket.create_connection = forbidden
for version in range(1, 6):
    importlib.import_module(f'sabueso.core.assembly_generation_v{version}').generation = forbidden

def audit(event, args):
    if event == 'open' and isinstance(args[0], str):
        if 'temp_data' in args[0].replace(chr(92), '/').split('/'):
            forbidden()

sys.addaudithook(audit)
manifest = json.loads(Path(sys.argv[1]).read_text())
for row in manifest:
    saved = sabueso.read_exploration(row['file'])
    assert saved.native_payload['physical_membership'] == 'not_computed'
    assert saved.native_payload['rule'] == 'rcsb_assembly_generation@5'
    assert saved.result_ref == row['result_ref']
    assert saved.explorer.access.select('assembly_generation', options=row['options']).result_ref == row['result_ref']
    positions = [
        g.get('declared_occurrences', [])
        for s in saved.native_payload['sources']
        for a in s['assemblies'] for g in a['generators']
    ]
    assert sum(map(len, positions)) == row['delivered_occurrence_row_count']
print('PASS independent original saved reading for four public scope journeys')
"""


def forbidden(*args, **kwargs):
    raise AssertionError("No provider access in the B3 source-scope review")


def source(card):
    return next(
        s
        for s in card.source_assertion_store.store.values()
        if s["source"]["name"] == "RCSB PDB"
    )


def parents(native):
    return [a for s in native["sources"] for a in s["assemblies"]]


def occurrences(native):
    return [
        (
            a["assembly_id"],
            [
                (r["asym_id"], r["operator_ids"])
                for r in g.get("declared_occurrences", [])
            ],
        )
        for a in parents(native)
        for g in a["generators"]
    ]


def role(view, name):
    return view.filter("role", equals=name).items()[0]


def run_public(label, case, output):
    card = Card.from_dict(deepcopy(case["card"]))
    before, pin = card.to_dict(), card.pinned_ref()
    original = source(card)
    raw = original["asserted_value"]
    pdb = label if label != "legacy" else "1SUX"
    options = {
        "structure_ref": "pdb:" + pdb,
        "generation_rule": RULE,
        "expand_occurrences": True,
    }
    expected = card.assembly_generation(**options)
    assert expected["physical_membership"] == "not_computed"
    if label in EXPECTED:
        assert occurrences(expected) == EXPECTED[label]
    else:
        assert expected["sources"][0]["status"] == "not_retained"
        assert (
            not parents(expected)
            and expected["occurrence_expansion_state"] == "incomplete"
        )
    registry = expected["sources"][0].get("component_registry", [])
    if label == "1HTI":
        c = next(r for r in registry if r["asym_id"] == "C")
        assert c["basis"] == "native_nonpolymer_instance_identifier"
        ref = next(r for r in c["references"] if r["role"] == "nonpolymer_instance")
        assert ref["descriptors"]["author_asym_id"] == "B"
        assert (
            next(r for r in registry if r["asym_id"] == "B")["basis"]
            == "native_polymer_instance_identifier"
        )
    declared_bindings = [
        r
        for a in parents(expected)
        for g in a["generators"]
        for r in g["component_bindings"]
    ]
    unknown = {r["asym_id"] for r in declared_bindings if r["state"] == "unresolved"}
    assert unknown == {"1SUX": {"K", "L"}, "2V5B": {"B"}}.get(label, set())

    import sabueso.core.assembly_generation_v5 as backend

    original_reader, calls = backend.generation, []

    def observe(*args, **kwargs):
        calls.append(1)
        return original_reader(*args, **kwargs)

    backend.generation = observe
    try:
        explorer = card.explore()
        structure = next(
            i for i in explorer.view("structures").items() if i.label == "pdb:" + pdb
        )
        link = role(structure.related(), "question")
        assert not calls
        # The natural structure question uses compact delivery by default. This
        # explicit wider request then shares one result with the exact agent call.
        natural = link.open()
        natural_selection = explorer.access.select(
            "assembly_generation", options=natural.request["options"]
        )
        assert natural.result_ref == natural_selection.result_ref and calls == [1]
        human = explorer.answer("assembly_generation", options=options)
        machine = explorer.access.select(
            "assembly_generation",
            fields=["structure_ref", "assembly_id", "declaration_count"],
            options=options,
        )
        assert human.result_ref == machine.result_ref and calls == [1, 1]
        assert human.native_payload == expected
        page = machine.page(max_bytes=65536)
        assert page["items"]
        assert all(
            i["interpretation"]["physical_membership"] == "not_computed"
            for i in page["items"]
        )
        # Inspect one exact component position, the original binding and source;
        # retain that destination without manufacturing all unvisited operations.
        if label != "legacy":
            components = role(human.items()[0].related(), "components").open()
            positions = components.filter("role", equals="component")
            position = positions.items()[0]
            detail = position.open()
            assert detail.back() is positions
            assert role(detail, "component_binding").open().native_payload
            assert role(detail, "source").open().native_payload["id"] == original["id"]
        text, html = str(human), human._repr_html_()
        assert "assembly contacts remain uncomputed" in text
        assert "distinct physical molecules" in html
        path = output / (label + ".json")
        human.save(path)
        assert calls == [1, 1]
    finally:
        backend.generation = original_reader
    assert card.to_dict() == before and card.pinned_ref() == pin
    generation = raw.get("assembly_generation_inputs", {})
    declarations = [
        {
            "assembly_id": a["rcsb_assembly_container_identifiers"]["assembly_id"],
            "oligomeric_count_as_stated": a.get("pdbx_struct_assembly", {}).get(
                "oligomeric_count"
            ),
            "original_generators": a.get("pdbx_struct_assembly_gen"),
            "operator_field_names": [
                sorted(o) for o in a.get("pdbx_struct_oper_list", [])
            ],
        }
        for a in generation.get("assemblies", [])
    ]
    neighbor_collections = [
        instance
        for entity in raw.get("ligand_contact_inputs", {}).get("polymer_entities", [])
        for instance in (entity.get("polymer_entity_instances") or [])
    ]
    neighbor_states = []
    neighbors = []
    for instance in neighbor_collections:
        value = instance.get("rcsb_ligand_neighbors")
        state = (
            "not_retained"
            if "rcsb_ligand_neighbors" not in instance
            else "retained_null"
            if value is None
            else "unrecognized_shape"
            if not isinstance(value, list)
            else "retained_empty"
            if not value
            else "retained"
        )
        neighbor_states.append(
            {
                "state": state,
                "record_count": len(value) if isinstance(value, list) else None,
            }
        )
        if isinstance(value, list):
            neighbors.extend(value)
    return {
        "case": label,
        "kind": "retained_public",
        "card_ref": pin,
        "original_source_assertion_id": original["id"],
        "original_declarations": declarations,
        "declared_occurrence_count": None
        if label == "legacy"
        else sum(len(x[1]) for x in occurrences(expected)),
        "declared_count_state": "unavailable"
        if label == "legacy"
        else "exact_source_declarations",
        "declared_count_scope": "Sum across original alternative assembly declarations, never a physical molecule count or a chosen biological assembly.",
        "delivered_occurrence_row_count": sum(len(x[1]) for x in occurrences(expected)),
        "occurrence_delivery_state": expected["occurrence_expansion_state"],
        "component_key_states": dict(Counter(r["binding_state"] for r in registry)),
        "declared_component_binding_states": dict(
            Counter(r["state"] for r in declared_bindings)
        ),
        "unresolved_declared_labels": sorted(unknown),
        "retained_neighbor_count": len(neighbors),
        "neighbor_collection_states": neighbor_states,
        "neighbor_count_scope": "Only records in retained list collections; null/missing collections do not establish zero source contacts.",
        "retained_neighbor_field_names": sorted({k for n in neighbors for k in n}),
        "physical_membership": expected["physical_membership"],
        "source_card_unchanged": True,
        "native_evaluations": 2,
        "evaluation_scope": "One natural compact question plus one explicit expanded request; human/agent reuse each exact result.",
        "saved": {
            "file": str(path.resolve()),
            "result_ref": human.result_ref,
            "options": human.request["options"],
            "delivered_occurrence_row_count": sum(
                len(x[1]) for x in occurrences(expected)
            ),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
    }


def synthetic_card(case, mutate):
    card = Card.from_dict(deepcopy(case["card"]))
    old = source(card)
    value = deepcopy(old["asserted_value"])
    mutate(value)
    altered = make_source_assertion(
        old["field_path"],
        value,
        "RCSB PDB",
        "1HTI",
        "synthetic-benchmark",
        subject_ref=old["subject_ref"],
    )
    card.source_assertion_store.add(altered)
    for relationship in card.relationships("has_structure"):
        relationship["source_assertion_ids"] = [
            altered["id"] if ref == old["id"] else ref
            for ref in relationship["source_assertion_ids"]
        ]
    return card


def run_synthetic(case):
    def generator(value):
        return value["assembly_generation_inputs"]["assemblies"][0][
            "pdbx_struct_assembly_gen"
        ][0]

    def duplicate(value):
        generator(value)["asym_id_list"] = ["A", "A"]

    def product(value):
        generator(value)["asym_id_list"] = ["A"]
        generator(value)["oper_expression"] = "(1,2)(3,4)"
        parent = value["assembly_generation_inputs"]["assemblies"][0]
        parent["pdbx_struct_oper_list"] = [
            {"id": str(i), "type": "synthetic", "symmetry_operation": "x,y,z"}
            for i in range(1, 5)
        ]

    def missing_operator(value):
        generator(value)["oper_expression"] = "999"

    def duplicate_operator(value):
        rows = value["assembly_generation_inputs"]["assemblies"][0][
            "pdbx_struct_oper_list"
        ]
        rows.append(deepcopy(rows[0]))

    def incomplete_instance(value):
        entity = value["assembly_component_inputs"]["nonpolymer_entities"][0]
        del entity["nonpolymer_entity_instances"][0][
            "rcsb_nonpolymer_entity_instance_container_identifiers"
        ]["entry_id"]

    def foreign_parent(value):
        generator(value)["assembly_id"] = "OTHER"

    rows = []
    for name, mutate in [
        ("repeated_component", duplicate),
        ("right_to_left_product", product),
        ("missing_operator", missing_operator),
        ("repeated_operator_key", duplicate_operator),
        ("incomplete_nonpolymer_identity", incomplete_instance),
        ("foreign_generator_parent", foreign_parent),
    ]:
        card = synthetic_card(case, mutate)
        before = card.to_dict()
        native = card.assembly_generation(generation_rule=RULE, expand_occurrences=True)
        gen = parents(native)[0]["generators"][0]
        if name == "repeated_component":
            assert [
                (r["asym_id"], r["component_binding_index"])
                for r in gen["declared_occurrences"]
            ] == [("A", 0), ("A", 1)]
        elif name == "right_to_left_product":
            assert [r["operator_ids"] for r in gen["declared_occurrences"]] == [
                ["1", "3"],
                ["1", "4"],
                ["2", "3"],
                ["2", "4"],
            ]
            assert gen["occurrence_plan"]["application_order"] == "right_to_left"
        elif name == "missing_operator":
            assert all(
                r["operator_states"] == ["unresolved"]
                for r in gen["declared_occurrences"]
            )
        elif name == "repeated_operator_key":
            assert all(
                r["operator_states"] == ["ambiguous"]
                for r in gen["declared_occurrences"]
            )
        elif name == "incomplete_nonpolymer_identity":
            c = next(
                r
                for r in native["sources"][0]["component_registry"]
                if r["asym_id"] == "C"
            )
            assert c["binding_state"] == "referenced"
        else:
            assert gen["occurrence_plan"]["status"] == "unavailable"
        assert (
            native["physical_membership"] == "not_computed" and card.to_dict() == before
        )
        rows.append(
            {
                "case": name,
                "kind": "synthetic_perturbation_not_provider_observation",
                "card_ref": card.pinned_ref(),
                "original_source_assertion_id": source(card)["id"],
                "new_synthetic_source_assertion_id": next(
                    s["id"]
                    for s in card.source_assertion_store.store.values()
                    if s.get("retrieved_at") == "synthetic-benchmark"
                ),
                "status": "passed",
                "physical_membership": "not_computed",
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    output = options.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    socket.socket.connect = forbidden
    socket.create_connection = forbidden
    raw = CAPSULE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CAPSULE_SHA256
    original = json.loads(gzip.decompress(raw))
    public = [
        run_public(name, case, output) for name, case in original["cases"].items()
    ]
    synthetic = run_synthetic(original["cases"]["1HTI"])
    manifest = output / "saved-manifest.json"
    manifest.write_text(
        json.dumps([r["saved"] for r in public], indent=2), encoding="utf-8"
    )
    receiving = subprocess.run(
        [sys.executable, "-c", READER, str(manifest)],
        cwd=output,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    (output / "independent-reader.log").write_text(
        receiving.stdout + receiving.stderr, encoding="utf-8"
    )
    assert receiving.returncode == 0, receiving.stdout + receiving.stderr
    assert hashlib.sha256(CAPSULE.read_bytes()).hexdigest() == CAPSULE_SHA256
    receipt = {
        "format": "sabueso.structural_journey_scope_audit@1",
        "owner": "#173/#148/#112",
        "review_trigger": "B3 scientific scope decision and before 0.15.0",
        "sdk": sabueso.__version__,
        "capsule_sha256": CAPSULE_SHA256,
        "original_producer": original["producer"]["source"],
        "original_sdk": original["producer"]["sdk"],
        "molecular_provider_queries": 0,
        "original_capsule_unchanged": True,
        "public": public,
        "synthetic": synthetic,
        "independent_saved_reading": "four journeys passed",
        "review_scope": "Source-contract and technical checks, not independent scientific or uncoached researcher acceptance.",
        "release_consolidation": "paused",
    }
    (output / "observations.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "PASS: four public source/native/human/agent/saved journeys and six explicitly synthetic scope counterexamples; no provider queries or original mutations."
    )


if __name__ == "__main__":
    main()
