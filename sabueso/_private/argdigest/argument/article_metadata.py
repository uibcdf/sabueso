from sabueso._private.argdigest._shared import refuse


def digest_article_metadata(article_metadata, caller=None):
    """An explicit source-access article envelope, or no supplied metadata."""
    if article_metadata is None or isinstance(article_metadata, dict):
        return article_metadata
    raise refuse(
        "article_metadata",
        article_metadata,
        caller,
        "expected an article metadata envelope or None",
    )
