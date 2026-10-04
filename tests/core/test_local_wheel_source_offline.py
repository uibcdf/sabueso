"""An installed diagnostic must not validate stale incremental build output."""

import importlib.util
from pathlib import Path
from zipfile import ZipFile


def test_wheel_guard_rejects_stale_missing_and_ghost_modules(tmp_path):
    path = Path("devtools/conda-build/check_local_wheel.py")
    spec = importlib.util.spec_from_file_location("local_wheel_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "source"
    package = root / "sabueso"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("current source\n")
    (package / "new.py").write_text("new module\n")
    wheel = tmp_path / "candidate.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr("sabueso/__init__.py", "old source\n")
        archive.writestr("sabueso/ghost.py", "retired module\n")
    assert module.check(wheel, root) == [
        "missing: sabueso/new.py",
        "unexpected: sabueso/ghost.py",
        "stale bytes: sabueso/__init__.py",
    ]
    with ZipFile(wheel, "w") as archive:
        for source in package.iterdir():
            archive.writestr("sabueso/" + source.name, source.read_bytes())
        archive.writestr("sabueso/_version.py", "generated version\n")
    assert module.check(wheel, root) == []
