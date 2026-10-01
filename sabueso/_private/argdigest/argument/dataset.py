import re

from sabueso._private.argdigest._shared import refuse


def digest_dataset(dataset, caller=None):
    """A source's dataset id, such as GTEx's ``gtex_v10``: letters, digits and ``_``."""
    if isinstance(dataset, str) and re.fullmatch(r"[A-Za-z0-9_]+", dataset.strip()):
        return dataset.strip()
    raise refuse("dataset", dataset, caller, "expected a dataset id such as gtex_v10")
