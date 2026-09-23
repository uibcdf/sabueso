import sabueso.resolver as resolver


def _sa(value, src, retrieved_at, sa_id):
    return {
        "value": value,
        "source": {"name": src},
        "retrieved_at": retrieved_at,
        "source_assertion_id": sa_id,
    }


def test_priority_sources_picks_preferred():
    assertions = [
        _sa("A", "Other", "2026-02-01", "sa1"),
        _sa("B", "UniProt", "2026-02-02", "sa2"),
    ]
    rules = {"priority_sources": ["UniProt", "PDB"]}
    out = resolver.resolve_field("annotations.domains", assertions, rules)
    assert out["selected_value"] == "B"
    assert out["source_assertion_ids"] == ["sa2"]
    assert out["conflict"] is not None


def test_most_recent_strategy():
    assertions = [
        _sa("A", "UniProt", "2026-02-01", "sa1"),
        _sa("B", "UniProt", "2026-02-03", "sa2"),
    ]
    rules = {"field_rules": {"x": {"strategy": "most_recent"}}}
    out = resolver.resolve_field("x", assertions, rules)
    assert out["selected_value"] == "B"
    assert out["conflict"] is not None


def test_most_frequent_tie_conflict():
    assertions = [
        _sa("A", "UniProt", "2026-02-01", "sa1"),
        _sa("B", "PDB", "2026-02-02", "sa2"),
    ]
    rules = {"strategy": "most_frequent"}
    out = resolver.resolve_field("y", assertions, rules)
    assert out["conflict"] is not None
    assert out["conflict"]["type"] == "disagreement"


def test_tolerant_equal_values():
    assertions = [
        _sa("ATP", "UniProt", "2026-02-01", "sa1"),
        _sa("  atp ", "PDB", "2026-02-02", "sa2"),
    ]
    rules = {"strategy": "most_frequent"}
    out = resolver.resolve_field("z", assertions, rules, mode="tolerant")
    assert out["conflict"] is None
