"""Desktop entry point: serve the Dash app locally and host it in a pywebview window.

This is the entry point used by the PyInstaller build (``reacto.spec``). It does
NOT replace ``app.py`` — that module remains the canonical Flask server used by
the VM / gunicorn deployment via ``if __name__ == '__main__'``.

The server is bound to ``127.0.0.1`` so the process never accepts connections
from other machines. The port is picked dynamically at startup so two instances
of the desktop app can coexist.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from contextlib import closing

# Importing ``app`` registers all pages and callbacks; we then run its Flask server.
from app import app as dash_app, server as flask_server

HOST = "127.0.0.1"
WINDOW_TITLE = "REACTO"


def _pick_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


def _run_server(port: int) -> None:
    # debug=False + use_reloader=False are required so PyInstaller-frozen builds
    # don't fork or try to watch source files.
    flask_server.run(host=HOST, port=port, debug=False, use_reloader=False, threaded=True)


def _wait_for_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            try:
                sock.connect((HOST, port))
                return
            except OSError:
                time.sleep(0.1)
    raise RuntimeError(f"Dash server did not start listening on {HOST}:{port} within {timeout}s")


def main() -> int:
    # Importing pywebview here keeps the import error message readable when running
    # the desktop entry point from a fresh checkout without the desktop deps.
    import webview

    port = _pick_free_port()
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()
    _wait_for_port(port)

    url = f"http://{HOST}:{port}/"
    webview.create_window(WINDOW_TITLE, url, width=1400, height=900, min_size=(1000, 700))
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
