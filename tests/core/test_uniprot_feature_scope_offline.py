"""Native feature scope must survive every mapper branch; inputs are synthetic."""

from copy import deepcopy

import pytest

from sabueso.core.errors import ConnectorError
from sabueso.mappings.uniprot import map_protein

TYPES = (
    "Active site",
    "Binding site",
    "Disulfide bond",
    "Natural variant",
    "Mutagenesis",
    "Alternative sequence",
    "Sequence conflict",
    "Glycosylation",
    "Lipidation",
    "Modified residue",
    "Transmembrane",
    "Topological domain",
    "Domain",
    "Chain",
    "Motif",
    "Region",
    "Helix",
    "Beta strand",
    "Turn",
)


def original(kind="Active site"):
    return {
        "primaryAccession": "P52270",
        "sequence": {"value": "M" * 10, "length": 10},
        "entryAudit": {"sequenceVersion": 7},
        "features": [
            {
                "type": kind,
                "description": "explicit synthetic feature",
                "location": {
                    "start": {"value": 2, "modifier": "EXACT"},
                    "end": {"value": 4, "modifier": "EXACT"},
                },
            }
        ],
    }


@pytest.mark.parametrize("kind", TYPES)
def test_all_feature_types_keep_native_molecule_uncertainty_and_revision(kind):
    record = original(kind)
    feature = record["features"][0]
    feature["molecule"] = "P52270-2"
    feature["location"]["start"]["modifier"] = "LESS_THAN"
    before = deepcopy(record)
    result = map_protein(record, "synthetic")
    assert record == before
    field, rows = next(iter(result["features"].items()))
    (value,) = rows
    assert value["location"]["sequence"] == {
        "sequence_id": None,
        "start": 2,
        "end": 4,
        "indexing": "1-based",
        "start_modifier": "LESS_THAN",
        "end_modifier": "EXACT",
    }
    (source,) = [a for a in result["source_assertions"] if a["field_path"] == field]
    assert source["asserted_value"] == value
    assert source["source_metadata"]["uniprot_feature"] == feature
    assert source["source_metadata"]["sequence_version"] == 7
    assert source["id"] in result["field_source_assertions"][field]


@pytest.mark.parametrize(
    "kind",
    ["Active site", "Binding site", "Natural variant", "Disulfide bond", "Helix"],
)
@pytest.mark.parametrize("endpoint", ["start", "end"])
def test_unknown_endpoints_are_not_dropped_or_replaced_with_another_position(
    kind, endpoint
):
    record = original(kind)
    record["features"][0]["location"][endpoint] = {"modifier": "UNKNOWN"}
    result = map_protein(record, "synthetic")
    (row,) = next(iter(result["features"].values()))
    axis = row["location"]["sequence"]
    assert axis[endpoint] is None and axis[endpoint + "_modifier"] == "UNKNOWN"
    assert axis["end" if endpoint == "start" else "start"] == (
        4 if endpoint == "start" else 2
    )


@pytest.mark.parametrize(
    "molecule", [None, "P52270", "UniProt:P52270", "Isoform 2", "P52270-2", ""]
)
def test_only_explicit_focal_or_implicit_canonical_scope_gets_the_canonical_axis(
    molecule,
):
    record = original()
    record["features"][0]["molecule"] = molecule
    result = map_protein(record, "synthetic")
    (row,) = result["features"]["features_positional.active_site"]
    assert row["location"]["sequence"]["sequence_id"] == (
        "UniProt:P52270" if molecule in (None, "P52270", "UniProt:P52270") else None
    )


@pytest.mark.parametrize(
    "malformed", ["feature", "location", "endpoint", "bool", "text"]
)
def test_existing_feature_types_reject_malformed_native_shapes(malformed):
    record = original()
    feature = record["features"][0]
    if malformed == "feature":
        record["features"] = [False]
    elif malformed == "location":
        feature["location"] = []
    elif malformed == "endpoint":
        feature["location"]["start"] = 2
    else:
        feature["location"]["start"]["value"] = True if malformed == "bool" else "2"
    with pytest.raises(ConnectorError):
        map_protein(record, "synthetic")


@pytest.mark.parametrize("value", [False, 0, "", {}, "not-an-array"])
def test_falsy_malformed_feature_collections_are_not_reported_as_missing_annotations(
    value,
):
    record = original()
    record["features"] = value
    with pytest.raises(ConnectorError, match="native array"):
        map_protein(record, "synthetic")


@pytest.mark.parametrize("value", [None, False, [], ""])
def test_malformed_native_feature_types_are_not_silently_skipped(value):
    record = original()
    record["features"][0]["type"] = value
    with pytest.raises(ConnectorError, match="nonempty native strings"):
        map_protein(record, "synthetic")
