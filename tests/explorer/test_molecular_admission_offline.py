"""Model input capture and explicit unknown correspondence need no renderer."""

import asyncio
import gzip
import hashlib
from pathlib import Path

import pytest

from sabueso.core.errors import ArgumentError
from sabueso.explorer import _molecular


def test_model_snapshot_is_detached_and_never_claims_card_identity(tmp_path):
    source = tmp_path / "local.pdb"
    original = b"HEADER    synthetic capture-only control\nEND\n"
    source.write_bytes(original)
    model = _molecular._Molecular(source)
    try:
        captured = model._capture()
        source.write_bytes(b"changed by the caller")
        assert captured.read_bytes() == original
        descriptor = model.descriptor()
        assert (
            descriptor["initial_input_digest"]
            == "sha256:" + hashlib.sha256(original).hexdigest()
        )
        assert descriptor["correspondence"] == "not_established"
        assert descriptor["client_url"] is None
        assert descriptor["initial_renderer_ready"] is None
        directory = captured.parent
    finally:
        asyncio.run(model.close())
    assert not directory.exists() and model.descriptor()["status"] == "closed"
    asyncio.run(model.close())


@pytest.mark.parametrize(
    "case", ["empty", "suffix", "encoded", "decoded", "invalid_gzip"]
)
def test_model_admission_is_bounded_and_disposable(tmp_path, monkeypatch, case):
    monkeypatch.setattr(_molecular, "ENCODED_LIMIT", 128)
    monkeypatch.setattr(_molecular, "DECODED_LIMIT", 256)
    name, raw = {
        "empty": ("input.pdb", b""),
        "suffix": ("input.py", b"pass"),
        "encoded": ("input.bcif", b"x" * 129),
        "decoded": ("input.cif.gz", gzip.compress(b"x" * 257)),
        "invalid_gzip": ("input.pdb.gz", b"not gzip"),
    }[case]
    source = tmp_path / name
    source.write_bytes(raw)
    model = _molecular._Molecular(source)
    try:
        with pytest.raises((ArgumentError, OSError)):
            model._capture()
        directory = Path(model.directory.name) if model.directory else None
    finally:
        asyncio.run(model.close())
    assert source.read_bytes() == raw
    assert directory is None or not directory.exists()
