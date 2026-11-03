"""Local physical-layout experiment; never a Sabueso reader or scientific verifier.

Only canonical JSON is considered. References exist exclusively in the experiment
scaffold: a reference-like dictionary inside a literal value remains literal.
The parsed input/parts remain in memory; use an owned resource supervisor.
"""

import argparse
import gzip
import hashlib
import json
import platform
import sys
import time
import zlib
from pathlib import Path

FORMAT = "sabueso.exploration_shared_parts_experiment@1"
PARTS = ("selection", "state", "native_payload", "flags")
DEFAULT_LIMIT = 64 * 1024**2


def encode(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def measure(value):
    size = 0
    sha = hashlib.sha256()
    for text in json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).iterencode(value):
        chunk = text.encode("utf-8")
        size += len(chunk)
        sha.update(chunk)
    return size, sha.hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def nonfinite(value):
    raise ValueError("Nonfinite JSON value")


def parse(raw):
    return json.loads(
        raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=nonfinite
    )


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pack(raw):
    data = parse(raw)
    require(
        isinstance(data, dict) and isinstance(data.get("views"), dict),
        "Expected a views object",
    )
    require(
        encode(data) == raw,
        "Experiment requires canonical original JSON; never normalize it silently",
    )
    header = {k: v for k, v in data.items() if k != "views"}
    pools = {name: {} for name in PARTS}
    views = {}
    for key, record in data["views"].items():
        require(isinstance(record, dict), "Expected view records to be objects")
        refs = {}
        for name in PARTS:
            if name not in record:
                continue
            value = record[name]
            _, digest = measure(value)
            if digest in pools[name]:
                require(
                    encode(pools[name][digest]) == encode(value),
                    "Canonical content hash collision",
                )
            else:
                pools[name][digest] = value
            refs[name] = digest
        views[key] = {
            "fields": {k: v for k, v in record.items() if k not in PARTS},
            "parts": refs,
        }
    return {
        "format": FORMAT,
        "original": {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
        "header": header,
        "views": views,
        "pools": pools,
    }


def mapping_bytes(sizes):
    return (
        2
        + max(0, len(sizes) - 1)
        + sum(len(encode(key)) + 1 + value for key, value in sizes.items())
    )


def unpack(packed, *, max_expanded_bytes=DEFAULT_LIMIT):
    """Return original bytes only after exact size preflight and hash checks.

    None explicitly disables the expanded-output ceiling. This does not limit
    JSON input parsing or replace the separate process RSS/scratch supervisor.
    """
    require(
        max_expanded_bytes is None
        or (type(max_expanded_bytes) is int and max_expanded_bytes > 0),
        "Expanded-byte limit must be positive or None",
    )
    require(
        isinstance(packed, dict)
        and set(packed) == {"format", "original", "header", "views", "pools"},
        "Unknown experimental envelope shape",
    )
    require(packed["format"] == FORMAT, "Unsupported experimental layout")
    original, header, views, pools = (
        packed[k] for k in ("original", "header", "views", "pools")
    )
    require(
        isinstance(original, dict) and set(original) == {"bytes", "sha256"},
        "Malformed original receipt",
    )
    require(
        type(original["bytes"]) is int and original["bytes"] > 0,
        "Invalid original byte count",
    )
    require(
        isinstance(original["sha256"], str) and len(original["sha256"]) == 64,
        "Invalid original hash",
    )
    require(
        isinstance(header, dict) and "views" not in header and isinstance(views, dict),
        "Invalid header/views",
    )
    require(
        isinstance(pools, dict) and set(pools) == set(PARTS), "Unknown part namespace"
    )
    sizes = {}
    used = {name: set() for name in PARTS}
    for name, pool in pools.items():
        require(isinstance(pool, dict), "Invalid pool")
        sizes[name] = {}
        for digest, value in pool.items():
            size, actual = measure(value)
            require(digest == actual, "Changed or incorrectly identified shared part")
            sizes[name][digest] = size
    view_sizes = {}
    for key, record in views.items():
        require(
            isinstance(record, dict) and set(record) == {"fields", "parts"},
            "Unknown view scaffold",
        )
        fields, refs = record["fields"], record["parts"]
        require(
            isinstance(fields, dict) and not set(fields).intersection(PARTS),
            "Part shadowing in view fields",
        )
        require(isinstance(refs, dict) and set(refs) <= set(PARTS), "Unknown part kind")
        field_sizes = {k: measure(v)[0] for k, v in fields.items()}
        for name, digest in refs.items():
            require(
                isinstance(digest, str) and digest in pools[name],
                "Missing or foreign-kind part reference",
            )
            used[name].add(digest)
            field_sizes[name] = sizes[name][digest]
        view_sizes[key] = mapping_bytes(field_sizes)
    require(
        all(used[name] == set(pools[name]) for name in PARTS),
        "Unreferenced part would be discarded",
    )
    header_sizes = {k: measure(v)[0] for k, v in header.items()}
    header_sizes["views"] = mapping_bytes(view_sizes)
    expanded_bytes = mapping_bytes(header_sizes)
    require(
        expanded_bytes == original["bytes"],
        "Original byte-count receipt differs from exact expansion",
    )
    require(
        max_expanded_bytes is None or expanded_bytes <= max_expanded_bytes,
        f"Expanded output requires {expanded_bytes} bytes; configured limit {max_expanded_bytes}. Raise it explicitly or use None to disable it.",
    )
    # This allocates only scaffold dictionaries; part payloads are not copied.
    # Public output is bytes, so no mutable alias is exposed to a caller.
    rebuilt = {
        **header,
        "views": {
            key: {
                **record["fields"],
                **{
                    name: pools[name][digest]
                    for name, digest in record["parts"].items()
                },
            }
            for key, record in views.items()
        },
    }
    raw = encode(rebuilt)
    require(
        len(raw) == expanded_bytes
        and hashlib.sha256(raw).hexdigest() == original["sha256"],
        "Original reconstruction hash differs",
    )
    return raw


def _limit(value):
    if value.lower() == "none":
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Use a positive byte count or 'none'."
        ) from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("Use a positive byte count or 'none'.")
    return number


