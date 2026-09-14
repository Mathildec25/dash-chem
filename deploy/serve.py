# -*- coding: utf-8 -*-
"""Serve REACTO with a production server instead of Flask's development one.

    python deploy/serve.py            # port 8088, or $PORT

Waitress is pure Python and runs the same on Windows and Linux; it serves the
Dash app from one process with a pool of threads, which is what the live HITL
page assumes: its per-campaign and optimiser locks live in process memory, so
never run several worker processes behind the same data folder. HTTPS is the
reverse proxy's job (nginx, Caddy, IIS), not this script's.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from waitress import serve

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8088"))
    print("REACTO on http://0.0.0.0:%d (waitress, 8 threads)" % port, flush=True)
    serve(app.server, host="0.0.0.0", port=port, threads=8, channel_timeout=120)
