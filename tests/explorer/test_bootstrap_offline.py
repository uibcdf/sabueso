"""A launcher can only observe a complete descriptor; caller paths stay owned."""

import json
import os
import stat
from pathlib import Path

import pytest

from sabueso.explorer._service import _publish_bootstrap, _remove_bootstrap


def test_bootstrap_is_complete_and_private_at_first_visibility(tmp_path, monkeypatch):
    path = tmp_path / "bootstrap.json"
    configuration = {"url": "http://127.0.0.1:12345/#token=synthetic"}
    link = os.link
    observations = []

    def receive(source, destination):
        assert not path.exists()
        observations.append(json.loads(Path(source).read_text()))
        link(source, destination)

    monkeypatch.setattr(os, "link", receive)
    owned = _publish_bootstrap(path, configuration)
    assert observations == [configuration]
    assert json.loads(path.read_text()) == configuration
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list(tmp_path.iterdir()) == [path]
    _remove_bootstrap(path, owned)
    assert not path.exists()


def test_bootstrap_collision_and_failure_never_remove_caller_file(tmp_path):
    path = tmp_path / "caller.json"
    path.write_text("caller-owned")
    with pytest.raises(FileExistsError):
        _publish_bootstrap(path, {"url": "synthetic"})
    _remove_bootstrap(path, None)
    assert path.read_text() == "caller-owned"
    assert list(tmp_path.iterdir()) == [path]


def test_bootstrap_cleanup_leaves_replacement_and_symlink_untouched(tmp_path):
    path = tmp_path / "bootstrap.json"
    owned = _publish_bootstrap(path, {"url": "synthetic"})
    original = tmp_path / "original.json"
    path.rename(original)  # Keep the inode allocated while replacing its path.
    path.write_text("replacement")
    _remove_bootstrap(path, owned)
    assert path.read_text() == "replacement"
    path.unlink()
    path.symlink_to(original)
    _remove_bootstrap(path, owned)
    assert path.is_symlink()
    assert original.exists()
