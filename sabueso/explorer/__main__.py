"""Launch the optional development desktop application."""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Explore retained Sabueso knowledge")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--card", type=Path, help="Open a serialized Card JSON file")
    inputs.add_argument(
        "--reading", type=Path, help="Open an original saved exploration"
    )
    inputs.add_argument("--deck", type=Path, help="Open a stored Deck JSONL file")
    parser.add_argument(
        "--output-directory",
        type=Path,
        required=True,
        help="Directory for new saved readings",
    )
    parser.add_argument("--debug-port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--capture-directory", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    from ._qt import _window

    with tempfile.TemporaryDirectory(prefix="sabueso-explorer-") as directory:
        bootstrap = Path(directory) / "bootstrap.json"
        command = [
            sys.executable,
            "-m",
            "sabueso.explorer._service",
            "--bootstrap",
            str(bootstrap),
            "--output-directory",
            str(args.output_directory.resolve()),
        ]
        for key in ("card", "reading", "deck"):
            path = getattr(args, key)
            if path:
                command.extend([f"--{key}", str(path.resolve())])
        process = subprocess.Popen(command)
        try:
            deadline = time.monotonic() + 60
            while not bootstrap.exists():
                if process.poll() is not None:
                    raise SystemExit(
                        "The reading service could not start; inspect its diagnostic."
                    )
                if time.monotonic() >= deadline:
                    raise SystemExit(
                        "The reading service did not start within 60 seconds."
                    )
                time.sleep(0.05)
            _window(
                json.loads(bootstrap.read_text())["url"],
                args.debug_port,
                args.capture_directory,
                process,
            )
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
