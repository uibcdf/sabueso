"""Version-specific binding selection and immutable cross-backend frames."""

import copy
import importlib
from types import SimpleNamespace

import pytest

from devtools import compare_exploration_compressors as bench
from devtools import probe_zstd_backend as probe


@pytest.mark.parametrize(
    "minor,expected",
    [
        (11, "backports.zstd"),
        (12, "backports.zstd"),
        (13, "backports.zstd"),
        (14, "compression.zstd"),
    ],
)
def test_version_selects_same_api_without_algorithm_fallback(
    monkeypatch, minor, expected
):
    calls = []
    fake = SimpleNamespace(
        CompressionParameter=SimpleNamespace(
            compression_level=SimpleNamespace(bounds=lambda: (-100, 22)),
            nb_workers=400,
            checksum_flag=201,
        ),
        compress=lambda *a, **k: b"frame",
        decompress=lambda raw: b"original",
        zstd_version="synthetic",
    )

    # SimpleNamespace is unhashable; use an integer-like enum key with bounds.
    class Level(int):
        def bounds(self):
            return (-100, 22)

    fake.CompressionParameter.compression_level = Level(100)
    with monkeypatch.context() as context:
        context.setattr(bench.sys, "version_info", (3, minor))
        context.setattr(
            bench.importlib, "import_module", lambda name: calls.append(name) or fake
        )
        context.setattr(bench.importlib.metadata, "version", lambda name: "1.8.0")
        _, _, metadata = bench._functions("zstd", 3)
    assert calls == [expected] and metadata["module"] == expected
    assert metadata["distribution_version"] == ("1.8.0" if minor < 14 else None)


def test_missing_native_does_not_try_illegal_backport_on_python314(monkeypatch):
    calls = []

    def missing(name):
        calls.append(name)
        raise ModuleNotFoundError(name)

    with monkeypatch.context() as context:
        context.setattr(bench.sys, "version_info", (3, 14))
        context.setattr(bench.importlib, "import_module", missing)
        with pytest.raises(ImportError):
            bench._functions("zstd", 3)
    assert calls == ["compression.zstd"]


def test_selected_backend_reads_both_genuine_producers_and_new_frames():
    report = probe.emit()
    result = probe.verify_report(report)
    assert result["payloads_verified"] == 2 and result["original_byte_exact"]
    assert result["consumer_backend"]["module"] in {
        "compression.zstd",
        "backports.zstd",
    }


@pytest.mark.parametrize(
    "mutation", ["truncated", "corrupt", "trailing", "concatenated", "expansion"]
)
def test_bounded_complete_frame_contract(mutation):
    compress, _, backend = bench._functions("zstd", 3)
    module = importlib.import_module(backend["module"])
    raw = b"original" * 50
    frame = compress(raw)
    if mutation == "truncated":
        frame = frame[:-1]
    elif mutation == "corrupt":
        frame = frame[:-1] + bytes([frame[-1] ^ 1])
    elif mutation == "trailing":
        frame += b"unexpected"
    elif mutation == "concatenated":
        frame += compress(b"")
    else:
        frame = compress(raw + b"too much")
    with pytest.raises(ValueError):
        probe.decode_frame(module, frame, raw)


@pytest.mark.parametrize(
    "mutation", ["head", "membership", "original", "frame", "unknown"]
)
def test_report_scope_is_not_silently_rebound(mutation):
    report = probe.emit()
    report["producer"]["head_sha"] = "expected"
    if mutation == "head":
        report["producer"]["head_sha"] = "foreign"
    elif mutation == "membership":
        report["payloads"][1] = copy.deepcopy(report["payloads"][0])
    elif mutation == "original":
        report["payloads"][0]["original_sha256"] = "0" * 64
    elif mutation == "frame":
        report["payloads"][0]["frame_sha256"] = "0" * 64
    else:
        report["unexpected"] = None
    with pytest.raises(ValueError):
        probe.verify_report(report, expected_head="expected")


def test_frozen_producer_frames_keep_actual_hashes():
    import hashlib

    assert (
        hashlib.sha256(probe.FIXTURE.read_bytes()).hexdigest() == probe.FIXTURE_SHA256
    )
    assert (
        hashlib.sha256(probe.BACKPORT_FIXTURE.read_bytes()).hexdigest()
        == probe.BACKPORT_SHA256
    )
