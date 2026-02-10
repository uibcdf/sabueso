import sabueso.resolver as resolver


def _ev(value, src, retrieved_at, evid):
    return {
        "value": value,
        "source": {"name": src},
        "retrieved_at": retrieved_at,
        "evidence_id": evid,
    }


def test_domains_priority_sources_allow_multiple():
    evidences = [
        _ev({"id": "IPR0001", "name": "DomainA"}, "InterPro", "2026-02-01", "e1"),
        _ev({"id": "IPR0002", "name": "DomainB"}, "InterPro", "2026-02-02", "e2"),
        _ev({"id": "CATH1", "name": "DomainC"}, "CATH", "2026-02-03", "e3"),
    ]
    rules = {
        "priority_sources": ["InterPro", "CATH", "SCOPe", "TED"],
        "field_rules": {
            "annotations.domains": {"strategy": "priority_sources", "allow_multiple": True}
        },
    }
    out = resolver.resolve_field("annotations.domains", evidences, rules)
    assert isinstance(out["selected_value"], list)
    assert len(out["selected_value"]) == 2
    assert all(v["id"].startswith("IPR") for v in out["selected_value"])
    assert out["conflict"] is not None


def test_molecular_weight_most_recent():
    evidences = [
        _ev(350.1, "PubChem", "2026-02-01", "e1"),
        _ev(351.0, "ChEMBL", "2026-02-05", "e2"),
    ]
    rules = {
        "field_rules": {
            "properties.physchem.molecular_weight": {"strategy": "most_recent", "allow_multiple": False}
        }
    }
    out = resolver.resolve_field("properties.physchem.molecular_weight", evidences, rules)
    assert out["selected_value"] == 351.0
    assert out["conflict"] is not None


def test_smiles_priority_sources_single():
    evidences = [
        _ev("C1CC", "PubChem", "2026-02-01", "e1"),
        _ev("C1CCC", "ChEMBL", "2026-02-02", "e2"),
    ]
    rules = {
        "priority_sources": ["ChEMBL", "PubChem"],
        "field_rules": {
            "identifiers.smiles": {"strategy": "priority_sources", "allow_multiple": False}
        },
    }
    out = resolver.resolve_field("identifiers.smiles", evidences, rules)
    assert out["selected_value"] == "C1CCC"
    assert out["conflict"] is not None
