"""Bind supplied original files before loading; native validation stays with clients."""

from sabueso._private.argdigest.argument.expected_sha256 import digest_expected_sha256
from sabueso._private.argdigest.argument.path import digest_path
from sabueso._private.argdigest.argument.source_metadata import digest_source_metadata
from sabueso.core.errors import ConnectorError
from sabueso.core.source_acquisition import missing_fixture
from sabueso.tools.source_snapshot import load_source_snapshot


class BoundSourceSnapshot:
    """Private source-client configuration, without remote access or card admission."""

    def __init__(self, path, *, source_metadata, expected_sha256=None):
        self.path = digest_path(path)
        self.source_metadata = digest_source_metadata(source_metadata)
        self.expected_sha256 = digest_expected_sha256(expected_sha256)

    def read(self, source, kind, query, *, file_format):
        """Refuse foreign declarations before touching the file, then retain its receipt."""
        metadata = self.source_metadata
        if (
            metadata["source"] != source
            or metadata["kind"] != kind
            or metadata.get("query") != query
            or metadata.get("version") is not None
        ):
            raise ConnectorError(
                f"Supplied {source} source/kind/query/revision differ from the request."
            )
        try:
            return load_source_snapshot(
                self.path,
                source_metadata=metadata,
                file_format=file_format,
                expected_sha256=self.expected_sha256,
            )
        except OSError as error:
            raise missing_fixture(
                f"Supplied {source} snapshot is unavailable: {self.path}"
            ) from error
