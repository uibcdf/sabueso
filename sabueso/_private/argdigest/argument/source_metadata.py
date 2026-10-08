import json

from sabueso._private.argdigest._shared import refuse


def digest_source_metadata(source_metadata, caller=None):
    allowed = {"source", "kind", "query", "retrieved_at", "version", "terms"}
    if not isinstance(source_metadata, dict) or set(source_metadata) - allowed:
        raise refuse(
            "source_metadata",
            source_metadata,
            caller,
            "expected declared source/kind/query/retrieved_at/version/terms metadata",
        )
    for key in ("source", "kind"):
        if (
            not isinstance(source_metadata.get(key), str)
            or not source_metadata[key].strip()
        ):
            raise refuse(
                "source_metadata",
                source_metadata,
                caller,
                f"{key} must be a non-empty string",
            )
    if not isinstance(source_metadata.get("query", {}), dict):
        raise refuse(
            "source_metadata", source_metadata, caller, "query must be a mapping"
        )
    for key in ("retrieved_at", "version"):
        value = source_metadata.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise refuse(
                "source_metadata",
                source_metadata,
                caller,
                f"{key} must be non-empty text or None",
            )
    try:
        return json.loads(json.dumps(source_metadata, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise refuse(
            "source_metadata",
            source_metadata,
            caller,
            "metadata must be finite JSON data",
        ) from error