def experiment(path, *, max_expanded_bytes=DEFAULT_LIMIT):
    """Measure one canonical input; this does not establish scientific validity."""
    require(
        max_expanded_bytes is None
        or (type(max_expanded_bytes) is int and max_expanded_bytes > 0),
        "Expanded-byte limit must be positive or None",
    )
    path = Path(path)
    with path.open("rb") as stream:
        raw = (
            stream.read()
            if max_expanded_bytes is None
            else stream.read(max_expanded_bytes + 1)
        )
    require(
        max_expanded_bytes is None or len(raw) <= max_expanded_bytes,
        f"Input exceeds configured expanded-byte limit {max_expanded_bytes}; raise --max-expanded-bytes explicitly or use 'none'.",
    )
    fingerprint = hashlib.sha256(raw).hexdigest()
    started = time.perf_counter()
    shared = encode(pack(raw))
    pack_seconds = time.perf_counter() - started
    started = time.perf_counter()
    restored = unpack(parse(shared), max_expanded_bytes=max_expanded_bytes)
    unpack_seconds = time.perf_counter() - started
    require(restored == raw, "Original byte reconstruction differs")
    original_gzip = gzip.compress(raw, compresslevel=6, mtime=0)
    shared_gzip = gzip.compress(shared, compresslevel=6, mtime=0)
    require(
        gzip.decompress(original_gzip) == raw, "Original gzip reconstruction differs"
    )
    require(
        gzip.decompress(shared_gzip) == shared, "Shared gzip reconstruction differs"
    )
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    require(
        digest.hexdigest() == fingerprint,
        "The original input changed during measurement",
    )
    artifacts = {
        "unsupported-shared-layout.json": shared,
        "original.experimental.json.gz": original_gzip,
        "shared.experimental.json.gz": shared_gzip,
    }
    report = {
        "format": "exploration_storage_experiment_observation@1",
        "owner": "uibcdf/sabueso#167",
        "review_trigger": "before physical-layout adoption or workload acceptance",
        "input": {
            "path": str(path),
            "bytes": len(raw),
            "sha256": fingerprint,
            "unchanged": True,
        },
        "shared_bytes": len(shared),
        "gzip_original_bytes": len(original_gzip),
        "gzip_shared_bytes": len(shared_gzip),
        "reconstructed_bytes": len(restored),
        "reconstructed_sha256": hashlib.sha256(restored).hexdigest(),
        "byte_exact": True,
        "max_expanded_bytes": max_expanded_bytes,
        "pack_seconds_single_observation": pack_seconds,
        "unpack_seconds_single_observation": unpack_seconds,
        "gzip": {"level": 6, "mtime": 0, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION},
        "artifacts": {
            name: {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
            for name, value in artifacts.items()
        },
        "python": sys.version,
        "platform": platform.platform(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "network_requests": 0,
        "verification": "Physical byte reconstruction only; verify original scientific decisions separately with read_exploration and a trusted expected digest.",
        "limitations": "Unsupported engineering artifacts, not accepted by read_exploration. Full parsed JSON and original reconstruction remain in memory; use an owned process resource supervisor. Single uncontrolled timings are not a benchmark, latency improvement, RSS reduction or accepted budget. Matching content shares storage only, never molecular identity. Compressed bytes can differ across Python/zlib versions.",
    }
    return report, artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--max-expanded-bytes",
        type=_limit,
        default=DEFAULT_LIMIT,
        help="Visible input/reconstructed-output ceiling in bytes (default: %(default)s); use 'none' explicitly to disable it. Does not bound all process memory.",
    )
    args = parser.parse_args(argv)
    try:
        report, artifacts = experiment(
            args.input_file, max_expanded_bytes=args.max_expanded_bytes
        )
        args.output_directory.mkdir(parents=True, exist_ok=False)
        for name, raw in artifacts.items():
            with (args.output_directory / name).open("xb") as stream:
                stream.write(raw)
        with (args.output_directory / "report.json").open(
            "x", encoding="utf-8"
        ) as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
