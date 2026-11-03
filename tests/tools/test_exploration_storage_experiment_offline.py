"""Adversarial checks for an engineering prototype, not an admitted reader."""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from devtools import experiment_exploration_storage as layout


def original():
    return layout.encode(
        {
            "format": "synthetic; not a scientific reading",
            "extension": {"null": None, "unit": "µM"},
            "views": {
                "one": {
                    "state": {"a": False},
                    "native_payload": {"a": 0},
                    "selection": ["α🧬", {"part_ref": "literal"}],
                    "flags": None,
                    "origin": None,
                },
                "two": {
                    "state": {"a": False},
                    "native_payload": {"a": 0.0},
                    "selection": ["α🧬", {"part_ref": "literal"}],
                    "flags": None,
                    "origin": "one",
                },
            },
        }
    )


def test_exact_typed_occurrences_unknown_fields_and_literal_reference_lookalikes():
    raw = original()
    packed = layout.pack(raw)
    assert len(packed["pools"]["state"]) == 1
    assert len(packed["pools"]["native_payload"]) == 2
    assert layout.unpack(layout.parse(layout.encode(packed))) == raw
    expanded = layout.parse(layout.unpack(packed))
    expanded["views"]["one"]["state"]["a"] = True
    assert layout.parse(layout.unpack(packed))["views"]["one"]["state"]["a"] is False
    assert expanded["views"]["two"]["state"]["a"] is False


def test_empty_views_and_absent_parts_are_not_filled_in():
    for data in [
        {"views": {}},
        {"views": {"one": {"unknown": False}, "two": {"state": None}}},
    ]:
        raw = layout.encode(data)
        assert layout.unpack(layout.pack(raw)) == raw


@pytest.mark.parametrize(
    "raw",
    [
        b'{"views":{},"views":{}}',
        b'{"views":{},"bad":NaN}',
        b'{"views":{},"bad":1e999}',
        b'{ "views": {} }',
    ],
)
def test_ambiguous_nonfinite_or_noncanonical_inputs_are_refused(raw):
    with pytest.raises(ValueError):
        layout.pack(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        "format",
        "unknown_top",
        "unknown_pool",
        "unknown_scaffold",
        "unreferenced",
        "changed_part",
        "foreign_kind",
        "missing",
        "shadow",
        "bytes_bool",
        "bytes_lie",
        "hash",
    ],
)
def test_changed_layout_is_not_silently_repaired(mutation):
    packed = layout.pack(original())
    if mutation == "format":
        packed["format"] += "unknown"
    elif mutation == "unknown_top":
        packed["new"] = None
    elif mutation == "unknown_pool":
        packed["pools"]["other"] = {}
    elif mutation == "unknown_scaffold":
        packed["views"]["one"]["extra"] = None
    elif mutation == "unreferenced":
        packed["pools"]["state"][hashlib.sha256(b'"unused"').hexdigest()] = "unused"
    elif mutation == "changed_part":
        key = next(iter(packed["pools"]["state"]))
        packed["pools"]["state"][key] = {"a": True}
    elif mutation == "foreign_kind":
        packed["views"]["one"]["parts"]["state"] = packed["views"]["one"]["parts"][
            "native_payload"
        ]
    elif mutation == "missing":
        packed["views"]["one"]["parts"]["state"] = "0" * 64
    elif mutation == "shadow":
        packed["views"]["one"]["fields"]["state"] = {}
    elif mutation == "bytes_bool":
        packed["original"]["bytes"] = True
    elif mutation == "bytes_lie":
        packed["original"]["bytes"] -= 1
    else:
        packed["original"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        layout.unpack(packed)


def test_amplified_output_refuses_before_full_encoding_and_allows_explicit_override(
    monkeypatch,
):
    raw = layout.encode({"views": {str(i): {"state": "x" * 4000} for i in range(100)}})
    packed = layout.pack(raw)
    encode = layout.encode

    def guarded(value):
        if isinstance(value, dict) and "views" in value:
            pytest.fail("Expanded wire was encoded before its byte preflight")
        return encode(value)

    with monkeypatch.context() as temporary:
        temporary.setattr(layout, "encode", guarded)
        with pytest.raises(
            ValueError, match=f"requires {len(raw)} bytes; configured limit 1024"
        ):
            layout.unpack(packed, max_expanded_bytes=1024)
    assert layout.unpack(packed, max_expanded_bytes=len(raw)) == raw
    assert layout.unpack(packed, max_expanded_bytes=None) == raw


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.0, "none"])
def test_limit_type_is_explicit(limit):
    with pytest.raises(ValueError, match="limit must be positive or None"):
        layout.unpack(layout.pack(original()), max_expanded_bytes=limit)


