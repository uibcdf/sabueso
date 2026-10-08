"""Offline source metadata from the maintained registry, without source activation."""

import json
from importlib.resources import files

from smonitor import signal

from sabueso._private.argdigest import arg_digest


@signal(tags=["api", "local"])
@arg_digest()
def get_catalog(skip_digestion=False):
    """Read detached registry decisions and category profiles from packaged metadata.

    Status describes repository adoption, not live health or scientific completeness.
    A category profile keeps deferred/retired/evaluating resources separate from
    in-use members. ``capabilities`` records native function/client declarations,
    declared enrichers and reviewed recovery-input delivery; it does not assess
    live health, complete journeys or consumer acceptance. Reading this catalog
    never queries sources or enriches a card.
    """
    return json.loads(
        files("sabueso")
        .joinpath("resolver", "source_catalog.json")
        .read_text(encoding="utf-8")
    )
