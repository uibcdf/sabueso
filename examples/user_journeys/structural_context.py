"""Explore a public TcTIM structure and explicitly qualify one modeling input.

Knowledge production/reading is offline and does not import MolSysMT. The separate
model command needs MolSysMT and deliberately supports only the retained 1TCD
single-model, single-generator, identity-operation control. Its local criteria
and calculation log are not a generic bridge or a shared MolI result protocol.
"""

import argparse
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import sabueso

FORMAT = "sabueso.public_structural_context_example@1"
CRITERIA = "public_tctim_coordinate_correspondence@1"
MODEL_FORMAT = "sabueso.public_structural_calculation_log@1"
CONTACT_CRITERION_V1 = {
    "endpoint_semantics": "atomic C-alpha A/B; no group reduction or centers",
    "threshold": {"value": 1.0, "unit": "nm"},
    "inclusive": True,
    "pbc": False,
    "structure_indices": [0],
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _one(values, description):
    values = list(values)
    _need(len(values) == 1, f"One unambiguous {description} is required.")
    return values[0]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, value):
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _role(view, role):
    return _one(view.filter("role", equals=role).items(), f"{role} link")


def _records(container, category):
    table = container.getObj(category)
    _need(table is not None, f"Original coordinate category {category} is required.")
    return [dict(zip(table.getAttributeList(), row, strict=True)) for row in table]


def _unique(rows, key):
    ids = [str(row[key]) for row in rows]
    _need(len(ids) == len(set(ids)), f"Ambiguous coordinate {key} identifiers.")
    return dict(zip(ids, rows, strict=True))


def _revision(info):
    _need(isinstance(info, dict), "Original entry revision is unavailable.")
    major, minor, when = (
        info.get(key) for key in ("major_revision", "minor_revision", "revision_date")
    )
    _need(
        type(major) is int and type(minor) is int and isinstance(when, str),
        "Original entry revision is unavailable.",
    )
    return {
        "major_revision": major,
        "minor_revision": minor,
        "revision_date": date.fromisoformat(when.partition("T")[0]).isoformat(),
    }


