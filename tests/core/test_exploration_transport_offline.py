"""Public lossless transport preserves original history, quantities and atomic output."""

import gzip
import hashlib
import io
import json
import socket
from pathlib import Path

import pytest

import sabueso
from sabueso.core import exploration_transport as transport
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError, LibraryNotFoundError, StorageError

CODECS = ("none", "gzip", "zstd")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Transport must not acquire knowledge")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


def pack(raw, name):
    stream = io.BytesIO()
    codec, backend = transport.encoder(name)
    receipt = transport.write(stream, raw, name, codec, backend, None)
    return stream.getvalue(), receipt


def decode(raw, **options):
    return transport.read(
        io.BytesIO(raw),
        encoded_limit=options.get("encoded_limit"),
        decoded_limit=options.get("decoded_limit"),
        window_limit=options.get("window_limit", transport.WINDOW_LIMIT),
    )


def original():
    card = Card()
    card.unknown_stored["literal"] = [
        False,
        0,
        0.0,
        None,
        "",
        "α🧬",
        {"value": 1.0, "unit": "nanomolar"},
    ]
    return card


@pytest.mark.parametrize("codec", CODECS)
@pytest.mark.parametrize("size", [0, 1, 65535, 65536, 65537, 300000])
def test_incremental_empty_chunk_edges_and_binary_values(codec, size):
    raw = (bytes(range(256)) * (size // 256 + 1))[:size]
    encoded, receipt = pack(raw, codec)
    restored, received = decode(
        encoded, encoded_limit=len(encoded), decoded_limit=max(1, size)
    )
    assert restored == raw
    assert (
        receipt["decoded_sha256"]
        == received["decoded_sha256"]
        == "sha256:" + hashlib.sha256(raw).hexdigest()
    )
    assert receipt["encoded_bytes"] == len(encoded)
    assert received["encoded_sha256"] == receipt["encoded_sha256"]


@pytest.mark.parametrize("codec", CODECS)
def test_public_human_and_agent_save_same_original_without_suffix_inference(
    tmp_path, codec
):
    card = original()
    human = card.explore().inspect()
    reference = tmp_path / "reference.json"
    plain = human.save(reference)
    path = tmp_path / "misleading.json.gz"
    receipt = human.save(path, compression=codec)
    raw, _ = decode(path.read_bytes())
    assert bytes(raw) == reference.read_bytes()
    assert receipt["bundle_digest"] == plain["bundle_digest"]
    saved = sabueso.read_exploration(path, expected_digest=plain["bundle_digest"])
    assert saved.native_payload == card.to_dict()
    assert saved.view_ref == human.view_ref
    assert saved.validation["transport"]["compression"] == codec
    assert saved.validation["transport"]["encoded_bytes"] == path.stat().st_size
    detached = saved.validation
    detached["transport"]["compression"] = "foreign"
    assert saved.validation["transport"]["compression"] == codec
    second = tmp_path / "resave"
    saved.save(second, compression=codec)
    assert sabueso.read_exploration(second).native_payload == saved.native_payload
    access = card.access()
    selection = access.read(access.root_location)
    machine = selection.save(tmp_path / "machine", compression=codec)
    recovered = sabueso.read_exploration(
        tmp_path / "machine", expected_digest=machine["bundle_digest"]
    )
    assert recovered.native_payload == card.to_dict()


@pytest.mark.parametrize("codec", ("gzip", "zstd"))
@pytest.mark.parametrize(
    "mutation", ("truncate", "checksum", "trailing", "empty_member", "second_member")
)
def test_complete_single_frame_required_before_json_or_science(
    tmp_path, monkeypatch, codec, mutation
):
    import sabueso.core.card_exploration_storage as storage

    frame, _ = pack(b'{"literal":"value"}', codec)
    if mutation == "truncate":
        frame = frame[:-1]
    elif mutation == "checksum":
        frame = frame[:-1] + bytes([frame[-1] ^ 1])
    elif mutation == "trailing":
        frame += b"junk"
    else:
        frame += pack(b"" if mutation == "empty_member" else b"another", codec)[0]
    path = tmp_path / "frame"
    path.write_bytes(frame)
    monkeypatch.setattr(
        storage,
        "_restore",
        lambda *a: pytest.fail("Scientific validation ran on invalid transport"),
    )
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)


@pytest.mark.parametrize("codec", CODECS)
@pytest.mark.parametrize("name", ("max_encoded_bytes", "max_decoded_bytes"))
def test_public_budgets_are_visible_and_explicitly_overridable(tmp_path, codec, name):
    path = tmp_path / "input"
    receipt = original().explore().inspect().save(path, compression=codec)
    key = "encoded_bytes" if name == "max_encoded_bytes" else "decoded_bytes"
    size = receipt["transport"][key]
    with pytest.raises(ArgumentError, match=name + "=None"):
        sabueso.read_exploration(path, **{name: size - 1})
    for budget in (size, None):
        assert (
            sabueso.read_exploration(path, **{name: budget}).validation["integrity"]
            == "verified"
        )
    destination = tmp_path / "preserved"
    destination.write_bytes(b"caller output")
    with pytest.raises(ArgumentError, match=name):
        original().explore().inspect().save(
            destination, compression=codec, overwrite=True, **{name: 1}
        )
    assert destination.read_bytes() == b"caller output"
    assert not list(tmp_path.glob(".sabueso-exploration-*"))


@pytest.mark.parametrize(
    "name", ("max_encoded_bytes", "max_decoded_bytes", "max_window_bytes")
)
@pytest.mark.parametrize("bad", (False, True, 0, -1, 1.5, "none"))
@pytest.mark.parametrize("skip", (False, True))
def test_invalid_reader_limits_fail_before_file_access(monkeypatch, name, bad, skip):
    monkeypatch.setattr(
        Path,
        "open",
        lambda *a, **k: pytest.fail("Invalid arguments reached file access"),
    )
    with pytest.raises(ArgumentError):
        sabueso.read_exploration("missing", skip_digestion=skip, **{name: bad})


@pytest.mark.parametrize("bad", (None, True, 1, "auto", "xz", "GZIP"))
@pytest.mark.parametrize("skip", (False, True))
def test_invalid_codec_fails_before_view_preparation(monkeypatch, bad, skip):
    import sabueso.core.card_exploration_storage as storage

    view = original().explore().inspect()
    monkeypatch.setattr(
        storage, "_prepare", lambda *a: pytest.fail("Invalid codec prepared a bundle")
    )
    with pytest.raises(ArgumentError):
        view.save("missing", compression=bad, skip_digestion=skip)


@pytest.mark.parametrize("codec", CODECS)
def test_atomic_no_clobber_and_failed_publish_cleanup(tmp_path, monkeypatch, codec):
    import sabueso.core.card_exploration_storage as storage

    path = tmp_path / "caller"
    path.write_bytes(b"caller")
    view = original().explore().inspect()
    with pytest.raises(StorageError):
        view.save(path, compression=codec)
    assert path.read_bytes() == b"caller"

    def fail(*a):
        raise OSError("controlled replace failure")

    monkeypatch.setattr(storage.os, "replace", fail)
    with pytest.raises(StorageError):
        view.save(path, overwrite=True, compression=codec)
    assert path.read_bytes() == b"caller"
    assert not list(tmp_path.glob(".sabueso-exploration-*"))


def test_missing_native_never_falls_back_or_prepares_output(tmp_path, monkeypatch):
    import sabueso.core.card_exploration_storage as storage

    view = original().explore().inspect()
    calls = []

    def missing(name):
        calls.append(name)
        raise ModuleNotFoundError(name)

    with monkeypatch.context() as context:
        context.setattr(transport.sys, "version_info", (3, 14))
        context.setattr(transport.importlib, "import_module", missing)
        context.setattr(
            storage,
            "_prepare",
            lambda *a: pytest.fail("Missing optional backend prepared a bundle"),
        )
        with pytest.raises(LibraryNotFoundError):
            view.save(tmp_path / "new", compression="zstd")
    assert calls == ["compression.zstd"]
    assert not list(tmp_path.iterdir())


def test_plain_and_gzip_do_not_request_zstandard(tmp_path, monkeypatch):
    monkeypatch.setattr(
        transport, "_zstd", lambda: pytest.fail("Unrequested Zstandard was loaded")
    )
    for codec in ("none", "gzip"):
        path = tmp_path / codec
        receipt = original().explore().inspect().save(path, compression=codec)
        assert (
            sabueso.read_exploration(path, receipt["bundle_digest"]).validation[
                "transport"
            ]["compression"]
            == codec
        )


@pytest.mark.parametrize("codec", CODECS)
def test_genuine_frozen_literal_reader_and_trusted_digest_remain_active(
    tmp_path, codec
):
    raw = Path("tests/core/data/card_exploration_literal_v1.json").read_bytes()
    path = tmp_path / codec
    path.write_bytes(pack(raw, codec)[0])
    expected = json.loads(raw)["bundle_digest"]
    saved = sabueso.read_exploration(path, expected)
    assert saved.validation["integrity"] == "verified"
    with pytest.raises(StorageError):
        sabueso.read_exploration(path, "sha256:" + "0" * 64)


def test_gzip_standard_external_frame_is_readable(tmp_path):
    raw = Path("tests/core/data/card_exploration_literal_v1.json").read_bytes()
    path = tmp_path / "not-a-gzip-suffix"
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert sabueso.read_exploration(path).validation["integrity"] == "verified"


@pytest.mark.parametrize("codec", CODECS)
@pytest.mark.parametrize("fixture", ("science_v2", "sites_v1", "quaternary_v1"))
def test_genuine_scientific_history_survives_transport_without_live_rules(
    tmp_path, monkeypatch, codec, fixture
):
    import importlib

    raw = gzip.decompress(
        Path(f"tests/core/data/card_exploration_{fixture}.json.gz").read_bytes()
    )
    original_bundle = json.loads(raw)
    frame, receipt = pack(raw, codec)
    assert receipt["decoded_sha256"] == "sha256:" + hashlib.sha256(raw).hexdigest()
    path = tmp_path / "original"
    path.write_bytes(frame)

    def forbidden(*a, **k):
        pytest.fail("Original receiving invoked current Card/science")

    monkeypatch.setattr(Card, "from_dict", forbidden)
    monkeypatch.setattr(Card, "to_dict", forbidden)
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.card_scientific_access"),
        "materialize",
        forbidden,
    )
    monkeypatch.setattr(
        importlib.import_module("sabueso.core.knowledge_state"),
        "knowledge_state",
        forbidden,
    )
    saved = sabueso.read_exploration(path, original_bundle["bundle_digest"])
    assert saved.validation["integrity"] == "verified"
    assert saved.validation["transport"]["decoded_sha256"] == receipt["decoded_sha256"]
    assert saved.view_ref == original_bundle["root_view_ref"]
    assert saved.items()
    repr(saved)
    saved._repr_html_()
    saved.items()[0].explain()


