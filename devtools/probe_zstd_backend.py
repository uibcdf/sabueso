"""Standalone backend qualification; no public compressed-reader or runtime change.

Reports contain only two fixed public/synthetic payloads. Decode is bounded by
their known lengths and a 1 MiB window; this is not a general Card file decoder.
Direct optional imports qualify the external binding independently of Sabueso.
Production optional integration still requires DepDigest.
"""

import argparse
import base64
import hashlib
import importlib
import json
import os
import platform
import sys
from pathlib import Path

if __package__:
    from .compare_exploration_compressors import _functions
else:
    from compare_exploration_compressors import _functions

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/tools/data/zstd_native_v1.json"
FIXTURE_SHA256 = "b649597374069aa5e45105987691159fa674577dfbc2089c715eab52ccac2d0e"
BACKPORT_FIXTURE = ROOT / "tests/tools/data/zstd_backport_v1.json"
BACKPORT_SHA256 = "06627c52002c8c496fc12050a2931be5ad9f3109d831f89efa1d29867448feb5"
PREFIX = "ZSTD_BACKEND_PROBE_JSON "
FORMAT = "zstd_backend_probe@1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON member in backend report")
        result[key] = value
    return result


def parse_report(raw):
    require(len(raw) <= 4 * 1024**2, "Probe report exceeds its explicit 4 MiB scope")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)


def payloads():
    typed = {
        "scope": "Fully synthetic codec payload; no scientific claim",
        "values": [
            False,
            0,
            0.0,
            None,
            "",
            "α🧬",
            "µM",
            {"value": 1.0, "unit": "nanomolar"},
        ],
    }
    return {
        "typed-values": json.dumps(
            typed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8"),
        "original-literal-v1": (
            ROOT / "tests/core/data/card_exploration_literal_v1.json"
        ).read_bytes(),
    }


def decode_frame(module, frame, expected):
    require(
        isinstance(frame, bytes) and len(frame) <= 1024**2,
        "Probe frame exceeds its explicit 1 MiB scope",
    )
    decoder = module.ZstdDecompressor(
        options={module.DecompressionParameter.window_log_max: 20}
    )
    output = bytearray()
    pending = frame
    while True:
        try:
            output.extend(
                decoder.decompress(pending, max_length=len(expected) + 1 - len(output))
            )
        except module.ZstdError as exc:
            raise ValueError(f"Invalid Zstandard probe frame: {exc}") from exc
        require(
            len(output) <= len(expected),
            "Probe expanded beyond its fixed expected payload",
        )
        if decoder.eof:
            require(
                not decoder.unused_data,
                "Unexpected concatenated frame or trailing data in probe",
            )
            break
        require(not decoder.needs_input, "Truncated Zstandard probe frame")
        pending = b""
    require(bytes(output) == expected, "Probe original byte reconstruction differs")
    return bytes(output)


def _verify_payloads(rows, module, expected):
    require(
        isinstance(rows, list) and len(rows) == len(expected),
        "Probe payload membership differs",
    )
    seen = set()
    for row in rows:
        require(
            isinstance(row, dict)
            and set(row)
            == {
                "name",
                "original_bytes",
                "original_sha256",
                "frame_sha256",
                "frame_base64",
            },
            "Unknown probe payload shape",
        )
        name = row["name"]
        require(
            name in expected and name not in seen, "Unknown or duplicate probe payload"
        )
        seen.add(name)
        raw = expected[name]
        require(
            type(row["original_bytes"]) is int
            and row["original_bytes"] == len(raw)
            and row["original_sha256"] == hashlib.sha256(raw).hexdigest(),
            "Probe original identity differs",
        )
        require(
            isinstance(row["frame_base64"], str)
            and len(row["frame_base64"]) <= 2 * 1024**2,
            "Probe encoded-frame budget exceeded",
        )
        frame = base64.b64decode(row["frame_base64"], validate=True)
        require(
            hashlib.sha256(frame).hexdigest() == row["frame_sha256"],
            "Probe frame checksum differs",
        )
        decode_frame(module, frame, raw)
    return len(seen)


def emit():
    compress, _, backend = _functions("zstd", 3)
    module = importlib.import_module(backend["module"])
    if backend["module"] == "backports.zstd":
        require(
            backend["distribution_version"] == "1.8.0",
            "Qualification requires pinned backports.zstd 1.8.0",
        )
    raw_fixture = FIXTURE.read_bytes()
    require(
        hashlib.sha256(raw_fixture).hexdigest() == FIXTURE_SHA256,
        "Original native fixture bytes changed",
    )
    fixture = json.loads(raw_fixture)
    require(
        fixture["format"] == "zstd_native_codec_fixture@1", "Unsupported native fixture"
    )
    expected = payloads()
    _verify_payloads(fixture["payloads"], module, expected)
    backport_raw = BACKPORT_FIXTURE.read_bytes()
    require(
        hashlib.sha256(backport_raw).hexdigest() == BACKPORT_SHA256,
        "Original backport fixture bytes changed",
    )
    _verify_payloads(json.loads(backport_raw)["payloads"], module, expected)
    rows = []
    for name, raw in expected.items():
        frame = compress(raw)
        decode_frame(module, frame, raw)
        rows.append(
            {
                "name": name,
                "original_bytes": len(raw),
                "original_sha256": hashlib.sha256(raw).hexdigest(),
                "frame_sha256": hashlib.sha256(frame).hexdigest(),
                "frame_base64": base64.b64encode(frame).decode("ascii"),
            }
        )
    return {
        "format": FORMAT,
        "producer": {
            "head_sha": os.environ.get("GITHUB_SHA"),
            "python": list(sys.version_info[:3]),
            "platform": platform.system(),
            "backend": backend,
            "fixture_sha256": FIXTURE_SHA256,
            "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "payloads": rows,
    }


def verify_report(report, *, expected_head=None):
    require(
        isinstance(report, dict)
        and set(report) == {"format", "producer", "payloads"}
        and report["format"] == FORMAT,
        "Unknown backend probe report",
    )
    producer = report["producer"]
    require(
        isinstance(producer, dict) and producer.get("fixture_sha256") == FIXTURE_SHA256,
        "Probe fixture identity differs",
    )
    if expected_head is not None:
        require(producer.get("head_sha") == expected_head, "Probe source head differs")
    _, _, backend = _functions("zstd", 3)
    module = importlib.import_module(backend["module"])
    count = _verify_payloads(report["payloads"], module, payloads())
    return {
        "producer": producer,
        "consumer_backend": backend,
        "payloads_verified": count,
        "original_byte_exact": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("emit")
    verify = sub.add_parser("verify")
    verify.add_argument("reports", nargs="+", type=Path)
    verify.add_argument("--expected-head")
    args = parser.parse_args(argv)
    try:
        if args.operation == "emit":
            print(PREFIX + json.dumps(emit(), sort_keys=True, separators=(",", ":")))
        else:
            results = []
            for path in args.reports:
                with path.open("rb") as stream:
                    raw = stream.read(4 * 1024**2 + 1)
                results.append(
                    verify_report(parse_report(raw), expected_head=args.expected_head)
                )
            print(
                json.dumps(
                    {"reports_verified": len(results), "results": results},
                    sort_keys=True,
                )
            )
    except (OSError, ValueError, TypeError, ImportError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
