import re

from sabueso._private.argdigest._shared import refuse

# The table name is interpolated into SQL, so only plain identifiers are accepted.
TABLE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Holds the meta of every deck stored in a database (sabueso/tools/deck/storage.py).
RESERVED = ("deck_meta",)


def digest_table(table, caller=None):
    """The SQLite table that holds the cards: a plain identifier, not a reserved one."""
    if not isinstance(table, str) or not TABLE_NAME.fullmatch(table):
        raise refuse("table", table, caller, "expected a plain SQL identifier")
    if table in RESERVED:
        raise refuse("table", table, caller, "reserved by Sabueso's storage")
    return table