def _correspondence(card, container, native):
    """Admit this bounded public example before invoking any geometry builder."""
    _need(
        card.id == "sabueso:protein:uniprot:P52270",
        "This control requires the source-identified TcTIM Card.",
    )
    _need(
        native["card_ref"] == card.pinned_ref(),
        "The original assembly result belongs to another Card pin.",
    )
    source = _one(
        (s for s in native["sources"] if s["structure_ref"] == "pdb:1TCD"),
        "original assembly source",
    )
    assertion = card.source_assertion_store.get(source["source_assertion_id"])
    _need(
        isinstance(assertion, dict)
        and assertion["source"]["name"] == "RCSB PDB"
        and assertion["subject_ref"] == "pdb:1TCD"
        and assertion["source"]["record_id"] == "1TCD",
        "The original RCSB source identity is incompatible.",
    )
    value = assertion["asserted_value"]
    _need(
        value["subject_ref"] == "uniprot:P52270" and value["object_ref"] == "pdb:1TCD",
        "The original structure source names another molecular context.",
    )
    entry = _one(_records(container, "entry"), "coordinate entry")
    _need(
        entry["id"] == "1TCD", "Coordinate entry identity differs from the Card source."
    )
    history = _records(container, "pdbx_audit_revision_history")
    _need(bool(history), "Original coordinate revision is unavailable.")
    _need(
        len({row["ordinal"] for row in history}) == len(history),
        "Coordinate revision order is ambiguous.",
    )
    latest = max(history, key=lambda row: int(row["ordinal"]))
    file_revision = _revision(latest)
    card_revision = _revision(value.get("accession_info"))
    _need(
        card_revision == _revision(source["entry_revision"]) == file_revision,
        "The Card and coordinate entry revisions differ.",
    )

    parent = _one(
        (row for row in source["assemblies"] if row["assembly_id"] == "1"), "assembly 1"
    )
    generator = _one(parent["generators"], "retained assembly generator")
    raw_parent = _one(
        (
            row
            for row in value["assembly_generation_inputs"]["assemblies"]
            if row["rcsb_assembly_container_identifiers"]["assembly_id"] == "1"
        ),
        "original assembly record",
    )
    raw = _one(raw_parent["pdbx_struct_assembly_gen"], "original generator")
    file_gen = _one(
        (
            row
            for row in _records(container, "pdbx_struct_assembly_gen")
            if row["assembly_id"] == "1"
        ),
        "coordinate generator",
    )
    _need(
        raw["assembly_id"] == file_gen["assembly_id"] == "1"
        and raw["oper_expression"] == file_gen["oper_expression"] == "1"
        and raw["asym_id_list"]
        == file_gen["asym_id_list"].split(",")
        == ["A", "B", "C", "D"],
        "This control requires the same original ordered generator and identity operation.",
    )
    _need(
        [row["asym_id"] for row in generator["component_bindings"]]
        == raw["asym_id_list"],
        "Original component positions do not match the generator.",
    )
    operator = _one(
        (
            row
            for row in _records(container, "pdbx_struct_oper_list")
            if str(row["id"]) == "1"
        ),
        "coordinate operation 1",
    )
    original_operator = _one(
        (row for row in raw_parent["pdbx_struct_oper_list"] if row["id"] == "1"),
        "original source operation 1",
    )
    _need(
        operator["type"] == original_operator["type"] == "identity operation",
        "The operator identity descriptors differ.",
    )
    rotation = [
        [float(operator[f"matrix[{i}][{j}]"]) for j in range(1, 4)] for i in range(1, 4)
    ]
    vector = [float(operator[f"vector[{i}]"]) for i in range(1, 4)]
    _need(
        rotation == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        and vector == [0.0, 0.0, 0.0],
        "The numeric transform is outside this identity-operation control.",
    )

    entities = _unique(_records(container, "entity"), "id")
    chains = _unique(_records(container, "struct_asym"), "id")
    _need(
        set(chains) == {"A", "B", "C", "D"},
        "Native coordinate component identities differ.",
    )
    polymers = _one(
        (
            e
            for e in value["ligand_contact_inputs"]["polymer_entities"]
            if e["rcsb_polymer_entity_container_identifiers"]["entity_id"] == "1"
        ),
        "source polymer entity 1",
    )
    ids = polymers["rcsb_polymer_entity_container_identifiers"]
    _need(
        "P52270" in ids["uniprot_ids"],
        "Original RCSB polymer identity does not name TcTIM.",
    )
    reference = _one(
        (
            r
            for r in _records(container, "struct_ref")
            if r["db_name"] == "UNP" and r["pdbx_db_accession"] == "P52270"
        ),
        "coordinate database reference",
    )
    file_polymer = _one(
        (r for r in _records(container, "entity_poly") if str(r["entity_id"]) == "1"),
        "coordinate polymer sequence",
    )
    _need(
        "".join(file_polymer["pdbx_seq_one_letter_code_can"].split())
        == polymers["entity_poly"]["pdbx_seq_one_letter_code_can"],
        "The original polymer sequence declarations differ.",
    )
    _need(
        str(reference["entity_id"]) == "1",
        "Coordinate database reference names another entity.",
    )
    alignment = _one(
        (
            r
            for r in polymers["rcsb_polymer_entity_align"]
            if r["reference_database_name"] == "UniProt"
            and r["reference_database_accession"] == "P52270"
        ),
        "original UniProt alignment",
    )
    _need(
        alignment["aligned_regions"]
        == [{"entity_beg_seq_id": 1, "ref_beg_seq_id": 3, "length": 249}],
        "This control requires the declared entity-to-reference axis, not equal residue numbers.",
    )
    regional = _one(
        (
            r
            for r in card.structures(region=[96])["items"]
            if r["relationship_id"] == source["relationship_id"]
        ),
        "regional structure declaration",
    )
    _need(
        regional["coordinate_scope"]["status"] == "comparable",
        "Original reference/coordinate admission failed.",
    )
    _need(
        source["source_assertion_id"]
        in regional["coordinate_scope"]["projection_source_assertion_ids"],
        "Regional coordinates lack the selected original structure support.",
    )
    mapping = []
    source_author_axes = {}
    for position, label in enumerate(raw["asym_id_list"]):
        entity_id = str(chains[label]["entity_id"])
        if label in ("A", "B"):
            _need(
                entity_id == "1" and entities[entity_id]["type"] == "polymer",
                "The native polymer component differs.",
            )
            instance = _one(
                (
                    r
                    for r in polymers["polymer_entity_instances"]
                    if r["rcsb_polymer_entity_instance_container_identifiers"][
                        "asym_id"
                    ]
                    == label
                ),
                "native polymer instance",
            )
            author = instance["rcsb_polymer_entity_instance_container_identifiers"][
                "auth_asym_id"
            ]
            labels = instance["rcsb_polymer_entity_instance_container_identifiers"][
                "auth_to_entity_poly_seq_mapping"
            ]
            _need(
                isinstance(labels, list)
                and len(labels) == 249
                and len(set(labels)) == 249,
                "Original author numbering is unavailable or ambiguous for this control.",
            )
            source_author_axes[label] = (author, labels)
            span = _one(
                (
                    r
                    for r in _records(container, "struct_ref_seq")
                    if r["pdbx_strand_id"] == author and r["ref_id"] == reference["id"]
                ),
                "coordinate declared reference span",
            )
            _need(
                span["pdbx_db_accession"] == "P52270"
                and span["pdbx_PDB_id_code"] == "1TCD",
                "The coordinate numbering declaration names another reference.",
            )
            _need(
                [
                    int(span[k])
                    for k in [
                        "seq_align_beg",
                        "seq_align_end",
                        "db_align_beg",
                        "db_align_end",
                    ]
                ]
                == [1, 249, 3, 251],
                "The coordinate and Card numbering declarations differ.",
            )
        mapping.append(
            {
                "source_asym_id": label,
                "coordinate_entity_id": entity_id,
                "coordinate_entity_type": entities[entity_id]["type"],
                "card_component_state": generator["component_bindings"][position][
                    "state"
                ],
                "basis": "same_entry_revision_and_original_native_generator_position",
            }
        )
    atoms = _unique(_records(container, "atom_site"), "id")
    sequence_rows = [
        r for r in _records(container, "entity_poly_seq") if str(r["entity_id"]) == "1"
    ]
    positions = _unique(sequence_rows, "num")
    _need(
        set(positions) == {str(i) for i in range(1, 250)},
        "The coordinate polymer position axis is incomplete or ambiguous.",
    )
    _need(
        all(
            str(r["label_seq_id"]) in positions
            and r["label_comp_id"] == positions[str(r["label_seq_id"])]["mon_id"]
            for r in atoms.values()
            if r["label_asym_id"] in ("A", "B")
        ),
        "Atomic position/type pointers contradict the original polymer sequence.",
    )
    _need(
        all(
            r["auth_asym_id"] == source_author_axes[r["label_asym_id"]][0]
            and str(r["auth_seq_id"])
            == source_author_axes[r["label_asym_id"]][1][int(r["label_seq_id"]) - 1]
            for r in atoms.values()
            if r["label_asym_id"] in ("A", "B")
        ),
        "Atomic author numbering differs from the original source axis.",
    )
    _need(
        {str(row["pdbx_PDB_model_num"]) for row in atoms.values()} == {"1"},
        "Multiple coordinate models require another declared task.",
    )
    _need(
        {row["label_alt_id"] for row in atoms.values()} == {"."},
        "Alternate locations require another declared task.",
    )
    _need(
        all(
            row["label_asym_id"] in chains
            and str(row["label_entity_id"])
            == str(chains[row["label_asym_id"]]["entity_id"])
            for row in atoms.values()
        ),
        "Atomic labels contradict native component/entity pointers.",
    )
    return {
        "criteria": CRITERIA,
        "status": "admitted_for_this_control",
        "card_ref": card.pinned_ref(),
        "source_assertion_id": source["source_assertion_id"],
        "relationship_id": source["relationship_id"],
        "structure_ref": "pdb:1TCD",
        "entry_revision": card_revision,
        "assembly_id": "1",
        "generator_position": 0,
        "operator_ids": ["1"],
        "structure_index": 0,
        "source_model_id": "1",
        "component_correspondence": mapping,
        "coordinate_scope": regional["coordinate_scope"],
        "transform_basis": "original_coordinate_file; numeric transforms are not stored in this Card",
        "reference_revision": "not_stated; no source/reference revision equality inferred",
    }