def test_window_ceiling_has_a_visible_deliberate_override():
    raw = b"window payload" * 100000
    encoded, _ = pack(raw, "zstd")
    with pytest.raises(StorageError, match="max_window_bytes"):
        decode(encoded, window_limit=1024)
    assert decode(encoded, window_limit=None)[0] == raw
    assert decode(encoded, window_limit=transport.WINDOW_LIMIT)[0] == raw


@pytest.mark.parametrize("skip", (False, True))
def test_window_non_power_of_two_is_refused_before_input(skip, monkeypatch):
    monkeypatch.setattr(
        Path, "open", lambda *a, **k: pytest.fail("Invalid window accessed file")
    )
    with pytest.raises(ArgumentError):
        sabueso.read_exploration("missing", max_window_bytes=1025, skip_digestion=skip)


def test_missing_backport_uses_depdigest_catalog_without_substitution(
    tmp_path, monkeypatch
):
    from depdigest.core import checker

    real = checker.is_installed
    monkeypatch.setattr(
        checker,
        "is_installed",
        lambda name: False if name == "backports.zstd" else real(name),
    )
    with monkeypatch.context() as context:
        context.setattr(transport.sys, "version_info", (3, 13))
        with pytest.raises(LibraryNotFoundError) as error:
            transport.encoder("zstd")
    assert error.value.code == "SABUESO-E-LIBRARY-001"
    assert "backports.zstd" in str(error.value)


