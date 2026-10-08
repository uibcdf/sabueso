"""Recovered reports are inert snapshots with readable quantities and support."""

import json
import shutil

import pytest

import sabueso
from sabueso.core.card import Card
from sabueso.core.errors import ArgumentError
from sabueso.resolver import EntityResolver, FixtureUniProtClient
from sabueso.tools.card import notebook as reporting


@pytest.fixture
def card():
    return sabueso.resolve(
        "P60174", resolver=EntityResolver(FixtureUniProtClient("temp_data"))
    )[0]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_deterministic_valid_inert_report_preserves_units_and_support(
    card, tmp_path, monkeypatch
):
    before = card.to_dict()
    monkeypatch.setattr(
        sabueso, "resolve", lambda *a, **k: pytest.fail("Report acquired data")
    )
    path = card.to_notebook(tmp_path / "report.ipynb")
    original = path.read_bytes()
    card.to_notebook(path)
    assert path.read_bytes() == original
    document = read(path)
    assert document["metadata"]["sabueso"]["card_ref"] == card.pinned_ref()
    assert document["metadata"]["sabueso"]["missing_source_assertion_ids"] == []
    text = "\n".join(cell["source"] for cell in document["cells"])
    assert "dalton" in text and "has_structure" in text
    assert card.get("sequence.primary")["source_assertion_ids"][0] in text
    assert not any(cell["cell_type"] == "code" for cell in document["cells"])
    assert card.to_dict() == before and not path.with_suffix(".card.json").exists()
    import nbformat

    nbformat.validate(nbformat.from_dict(document))


def test_snapshot_load_and_regeneration_need_no_fixtures(card, tmp_path):
    path = card.to_notebook(tmp_path / "original.ipynb", include_card_snapshot=True)
    restored = Card.from_json(path.with_suffix(".card.json"))
    assert (
        restored.pinned_ref() == card.pinned_ref()
        and restored.acquisition_trace is None
    )
    regenerated = restored.to_notebook(
        tmp_path / "regenerated.ipynb", include_card_snapshot=True
    )
    assert read(regenerated)["metadata"] == read(path)["metadata"]
    assert [
        c["source"] for c in read(regenerated)["cells"] if c["cell_type"] == "markdown"
    ] == [c["source"] for c in read(path)["cells"] if c["cell_type"] == "markdown"]
    compile(
        next(c["source"] for c in read(path)["cells"] if c["cell_type"] == "code"),
        str(path),
        "exec",
    )


@pytest.mark.parametrize("mode", ["full", "minimal"])
@pytest.mark.parametrize("language", ["en", "es"])
def test_saved_cell_regenerates_a_moved_report_with_original_options(
    card, tmp_path, monkeypatch, mode, language
):
    title = "Stored 'report' — \"quoted\"\nsecond line"
    path = card.to_notebook(
        tmp_path / "original" / "a'b report.ipynb",
        title=title,
        mode=mode,
        language=language,
        include_card_snapshot=True,
    )
    document = read(path)
    original = path.read_bytes()
    snapshot = path.with_suffix(".card.json").read_bytes()
    moved = tmp_path / "moved"
    moved.mkdir()
    shutil.copy(path, moved / path.name)
    shutil.copy(
        path.with_suffix(".card.json"), moved / path.with_suffix(".card.json").name
    )
    monkeypatch.chdir(moved)

    def no_acquisition(*args, **kwargs):
        pytest.fail("Saved report regeneration acquired data")

    monkeypatch.setattr(sabueso, "resolve", no_acquisition)
    from sabueso.tools.db import _http

    monkeypatch.setattr(_http, "urlopen", no_acquisition)
    source = next(c["source"] for c in document["cells"] if c["cell_type"] == "code")
    scope = {"__name__": "__main__"}
    exec(compile(source, str(path), "exec"), scope)

    regenerated = moved / (path.stem + "_regenerated.ipynb")
    restored = read(regenerated)
    assert restored["metadata"] == document["metadata"]
    assert [c for c in restored["cells"] if c["cell_type"] == "markdown"] == [
        c for c in document["cells"] if c["cell_type"] == "markdown"
    ]
    assert regenerated.with_suffix(".card.json").read_bytes() == snapshot
    assert (moved / path.name).read_bytes() == original
    assert (moved / path.with_suffix(".card.json").name).read_bytes() == snapshot
    assert scope["card"].pinned_ref() == card.pinned_ref()
    assert scope["card"].acquisition_trace is None
    import nbformat

    nbformat.validate(nbformat.from_dict(restored))


def test_saved_cell_refuses_a_different_valid_snapshot(card, tmp_path, monkeypatch):
    path = card.to_notebook(tmp_path / "report.ipynb", include_card_snapshot=True)
    document = read(path)
    other = Card.from_json(path.with_suffix(".card.json"))
    other.get("names.canonical_name")["value"] = "Different stored snapshot"
    assert other.snapshot_id() != card.snapshot_id()
    other.to_json(path.with_suffix(".card.json"))
    monkeypatch.chdir(tmp_path)
    source = next(c["source"] for c in document["cells"] if c["cell_type"] == "code")
    with pytest.raises(AssertionError):
        exec(compile(source, str(path), "exec"), {"__name__": "__main__"})
    assert not (tmp_path / "report_regenerated.ipynb").exists()
    assert not (tmp_path / "report_regenerated.card.json").exists()


def test_missing_support_and_conflicts_are_reported(card, tmp_path):
    card.get("sequence.primary")["source_assertion_ids"].append("missing")
    card.quality["conflicts"] = [{"detail": "conflicting-source"}]
    document = read(card.to_notebook(tmp_path / "report.ipynb"))
    assert document["metadata"]["sabueso"]["missing_source_assertion_ids"] == [
        "missing"
    ]
    assert "conflicting-source" in "\n".join(c["source"] for c in document["cells"])


def test_source_html_and_quoted_paths_are_literal(card, tmp_path):
    card.get("names.canonical_name")["value"] = (
        "<script>alert(1)</script> ![remote](https://example.com/image) `code`"
    )
    path = card.to_notebook(tmp_path / "a'b.ipynb", include_card_snapshot=True)
    document = read(path)
    assert "<script>" not in "\n".join(c["source"] for c in document["cells"])
    assert "![remote]" not in "\n".join(c["source"] for c in document["cells"])
    compile(
        next(c["source"] for c in document["cells"] if c["cell_type"] == "code"),
        str(path),
        "exec",
    )


def test_modes_languages_and_relative_paths(card, tmp_path, monkeypatch):
    monkeypatch.setattr(reporting, "_execution_directory", lambda: tmp_path)
    output = card.to_notebook(
        "reports", language="es", mode="minimal", include_code=False
    )
    assert output.parent == tmp_path / "reports"
    document = read(output)
    assert "Alcance y cobertura" in "\n".join(c["source"] for c in document["cells"])
    assert document["metadata"]["sabueso"]["mode"] == "minimal"


@pytest.mark.parametrize(
    "options",
    [
        {"mode": "refresh"},
        {"language": "fr"},
        {"include_code": 1},
        {"include_card_snapshot": "yes"},
    ],
)
def test_bad_options_fail_before_writing(card, tmp_path, options):
    with pytest.raises(ArgumentError):
        card.to_notebook(tmp_path / "report.ipynb", **options)
    assert not list(tmp_path.iterdir())