def produce(fixtures, output):
    from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

    output.mkdir(parents=True, exist_ok=False)
    source_dir = fixtures / "rcsb_structural_context"
    current, _ = sabueso.resolve(
        "P52270",
        resolver=EntityResolver(
            FixtureUniProtClient(fixtures), rcsb_client=FixtureRCSBClient(source_dir)
        ),
        structures=["1TCD"],
    )
    before = current.to_dict()
    explorer = current.explore()
    active = _one(
        explorer.view("annotated_regions")
        .filter("feature_type", equals="active_site")
        .filter("label", equals="Active sites · annotation 1 · Electrophile")
        .items(),
        "original active-site annotation",
    )
    region = _role(active.related(), "question").open()
    selected = _one(
        explorer.view("structures").filter("structure_ref", equals="pdb:1TCD").items(),
        "1TCD declaration",
    )
    structure = selected.open()
    assembly = _role(selected.related(), "question").open()
    components = _role(assembly.items()[0].related(), "components").open()
    machine = explorer.access.select(
        "assembly_generation",
        fields=["structure_ref", "assembly_id", "declaration_count"],
        options=assembly.request["options"],
    )
    _need(
        machine.result_ref == assembly.result_ref,
        "Human and agent assembly results differ.",
    )
    print(
        "What does the source annotation say, and which structures cover it?\n", region
    )
    print("Which exact TcTIM structure am I inspecting?\n", structure)
    print("Which components and operations does its source declare?\n", assembly)
    print(
        "Open the original component records, including unresolved keys:\n", components
    )
    print(
        "C and D remain unresolved in the retained Card input. A coordinate file may supply additional context separately."
    )
    # A save contains the whole visited session. Save it once, with the exact
    # compact agent request as root, so both access routes survive unchanged.
    receipt = machine.save(output / "exploration.json.gz", compression="gzip")
    _write(output / "card.json", before)
    _need(current.to_dict() == before, "Inspection changed the Card.")
    _write(
        output / "manifest.json",
        {
            "format": FORMAT,
            "producer_sdk": sabueso.__version__,
            "card_ref": current.pinned_ref(),
            "receipt": receipt,
            "coordinate_input": _load(source_dir / "capture.json")["files"][
                "coordinates/1tcd.bcif.gz"
            ],
            "requests": {"region": region.request, "assembly": assembly.request},
            "result_refs": {
                "region": region.result_ref,
                "assembly": assembly.result_ref,
            },
            "files": {
                name: _hash(output / name)
                for name in ["exploration.json.gz", "card.json"]
            },
            "scope": "Only 1TCD RCSB input was requested. Other UniProt-linked structures lack new RCSB receiving. No model recommendation or biological inference.",
        },
    )


