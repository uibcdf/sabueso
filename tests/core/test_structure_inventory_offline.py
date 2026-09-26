"""The structural inventory: per-structure facts from RCSB, and proteins side by side."""

import pytest

import sabueso
from sabueso.core.deck import Deck
from sabueso.core.errors import ArgumentError
from sabueso.core.structures import INVENTORY_RULE, STATE_RULE
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient

TCTIM, HSTIM = "sabueso:protein:uniprot:P52270", "sabueso:protein:uniprot:P60174"


@pytest.fixture(scope="module")
def cards():
    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    tc, _ = sabueso.resolve("P52270", resolver=resolver, structures="all")
    hs, _ = sabueso.resolve("P60174", resolver=resolver, structures="all")
    return tc, hs


def _item(card, ref, **kwargs):
    view = card.structures(**kwargs)
    return next(i for i in view["items"] if i["structure_ref"] == ref)


def _qualifiers(card, ref):
    (rel,) = [r for r in card.relationships("has_structure") if r["object_ref"] == ref]
    return rel["qualifiers"]


def test_an_engineered_mutation_is_placed_in_uniprot_numbering(cards):
    _, hs = cards
    q = _qualifiers(hs, "pdb:4UNK")
    # RCSB states entity residue 17; the alignment places it at UniProt 16.
    assert q["mutations"] == [
        {
            "polymer_entity": "1",
            "seq_id": 17,
            "position": 16,
            "residue": "D",
            "reference": "N",
            "name": "engineered mutation",
        }
    ]
    assert q["sequence_differences"] == [
        {
            "polymer_entity": "1",
            "seq_id": 17,
            "position": 16,
            "reference": "N",
            "residue": "D",
        }
    ]
    (construct,) = q["construct"]
    assert construct["length"] == 250
    assert construct["tags"] == [{"name": "expression tag", "seq_ids": [[1, 2]]}]
    assert construct["expression_host"] == [
        {"name": "Escherichia coli BL21(DE3)", "taxon_id": 469008}
    ]
    assert q["refinement"] == [{"method": "X-ray", "r_free": 0.2242, "r_work": 0.1794}]
    assert (q["deposited"], q["released"]) == ("2014-05-29", "2015-02-04")
    item = _item(hs, "pdb:4UNK")
    assert item["substitutions"] == ["N16D"]
    assert item["state"]["sequence"] == "mutant"


def test_a_modified_residue_is_not_a_substitution(cards):
    tc, _ = cards
    item = _item(tc, "pdb:2OMA")
    # RCSB lists a modified cysteine among "mutations"; the sequence is the reference.
    assert item["substitutions"] == []
    assert item["modified_residues"] == ["C118"]
    assert item["state"]["sequence"] == "reference"


def test_a_chimera_is_never_the_reference(cards):
    tc, _ = cards
    item = _item(tc, "pdb:3Q37", region=[[10, 20]])
    assert item["state"]["sequence"] == "chimera"
    # The TbTIM segments are not TcTIM residues: TcTIM 19-43 has no coordinates here.
    assert item["observed"]["A"][:2] == [[4, 18], [44, 100]]
    assert item["missing_in_region"]["A"] == [19, 20]
    assert item["complete_chains"] == []


def test_missing_residues_are_reported_per_chain(cards):
    _, hs = cards
    item = _item(hs, "pdb:4UNK", region=[1, 2, [3, 6], 247])
    # Chain A has coordinates for UniProt 3-247, chain B for 5-246 ...
    assert item["missing_in_region"] == {"A": [1, 2], "B": [1, 2, 3, 4, 247]}
    assert item["complete_chains"] == []
    # ... and without a region nothing is computed.
    assert _item(hs, "pdb:4UNK")["missing_in_region"] is None


