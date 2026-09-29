from sabueso._private.argdigest._shared import optional_text, refuse

#: A short excerpt with attribution, not a copy of the text (uibcdf/sabueso#29).
MAX_QUOTE = 300


def digest_quote(quote, caller=None):
    """An optional verbatim excerpt, at most MAX_QUOTE characters."""
    quote = optional_text("quote", quote, caller)
    if quote is not None and len(quote) > MAX_QUOTE:
        raise refuse(
            "quote",
            quote[:40] + "...",
            caller,
            f"keep quotes under {MAX_QUOTE} characters",
        )
    return quote