def model(output, coordinates):
    # This explicit optional command is the modeling consumer, not Card intake.
    manifest = _checked_manifest(output)
    _need(
        "modeling" not in manifest, "The original calculation must not be overwritten."
    )
    _need(
        not any(
            (output / name).exists()
            for name in [
                "modeling-input.bcif.gz",
                "atom-correspondence.json",
                "calculated-pairs.json",
                "modeling.json",
            ]
        ),
        "An existing caller calculation file would be overwritten.",
    )
    declared = manifest.get("coordinate_input")
    _need(
        isinstance(declared, dict)
        and type(declared.get("bytes")) is int
        and isinstance(declared.get("sha256"), str),
        "The retained original coordinate input declaration is unavailable.",
    )
    _need(
        coordinates.stat().st_size == declared["bytes"],
        "This control requires the retained original coordinate input bytes.",
    )
    original_hash = _hash(coordinates)
    _need(
        original_hash == declared["sha256"],
        "This control requires the retained original coordinate input hash.",
    )
    import molsysmt as msm
    import numpy as np

    from sabueso.core.card import Card

    card = Card.from_dict(_load(output / "card.json"))
    saved = sabueso.read_exploration(
        output / "exploration.json.gz",
        expected_digest=manifest["receipt"]["bundle_digest"],
    )
    container = msm.convert(
        str(coordinates), to_form="mmcif.PdbxContainers.DataContainer"
    )
    admitted = _correspondence(card, container, saved.native_payload)
    before = card.to_dict()
    puw = msm.pyunitwizard
    with puw.context(standard_units=["angstrom", "ns", "kcal/mol", "K"]):
        molsys = msm.convert(container, to_form="molsysmt.MolSys")
        chain_ids = msm.get(molsys, element="chain", chain_id=True)
        _need(
            chain_ids == ["A", "B", "C", "D"],
            "Native coordinate chain order differs from the admitted generator.",
        )
        atom_ids = msm.get(molsys, element="atom", atom_id=True)
        input_atoms = _unique(_records(container, "atom_site"), "id")
        native_chains = msm.get(molsys, element="atom", chain_index=True)
        native_names = msm.get(molsys, element="atom", atom_name=True)
        _need(
            all(
                chain_ids[native_chains[i]] == input_atoms[str(key)]["label_asym_id"]
                and native_names[i] == input_atoms[str(key)]["label_atom_id"]
                for i, key in enumerate(atom_ids)
            ),
            "Native atom/chain fields contradict the original coordinate IDs.",
        )
        raw = np.array(
            [
                [float(input_atoms[str(key)][f"Cartn_{axis}"]) for axis in "xyz"]
                for key in atom_ids
            ]
        )[None]
        xyz = puw.get_value(msm.get(molsys, coordinates=True), to_unit="nm")
        np.testing.assert_allclose(
            xyz,
            puw.get_value(puw.quantity(raw, "angstrom"), to_unit="nm"),
            rtol=0,
            atol=1e-12,
        )
        assembled = msm.build.make_bioassembly(
            molsys, bioassembly="1", structure_indices=[0]
        )
        built = puw.get_value(msm.get(assembled, coordinates=True), to_unit="nm")
        np.testing.assert_allclose(built, xyz, rtol=0, atol=1e-12)
        _need(
            msm.get(assembled, element="atom", atom_id=True) == atom_ids,
            "Generated atom order differs from this identity-operation control.",
        )
        correspondence = [
            {
                "generated_atom_index": i,
                "original_atom_id": str(key),
                "atom_name": input_atoms[str(key)]["label_atom_id"],
                "entity_position": int(input_atoms[str(key)]["label_seq_id"])
                if input_atoms[str(key)]["label_asym_id"] in ("A", "B")
                else None,
                "author_chain_id": input_atoms[str(key)]["auth_asym_id"],
                "author_position": str(input_atoms[str(key)]["auth_seq_id"]),
                "author_insertion_code": input_atoms[str(key)]["pdbx_PDB_ins_code"],
                "source_asym_id": input_atoms[str(key)]["label_asym_id"],
                "generator_position": 0,
                "operator_ids": ["1"],
                "structure_index": 0,
                "reference_position": int(input_atoms[str(key)]["label_seq_id"]) + 2
                if input_atoms[str(key)]["label_asym_id"] in ("A", "B")
                else None,
            }
            for i, key in enumerate(atom_ids)
        ]
        endpoints = {
            label: [
                i
                for i, key in enumerate(atom_ids)
                if input_atoms[str(key)]["label_asym_id"] == label
                and input_atoms[str(key)]["label_atom_id"] == "CA"
            ]
            for label in ["A", "B"]
        }
        contacts = msm.structure.get_contacts(
            assembled,
            selection=endpoints["A"],
            selection_2=endpoints["B"],
            structure_indices=[0],
            structure_indices_2=[0],
            threshold=puw.quantity(10.0, "angstrom"),
            pbc=False,
            cell_list=False,
            use_gpu=False,
            parallel=False,
            num_threads=1,
        )
        expected = (
            np.sum(
                (built[:, endpoints["A"], None] - built[:, None, endpoints["B"]]) ** 2,
                axis=-1,
            )
            <= 1.0
        )
        np.testing.assert_array_equal(contacts, expected)
        pairs = [
            [endpoints["A"][int(i)], endpoints["B"][int(j)]]
            for i, j in np.argwhere(contacts[0])
        ]
        _need(
            all(
                any(
                    correspondence[i]["reference_position"] == 96
                    for i in endpoints[chain]
                )
                for chain in ["A", "B"]
            ),
            "The source-mapped position 96 is not observed in both coordinate chains.",
        )
    _need(
        card.to_dict() == before and _hash(coordinates) == original_hash,
        "The calculation changed an original input.",
    )
    shutil.copyfile(coordinates, output / "modeling-input.bcif.gz")
    _write(output / "atom-correspondence.json", correspondence)
    _write(output / "calculated-pairs.json", pairs)
    report = {
        "format": MODEL_FORMAT,
        "producer_sdk": sabueso.__version__,
        "provider_sdk": msm.__version__,
        "correspondence": admitted,
        "coordinate_input_sha256": original_hash,
        "generated_atom_count": built.shape[1],
        "contact_criterion": CONTACT_CRITERION_V1,
        "contact_shape": list(contacts.shape),
        "contact_count": int(contacts.sum()),
        "contact_pairs_file": "calculated-pairs.json",
        "pair_index_scope": "zero-based generated_atom_index in atom-correspondence.json; complete selected contact result",
        "independent_formula_agrees": True,
        "new_source_assertions": 0,
        "scope": "Example-local calculation record, separate from the unchanged Card. No source-contact join, physical-copy deduplication, binding/biological-interface conclusion or generic bridge qualification.",
    }
    _write(output / "modeling.json", report)
    manifest["modeling"] = {
        name: _hash(output / name)
        for name in [
            "modeling-input.bcif.gz",
            "atom-correspondence.json",
            "calculated-pairs.json",
            "modeling.json",
        ]
    }
    _write(output / "manifest.json", manifest)
    print(
        "The Card and coordinate file have the same declared entry revision and generator."
    )
    print(
        "The coordinate file explicitly identifies C/D as water; the Card's unresolved keys remain unchanged."
    )
    print(
        f"Recorded calculation: {built.shape[1]} atoms; {int(contacts.sum())} C-alpha pairs satisfy the declared 1 nm criterion."
    )