def test_the_inventory_groups_like_with_like(cards):
    tc, hs = cards
    inventory = Deck([tc, hs]).structure_inventory(regions={TCTIM: [96], HSTIM: [95]})
    assert inventory["rule"]["rule"] == INVENTORY_RULE
    assert inventory["rule"]["parameters"]["state_rule"] == STATE_RULE
    shared = [g for g in inventory["states"] if g["shared"]]
    (group,) = shared
    assert group["state"] == {
        "method": "X-ray",
        "coverage": "full_length",
        "sequence": "reference",
        "ligands": "ligand_of_interest",
        "oligomer": "Homo 2-mer",
        "in_complex": False,
    }
    assert group["structures"] == {TCTIM: ["pdb:1SUX"], HSTIM: ["pdb:1HTI"]}
    # Mutants are never grouped with the wild type.
    mutants = {
        ref
        for g in inventory["states"]
        if g["state"]["sequence"] == "mutant"
        for refs in g["structures"].values()
        for ref in refs
    }
    assert mutants == {"pdb:2VOM", "pdb:4HHP", "pdb:4UNK"}
    # Each protein's region in its own numbering.
    rows = {(r["card_id"], r["structure_ref"]): r for r in inventory["items"]}
    assert rows[(TCTIM, "pdb:1SUX")]["complete_chains"] == ["A", "B"]


def test_structures_without_state_say_why(cards):
    tc, hs = cards
    inventory = Deck([tc, hs]).structure_inventory()
    reasons = {
        e["structure_ref"]: e["reason"] for e in inventory["not_inventoried"][TCTIM]
    }
    assert reasons == {"pdb:1CI1": "not_found"}
    # Peptide complexes are excluded, and the exclusion is reported.
    assert "pdb:1KLG" in inventory["excluded"][HSTIM]

    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    bare, _ = sabueso.resolve("P52270", resolver=resolver)
    listed = Deck([bare]).structure_inventory()["not_inventoried"][TCTIM]
    assert {e["reason"] for e in listed} == {"not_requested"}


def test_a_region_is_checked():
    with pytest.raises(ArgumentError):
        Deck([]).structure_inventory(regions=[[5, 2]])


#: TcTIM -> HsTIM positions over a gap-free window of the two sequences
#: (GHSERR...GE, 95-115), as an alignment would give them.
WINDOW = {p: p for p in range(95, 116)}


def test_groups_can_read_ligands_coarsely(cards):
    tc, hs = cards
    inventory = Deck([tc, hs]).structure_inventory(
        group_by=("method", "coverage", "sequence", "ligands:interest")
    )
    assert inventory["rule"]["parameters"]["state"] == [
        "method",
        "coverage",
        "sequence",
        "ligands:interest",
    ]
    apo = [
        g
        for g in inventory["states"]
        if g["state"]["sequence"] == "reference"
        and g["state"]["ligands:interest"] == "none_of_interest"
    ]
    # "no ligands" (1TCD) and "no ligand of interest" (2OMA) are one apo group now.
    (group,) = apo
    assert group["structures"][TCTIM] == ["pdb:1TCD", "pdb:2OMA"]


def test_substitutions_are_related_through_residue_maps(cards):
    tc, hs = cards
    deck = Deck([tc, hs])
    keys = ("method", "coverage", "sequence", "ligands:interest", "substitutions")
    mapped = deck.structure_inventory(
        group_by=keys, residue_maps={TCTIM: WINDOW}, reference=HSTIM
    )
    # E105D in TcTIM (4HHP) and HsTIM (2VOM), at one reference position.
    assert mapped["shared_substitutions"] == [
        {
            "reference_position": 105,
            "residue": "D",
            "structures": {TCTIM: ["pdb:4HHP"], HSTIM: ["pdb:2VOM"]},
        }
    ]
    (group,) = [g for g in mapped["states"] if g["state"]["substitutions"] == ["105D"]]
    assert group["shared"]
    assert group["structures"] == {TCTIM: ["pdb:4HHP"], HSTIM: ["pdb:2VOM"]}
    rows = {r["structure_ref"]: r for r in mapped["items"]}
    assert rows["pdb:4HHP"]["substitutions_in_reference"] == [
        {"label": "E105D", "position": 105, "reference_position": 105, "residue": "D"}
    ]
    assert mapped["rule"]["parameters"]["mapped"] == [TCTIM]

    # Without a map, equal numbers are never taken as equivalent positions.
    unmapped = deck.structure_inventory(group_by=keys)
    assert unmapped["shared_substitutions"] == []
    assert not any(
        g["shared"] for g in unmapped["states"] if g["state"]["sequence"] == "mutant"
    )


def test_group_by_and_reference_are_checked(cards):
    tc, hs = cards
    with pytest.raises(ArgumentError):
        Deck([tc, hs]).structure_inventory(group_by=("resolution",))
    with pytest.raises(ArgumentError):
        Deck([tc, hs]).structure_inventory(reference="sabueso:protein:uniprot:P00000")
    with pytest.raises(ArgumentError):
        Deck([tc, hs]).structure_inventory(residue_maps={TCTIM: {0: 1}})


