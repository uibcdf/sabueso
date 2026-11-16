"""Check or launch the component-owned exploratory desktop workspace.

This is a source-development entry point, not an installer or public package route.
"""

import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "devtools/explorer_cohort.json"
DEFAULT = ROOT / "build/explorer-development"


def _git(path, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(path), *arguments], text=True, stderr=subprocess.PIPE
    ).strip()


def _inspect(workspace):
    cohort = json.loads(COHORT.read_text())
    if list(sys.version_info[:2]) != cohort["python"]:
        raise ValueError("The explorer workspace requires Python 3.14")
    if sys.platform != cohort["platform"]:
        raise ValueError("This received development profile is Linux-only")
    if Path(sys.prefix).resolve() != (workspace / "env").resolve():
        raise ValueError("The interpreter is outside the owned workspace")
    binding = json.loads((workspace / "workspace.json").read_text())
    if binding["cohort_sha256"] != hashlib.sha256(COHORT.read_bytes()).hexdigest():
        raise ValueError("The local workspace belongs to a different cohort")
    report = {"python": sys.executable, "prefix": sys.prefix, "providers": {}}
    report["distributions"] = {}
    for name, expected in cohort["distributions"].items():
        actual = metadata.version(name)
        if actual != expected:
            raise ValueError(f"{name} version changed; receive the new cohort first")
        report["distributions"][name] = actual
    for name in ["sabueso", *cohort["providers"]]:
        module = importlib.import_module(name)
        source = Path(module.__file__).resolve().parent.parent
        origin = json.loads(metadata.distribution(name).read_text("direct_url.json"))
        if not origin.get("dir_info", {}).get("editable"):
            raise ValueError(f"{name} must use its local editable checkout")
        address = urlsplit(origin["url"])
        if address.scheme != "file" or address.netloc:
            raise ValueError(f"{name} editable metadata must name a local checkout")
        declared = Path(unquote(address.path)).resolve()
        if declared != source:
            raise ValueError(f"{name} import and editable metadata disagree")
        if name == "sabueso":
            if source != ROOT:
                raise ValueError("Sabueso must use this checkout")
        else:
            if _git(source, "rev-parse", "HEAD") != cohort["providers"][name]:
                raise ValueError(f"{name} source changed; receive the new cohort first")
            if _git(source, "status", "--porcelain"):
                raise ValueError(f"{name} has unreceived local changes")
            if name == "molsysmt" and source != workspace / "providers/molsysmt":
                raise ValueError("MolSysMT must use the owned fixed-source checkout")
        report["providers"][name] = {
            "source": str(source),
            "version": metadata.version(name),
        }
    native = Path(importlib.import_module("molsysmt._rust").__file__)
    if not native.resolve().is_relative_to(workspace / "providers/molsysmt"):
        raise ValueError("MolSysMT native module is outside its owned source")
    if hashlib.sha256(native.read_bytes()).hexdigest() != binding["native_sha256"]:
        raise ValueError("MolSysMT native bytes changed; receive the new build first")
    report["native_sha256"] = binding["native_sha256"]
    report["scope"] = cohort["scope"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT)
    parser.add_argument("operation", choices=["check", "run", "_inspect"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if not workspace.is_relative_to(ROOT / "build"):
        parser.error("Use a component-owned workspace under this checkout's build/")
    try:
        if args.operation == "_inspect":
            print(json.dumps(_inspect(workspace)))
            return
        python = workspace / "env/bin/python"
        if not python.is_file():
            raise ValueError(
                "Workspace is absent; see devguide/pending_proposals/interactive_development_workspace_0160.md"
            )
        result = subprocess.run(
            [
                str(python),
                str(Path(__file__).resolve()),
                "--workspace",
                str(workspace),
                "_inspect",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip() or "Workspace inspection failed")
        report = json.loads(result.stdout)
        if args.operation == "check":
            print(json.dumps(report, indent=2))
            return
        cohort = json.loads(COHORT.read_text())
        env = os.environ.copy()
        for key in [
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "RAYON_NUM_THREADS",
            "NUMBA_NUM_THREADS",
            "OPENMM_CPU_THREADS",
            "LP_NUM_THREADS",
        ]:
            env[key] = str(cohort["native_threads"])
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[: cohort["cpu_limit"]])
        forwarded = (
            args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        )
        os.execve(str(python), [str(python), "-m", "sabueso.explorer", *forwarded], env)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"Explorer workspace refused: {error}\n")


if __name__ == "__main__":
    main()
