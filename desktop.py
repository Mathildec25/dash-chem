"""Desktop entry point: serve the Dash app locally and host it in a pywebview window.

This is the entry point used by the PyInstaller build (``reacto.spec``). It does
NOT replace ``app.py`` — that module remains the canonical Flask server used by
the VM / gunicorn deployment via ``if __name__ == '__main__'``.

The server is bound to ``127.0.0.1`` so the process never accepts connections
from other machines. The port is picked dynamically at startup so two instances
of the desktop app can coexist.
"""

from __future__ import annotations

import ctypes
import os
import socket
import sys
import threading
import time
from contextlib import closing

# Pin pywebview's .NET runtime to .NET Framework BEFORE pywebview's winforms
# module is imported. winforms.py does:
#
#     try:
#         import clr
#     except Exception:
#         os.environ['PYTHONNET_RUNTIME'] = 'coreclr'
#         import clr
#
# If the first import fails for any reason, it falls back to ``coreclr`` —
# which then fails with the cryptic
#   "Failed to resolve Python.Runtime.Loader.Initialize from Python.Runtime.dll"
# because the coreclr loader needs a Python.Runtime.runtimeconfig.json we
# don't ship, and even if we did the user might not have .NET 6+ installed.
#
# Pinning to ``netfx`` keeps us on .NET Framework, which ships with every
# in-support build of Windows 10/11. If netfx itself fails we surface a
# clear messagebox below rather than letting pywebview swallow it.
os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")

# Importing ``app`` registers all pages and callbacks; we then run its Flask server.
from app import app as dash_app, server as flask_server

HOST = "127.0.0.1"
WINDOW_TITLE = "REACTO"
WEBVIEW2_DOWNLOAD_URL = "https://developer.microsoft.com/microsoft-edge/webview2/"
NETFX_DOWNLOAD_URL = "https://dotnet.microsoft.com/download/dotnet-framework"

_MB_ICONERROR = 0x00000010
_MB_OK = 0x00000000


def _show_error_dialog(title: str, message: str) -> None:
    """Show a native Win32 error dialog. No-op on non-Windows / headless."""
    try:
        ctypes.windll.user32.MessageBoxW(None, message, title, _MB_ICONERROR | _MB_OK)
    except Exception:
        # Last-resort console output (visible in the debug-console build).
        print(f"[{title}] {message}", file=sys.stderr)


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
    # Importing pywebview here keeps the import error message readable when
    # running the desktop entry point from a fresh checkout without the desktop
    # deps — and lets us catch pythonnet bootstrap failures with a friendly
    # dialog instead of an opaque traceback.
    try:
        import webview
        from webview import WebViewException
    except Exception as exc:
        _show_error_dialog(
            f"{WINDOW_TITLE} — startup error",
            "REACTO could not initialize the .NET runtime needed by its window "
            "host (pywebview / pythonnet).\n\n"
            "Please make sure .NET Framework 4.7.2 or later is installed:\n"
            f"  {NETFX_DOWNLOAD_URL}\n\n"
            f"Technical details: {type(exc).__name__}: {exc}",
        )
        return 1

    port = _pick_free_port()
    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()
    _wait_for_port(port)

    url = f"http://{HOST}:{port}/"
    webview.create_window(WINDOW_TITLE, url, width=1400, height=900, min_size=(1000, 700))

    # gui='edgechromium' documents that we want the WebView2 (Edge Chromium)
    # render engine. On Windows pywebview 6.x always dispatches through the
    # winforms backend regardless, but winforms picks WebView2 over MSHTML
    # when the WebView2 Runtime is present, so absence of the runtime is the
    # most common reason the window stays blank or fails to open.
    try:
        webview.start(gui="edgechromium")
    except WebViewException as exc:
        _show_error_dialog(
            f"{WINDOW_TITLE} — WebView2 not available",
            "REACTO needs the Microsoft Edge WebView2 Runtime to display its "
            "interface.\n\n"
            "Download the free \"Evergreen Standalone Installer\" from:\n"
            f"  {WEBVIEW2_DOWNLOAD_URL}\n\n"
            "Run the installer, then start REACTO again.\n\n"
            f"Technical details: {exc}",
        )
        return 1
    except Exception as exc:  # pythonnet/clr loader failures surface here too
        _show_error_dialog(
            f"{WINDOW_TITLE} — startup error",
            "REACTO failed to open its window. This usually means one of these "
            "Windows components is missing:\n\n"
            f"  • Microsoft Edge WebView2 Runtime — {WEBVIEW2_DOWNLOAD_URL}\n"
            f"  • .NET Framework 4.7.2 or later — {NETFX_DOWNLOAD_URL}\n\n"
            f"Technical details: {type(exc).__name__}: {exc}",
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
