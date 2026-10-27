"""Storage accounting preserves UTF-8 and distinguishes exact JSON values."""

import json

import pytest

from devtools.inspect_exploration_storage import inspect_storage


def test_complete_byte_accounting_and_exact_repetition_preserve_original(tmp_path):
    payload = {"nested": [False, 0, None, "", "α🧬", {"unit": "µM"}]}
    data = {
        "format": "synthetic diagnostic input, not a validated exploration",
        "cards": {},
        "views": {
            "one": {"native_payload": payload, "selection": True},
            "two": {"native_payload": payload, "selection": 1},
        },
        "unknown_extension": {"quote": '"\\'},
    }
    raw = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    path = tmp_path / "input.json"
    path.write_bytes(raw)
    report = inspect_storage(path)
    assert report["canonical_total_bytes"] == len(raw)
    assert sum(report["section_canonical_bytes"].values()) + report[
        "root_framing_bytes"
    ] == len(raw)
    part = report["view_parts"]["native_payload"]
    assert part["occurrences"] == 2 and part["distinct_canonical_values"] == 1
    assert part["repeated_occurrence_bytes"] == part["distinct_canonical_bytes"]
    assert report["view_parts"]["selection"]["distinct_canonical_values"] == 2
    assert report["source_queries"] == 0 and path.read_bytes() == raw


@pytest.mark.parametrize("raw", ['{"views":{},"views":{}}', '{"views":{},"x":NaN}'])
def test_ambiguous_or_nonfinite_json_is_refused_without_rewriting(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        inspect_storage(path)
    assert path.read_text(encoding="utf-8") == raw