@pytest.mark.parametrize("codec", CODECS)
def test_independent_reader_outside_checkout_needs_no_original_card_or_sources(
    tmp_path, codec
):
    import subprocess
    import sys
    from tempfile import TemporaryDirectory

    path = tmp_path / "reading"
    receipt = original().explore().inspect().save(path, compression=codec)
    script = """
import sys,socket,sabueso
from sabueso.core.card import Card
from sabueso.core import card_scientific_access,knowledge_state

def forbidden(*args, **kwargs): raise AssertionError('Current Card/science/network forbidden')
Card.from_dict=Card.to_dict=Card.__init__=forbidden
socket.create_connection=socket.socket.connect=forbidden
card_scientific_access.materialize=knowledge_state.knowledge_state=forbidden
view=sabueso.read_exploration(sys.argv[1],expected_digest=sys.argv[2])
assert view.validation['integrity']=='verified'
assert view.native_payload['literal'][0] is False
assert view.native_payload['literal'][1]==0
assert view.native_payload['literal'][-1]['unit']=='nanomolar'
repr(view);view._repr_html_()
print('PASS: original inert transport receiving')
"""
    with TemporaryDirectory() as directory:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
                str(path.resolve()),
                receipt["bundle_digest"],
            ],
            cwd=directory,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: original inert transport receiving" in result.stdout


