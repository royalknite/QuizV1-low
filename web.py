"""
╔══════════════════════════════════════════════════════════════╗
║   QUIZBOT — Render Web Service entrypoint                    ║
║                                                              ║
║   Render's free Web Service plan kills any process that      ║
║   doesn't bind to $PORT.  This module:                       ║
║                                                              ║
║     1. Starts main.py and bot.py as subprocesses             ║
║     2. Runs a tiny HTTP server on $PORT that returns         ║
║        a health-check response (keeps Render happy)          ║
║     3. Restarts a bot if it crashes (so it stays 24/7)       ║
║     4. Forwards SIGTERM/SIGINT to the children for clean     ║
║        shutdowns on redeploys                                ║
║                                                              ║
║   Render start command:   python web.py                      ║
╚══════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.getenv("PORT", "10000"))

# ── Self-ping (anti-sleep) ──────────────────────────────────────────────
# Render's free Web Service plan puts the app to sleep after ~15 min of
# inbound traffic silence.  We hit our own /healthz every few minutes so
# the service stays awake 24/7.
#
# URL resolution order:
#   1. PING_URL                (set this manually if you want to override)
#   2. RENDER_EXTERNAL_URL     (auto-injected by Render)
#   3. None                    (self-ping disabled — fine for VPS / paid plans)
PING_URL = os.getenv("PING_URL") or os.getenv("RENDER_EXTERNAL_URL")
PING_INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "240"))  # 4 min

BOTS = [
    ("main",      [sys.executable, "-u", "main.py"]),
    ("scheduler", [sys.executable, "-u", "bot.py"]),
]

RESTART_BACKOFF_SECONDS = 5
_processes: dict[str, subprocess.Popen] = {}
_shutdown = threading.Event()


# ── HTTP keep-alive server ──────────────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        alive = {name: (p.poll() is None) for name, p in _processes.items()}
        body = "QuizBot alive — " + ", ".join(f"{k}={'up' if v else 'down'}" for k, v in alive.items())
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())

    def do_HEAD(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):  # silence default access log
        return


def start_http_server() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"[web] Health server listening on 0.0.0.0:{PORT}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


# ── Self-ping loop (keeps Render free plan awake) ───────────────────────
def self_ping_loop() -> None:
    if not PING_URL:
        print("[web] Self-ping disabled (no PING_URL / RENDER_EXTERNAL_URL set).", flush=True)
        return

    url = PING_URL.rstrip("/") + "/"
    print(f"[web] Self-ping enabled: {url} every {PING_INTERVAL_SECONDS}s", flush=True)

    # Wait once before the first ping so the service has time to bind PORT.
    if _shutdown.wait(timeout=30):
        return

    while not _shutdown.is_set():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuizBot-SelfPing/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp.read(64)  # consume a tiny bit so the connection closes cleanly
        except Exception as e:
            print(f"[web] Self-ping failed: {e}", flush=True)
        if _shutdown.wait(timeout=PING_INTERVAL_SECONDS):
            return


# ── Bot supervisor ──────────────────────────────────────────────────────
def _stream_output(name: str, proc: subprocess.Popen) -> None:
    assert proc.stdout is not None
    prefix = f"[{name}] "
    for line in iter(proc.stdout.readline, b""):
        try:
            sys.stdout.write(prefix + line.decode("utf-8", errors="replace"))
            sys.stdout.flush()
        except Exception:
            break


def _spawn(name: str, cmd: list[str]) -> subprocess.Popen:
    print(f"[web] Starting {name}: {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    _processes[name] = proc
    threading.Thread(target=_stream_output, args=(name, proc), daemon=True).start()
    return proc


def supervise(name: str, cmd: list[str]) -> None:
    """Keep `cmd` running until shutdown is requested."""
    while not _shutdown.is_set():
        proc = _spawn(name, cmd)
        proc.wait()
        if _shutdown.is_set():
            return
        print(
            f"[web] {name} exited with code {proc.returncode} — "
            f"restarting in {RESTART_BACKOFF_SECONDS}s",
            flush=True,
        )
        time.sleep(RESTART_BACKOFF_SECONDS)


# ── Signal handling ─────────────────────────────────────────────────────
def _shutdown_handler(signum, _frame):
    if _shutdown.is_set():
        return
    print(f"[web] Received signal {signum} — shutting down children...", flush=True)
    _shutdown.set()
    for name, proc in _processes.items():
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
    deadline = time.time() + 10
    for name, proc in _processes.items():
        timeout = max(0.1, deadline - time.time())
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT, _shutdown_handler)

    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=self_ping_loop, daemon=True).start()

    supervisors = []
    for name, cmd in BOTS:
        t = threading.Thread(target=supervise, args=(name, cmd), daemon=False)
        t.start()
        supervisors.append(t)

    for t in supervisors:
        t.join()


if __name__ == "__main__":
    main()
