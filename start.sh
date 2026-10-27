#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║   QUIZBOT — One-shot VPS launcher                            ║
# ║   Usage:  bash start.sh                                      ║
# ║                                                              ║
# ║   What it does:                                              ║
# ║     1. Verifies .env exists (copies from .env.example if not)║
# ║     2. Installs Python dependencies                          ║
# ║     3. Launches main.py and bot.py together                  ║
# ║        (bot.py output is prefixed [scheduler],               ║
# ║         main.py output is prefixed [main])                   ║
# ║     4. Stops both cleanly on Ctrl+C                          ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

cd "$(dirname "$0")"

# ── 1. .env check ─────────────────────────────────────────────
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    echo "[start.sh] No .env found — copying from .env.example."
    cp .env.example .env
    echo "[start.sh] >>> Edit .env now and fill in your secrets, then re-run: bash start.sh"
    exit 1
  else
    echo "[start.sh] ERROR: neither .env nor .env.example exists." >&2
    exit 1
  fi
fi

# ── 2. Pick a Python ──────────────────────────────────────────
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "[start.sh] ERROR: $PY not found. Install Python 3.10+." >&2
  exit 1
fi

# ── 3. Install dependencies (idempotent) ──────────────────────
if [[ ! -f .deps_installed ]] || [[ requirements.txt -nt .deps_installed ]]; then
  echo "[start.sh] Installing Python dependencies..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r requirements.txt
  touch .deps_installed
else
  echo "[start.sh] Dependencies already installed (delete .deps_installed to reinstall)."
fi

# ── 4. Launch both bots ───────────────────────────────────────
echo "[start.sh] Starting Main Bot (main.py) and Scheduler Bot (bot.py)..."

cleanup() {
  echo
  echo "[start.sh] Stopping bots..."
  kill 0 2>/dev/null || true
  wait 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

"$PY" -u main.py 2>&1 | sed -u 's/^/[main] /' &
MAIN_PID=$!

"$PY" -u bot.py 2>&1 | sed -u 's/^/[scheduler] /' &
BOT_PID=$!

wait -n "$MAIN_PID" "$BOT_PID"
EXIT_CODE=$?
echo "[start.sh] One process exited with code $EXIT_CODE — shutting down the other."
cleanup