@pytest.mark.parametrize("codec", CODECS)
def test_resealed_semantic_change_and_duplicate_json_are_still_refused(tmp_path, codec):
    from copy import deepcopy

    from sabueso.core.card_exploration_storage import _seal

    raw = Path("tests/core/data/card_exploration_literal_v1.json").read_bytes()
    bundle = json.loads(raw)
    modified = deepcopy(bundle)
    view = modified["views"][modified["root_navigation_ref"]]
    view["native_payload"] = {"fabricated": "not the original capture"}
    path = tmp_path / "altered"
    path.write_bytes(pack(json.dumps(_seal(modified)).encode(), codec)[0])
    with pytest.raises(StorageError):
        sabueso.read_exploration(path)
    path.write_bytes(pack(b'{"format":1,"format":2}', codec)[0])
    with pytest.raises(StorageError, match="Duplicate JSON"):
        sabueso.read_exploration(path)


@pytest.mark.parametrize("codec", CODECS)
def test_real_molecule_quantities_and_original_support_survive(tmp_path, codec):
    import pyunitwizard as puw

    from sabueso.tools.card.small_molecule import single_molecule_card
    from sabueso.tools.db.chembl import FixtureChEMBLClient

    card = single_molecule_card(
        chembl=FixtureChEMBLClient("temp_data").molecules(["CHEMBL110"])
    )
    properties = (
        card.explore()
        .answer("property_context")
        .filter("label", equals="Molecular weight")
    )
    path = tmp_path / "molecule"
    receipt = properties.save(path, compression=codec)
    with puw.context(standard_units=["nm", "ps", "K", "mole", "gram"]):
        saved = sabueso.read_exploration(path, receipt["bundle_digest"])
        item = saved.items()[0]
        assert puw.get_value(item.cells["value"].value, to_unit="dalton") == 260.25
        assert item.open().native_payload["unit"] == "dalton"
    assert item.explain().items()[0].open().native_payload["asserted_value"] == "260.25"


