"""SMonitor configuration for Sabueso (uibcdf/sabueso#31).

Discovered by ``smonitor.integrations.ensure_configured`` from the package root, so it
must stay inside the package to be installed with it.
"""

PROFILE = "user"

SMONITOR = {
    "level": "WARNING",
    "trace_depth": 3,
    "capture_warnings": True,
    "capture_logging": True,
    "theme": "plain",
}

PROFILES = {
    "user": {"level": "WARNING"},
    "dev": {"level": "INFO", "show_traceback": True},
    "qa": {"level": "INFO", "show_traceback": True},
    "agent": {"level": "WARNING"},
    "debug": {"level": "DEBUG", "show_traceback": True},
}

# The catalog is the single source of truth for message templates.
from sabueso._private.smonitor.catalog import CODES, SIGNALS  # noqa: E402,F401
