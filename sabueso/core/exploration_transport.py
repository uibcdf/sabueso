"""Lossless file transport around unchanged, independently verified exploration JSON.

Only one gzip member or ordinary Zstandard frame is accepted. Incremental codec
buffers are bounded; JSON materialization and scientific verification still cost
memory independently of these byte/window ceilings.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import sys

from depdigest import dep_digest

from .errors import (
    ArgumentError,
    LibraryNotFoundError,
    StorageError,
    _diagnostic_details_allowed,
)

BYTE_LIMIT = 64 * 1024**2
WINDOW_LIMIT = 8 * 1024**2
CHUNK = 65536


def compression_option(value):
    if not isinstance(value, str) or value not in ("none", "gzip", "zstd"):
        raise ArgumentError(
            "compression must be 'none', 'gzip' or 'zstd'; no codec is substituted.",
            argument="compression",
        )
    return value


def byte_budget(name, value):
    if value is not None and (type(value) is not int or value <= 0):
        raise ArgumentError(
            f"{name} must be a positive integer or None to disable its ceiling.",
            argument=name,
        )
    if name == "max_window_bytes" and value is not None:
        if value < 1024 or value & (value - 1):
            raise ArgumentError(
                "max_window_bytes must be a power of two of at least 1024 bytes, "
                "or None to use the backend maximum.",
                argument=name,
            )
    return value


def _check(name, size, budget):
    if budget is not None and size > budget:
        ceiling = f"{name}={budget}" if _diagnostic_details_allowed() else name
        raise ArgumentError(
            f"Exploration exceeds {ceiling}; increase {name} explicitly "
            f"or pass {name}=None deliberately. No partial result is returned.",
            argument=name,
        )


@dep_digest("backports.zstd")
def _backport():
    return importlib.import_module("backports.zstd")


def _zstd():
    if sys.version_info < (3, 14):
        return _backport()
    try:
        return importlib.import_module("compression.zstd")
    except ImportError as exc:
        raise LibraryNotFoundError(
            "Zstandard requires Python 3.14's optional compression.zstd module. "
            "Ask your Python distributor for a build with Zstandard support, "
            "or explicitly use plain JSON or gzip. No fallback was performed.",
            library="compression.zstd",
        ) from exc


def _gzip_backend():
    try:
        return importlib.import_module("zlib")
    except ImportError as exc:
        raise LibraryNotFoundError(
            "Gzip requires Python's optional zlib module; ask your Python "
            "distributor for a build with zlib support.",
            library="zlib",
        ) from exc


def _codec_call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except MemoryError:
        raise
    except Exception as exc:
        raise StorageError("The exploration compression backend failed.") from exc


def _zstd_metadata(module):
    distribution = None
    if module.__name__ == "backports.zstd":
        try:
            distribution = importlib.metadata.version("backports.zstd")
        except importlib.metadata.PackageNotFoundError:
            pass  # Importable modules without distribution metadata remain explicit.
    return {
        "module": module.__name__,
        "version": module.zstd_version,
        "distribution_version": distribution,
    }


def encoder(compression):
    """Resolve before Card preparation or temporary output creation."""
    compression_option(compression)
    if compression == "none":
        return None, {"module": None, "version": None, "level": None}
    if compression == "gzip":
        module = _gzip_backend()
        return _codec_call(module.compressobj, 6, wbits=31), {
            "module": "zlib",
            "version": module.ZLIB_RUNTIME_VERSION,
            "level": 6,
        }
    module = _zstd()
    options = {
        module.CompressionParameter.compression_level: 3,
        module.CompressionParameter.nb_workers: 0,
        module.CompressionParameter.checksum_flag: 1,
        module.CompressionParameter.window_log: 23,
    }
    return _codec_call(module.ZstdCompressor, options=options), {
        **_zstd_metadata(module),
        "level": 3,
    }


def _receipt(compression, encoded, decoded, encoded_hash, decoded_hash, backend):
    return {
        "format": "exploration_transport@1",
        "compression": compression,
        "encoded_bytes": encoded,
        "decoded_bytes": decoded,
        "encoded_sha256": "sha256:" + encoded_hash.hexdigest(),
        "decoded_sha256": "sha256:" + decoded_hash.hexdigest(),
        "backend": backend,
    }


def write(stream, raw, compression, codec, backend, encoded_limit):
    encoded = 0
    encoded_hash = hashlib.sha256()

    def emit(part):
        nonlocal encoded
        encoded += len(part)
        _check("max_encoded_bytes", encoded, encoded_limit)
        stream.write(part)
        encoded_hash.update(part)

    if compression == "zstd":
        _codec_call(codec.set_pledged_input_size, len(raw))
    for start in range(0, len(raw), CHUNK):
        part = raw[start : start + CHUNK]
        emit(part if codec is None else _codec_call(codec.compress, part))
    if codec is not None:
        emit(_codec_call(codec.flush))
    return _receipt(
        compression, encoded, len(raw), encoded_hash, hashlib.sha256(raw), backend
    )


def read(stream, *, encoded_limit, decoded_limit, window_limit):
    encoded = decoded = 0
    encoded_hash, decoded_hash = hashlib.sha256(), hashlib.sha256()
    output = bytearray()

    def take(size=CHUNK):
        nonlocal encoded
        if encoded_limit is not None:
            size = min(size, max(1, encoded_limit + 1 - encoded))
        part = stream.read(size)
        encoded += len(part)
        _check("max_encoded_bytes", encoded, encoded_limit)
        encoded_hash.update(part)
        return part

    def receive(part):
        nonlocal decoded
        decoded += len(part)
        _check("max_decoded_bytes", decoded, decoded_limit)
        decoded_hash.update(part)
        output.extend(part)

    first = take(4)
    if first.startswith(b"\x1f\x8b"):
        compression = "gzip"
        module = _gzip_backend()
        codec = module.decompressobj(wbits=31)
        backend = {"module": "zlib", "version": module.ZLIB_RUNTIME_VERSION}
        errors = (module.error,)
    elif first == b"\x28\xb5\x2f\xfd":
        compression = "zstd"
        module = _zstd()
        lower, upper = module.DecompressionParameter.window_log_max.bounds()
        window_log = upper if window_limit is None else window_limit.bit_length() - 1
        if not lower <= window_log <= upper:
            raise ArgumentError(
                "max_window_bytes is outside this Zstandard backend's supported "
                "range; use a supported power of two or None.",
                argument="max_window_bytes",
            )
        codec = module.ZstdDecompressor(
            options={module.DecompressionParameter.window_log_max: window_log}
        )
        backend = _zstd_metadata(module)
        errors = (module.ZstdError,)
    else:
        compression, codec = "none", None
        backend = {"module": None, "version": None}

    pending = first
    if codec is None:
        while pending:
            receive(pending)
            size = (
                CHUNK
                if decoded_limit is None
                else min(CHUNK, decoded_limit + 1 - decoded)
            )
            pending = take(max(1, size))
    else:
        while True:
            maximum = (
                CHUNK
                if decoded_limit is None
                else min(CHUNK, decoded_limit + 1 - decoded)
            )
            try:
                receive(codec.decompress(pending, max_length=max(1, maximum)))
            except errors as exc:
                hint = (
                    " If a valid frame needs a larger window, increase "
                    "max_window_bytes or deliberately pass None."
                    if compression == "zstd"
                    else ""
                )
                raise StorageError(
                    f"Invalid {compression} exploration frame.{hint}"
                ) from exc
            if codec.eof:
                if codec.unused_data or take(1):
                    raise StorageError(
                        "Trailing data or concatenated exploration frames are not accepted."
                    )
                break
            if compression == "gzip":
                pending = codec.unconsumed_tail
                if pending:
                    continue
            elif not codec.needs_input:
                pending = b""
                continue
            pending = take()
            if not pending:
                raise StorageError("Truncated compressed exploration frame.")
    receipt = _receipt(
        compression, encoded, decoded, encoded_hash, decoded_hash, backend
    )
    receipt["limits"] = {
        "max_encoded_bytes": encoded_limit,
        "max_decoded_bytes": decoded_limit,
        "max_window_bytes": window_limit,
    }
    return output, receipt
