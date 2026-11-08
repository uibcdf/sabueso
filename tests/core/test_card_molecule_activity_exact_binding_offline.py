"""Independent typed-root predicates against both immutable SDK218 originals."""

import gzip
import hashlib
import json
import tarfile
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from test_card_molecule_activity_binding_offline import OriginalGraph, block_current

from sabueso.core import card_exploration_molecule_activity as original
from sabueso.core import card_exploration_molecule_activity_v2 as binding
from sabueso.core.errors import StorageError

ENCODED_SHA = "7bc8beb6f5220bbe73e1c2353eafaa4aead71b80f1b30f4a43c06a9e757cb266"
DECODED_SHA = "72b3f17d305f544e3be42cb6fa5aba081a571e88c4ec1236905cf2ee8fa60357"
MANIFEST_SHA = "d0b1d6b281a55fc9a7c4de0dcd7329ace9d16ee426ab0549f5bcb280efcb096c"


@pytest.fixture(scope="module")
def original_tar(tmp_path_factory):
    asset = (
        Path(__file__).with_name("data")
        / "molecule_activity_root_exact_live_sdk218.tar.gz"
    )
    with asset.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == ENCODED_SHA
    path = tmp_path_factory.mktemp("sdk218-exact-roots") / "original.tar"
    decoded = hashlib.sha256()
    size = 0
    with gzip.open(asset, "rb") as source, path.open("xb") as target:
        while block := source.read(1024**2):
            size += len(block)
            decoded.update(block)
            target.write(block)
    assert size == 247961600 and decoded.hexdigest() == DECODED_SHA
    with tarfile.open(path, "r:") as archive:
        with archive.extractfile("manifest.json") as stream:
            raw = stream.read()
        assert hashlib.sha256(raw).hexdigest() == MANIFEST_SHA
        manifest = json.loads(raw)
        assert manifest["producer_head"] == "b1bbfaa1fde03c1148a5150a047098ecfcc93fbf"
        assert manifest["producer_version"] == "0.14.0+218.gb1bbfaa"
        assert not manifest["admitted_saved_format"]
        members = archive.getmembers()
        assert len(members) == 1034
        assert {member.name for member in members} == {
            *manifest["files"],
            "manifest.json",
        }
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute()
            assert ".." not in Path(member.name).parts
            if member.name == "manifest.json":
                continue
            with archive.extractfile(member) as stream:
                assert (
                    hashlib.file_digest(stream, "sha256").hexdigest()
                    == (manifest["files"][member.name]["sha256"])
                )
            assert member.size == manifest["files"][member.name]["bytes"]
    return path


class ExactGraph(OriginalGraph):
    SAVED_FORMAT = binding.FORMAT

    def __init__(self, path, order):
        self.archive = tarfile.open(path, "r:")
        self.prefix, self.cache = order + "/", {}
        self.manifest = self.member("manifest.json")
        assert self.manifest["capture_complete"]
        assert self.manifest["root_return_policy"] == binding.ROOT_RETURN_POLICY
        assert self.manifest["operand_creation_order"] == order
        self.graph = self.value(self.manifest["graph"])
        self.observed = {
            key: self.value(ref) for key, ref in self.graph["nodes"].items()
        }
        self._hydrate_graph()

    def member(self, path):
        if path not in self.cache:
            with self.archive.extractfile(self.prefix + path) as stream:
                self.cache[path] = json.load(stream)
        return self.cache[path]


@pytest.fixture(scope="module", params=("node-first", "quantity-first"))
def exact_graph(request, original_tar):
    with pytest.MonkeyPatch.context() as guard:
        block_current(guard)
        graph = ExactGraph(original_tar, request.param)
        yield graph
        graph.archive.close()
        graph.cache.clear()


@pytest.mark.parametrize("node", [f"N{i}" for i in range(104)])
def test_every_genuine_original_view_retains_independent_binding(exact_graph, node):
    view, record = exact_graph.nodes[node], exact_graph.records[node]
    if original.is_view(view):
        binding.verify_view(view, record)
    elif original.is_context(view):
        original.verify_context(view, record)
    elif view._record_panel == "literature":
        original.verify_literature_view(view, record)
    else:
        from sabueso.core.card_exploration_verification_v19 import (
            _verify_display,
            _verify_profile,
            _verify_request,
            _verify_state,
        )

        access = view._explorer.access
        native = _verify_request(view, access)
        _verify_state(view, record, native, access)
        _verify_display(view, record)
        _verify_profile(view, native, access)


@pytest.mark.parametrize("index", range(6))
def test_every_original_machine_selection_remains_exact(exact_graph, index):
    observed = exact_graph.graph["machine"][index]
    access_id = next(
        key
        for key, access in exact_graph.accesses.items()
        if access._focal_key == observed["focal"]
    )
    selection = exact_graph.selection(access_id, observed["selection"])
    result = selection._scientific
    entries = original._machine(selection, selection._access, result)
    original.same(
        [vars(entry) for entry in entries],
        [vars(entry) for entry in selection._entries],
        "SDK218 original machine membership",
    )


def test_exact_origin_manifest_keeps_actual_instances_and_operand_types(exact_graph):
    manifest = binding.root_manifest(exact_graph.nodes)
    assert manifest["rule"] == binding.ROOT_RETURN_POLICY
    assert len(manifest["origins"]) == 6
    binding.verify_roots({binding.MEMBER: manifest}, exact_graph.nodes)
    for form, operand_type in (("node", int), ("pyunitwizard", float)):
        selected, _ = exact_graph.named("target/" + form + "/filtered")
        name = next(
            name
            for name in exact_graph.graph["named"]
            if name.startswith("target/" + form + "/link/")
            and name.endswith("/molecule_root")
        )
        returned, _ = exact_graph.named(name)
        assert binding._originating_root(returned) is selected
        assert type(returned._display_request["equals"]["value"]) is operand_type


def test_old_loose_numeric_return_cannot_enter_new_binding(exact_graph):
    name = next(
        name
        for name in exact_graph.graph["named"]
        if name.startswith("target/pyunitwizard/link/")
        and name.endswith("/molecule_root")
    )
    view, record = exact_graph.named(name)
    display = deepcopy(view._display_request)
    display["equals"]["value"] = 33
    changed = replace(view, _display_request=display)
    record = deepcopy(record)
    record["flags"]["_display_request"] = display
    original.verify_view(changed, record)
    with pytest.raises(StorageError, match="typed originating root"):
        binding.verify_view(changed, record)


@pytest.mark.parametrize("change", ("policy", "missing", "foreign_instance"))
def test_root_manifest_substitutions_are_refused(exact_graph, change):
    manifest = binding.root_manifest(exact_graph.nodes)
    if change == "policy":
        manifest["rule"] = original.ROOT_RETURN_EQUALITY
    elif change == "missing":
        manifest["origins"].pop(next(iter(manifest["origins"])))
    else:
        key = next(iter(manifest["origins"]))
        manifest["origins"][key] = exact_graph.graph["named"]["target/node/links"]
    with pytest.raises(StorageError, match="exact originating root instances"):
        binding.verify_roots({binding.MEMBER: manifest}, exact_graph.nodes)
