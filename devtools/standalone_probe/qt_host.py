"""Thin Qt window for the identical-workspace development experiment."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from pathlib import Path
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", type=Path, required=True)
    parser.add_argument("--cdp-port", type=int, required=True)
    parser.add_argument("--software", action="store_true")
    parser.add_argument(
        "--graphics-profile", choices=("software", "default", "angle-vulkan")
    )
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--lab-no-sandbox", action="store_true")
    args = parser.parse_args()
    if args.lab_no_sandbox:
        os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = f"127.0.0.1:{args.cdp_port}"
    flags = ["--num-raster-threads=1"]
    profile_name = args.graphics_profile or ("software" if args.software else "default")
    if args.software and profile_name != "software":
        raise ValueError("Conflicting graphics profile requests")
    profiles = json.loads(
        (Path(__file__).parent / "graphics_profiles.json").read_text()
    )
    flags += ["--" + flag for flag in profiles[profile_name]["chromium_switches"]]
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join(flags)
    from PySide6.QtCore import QCoreApplication, QEvent, QTimer, QUrl
    from PySide6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineUrlRequestInterceptor,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    class LocalOnly(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info):
            url = info.requestUrl()
            if (
                url.scheme() in {"http", "https", "ws", "wss"}
                and url.host() != "127.0.0.1"
            ):
                info.block(True)

    bootstrap = json.loads(args.bootstrap.read_text(encoding="utf-8"))
    if urlsplit(bootstrap["url"]).hostname != "127.0.0.1":
        raise ValueError("The probe requires its owned loopback backend")
    app = QApplication([sys.argv[0]])
    app.setApplicationName("Sabueso standalone probe")
    view = QWebEngineView()
    profile = QWebEngineProfile(app)
    interceptor = LocalOnly(profile)
    profile.setUrlRequestInterceptor(interceptor)
    page = QWebEnginePage(profile, view)
    view.setPage(page)
    view.resize(1280, 900)
    view.setWindowTitle("Sabueso — standalone integration probe")
    view.load(QUrl(bootstrap["url"]))
    view.show()
    timer = QTimer()

    def capture_requested():
        if args.capture_dir is None:
            return
        request = args.capture_dir / "native-capture-request.json"
        if not request.is_file():
            return
        phase = json.loads(request.read_text())["phase"]
        request.unlink()
        if phase not in {
            "initial-workspace",
            "selected-workspace",
            "final-workspace",
            "scale-workspace",
            "failure",
        }:
            raise ValueError("Unknown native capture phase")
        target = args.capture_dir / f"{phase}-qt-native.png"
        if target.exists():
            raise ValueError("Native capture must not overwrite prior evidence")
        view.grab().save(str(target))

    timer.timeout.connect(capture_requested)
    timer.start(250)
    signal.signal(signal.SIGTERM, lambda *unused: app.quit())
    signal.signal(signal.SIGINT, lambda *unused: app.quit())
    app.exec()
    view.close()
    page.deleteLater()
    view.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    profile.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    main()
