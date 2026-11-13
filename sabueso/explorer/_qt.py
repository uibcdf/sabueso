"""Thin optional native host; knowledge work runs in the separate service."""

import os
import signal
import sys
from urllib.parse import urlsplit

from depdigest import dep_digest


@dep_digest("PySide6")
def _window(
    url, debug_port=None, capture_directory=None, backend=None, *, molecular_origin=None
):
    if urlsplit(url).hostname != "127.0.0.1":
        raise ValueError("The window requires its owned loopback service")
    if debug_port is not None:
        if not 1024 <= debug_port <= 65535:
            raise ValueError("Invalid local development debug port")
        os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = f"127.0.0.1:{debug_port}"
    from PySide6.QtCore import QCoreApplication, QEvent, QTimer, QUrl
    from PySide6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineUrlRequestInterceptor,
    )
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    origin = urlsplit(url).netloc
    allowed = {origin}
    if molecular_origin:
        model = urlsplit(molecular_origin)
        if (
            model.scheme != "http"
            or model.hostname != "127.0.0.1"
            or not model.port
            or model.username
            or model.password
            or model.path
            or model.query
            or model.fragment
        ):
            raise ValueError("The molecular window requires its owned loopback origin")
        allowed.add(model.netloc)

    class LocalOnly(QWebEngineUrlRequestInterceptor):
        def interceptRequest(self, info):
            address = info.requestUrl()
            if address.scheme() not in {"http", "ws", "data", "about", "blob"} or (
                address.scheme() in {"http", "ws"}
                and address.authority() not in allowed
            ):
                info.block(True)

    class Page(QWebEnginePage):
        def acceptNavigationRequest(self, address, kind, main_frame):
            return address.scheme() == "about" or (
                address.scheme() == "http"
                and address.authority() in ({origin} if main_frame else allowed)
            )

    app = QApplication([sys.argv[0]])
    app.setApplicationName("Sabueso")
    view = QWebEngineView()
    profile = QWebEngineProfile(app)
    interceptor = LocalOnly(profile)
    profile.setUrlRequestInterceptor(interceptor)
    page = Page(profile, view)
    view.setPage(page)
    page.windowCloseRequested.connect(view.close)
    view.resize(1280, 900)
    view.setWindowTitle("Sabueso — Molecular knowledge explorer")
    view.load(QUrl(url))
    view.show()
    timer = QTimer()

    def tick():
        if backend is not None and backend.poll() is not None:
            view.setWindowTitle(
                "Sabueso — Reading service stopped; reopen the application"
            )
        if capture_directory is not None:
            request = capture_directory / "capture-request"
            if request.exists():
                request.unlink()
                target = capture_directory / "native.png"
                if not target.exists():
                    view.grab().save(str(target))

    timer.timeout.connect(tick)
    timer.start(250)
    signal.signal(signal.SIGTERM, lambda *unused: app.quit())
    signal.signal(signal.SIGINT, lambda *unused: app.quit())
    try:
        app.exec()
    finally:
        view.close()
        page.deleteLater()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        profile.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
