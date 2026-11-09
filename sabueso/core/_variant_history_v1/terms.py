"""Pure SDK230 GTEx tissue-key normalization, without a mapping or client."""

import re

KEY_RULE = "gtex_tissue_key@1"


def tissue_key(gtex_id: str) -> str:
    """The key gnomAD's pext names a GTEx tissue by (``gtex_tissue_key@1``)."""
    return re.sub(r"[^a-z0-9]+", "_", str(gtex_id).lower()).strip("_")
