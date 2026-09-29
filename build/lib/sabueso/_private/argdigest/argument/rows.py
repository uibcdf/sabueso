from sabueso._private.argdigest._shared import refuse


def digest_rows(rows, caller=None):
    """Table rows: a list of dicts (``Card.table`` output)."""
    if isinstance(rows, list) and all(isinstance(r, dict) for r in rows):
        return rows
    raise refuse("rows", rows, caller, "expected a list of row dicts (card.table)")
