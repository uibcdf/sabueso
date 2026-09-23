"""Scientific-context boundaries enforced on the package (devguide/DECISIONS.md).

Sabueso records what sources state. Computing descriptors, fingerprints or similarities
is modelling, which belongs to MolSysSuite, so no module of the ``sabueso`` package may
import a chemistry toolkit (uibcdf/sabueso#25). Tests and tooling are not covered.
"""

import re
from pathlib import Path

CHEMISTRY_TOOLKITS = (
    "rdkit",
    "openbabel",
    "pybel",
    "openeye",
    "oechem",
    "mordred",
    "datamol",
    "molfeat",
    "cdk",
    "indigo",
    "chemfp",
)
IMPORT = re.compile(
    r"^\s*(?:import|from)\s+(" + "|".join(CHEMISTRY_TOOLKITS) + r")\b", re.MULTILINE
)


def test_the_package_never_imports_a_chemistry_toolkit():
    offenders = {
        str(path): IMPORT.findall(path.read_text(encoding="utf-8"))
        for path in sorted(Path("sabueso").rglob("*.py"))
    }
    assert {path: found for path, found in offenders.items() if found} == {}


def test_the_guard_recognises_toolkit_imports():
    assert IMPORT.findall("from rdkit.Chem import Descriptors\nimport math\n") == [
        "rdkit"
    ]
    assert IMPORT.findall("    import openbabel as ob\n") == ["openbabel"]
    assert IMPORT.findall("import cdk_utils\nfrom indigoish import x\n") == []
