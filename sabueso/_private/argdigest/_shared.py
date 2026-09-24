"""Helpers shared by digesters (kept out of the digester package on purpose)."""

from __future__ import annotations

from typing import Any

from sabueso.core.errors import ArgumentError


def refuse(argument: str, value: Any, caller: str | None, reason: str) -> ArgumentError:
    return ArgumentError(argument=argument, value=value, caller=caller, reason=reason)


def boolean(argument: str, value: Any, caller: str | None) -> bool:
    if isinstance(value, bool):
        return value
    raise refuse(argument, value, caller, "expected True or False")


def client(argument: str, value: Any, caller: str | None) -> Any:
    """A source client is duck-typed: any object, or None for the online default.

    Its protocol is exercised by the call itself, and a failure there is recorded as a
    source outcome. A string is refused: it is a common slip (a URL or a source name
    where a client object was meant).
    """
    if isinstance(value, (str, bytes)):
        raise refuse(argument, value, caller, "expected a client object or None")
    return value


def options(
    argument: str, value: Any, caller: str | None, allowed: dict
) -> dict | None:
    """``None`` (source off) or a dict of the options the source's client accepts.

    ``allowed`` maps each option to a check returning a reason, or None when valid.
    """
    if value is None:
        return None
    if not isinstance(value, dict):
        raise refuse(argument, value, caller, "expected a dict of options, or None")
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise refuse(
            argument,
            value,
            caller,
            f"unknown options {unknown}; accepted: {sorted(allowed)}",
        )
    for key, check in allowed.items():
        if key in value:
            reason = check(value[key])
            if reason:
                raise refuse(argument, value, caller, f"{key}: {reason}")
    return dict(value)


def positive_int(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return "expected a positive integer"
    return None
