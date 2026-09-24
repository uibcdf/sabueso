"""Readable handles for entities in views (uibcdf/sabueso#47)."""

from __future__ import annotations

from typing import List


def molecule_label(name: str | None, refs: List[str], anchor: str) -> tuple:
    """``(label, source)``: a readable handle for a molecule (uibcdf/sabueso#47).

    Its name, else its ChEMBL id, else its PDB component code, else its standard
    InChIKey. Most ChEMBL molecules have no preferred name, and the InChIKey-anchored
    card id says nothing to a reader.
    """
    if name:
        return name, "name"
    for namespace, source in (("chembl:", "chembl"), ("pdb.ligand:", "pdb.ligand")):
        found = sorted(r for r in refs if r.startswith(namespace))
        if found:
            return found[0].split(":", 1)[1], source
    return anchor.rsplit(":", 1)[-1], "inchikey"
