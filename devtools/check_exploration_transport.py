"""Exercise installed exploration transport outside the checkout without sources."""

import argparse
import hashlib
import json
import socket
from pathlib import Path
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    import sabueso
    from sabueso.core.card import Card

    if args.installed:
        assert "site-packages" in Path(sabueso.__file__).parts, sabueso.__file__

    def forbidden(*a, **k):
        raise AssertionError("Transport smoke must not acquire knowledge")

    socket.create_connection = socket.socket.connect = forbidden
    card = Card()
    card.unknown_stored["codec_smoke"] = [
        False,
        0,
        None,
        "α🧬",
        {"value": 1.0, "unit": "nanomolar"},
    ]
    view = card.explore().inspect()
    rows = []
    with TemporaryDirectory() as directory:
        for compression in ("none", "gzip", "zstd"):
            path = Path(directory) / compression
            receipt = view.save(path, compression=compression)
            saved = sabueso.read_exploration(
                path, expected_digest=receipt["bundle_digest"]
            )
            assert saved.native_payload == card.to_dict()
            assert saved.validation["integrity"] == "verified"
            assert (
                saved.validation["transport"]["decoded_sha256"]
                == receipt["transport"]["decoded_sha256"]
            )
            assert (
                receipt["transport"]["encoded_sha256"]
                == "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            )
            rows.append(receipt["transport"])
        assert len({row["decoded_sha256"] for row in rows}) == 1
    scope = "installed" if args.installed else "development"
    print(
        f"PASS: {scope} exploration transport; plain/gzip/Zstandard; identical original JSON; inert scientific verification"
    )
    print(
        json.dumps(
            {
                "sdk": sabueso.__version__,
                "installed": args.installed,
                "transports": rows,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