def test_the_oligomer_is_the_one_the_authors_defined(cards):
    tc, hs = cards
    # 2V5B, "The monomerization of TcTIM": software predicts a dimer (assembly 1), the
    # authors defined a monomer (assembly 2). Rule structure_state@2 reads the authors'.
    item = _item(tc, "pdb:2V5B")
    assert item["state"]["oligomer"] == "Monomer"
    assert item["oligomer_basis"] == "author"
    assert item["oligomer_disagreement"] is True
    assert item["assembly_states"] == {
        "author": ["Monomer"],
        "software": ["Homo 2-mer"],
    }
    # 1WYI: the authors defined a tetramer, software a dimer; both are shown.
    item = _item(hs, "pdb:1WYI")
    assert item["state"]["oligomer"] == "Homo 4-mer"
    assert item["oligomer_disagreement"] is True
    # Author and software agree: no disagreement.
    item = _item(tc, "pdb:1TCD")
    assert (item["state"]["oligomer"], item["oligomer_basis"]) == (
        "Homo 2-mer",
        "author",
    )
    assert item["oligomer_disagreement"] is False
    assert tc.structures()["state_rule"]["rule"] == STATE_RULE == "structure_state@2"


def test_a_partial_rcsb_entry_is_kept_and_reported(tmp_path):
    # RCSB may fail on the instance-level fields of an entry (#74). The client then
    # fetches the entry without them and marks it partial; the card keeps what came.
    import json
    import shutil
    import warnings

    from sabueso._private.smonitor.warnings import EnrichmentPartialWarning

    shutil.copytree(
        "temp_data", tmp_path / "data", ignore=shutil.ignore_patterns("rcsb")
    )
    (tmp_path / "data" / "rcsb").mkdir()
    entry = json.loads(open("temp_data/rcsb/1TCD.json").read())
    for pe in entry["polymer_entities"]:
        for instance in pe["polymer_entity_instances"]:
            instance.pop("rcsb_polymer_instance_feature", None)
            instance.pop("rcsb_ligand_neighbors", None)
    entry["_partial"] = {
        "missing": ["rcsb_polymer_instance_feature", "rcsb_ligand_neighbors"],
        "reason": "server-side exception",
    }
    (tmp_path / "data" / "rcsb" / "1TCD.json").write_text(json.dumps(entry))
    data = str(tmp_path / "data")
    resolver = EntityResolver(
        FixtureUniProtClient(data), rcsb_client=FixtureRCSBClient(data)
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        card, _ = sabueso.resolve("P52270", resolver=resolver, structures=["1TCD"])
    assert any(isinstance(w.message, EnrichmentPartialWarning) for w in caught)
    (record,) = [e for e in card.quality["enrichments"] if e.get("structure") == "1TCD"]
    assert record["status"] == "partial" and record["missing"]
    item = _item(card, "pdb:1TCD")
    assert item["method"] == "X-ray" and item["state"]["oligomer"] == "Homo 2-mer"
    assert item["observed"] is None  # no instance features: unknown, never assumed
    (row,) = [r for r in card.knowledge_state()["rows"] if r["source"] == "RCSB PDB"]
    assert row["state"] == "partial"
    assert row["basis"]["incomplete_for"] == ["1TCD"]


def test_substitutions_are_given_in_the_authors_numbering_too(cards):
    tc, hs = cards
    # RCSB states the author numbering per residue (#73); depositors often number the
    # mature protein, one less than UniProt here.
    item = _item(hs, "pdb:2VOM")
    assert item["substitutions"] == ["E105D"]
    assert item["author_substitutions"] == ["E104D"]  # as the paper names it
    assert _item(hs, "pdb:4UNK")["author_substitutions"] == ["N15D"]
    # 2V5B renumbers the swapped loop: UniProt 69-71 are the authors' 76-78.
    from sabueso.mappings.rcsb_structures import author_position

    numbering = _item(tc, "pdb:2V5B")["author_numbering"]["A"]
    assert [author_position(numbering, p) for p in (68, 69, 71, 80)] == [
        "68",
        "76",
        "78",
        "80",
    ]
    rows = {r["structure_ref"]: r for r in hs.table("structures")}
    assert rows["pdb:2VOM"]["author_substitutions"] == "E104D"
