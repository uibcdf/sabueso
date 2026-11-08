"""Actual clinical transports, resaves and resealed semantic-refusal controls."""

import json
from copy import deepcopy

import pytest
from test_card_clinical_history_offline import (
    assert_saved_original,
    block_current,
    independent_receive,
)
from test_card_clinical_history_offline import original as original

import sabueso
from sabueso.core import card_exploration_storage as storage
from sabueso.core.card_exploration_shared_values_v7 import pack, unpack
from sabueso.core.errors import StorageError


@pytest.fixture(scope="module")
def clinical_file(original, tmp_path_factory):
    nodes, _ = original.hydrate("bare")
    root = nodes[original.case("bare")["named_views"]["root"]]
    path = tmp_path_factory.mktemp("clinical-original-file") / "original.json"
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        root.save(path)
    raw = json.loads(path.read_text())
    logical = (
        unpack(raw, limit=None, component_limit=None)[0]
        if raw["format"] == "sabueso.card_exploration@26"
        else {
            key: value
            for key, value in raw.items()
            if key not in ("digests", "bundle_digest")
        }
    )
    return path, logical


def test_resealed_original_clinical_control_is_accepted(clinical_file, monkeypatch):
    _, logical = clinical_file
    sealed = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    saved = storage._restore(
        sealed, sealed["bundle_digest"], max_logical_bytes=None, component_limit=None
    )
    assert saved.validation["verifier"] == "clinical_exploration_binding@1"


def test_saved_clinical_requests_and_catalogs_keep_original_scope(
    clinical_file, monkeypatch
):
    from sabueso.core import card_exploration as human
    from sabueso.core import card_exploration_profiles as profiles

    block_current(monkeypatch)
    saved = sabueso.read_exploration(clinical_file[0])
    monkeypatch.setattr(human, "_TOPICS", {})
    monkeypatch.setattr(profiles, "QUESTIONS", {})
    monkeypatch.setattr(profiles, "COMMON_QUESTIONS", {})
    monkeypatch.setattr(profiles, "NATURE_TOPICS", {})
    assert "clinical" in saved.explorer.topics().native_payload
    assert "clinical_context" in saved.explorer.questions().native_payload
    missing = saved.explorer.access.select(
        "clinical", where={"chembl_max_phase": 3.5}, skip_digestion=True
    )
    assert missing.count == 0
    assert missing.page()["outcome"]["status"] == "not_saved"


@pytest.mark.parametrize("compression", ("none", "gzip", "zstd"))
def test_clinical_original_transport_and_resave(
    clinical_file, original, monkeypatch, tmp_path, compression
):
    block_current(monkeypatch)
    source, _ = clinical_file
    root = sabueso.read_exploration(source)
    question = root.explorer.answer("clinical_context", skip_digestion=True)
    selected = question.filter("chembl_max_phase", equals=4.0)
    assert selected.items()[0].open().back() is selected
    assert selected.items()[0].explain().back() is selected
    assert selected.items()[0].related().back() is selected
    path = tmp_path / ("resaved-" + compression + ".json")
    root.save(path, compression=compression)
    saved = sabueso.read_exploration(path)
    assert_saved_original(saved, original, "bare")
    independent_receive(str(path), str(original.archive.name), "bare")


@pytest.mark.parametrize(
    "change",
    (
        "native_phase",
        "typed_cell",
        "coverage",
        "question",
        "display_operand_type",
        "source_endpoint",
        "origin",
        "focal",
    ),
)
def test_resealed_clinical_semantic_changes_are_refused(
    clinical_file, monkeypatch, change
):
    _, original = clinical_file
    logical = deepcopy(original)
    root_key = logical["root_navigation_ref"]
    root = logical["views"][root_key]
    if change == "native_phase":
        root["native_payload"]["max_phase"] = 3.0
    elif change == "typed_cell":
        item = next(iter(root["state"]["items"].values()))
        assert type(item["cells"]["chembl_max_phase"]["value"]) is float
        item["cells"]["chembl_max_phase"]["value"] = 4
    elif change == "coverage":
        root["state"]["coverage"]["rule"]["inputs"] = []
    elif change == "question":
        root["flags"]["_request"] = {
            "question": "measured_targets",
            "topic": "clinical",
            "options": {},
        }
    elif change == "display_operand_type":
        record = next(
            record
            for record in logical["views"].values()
            if record["flags"]["_record_panel"] == "clinical"
            and (record["flags"]["_display_request"] or {}).get("column")
            == "chembl_max_phase"
            and type(record["flags"]["_display_request"].get("equals")) is float
        )
        record["flags"]["_display_request"]["equals"] = 4
    elif change in ("source_endpoint", "origin"):
        record = next(
            record
            for record in logical["views"].values()
            if (record["flags"]["_context_override"] or {}).get("clinical_context")
            == "explanation"
        )
        if change == "source_endpoint":
            record["selection"]["target"]["location"] = root["selection"]["target"][
                "location"
            ]
        else:
            record["origin"] = next(
                key
                for key, candidate in logical["views"].items()
                if candidate["flags"]["_record_panel"] == "clinical"
                and not candidate["selected"]
            )
    else:
        root["focal"] = "unretained-capture"
    # Rebuild the complete shared-value DAG and outer digests. This tests semantic
    # binding beyond transport integrity; it makes no authenticity claim.
    sealed = storage._seal(pack(logical, None, threshold=0, min_saving=0))
    block_current(monkeypatch)
    with pytest.raises(StorageError):
        storage._restore(
            sealed,
            sealed["bundle_digest"],
            max_logical_bytes=None,
            component_limit=None,
        )
