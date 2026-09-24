"""Withdraw one exact Sabueso file from the public ``main`` label.

The file is not deleted: it gains the ``withdrawn`` label first, so it stays archived and
traceable, and only then loses ``main``, so ``conda install -c uibcdf sabueso`` can no
longer select it. Every call names the exact file; a label is never removed from a whole
package or channel (anaconda-client's ``remove_channel`` would do that if the file
coordinates were omitted).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any

OWNER = "uibcdf"
PACKAGE = "sabueso"
PUBLIC_LABEL = "main"
WITHDRAWN_LABEL = "withdrawn"
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class WithdrawalError(ValueError):
    """Refusing an unproven or unsafe withdrawal."""


def basename(version: str, build_number: int) -> str:
    if not VERSION.fullmatch(version) or build_number < 0:
        raise WithdrawalError(
            "withdrawal needs a canonical X.Y.Z version and a build number"
        )
    return f"noarch/{PACKAGE}-{version}-py_{build_number}.tar.bz2"


def exact_file(api: Any, version: str, name: str) -> dict:
    """The one distribution record of ``name`` in the public registry."""
    release = api.release(OWNER, PACKAGE, version)
    matches = [d for d in release.get("distributions", []) if d.get("basename") == name]
    if len(matches) != 1:
        raise WithdrawalError(f"expected exactly one {name}, found {len(matches)}")
    return matches[0]


def withdraw(
    read_api: Any, write_api: Any, *, version: str, build_number: int, sha256: str
) -> dict:
    """Relabel the verified file, then prove the public ``main`` label no longer holds it."""
    if not SHA256.fullmatch(sha256):
        raise WithdrawalError("withdrawal needs the file's SHA-256")
    name = basename(version, build_number)
    before = exact_file(read_api, version, name)
    if before.get("sha256") != sha256:
        raise WithdrawalError(f"{name} does not have the expected SHA-256")
    labels = set(before.get("labels", []))
    if PUBLIC_LABEL not in labels:
        raise WithdrawalError(f"{name} is not on the {PUBLIC_LABEL!r} label")
    if WITHDRAWN_LABEL not in labels:
        write_api.add_channel(
            WITHDRAWN_LABEL, OWNER, package=PACKAGE, version=version, filename=name
        )
    write_api.remove_channel(
        PUBLIC_LABEL, OWNER, package=PACKAGE, version=version, filename=name
    )
    after = exact_file(read_api, version, name)
    if PUBLIC_LABEL in after.get("labels", []) or WITHDRAWN_LABEL not in after.get(
        "labels", []
    ):
        raise WithdrawalError(
            f"{name} labels after withdrawal are {after.get('labels')}"
        )
    return {
        "file": f"{OWNER}/{PACKAGE}/{version}/{name}",
        "sha256": sha256,
        "labels_before": sorted(labels),
        "labels_after": sorted(after.get("labels", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--build-number", type=int, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    from binstar_client import Binstar

    read_api = Binstar(domain="https://api.anaconda.org")
    write_api = Binstar(
        token=os.environ["ANACONDA_TOKEN"], domain="https://api.anaconda.org"
    )
    receipt = withdraw(
        read_api,
        write_api,
        version=args.version,
        build_number=args.build_number,
        sha256=args.sha256,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
