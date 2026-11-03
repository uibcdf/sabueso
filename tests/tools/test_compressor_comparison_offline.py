"""Comparison receipts preserve identity, missing backends and caller outputs."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from devtools import compare_exploration_compressors as bench


@pytest.mark.parametrize(
    "codec,level", [("none", None), ("gzip", 6), ("xz", 0), ("zstd", 3)]
)
def test_actual_backend_roundtrip_or_explicit_unavailability(tmp_path, codec, level):
    raw = json.dumps(
        {"literal": [False, 0, None, "µM", "α🧬"] * 100}, ensure_ascii=False
    ).encode()
    source = tmp_path / "original.json"
    source.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    row = bench.sample(source, codec, level, expected_sha256=digest)
    if row["status"] == "unavailable":
        assert row["reason"] and "compressed_bytes" not in row
    else:
        assert row["original_sha256"] == row["reconstructed_sha256"] == digest
        assert row["byte_exact"] and row["original_bytes"] == len(raw)
        assert row["compressed_bytes"] > 0
        assert (
            row["whole_worker_peak_rss_bytes"] is None
            or row["whole_worker_peak_rss_bytes"] > 0
        )
        if codec == "zstd":
            assert row["backend"]["nb_workers"] == 0
            assert row["backend"]["integrity"] == "frame checksum enabled"
    assert source.read_bytes() == raw


def test_unavailable_backend_is_not_substituted(tmp_path, monkeypatch):
    def unavailable(*args):
        raise ModuleNotFoundError("Native optional backend missing")

    monkeypatch.setattr(bench, "_functions", unavailable)
    row = bench.sample(tmp_path / "unread", "zstd", 3, expected_sha256="0" * 64)
    assert row["status"] == "unavailable" and row["codec"] == "zstd"
    assert "compressed_bytes" not in row and "encode_wall_seconds" not in row
    assert bench.summarize([row])["status"] == "unavailable"


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.0, "none"])
def test_invalid_budget_is_rejected_before_backend_loading(
    tmp_path, monkeypatch, limit
):
    monkeypatch.setattr(
        bench,
        "_functions",
        lambda *a: pytest.fail("Backend loaded before argument check"),
    )
    with pytest.raises(ValueError, match="Byte limit"):
        bench.sample(
            tmp_path / "unread",
            "zstd",
            3,
            expected_sha256="0" * 64,
            max_expanded_bytes=limit,
        )


def test_input_guard_digest_and_explicit_override(tmp_path):
    raw = b"original" * 50
    source = tmp_path / "original"
    source.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="raise --max-expanded-bytes"):
        bench.sample(
            source,
            "none",
            None,
            expected_sha256=digest,
            max_expanded_bytes=len(raw) - 1,
        )
    for limit in (len(raw), None):
        assert bench.sample(
            source, "none", None, expected_sha256=digest, max_expanded_bytes=limit
        )["byte_exact"]
    with pytest.raises(ValueError, match="Input hash changed"):
        bench.sample(source, "gzip", 1, expected_sha256="0" * 64)


def test_inexact_decoder_fails_without_positive_receipt(tmp_path, monkeypatch):
    source = tmp_path / "original"
    source.write_bytes(b"abc")
    monkeypatch.setattr(
        bench, "_functions", lambda *a: (lambda raw: raw, lambda raw: b"different", {})
    )
    with pytest.raises(ValueError, match="exact original-byte"):
        bench.sample(
            source, "gzip", 1, expected_sha256=hashlib.sha256(b"abc").hexdigest()
        )


def measured(codec="gzip", level=1):
    return {
        "status": "measured",
        "codec": codec,
        "level": level,
        "backend": {"module": codec, "version": "synthetic"},
        "original_sha256": "a" * 64,
        "compressed_bytes": 20,
        "encode_wall_seconds": 0.1,
        "encode_cpu_seconds": 0.1,
        "decode_wall_seconds": 0.01,
        "decode_cpu_seconds": 0.01,
        "whole_worker_peak_rss_bytes": None,
        "rss_basis": "synthetic unavailable measurement",
    }


@pytest.mark.parametrize(
    "mutation", ["availability", "hash", "backend", "setting", "rss"]
)
def test_mixed_comparison_scope_is_rejected(mutation):
    first, second = measured(), measured()
    if mutation == "availability":
        second = {
            "status": "unavailable",
            "codec": "gzip",
            "level": 1,
            "reason": "missing",
        }
    elif mutation == "hash":
        second["original_sha256"] = "b" * 64
    elif mutation == "backend":
        second["backend"] = {"version": "changed"}
    elif mutation == "setting":
        second["level"] = 9
    else:
        second["rss_basis"] = "different measurement method"
    with pytest.raises(ValueError):
        bench.summarize([first, second])


def test_summary_keeps_unmeasured_memory_unknown():
    result = bench.summarize([measured(), measured()])
    assert result["samples"] == 2 and result["medians"]["compressed_bytes"] == 20
    assert result["maximum_whole_worker_peak_rss_bytes"] is None


def test_worker_refuses_foreign_receipts(monkeypatch):
    row = {
        "codec": "gzip",
        "level": 1,
        "status": "measured",
        "byte_exact": True,
        "original_sha256": "a" * 64,
        "reconstructed_sha256": "b" * 64,
    }
    monkeypatch.setattr(
        bench.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            returncode=0, stdout=json.dumps(row), stderr=""
        ),
    )
    with pytest.raises(ValueError, match="receipt differs"):
        bench._worker("unused", "gzip", 1, "a" * 64, None)


def test_seeded_order_and_complete_repeat_membership(tmp_path, monkeypatch):
    source = tmp_path / "original"
    source.write_bytes(b"abc")
    calls = []

    def fake(path, codec, level, expected, limit):
        calls.append((codec, level))
        return {**measured(codec, level), "original_sha256": expected}

    monkeypatch.setattr(bench, "_worker", fake)
    settings = (("none", None), ("gzip", 1))
    first = bench.compare([source], repeats=3, seed=8, settings=settings)
    order = list(calls)
    calls.clear()
    second = bench.compare([source], repeats=3, seed=8, settings=settings)
    assert calls == order and first["samples"] == second["samples"]
    assert len(first["samples"]) == 6
    assert all(row["samples"] == 3 for row in first["summaries"])


def test_cli_preserves_existing_caller_output(tmp_path, monkeypatch):
    output = tmp_path / "caller"
    output.mkdir()
    sentinel = output / "retain"
    sentinel.write_bytes(b"caller-owned")
    monkeypatch.setattr(
        bench,
        "compare",
        lambda *a, **k: pytest.fail("Existing output should be refused before work"),
    )
    with pytest.raises(SystemExit) as exc:
        bench.main(["compare", str(tmp_path / "missing"), "--output", str(output)])
    assert exc.value.code == 2 and sentinel.read_bytes() == b"caller-owned"


def test_linux_peak_uses_current_worker_vmhwm(monkeypatch):
    monkeypatch.setattr(bench.sys, "platform", "linux")
    monkeypatch.setattr(
        bench.Path, "read_text", lambda self: "VmHWM:\t1234 kB\nVmRSS:\t1000 kB\n"
    )
    peak, basis = bench._rss()
    assert peak == 1234 * 1024 and "since exec" in basis


def test_linux_missing_peak_remains_unknown_instead_of_inheriting_parent_peak(
    monkeypatch,
):
    def unavailable(self):
        raise OSError("proc not available")

    monkeypatch.setattr(bench.sys, "platform", "linux")
    monkeypatch.setattr(bench.Path, "read_text", unavailable)
    peak, basis = bench._rss()
    assert peak is None and "no isolated worker peak" in basis


@pytest.mark.parametrize(
    "settings", [(), (("gzip", 1), ("gzip", 1)), (("unknown", 1),)]
)
def test_empty_duplicate_or_unknown_settings_refuse_before_input(tmp_path, settings):
    with pytest.raises(ValueError, match="setting"):
        bench.compare([tmp_path / "unread"], settings=settings)