def _checked_manifest(output):
    manifest = _load(output / "manifest.json")
    _need(manifest["format"] == FORMAT, "Unsupported example format.")
    _need(
        set(manifest["files"]) == {"exploration.json.gz", "card.json"},
        "Incomplete original example inputs.",
    )
    _need(
        set(manifest["requests"]) == {"region", "assembly"},
        "Unknown original scientific request.",
    )
    for name, expected in manifest["files"].items():
        _need(
            _hash(output / name) == expected, f"Changed original example file: {name}."
        )
    return manifest


def _recorded_modeling(output, manifest):
    if "modeling" not in manifest:
        return None
    _need(
        set(manifest["modeling"])
        == {
            "modeling-input.bcif.gz",
            "atom-correspondence.json",
            "calculated-pairs.json",
            "modeling.json",
        },
        "Incomplete original calculation files.",
    )
    for name, expected in manifest["modeling"].items():
        _need(_hash(output / name) == expected, f"Changed calculation file: {name}.")
    report = _load(output / "modeling.json")
    _need(
        report.get("format") == MODEL_FORMAT, "Unsupported original calculation format."
    )
    _need(
        report.get("contact_criterion") == CONTACT_CRITERION_V1
        and report.get("correspondence", {}).get("criteria") == CRITERIA,
        "The original calculation criterion differs from this recorded example.",
    )
    pairs = _load(output / "calculated-pairs.json")
    atoms = _load(output / "atom-correspondence.json")
    _need(
        len(pairs) == report["contact_count"]
        and len(atoms) == report["generated_atom_count"],
        "Incomplete original calculation result.",
    )
    _need(
        all(
            isinstance(pair, list)
            and len(pair) == 2
            and all(type(i) is int and 0 <= i < len(atoms) for i in pair)
            and atoms[pair[0]]["source_asym_id"] == "A"
            and atoms[pair[1]]["source_asym_id"] == "B"
            and all(atoms[i]["atom_name"] == "CA" for i in pair)
            for pair in pairs
        ),
        "Calculation pair references differ from the declared atomic endpoints.",
    )
    _need(
        report["correspondence"]["card_ref"] == manifest["card_ref"]
        and report["new_source_assertions"] == 0,
        "Calculation context is not bound to the original Card.",
    )
    _need(
        report["coordinate_input_sha256"] == _hash(output / "modeling-input.bcif.gz"),
        "Calculation input hash differs.",
    )
    return report


