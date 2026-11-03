"""Compare lossless codecs in serial fresh workers; no public storage API changes.

Timings cover in-memory encoding/decoding, excluding startup and file input.
RSS is the whole worker lifetime high-water mark, not isolated codec allocation.
Use a separate owned process/RAM/swap supervisor, especially for large inputs.
"""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_LIMIT = 64 * 1024**2
SETTINGS = (
    ("none", None),
    ("gzip", 1),
    ("gzip", 6),
    ("gzip", 9),
    ("zstd", 1),
    ("zstd", 3),
    ("zstd", 6),
    ("xz", 0),
    ("xz", 3),
    ("xz", 6),
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _limit(value):
    if value.lower() == "none":
        return None
    number = int(value)
    if number <= 0:
        raise ValueError("Use a positive byte count or 'none'.")
    return number


def _read(path, limit):
    _require(
        limit is None or (type(limit) is int and limit > 0),
        "Byte limit must be positive or None",
    )
    with Path(path).open("rb") as stream:
        raw = stream.read() if limit is None else stream.read(limit + 1)
    _require(
        limit is None or len(raw) <= limit,
        f"Input exceeds limit {limit}; raise --max-expanded-bytes explicitly or use 'none'.",
    )
    return raw


def _functions(codec, level):
    _require(codec in {"none", "gzip", "zstd", "xz"}, "Unknown codec")
    _require(
        (codec == "none" and level is None) or (codec != "none" and type(level) is int),
        "Invalid compression level type",
    )
    if codec == "none":
        return (lambda raw: raw), (lambda raw: raw), {"module": None, "version": None}
    if codec == "gzip":
        _require(0 <= level <= 9, "gzip level must be between 0 and 9")
        module = importlib.import_module("gzip")
        zlib = importlib.import_module("zlib")
        return (
            (lambda raw: module.compress(raw, compresslevel=level, mtime=0)),
            module.decompress,
            {
                "module": "gzip",
                "version": zlib.ZLIB_RUNTIME_VERSION,
                "integrity": "gzip CRC",
                "mtime": 0,
            },
        )
    if codec == "xz":
        _require(0 <= level <= 9, "xz preset must be between 0 and 9")
        module = importlib.import_module("lzma")
        return (
            (lambda raw: module.compress(raw, preset=level, check=module.CHECK_CRC64)),
            module.decompress,
            {
                "module": "lzma",
                "version": None,
                "version_note": "liblzma runtime version is not exposed by the stdlib API",
                "integrity": "CRC64",
            },
        )
    name = "compression.zstd" if sys.version_info >= (3, 14) else "backports.zstd"
    module = importlib.import_module(name)
    distribution = None
    if name == "backports.zstd":
        distribution = importlib.metadata.version("backports.zstd")
    parameter = module.CompressionParameter
    lower, upper = parameter.compression_level.bounds()
    _require(lower <= level <= upper, "zstd level outside backend bounds")
    options = {
        parameter.compression_level: level,
        parameter.nb_workers: 0,
        parameter.checksum_flag: 1,
    }
    return (
        (lambda raw: module.compress(raw, options=options)),
        module.decompress,
        {
            "module": name,
            "version": module.zstd_version,
            "distribution_version": distribution,
            "integrity": "frame checksum enabled",
            "nb_workers": 0,
        },
    )


def _rss():
    if sys.platform.startswith("linux"):
        try:
            status = Path("/proc/self/status").read_text()
            value = next(
                int(line.split()[1]) * 1024
                for line in status.splitlines()
                if line.startswith("VmHWM:")
            )
            return (
                value,
                "Linux /proc/self/status VmHWM; worker high-water mark since exec",
            )
        except (OSError, ValueError, StopIteration):
            return None, "Linux VmHWM unavailable; no isolated worker peak claimed"
    try:
        resource = importlib.import_module("resource")
    except ImportError:
        return None, "resource.ru_maxrss unavailable on this platform"
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return (
        int(value if sys.platform == "darwin" else value * 1024),
        "resource.ru_maxrss, whole process lifetime (may include inherited pre-exec peak), bytes normalized for this platform",
    )


def sample(path, codec, level, *, expected_sha256, max_expanded_bytes=DEFAULT_LIMIT):
    """Measure only our own encoded output; not an untrusted compressed-file reader."""
    _require(
        isinstance(expected_sha256, str)
        and len(expected_sha256) == 64
        and all(c in "0123456789abcdef" for c in expected_sha256),
        "Expected original SHA-256 is required",
    )
    _require(
        max_expanded_bytes is None
        or (type(max_expanded_bytes) is int and max_expanded_bytes > 0),
        "Byte limit must be positive or None",
    )
    try:
        compress, decompress, backend = _functions(codec, level)
    except ImportError as exc:
        return {
            "codec": codec,
            "level": level,
            "status": "unavailable",
            "reason": str(exc),
            "exception": type(exc).__name__,
        }
    raw = _read(path, max_expanded_bytes)
    digest = hashlib.sha256(raw).hexdigest()
    _require(digest == expected_sha256, "Input hash changed before sampling")
    started, cpu = time.perf_counter(), time.process_time()
    packed = compress(raw)
    encode_wall, encode_cpu = time.perf_counter() - started, time.process_time() - cpu
    started, cpu = time.perf_counter(), time.process_time()
    restored = decompress(packed)
    decode_wall, decode_cpu = time.perf_counter() - started, time.process_time() - cpu
    _require(restored == raw, "Codec failed exact original-byte reconstruction")
    _require(
        hashlib.sha256(_read(path, max_expanded_bytes)).hexdigest() == digest,
        "Input changed during sampling",
    )
    peak, basis = _rss()
    return {
        "codec": codec,
        "level": level,
        "status": "measured",
        "backend": backend,
        "original_bytes": len(raw),
        "original_sha256": digest,
        "compressed_bytes": len(packed),
        "compressed_sha256": hashlib.sha256(packed).hexdigest(),
        "reconstructed_sha256": hashlib.sha256(restored).hexdigest(),
        "encode_wall_seconds": encode_wall,
        "encode_cpu_seconds": encode_cpu,
        "decode_wall_seconds": decode_wall,
        "decode_cpu_seconds": decode_cpu,
        "whole_worker_peak_rss_bytes": peak,
        "rss_basis": basis,
        "byte_exact": True,
        "python": sys.version,
        "platform": platform.platform(),
    }


def _worker(path, codec, level, expected, limit):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "sample",
        str(path),
        codec,
        "none" if level is None else str(level),
        "--expected-sha256",
        expected,
        "--max-expanded-bytes",
        "none" if limit is None else str(limit),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    _require(
        result.returncode == 0, f"Worker failed ({codec}/{level}): {result.stderr}"
    )
    row = json.loads(result.stdout)
    _require(
        row.get("codec") == codec and row.get("level") == level,
        "Worker setting binding differs",
    )
    if row.get("status") == "measured":
        _require(
            row.get("byte_exact") is True
            and row.get("original_sha256") == expected
            and row.get("reconstructed_sha256") == expected,
            "Worker original-byte receipt differs",
        )
    else:
        _require(
            row.get("status") == "unavailable" and bool(row.get("reason")),
            "Missing or invalid worker outcome",
        )
    return row


def summarize(rows):
    """Keep availability explicit; do not replace unavailable metrics with zero."""
    _require(bool(rows), "No samples")
    _require(
        len({(row["codec"], row["level"]) for row in rows}) == 1, "Mixed codec settings"
    )
    statuses = {row["status"] for row in rows}
    _require(len(statuses) == 1, "Backend availability changed during comparison")
    if statuses == {"unavailable"}:
        return {
            "status": "unavailable",
            "attempts": len(rows),
            "reasons": sorted({row["reason"] for row in rows}),
        }
    _require(statuses == {"measured"}, "Unknown sampling outcome")
    _require(len({row["original_sha256"] for row in rows}) == 1, "Mixed input hashes")
    _require(
        len({json.dumps(row["backend"], sort_keys=True) for row in rows}) == 1,
        "Backend changed during comparison",
    )
    _require(
        len({row["rss_basis"] for row in rows}) == 1,
        "RSS measurement basis changed during comparison",
    )
    metrics = [
        "compressed_bytes",
        "encode_wall_seconds",
        "encode_cpu_seconds",
        "decode_wall_seconds",
        "decode_cpu_seconds",
    ]
    result = {
        "status": "measured",
        "samples": len(rows),
        "backend": rows[0]["backend"],
        "medians": {
            name: statistics.median(row[name] for row in rows) for name in metrics
        },
    }
    peaks = [row["whole_worker_peak_rss_bytes"] for row in rows]
    result["maximum_whole_worker_peak_rss_bytes"] = (
        max(peaks) if all(v is not None for v in peaks) else None
    )
    return result


def compare(
    paths, *, repeats=3, seed=178, max_expanded_bytes=DEFAULT_LIMIT, settings=SETTINGS
):
    _require(type(repeats) is int and repeats > 0, "Repeats must be a positive integer")
    settings = tuple(settings)
    _require(bool(settings), "No codec settings")
    seen = set()
    for codec, level in settings:
        _require(
            codec in {"none", "gzip", "zstd", "xz"}
            and (
                (codec == "none" and level is None)
                or (codec != "none" and type(level) is int)
            ),
            "Invalid codec setting",
        )
        _require(
            (codec, level) not in seen,
            "Duplicate codec setting would inflate repeat counts",
        )
        seen.add((codec, level))
    inputs = []
    for path in paths:
        path = Path(path).resolve()
        raw = _read(path, max_expanded_bytes)
        inputs.append(
            {
                "path": str(path),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        del raw
    _require(bool(inputs), "No input files")
    jobs = [
        (i, codec, level, repetition)
        for i in range(len(inputs))
        for codec, level in settings
        for repetition in range(repeats)
    ]
    random.Random(seed).shuffle(jobs)
    results = []
    for index, codec, level, repetition in jobs:
        source = inputs[index]
        row = _worker(
            source["path"], codec, level, source["sha256"], max_expanded_bytes
        )
        results.append({"input_index": index, "repetition": repetition, **row})
    summaries = [
        {
            "input_index": i,
            "codec": codec,
            "level": level,
            **summarize(
                [
                    r
                    for r in results
                    if r["input_index"] == i
                    and r["codec"] == codec
                    and r["level"] == level
                ]
            ),
        }
        for i in range(len(inputs))
        for codec, level in settings
    ]
    for source in inputs:
        _require(
            hashlib.sha256(_read(source["path"], max_expanded_bytes)).hexdigest()
            == source["sha256"],
            "Input changed during comparison",
        )
    return {
        "format": "compressor_comparison_observation@1",
        "owner": "uibcdf/sabueso#178",
        "review_trigger": "compressor selection or workload acceptance",
        "inputs": inputs,
        "settings": list(settings),
        "repeats": repeats,
        "seed": seed,
        "execution": "serial fresh workers in seeded shuffled order; no warmups; OS cache/background load uncontrolled",
        "max_expanded_bytes": max_expanded_bytes,
        "samples": results,
        "summaries": summaries,
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "In-memory codec timing excludes startup, file I/O, JSON parsing and original scientific verification. Worker RSS includes its lifetime/setup/buffers. Own freshly encoded data only; not a production decoder or memory/latency budget. No source queries or package behavior changes.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    worker = commands.add_parser("sample", help="one fresh-worker measurement")
    worker.add_argument("input_file", type=Path)
    worker.add_argument("codec", choices=["none", "gzip", "zstd", "xz"])
    worker.add_argument(
        "level", type=lambda value: None if value == "none" else int(value)
    )
    worker.add_argument("--expected-sha256", required=True)
    worker.add_argument("--max-expanded-bytes", type=_limit, default=DEFAULT_LIMIT)
    batch = commands.add_parser("compare", help="serial repeat comparison")
    batch.add_argument("input_files", nargs="+", type=Path)
    batch.add_argument("--output", required=True, type=Path)
    batch.add_argument("--repeats", type=int, default=3)
    batch.add_argument("--seed", type=int, default=178)
    batch.add_argument("--max-expanded-bytes", type=_limit, default=DEFAULT_LIMIT)
    args = parser.parse_args(argv)
    try:
        if args.command == "sample":
            report = sample(
                args.input_file,
                args.codec,
                args.level,
                expected_sha256=args.expected_sha256,
                max_expanded_bytes=args.max_expanded_bytes,
            )
            print(json.dumps(report, allow_nan=False))
        else:
            _require(
                not args.output.exists(),
                "Output already exists; preserve caller outputs",
            )
            report = compare(
                args.input_files,
                repeats=args.repeats,
                seed=args.seed,
                max_expanded_bytes=args.max_expanded_bytes,
            )
            args.output.mkdir(parents=True, exist_ok=False)
            with (args.output / "report.json").open("x", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
                stream.write("\n")
            print(
                json.dumps(
                    {
                        "report": str(args.output / "report.json"),
                        "samples": len(report["samples"]),
                        "unavailable": sum(
                            row["status"] == "unavailable" for row in report["samples"]
                        ),
                    }
                )
            )
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
