from sabueso._private.argdigest._shared import refuse


def digest_file_format(file_format, caller=None):
    if file_format is None or file_format in (
        "json",
        "jsonl",
        "ndjson",
        "csv",
        "tsv",
        "html",
        "txt",
    ):
        return file_format
    raise refuse(
        "file_format",
        file_format,
        caller,
        "expected json, jsonl, ndjson, csv, tsv, html, txt or None",
    )