def read(output):
    manifest = _checked_manifest(output)
    report = _recorded_modeling(output, manifest)
    saved = sabueso.read_exploration(
        output / "exploration.json.gz",
        expected_digest=manifest["receipt"]["bundle_digest"],
    )
    explorer = saved.explorer
    assembly = explorer.answer(
        "assembly_generation", options=manifest["requests"]["assembly"]["options"]
    )
    region = explorer.answer(
        "region_coverage", options=manifest["requests"]["region"]["options"]
    )
    _need(
        assembly.result_ref == saved.result_ref == manifest["result_refs"]["assembly"],
        "The original saved assembly result differs.",
    )
    _need(
        region.result_ref == manifest["result_refs"]["region"],
        "The original saved regional result differs.",
    )
    _need(
        assembly.native_payload["card_ref"] == manifest["card_ref"],
        "The saved original Card pin differs.",
    )
    _need(
        assembly.native_payload["physical_membership"] == "not_computed",
        "A calculation was promoted into original source knowledge.",
    )
    selected = explorer.access.select(
        "assembly_generation",
        fields=["structure_ref", "assembly_id", "declaration_count"],
        options=assembly.request["options"],
    )
    _need(
        selected.result_ref == assembly.result_ref,
        "The original compact agent request was not retained.",
    )
    structure = _one(
        explorer.view("structures").filter("structure_ref", equals="pdb:1TCD").items(),
        "saved 1TCD declaration",
    ).open()
    components = _role(assembly.items()[0].related(), "components").open()
    views = {
        "assembly": assembly,
        "region": region,
        "structure": structure,
        "components": components,
        "agent": selected,
    }
    print(
        "Original Card knowledge reopened; no source access, Card rebuilding or geometry calculation.\n",
        assembly,
    )
    if report is not None:
        print(
            f"Separate recorded calculation: {report['generated_atom_count']} atoms, {report['contact_count']} C-alpha pairs. No recalculation or biological interpretation."
        )
    return views


def forbidden(*args, **kwargs):
    raise RuntimeError("This public fixture journey must remain offline")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="command", required=True)
    producer = actions.add_parser("produce")
    producer.add_argument("--fixtures", type=Path, default=Path("temp_data"))
    producer.add_argument("--output", type=Path, required=True)
    calculator = actions.add_parser("model")
    calculator.add_argument("--coordinates", type=Path, required=True)
    calculator.add_argument("--output", type=Path, required=True)
    reader = actions.add_parser("read")
    reader.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with (
        patch("socket.create_connection", forbidden),
        patch("socket.socket.connect", forbidden),
    ):
        if args.command == "produce":
            produce(args.fixtures, args.output)
        elif args.command == "model":
            model(args.output, args.coordinates)
        else:
            read(args.output)


if __name__ == "__main__":
    main()