def test_original_historical_capsule_bytes_are_not_regenerated():
    root = Path(__file__).resolve().parent.parent.parent
    raw = (root / "tests/core/data/card_exploration_literal_v1.json").read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    assert layout.unpack(layout.pack(raw)) == raw
    assert (
        hashlib.sha256(
            (root / "tests/core/data/card_exploration_literal_v1.json").read_bytes()
        ).hexdigest()
        == before
    )


def test_cli_reproduces_both_physical_baselines_and_preserves_input(tmp_path):
    raw = original()
    source, output = tmp_path / "input.json", tmp_path / "experiment"
    source.write_bytes(raw)
    layout.main([str(source), str(output), "--max-expanded-bytes", "none"])
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["byte_exact"] and report["max_expanded_bytes"] is None
    assert report["verification"].startswith("Physical byte reconstruction only")
    assert (
        gzip.decompress((output / "original.experimental.json.gz").read_bytes()) == raw
    )
    shared = (output / "unsupported-shared-layout.json").read_bytes()
    assert (
        gzip.decompress((output / "shared.experimental.json.gz").read_bytes()) == shared
    )
    assert layout.unpack(layout.parse(shared)) == raw
    for name, receipt in report["artifacts"].items():
        data = (output / name).read_bytes()
        assert len(data) == receipt["bytes"]
        assert hashlib.sha256(data).hexdigest() == receipt["sha256"]
    assert source.read_bytes() == raw


def test_cli_refuses_existing_destination_without_overwriting(tmp_path):
    source, output = tmp_path / "input.json", tmp_path / "existing"
    source.write_bytes(original())
    output.mkdir()
    sentinel = output / "caller-output"
    sentinel.write_bytes(b"retain caller output")
    with pytest.raises(SystemExit) as exc:
        layout.main([str(source), str(output)])
    assert exc.value.code == 2
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"retain caller output"


def test_input_limit_refuses_before_pack_and_before_output_creation(
    tmp_path, monkeypatch
):
    source, output = tmp_path / "input.json", tmp_path / "not-created"
    raw = original()
    source.write_bytes(raw)

    def forbidden(*args):
        pytest.fail("Input was parsed/packed before its byte guard")

    monkeypatch.setattr(layout, "pack", forbidden)
    with pytest.raises(SystemExit) as exc:
        layout.main(
            [str(source), str(output), "--max-expanded-bytes", str(len(raw) - 1)]
        )
    assert exc.value.code == 2 and not output.exists()
    assert source.read_bytes() == raw


@pytest.mark.parametrize("value", ["0", "-1", "1.0", "automatic"])
def test_cli_invalid_limits_fail_before_accessing_input(tmp_path, value):
    output = tmp_path / "not-created"
    with pytest.raises(SystemExit) as exc:
        layout.main(
            [
                str(tmp_path / "missing-input"),
                str(output),
                "--max-expanded-bytes",
                value,
            ]
        )
    assert exc.value.code == 2 and not output.exists()


def test_public_reader_does_not_admit_experimental_layout(tmp_path):
    import sabueso
    from sabueso.core.errors import StorageError

    source = tmp_path / "unsupported.json"
    source.write_bytes(layout.encode(layout.pack(original())))
    with pytest.raises(StorageError, match="Unsupported exploration format"):
        sabueso.read_exploration(source)


def test_reconstructed_genuine_original_keeps_its_inert_verifier(tmp_path, monkeypatch):
    import socket

    import sabueso
    from sabueso.core.card import Card

    def forbidden(*args, **kwargs):
        pytest.fail("Original receiving must not construct a Card or query a source")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    root = Path(__file__).resolve().parent.parent.parent
    original_path = root / "tests/core/data/card_exploration_literal_v1.json"
    raw = original_path.read_bytes()
    expected = layout.parse(raw)["bundle_digest"]
    reconstructed = tmp_path / "original.json"
    reconstructed.write_bytes(layout.unpack(layout.pack(raw)))
    saved = sabueso.read_exploration(reconstructed, expected_digest=expected)
    assert saved.validation["integrity"] == "verified"
    assert saved.validation["verifier"] == "literal_exploration_binding@1"
    assert saved.view_ref == layout.parse(raw)["root_view_ref"]
    assert original_path.read_bytes() == raw
