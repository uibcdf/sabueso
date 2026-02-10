# Sabueso — Selection Rules (Field Examples)

This document provides **field-level, real-world examples** of `selection_rules` for Resolver 0.1.0.
Versioning follows **x.y.z**.

## 1) ProteinCard — Domains (`annotations.domains`)
**Goal:** prefer curated domain sources and keep multiple domains.

```
{
  "version": "0.1.0",
  "priority_sources": ["InterPro", "CATH", "SCOPe", "TED"],
  "field_rules": {
    "annotations.domains": {
      "strategy": "priority_sources",
      "allow_multiple": true
    }
  }
}
```

**Behavior:**
- If InterPro values exist, select **all** InterPro domains.
- Otherwise, fall back to CATH → SCOPe → TED in that order.

## 2) ProteinCard — Catalytic Activity (`annotations.catalytic_activity`)
**Goal:** prefer UniProt curated statement; single value.

```
{
  "version": "0.1.0",
  "priority_sources": ["UniProt"],
  "field_rules": {
    "annotations.catalytic_activity": {
      "strategy": "priority_sources",
      "allow_multiple": false
    }
  }
}
```

## 3) SmallMoleculeCard — Molecular Weight (`properties.physchem.molecular_weight`)
**Goal:** select most recently retrieved numeric value.

```
{
  "version": "0.1.0",
  "field_rules": {
    "properties.physchem.molecular_weight": {
      "strategy": "most_recent",
      "allow_multiple": false
    }
  }
}
```

## 4) SmallMoleculeCard — SMILES (`properties.identifiers.smiles`)
**Goal:** prefer ChEMBL if present; otherwise PubChem.

```
{
  "version": "0.1.0",
  "priority_sources": ["ChEMBL", "PubChem"],
  "field_rules": {
    "properties.identifiers.smiles": {
      "strategy": "priority_sources",
      "allow_multiple": false
    }
  }
}
```

## 5) ProteinCard — Binding Sites (`features_positional.binding_site`)
**Goal:** preserve multiple positional features.

```
{
  "version": "0.1.0",
  "field_rules": {
    "features_positional.binding_site": {
      "strategy": "priority_sources",
      "allow_multiple": true
    }
  }
}
```

## Notes
- These examples are a **starting baseline** and should be refined per project needs.
- Future versions may incorporate confidence scores or LLM-assisted selection.
