import re

from sabueso._private.argdigest._shared import refuse

ARTICLE_ID = re.compile(r"(?:MED:[1-9][0-9]*|PMC:PMC[1-9][0-9]*)\Z")


def digest_article_ids(article_ids, caller=None):
    """Explicit Europe PMC article ids; never protein names or inferred publications."""
    values = [article_ids] if isinstance(article_ids, str) else article_ids
    if not isinstance(values, (list, tuple)) or not values:
        raise refuse("article_ids", article_ids, caller, "expected article ids")
    normalized = []
    for value in values:
        if not isinstance(value, str) or not ARTICLE_ID.fullmatch(
            value.strip().upper()
        ):
            raise refuse(
                "article_ids", article_ids, caller, "expected MED:<pmid> or PMC:PMC<id>"
            )
        value = value.strip().upper()
        if value not in normalized:
            normalized.append(value)
    return normalized