@pytest.mark.parametrize("codec", ("gzip", "zstd"))
@pytest.mark.parametrize("stage", ("compress", "flush"))
def test_backend_failure_uses_storage_diagnostic_and_preserves_caller(
    tmp_path, monkeypatch, codec, stage
):
    real = transport.encoder

    def broken(name):
        inner, metadata = real(name)

        class Broken:
            def __getattr__(self, attr):
                if attr == stage:

                    def fail(*a, **k):
                        raise ValueError("controlled backend failure")

                    return fail
                return getattr(inner, attr)

        return Broken(), metadata

    monkeypatch.setattr(transport, "encoder", broken)
    path = tmp_path / "caller"
    path.write_bytes(b"caller output")
    with pytest.raises(StorageError) as error:
        original().explore().inspect().save(path, compression=codec, overwrite=True)
    assert error.value.code == "SABUESO-E-STORAGE-001"
    assert path.read_bytes() == b"caller output"
    assert not list(tmp_path.glob(".sabueso-exploration-*"))


@pytest.mark.parametrize("machine", (False, True))
@pytest.mark.parametrize("skip", (False, True))
@pytest.mark.parametrize("name", ("max_encoded_bytes", "max_decoded_bytes"))
@pytest.mark.parametrize("bad", (False, 0, "none"))
def test_invalid_save_limits_do_not_prepare_or_publish(
    tmp_path, monkeypatch, machine, skip, name, bad
):
    import sabueso.core.card_exploration_storage as storage

    card = original()
    if machine:
        access = card.access()
        target = access.read(access.root_location)
    else:
        target = card.explore().inspect()
    monkeypatch.setattr(
        storage,
        "_prepare",
        lambda *a: pytest.fail("Invalid save limit prepared a bundle"),
    )
    with pytest.raises(ArgumentError):
        target.save(tmp_path / "new", skip_digestion=skip, **{name: bad})
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("codec", CODECS)
@pytest.mark.parametrize("root_kind", ("assembly", "structures", "machine"))
def test_current_formats_five_and_six_keep_exact_original_assembly_requests(
    tmp_path, monkeypatch, codec, root_kind
):
    import importlib

    capsule = json.loads(
        gzip.decompress(Path("tests/core/data/assembly_live_v1.json.gz").read_bytes())
    )
    card = Card.from_dict(capsule["cases"]["2V5B"]["card"])
    explorer = card.explore()
    options = {"structure_ref": "pdb:2V5B"}
    if root_kind == "machine":
        root = explorer.access.select(
            "assembly_generation", options=options, fields=["declaration_count"]
        )
        native = None
    else:
        root = (
            explorer.view("structures")
            if root_kind == "structures"
            else explorer.answer("assembly_generation", options=options)
        )
        native = root.native_payload
    path = tmp_path / "scientific"
    receipt = root.save(path, compression=codec)
    raw = decode(path.read_bytes())[0]
    assert json.loads(raw)["format"] == "sabueso.card_exploration@" + (
        "6" if root_kind == "structures" else "5"
    )
    names = [
        "assembly_generation_v1",
        "assembly_generation_v2",
        "assembly_generation_v3",
        "assembly_generation_v4",
        "card_assembly_access",
        "card_assembly_exploration",
        "card_scientific_access",
    ]
    modules = {name: importlib.import_module("sabueso.core." + name) for name in names}

    def forbidden(*a, **k):
        pytest.fail("Original compressed reading invoked current Card/assembly science")

    monkeypatch.setattr(Card, "__init__", forbidden)
    monkeypatch.setattr(Card, "from_dict", forbidden)
    for name, module in modules.items():
        method = (
            "generation"
            if name.startswith("assembly_generation")
            else (
                "_materialize" if name == "card_assembly_exploration" else "materialize"
            )
        )
        monkeypatch.setattr(module, method, forbidden)
    saved = sabueso.read_exploration(path, receipt["bundle_digest"])
    assert saved.validation["integrity"] == "verified"
    if root_kind == "machine":
        retained = saved.explorer.access.selection(root.selection_ref)
        assert (
            retained.selection_ref == root.selection_ref
            and retained.count == root.count
        )
    else:
        assert saved.native_payload == native
        assert saved.request == root.request
        assert saved.view_ref == root.view_ref
