from sabueso._private.argdigest._shared import options, positive_int, refuse

from .article_ids import digest_article_ids


def digest_europepmc(europepmc, caller=None):
    """Accession search, or located mentions in explicitly named articles."""
    value = options(
        "europepmc",
        europepmc,
        caller,
        {"limit": positive_int, "article_ids": lambda value: None},
    )
    if value is not None and "article_ids" in value:
        if "limit" in value:
            raise refuse(
                "europepmc", value, caller, "article_ids and limit are separate routes"
            )
        value["article_ids"] = digest_article_ids(value["article_ids"], caller)
    return value
