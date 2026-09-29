from datetime import date, datetime

from sabueso._private.argdigest._shared import refuse


def digest_when(when, caller=None):
    """A date or a datetime, or its ISO text (``2026-09-29`` or with a time)."""
    if isinstance(when, (date, datetime)):
        return when
    if isinstance(when, str):
        try:
            return (
                datetime.fromisoformat(when)
                if "T" in when
                else date.fromisoformat(when)
            )
        except ValueError:
            pass
    raise refuse("when", when, caller, "expected a date, a datetime or ISO text")
