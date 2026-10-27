"""
bw_guard.py — Render free-plan bandwidth guard (5 GB / month).

What it does (all best-effort; it can NEVER raise into the quiz flow):
  1. Meters an ESTIMATE of outbound bytes the scheduler bot sends to Telegram.
  2. Compares today's estimate with a daily budget (BW_DAILY_BUDGET_MB, default 150 MB
     which is 5 GB * ~0.95 / 31 days).
  3. When the budget gets close, it sheds only OPTIONAL extras:
        level 1 (>= 70 % of daily budget): no promo messages, explanation trimmed to 100 chars
        level 2 (>= 100 %)               : also no poll explanation
     Private (per-user) quizzes: explanation + promo always dropped (BW_PRIVATE_LEAN=false to keep)
     Questions, options, timers, scoring, results, schedules are never touched.

Env vars (all optional):
  BW_DAILY_BUDGET_MB   default 150
  BW_OVERHEAD_BYTES    per-request HTTP/TLS overhead added to the estimate, default 700
  BW_CALIBRATION       multiply the estimate (e.g. 1.3 if /bw shows less than Render's dashboard)
  BW_GUARD_ENABLED     "false" disables shedding (the meter still runs)
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

_IST = ZoneInfo("Asia/Kolkata")
_STATE_FILE = os.getenv("BW_STATE_FILE", "bw_usage.json")

DAILY_BUDGET_MB = float(os.getenv("BW_DAILY_BUDGET_MB", "150"))
OVERHEAD = int(os.getenv("BW_OVERHEAD_BYTES", "700"))
CALIBRATION = float(os.getenv("BW_CALIBRATION", "1.0"))
ENABLED = os.getenv("BW_GUARD_ENABLED", "true").lower() != "false"
# Private (self-attempt) quizzes send every poll once PER USER, so they dominate bandwidth.
# Lean mode drops the per-user poll explanation and promo there. Group quizzes are unaffected.
PRIVATE_LEAN = os.getenv("BW_PRIVATE_LEAN", "true").lower() != "false"

LEVEL1_AT = 0.70
LEVEL2_AT = 1.00

_day = ""
_bytes = 0.0
_msgs = 0
_last_save = 0.0
_last_level = 0
_history: dict = {}  # "YYYY-MM-DD" -> MB


def _today() -> str:
    return datetime.now(_IST).strftime("%Y-%m-%d")


def _load() -> None:
    global _day, _bytes, _msgs, _history
    try:
        with open(_STATE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        _history = d.get("history", {})
        if d.get("day") == _today():
            _day, _bytes, _msgs = d["day"], float(d.get("bytes", 0)), int(d.get("msgs", 0))
    except Exception:
        pass


def _save(force: bool = False) -> None:
    global _last_save
    now = time.time()
    if not force and now - _last_save < 60:
        return
    _last_save = now
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"day": _day, "bytes": _bytes, "msgs": _msgs, "history": _history}, f)
    except Exception:
        pass


def _roll() -> None:
    """Start a new day bucket at IST midnight."""
    global _day, _bytes, _msgs
    t = _today()
    if t != _day:
        if _day:
            _history[_day] = round(_bytes / 1e6, 1)
            for k in sorted(_history)[:-35]:
                _history.pop(k, None)
        _day, _bytes, _msgs = t, 0.0, 0


def _add(payload_bytes: int) -> None:
    global _bytes, _msgs
    try:
        _roll()
        _bytes += (payload_bytes + OVERHEAD) * CALIBRATION
        _msgs += 1
        _save()
    except Exception:
        pass


def _sz(*parts) -> int:
    n = 0
    for p in parts:
        if not p:
            continue
        if isinstance(p, (list, tuple)):
            n += sum(len(str(x).encode("utf-8")) for x in p)
        else:
            n += len(str(p).encode("utf-8"))
    return n


def record_message(text, extra=None) -> None:
    _add(_sz(text, extra) + 60)


def record_poll(question, options, explanation) -> None:
    _add(_sz(question, options, explanation) + 150)


def used_mb() -> float:
    _roll()
    return _bytes / 1e6


def level() -> int:
    """0 normal, 1 trim extras, 2 drop extras."""
    global _last_level
    if not ENABLED or DAILY_BUDGET_MB <= 0:
        return 0
    ratio = used_mb() / DAILY_BUDGET_MB
    lv = 2 if ratio >= LEVEL2_AT else 1 if ratio >= LEVEL1_AT else 0
    if lv != _last_level:
        _last_level = lv
        try:
            import logging
            logging.getLogger(__name__).warning(
                f"[bw_guard] saver level -> {lv} (est. {used_mb():.1f} MB of {DAILY_BUDGET_MB:.0f} MB today)"
            )
        except Exception:
            pass
    return lv


def lean_private() -> bool:
    return ENABLED and PRIVATE_LEAN


def skip_promo() -> bool:
    return level() >= 1


def adjust_explanation(expl):
    """Trim/drop the poll explanation depending on the saver level."""
    try:
        if not expl:
            return expl
        lv = level()
        if lv >= 2:
            return None
        if lv == 1 and len(expl) > 100:
            return expl[:99] + "…"
    except Exception:
        pass
    return expl


def report() -> str:
    _roll()
    month = datetime.now(_IST).strftime("%Y-%m")
    month_mb = sum(v for k, v in _history.items() if k.startswith(month)) + used_mb()
    return (
        "📶 <b>Bandwidth guard (estimate)</b>\n"
        f"Today: <b>{used_mb():.1f} MB</b> / {DAILY_BUDGET_MB:.0f} MB budget "
        f"({_msgs} sends)\n"
        f"This month (since last restart/file): ~{month_mb:.0f} MB\n"
        f"Saver level: <b>{level()}</b> "
        "(0 = full, 1 = no promo + short explanation, 2 = no explanation)\n"
        "Compare with Render → Metrics. If Render shows more, set BW_CALIBRATION "
        "(Render ÷ this number)."
    )


_load()
