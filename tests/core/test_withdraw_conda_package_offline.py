"""Withdrawing an exact file from the public label (the 0.1.0 package, #35)."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "devtools"
    / "conda-build"
    / "withdraw_package.py"
)
spec = importlib.util.spec_from_file_location("sabueso_withdraw_package", SCRIPT)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
NAME = "noarch/sabueso-0.1.0-py_0.tar.bz2"
DIGEST = "2211c65f03e19e5dbf54cd13acbe0781599c8f1f703d1c8ab0829927e8fc41cd"


class Registry:
    """A fake anaconda.org holding one release; records every write."""

    def __init__(self, labels, sha256=DIGEST):
        self.files = {
            NAME: {"basename": NAME, "sha256": sha256, "labels": list(labels)}
        }
        self.calls = []

    def release(self, owner, package, version):
        return {
            "distributions": [
                dict(d, labels=list(d["labels"])) for d in self.files.values()
            ]
        }

    def add_channel(self, channel, owner, package=None, version=None, filename=None):
        self.calls.append(("add", channel, owner, package, version, filename))
        self.files[filename]["labels"].append(channel)

    def remove_channel(self, channel, owner, package=None, version=None, filename=None):
        self.calls.append(("remove", channel, owner, package, version, filename))
        self.files[filename]["labels"].remove(channel)


def test_the_file_moves_from_main_to_withdrawn_by_exact_coordinates():
    registry = Registry(["staging", "main"])
    receipt = w.withdraw(
        registry, registry, version="0.1.0", build_number=0, sha256=DIGEST
    )
    assert receipt["labels_after"] == ["staging", "withdrawn"]
    # Archived first, then withdrawn; every call names the exact file.
    assert [c[:2] for c in registry.calls] == [("add", "withdrawn"), ("remove", "main")]
    assert all(c[2:] == ("uibcdf", "sabueso", "0.1.0", NAME) for c in registry.calls)


@pytest.mark.parametrize(
    "labels, sha256, message",
    [
        (["staging", "main"], "0" * 64, "SHA-256"),
        (["staging"], DIGEST, "not on the 'main' label"),
    ],
)
def test_nothing_is_written_unless_the_exact_public_file_is_proven(
    labels, sha256, message
):
    registry = Registry(labels, sha256=sha256)
    with pytest.raises(w.WithdrawalError, match=message):
        w.withdraw(registry, registry, version="0.1.0", build_number=0, sha256=DIGEST)
    assert registry.calls == []


@pytest.mark.parametrize("version, build", [("0.1", 0), ("v0.1.0", 0), ("0.1.0", -1)])
def test_malformed_coordinates_are_refused(version, build):
    with pytest.raises(w.WithdrawalError):
        w.basename(version, build)
