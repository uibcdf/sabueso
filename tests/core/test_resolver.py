import sabueso.resolver as resolver


def _ev(value, src, retrieved_at, evid):
    return {
        "value": value,
        "source": {"name": src},
        "retrieved_at": retrieved_at,
        "evidence_id": evid,
    }


def test_priority_sources_picks_preferred():
    evidences = [
        _ev("A", "Other", "2026-02-01", "e1"),
        _ev("B", "UniProt", "2026-02-02", "e2"),
    ]
    rules = {"priority_sources": ["UniProt", "PDB"]}
    out = resolver.resolve_field("annotations.domains", evidences, rules)
    assert out["selected_value"] == "B"
    assert out["evidence_ids"] == ["e2"]


def test_most_recent_strategy():
    evidences = [
        _ev("A", "UniProt", "2026-02-01", "e1"),
        _ev("B", "UniProt", "2026-02-03", "e2"),
    ]
    rules = {"field_rules": {"x": {"strategy": "most_recent"}}}
    out = resolver.resolve_field("x", evidences, rules)
    assert out["selected_value"] == "B"


def test_most_frequent_tie_conflict():
    evidences = [
        _ev("A", "UniProt", "2026-02-01", "e1"),
        _ev("B", "PDB", "2026-02-02", "e2"),
    ]
    rules = {"strategy": "most_frequent"}
    out = resolver.resolve_field("y", evidences, rules)
    assert out["conflict"] is not None
    assert out["conflict"]["type"] == "disagreement"


def test_tolerant_equal_values():
    evidences = [
        _ev("ATP", "UniProt", "2026-02-01", "e1"),
        _ev("  atp ", "PDB", "2026-02-02", "e2"),
    ]
    rules = {"strategy": "most_frequent"}
    out = resolver.resolve_field("z", evidences, rules, mode="tolerant")
    assert out["conflict"] is None
