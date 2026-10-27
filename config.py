"""
╔══════════════════════════════════════════════════════════════╗
║                         QUIZBOT — Configuration              ║
║                                                              ║
║  Sponsored by  : Qzio — qzio.in                              ║
║  Developed by  : devgagan — devgagan.in                      ║
╚══════════════════════════════════════════════════════════════╝

All sensitive values must be set via environment variables or
a `.env` file placed in the project root.  Never commit real
credentials to version control.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Pyrogram (main.py bot) ────────────────────────────────────────────────────
API_ID    = int(os.getenv("API_ID", "0"))
API_HASH  = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ── Telegram — secondary bot token used for HTML/API calls ───────────────────
BOT_TOKEN_2 = os.getenv("BOT_TOKEN_2", "")

# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "")          # Primary connection string
MONGO_URI_2 = os.getenv("MONGO_URI_2", "")      # Secondary / replica connection
MONGO_URIX = os.getenv("MONGO_URIX", "")        # Quizzes async collection URI
DB_NAME   = os.getenv("DB_NAME", "quiz_bot")

# ── MySQL (Quizbot web panel) ───────────────────────────────────────
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB   = os.getenv("MYSQL_DB", "quizbot")

# ── Owner & Groups ────────────────────────────────────────────────────────────
OWNER_ID   = list(map(int, os.getenv("OWNER_ID", "0").split()))
LOG_GROUP  = int(os.getenv("LOG_GROUP", "0"))
FORCE_SUB  = int(os.getenv("FORCE_SUB", "0"))
BOT_GROUP  = int(os.getenv("BOT_GROUP", "0"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# ── Encryption ────────────────────────────────────────────────────────────────
MASTER_KEY = os.getenv("MASTER_KEY", "")
IV_KEY     = os.getenv("IV_KEY", "")

# ── Limits ────────────────────────────────────────────────────────────────────
FREEMIUM_LIMIT = int(os.getenv("FREEMIUM_LIMIT", "0"))
PREMIUM_LIMIT  = int(os.getenv("PREMIUM_LIMIT", "500"))

# ── Optional integrations ─────────────────────────────────────────────────────
PAY_API       = os.getenv("PAY_API", "")
YT_COOKIES    = os.getenv("YT_COOKIES", None)
INSTA_COOKIES = os.getenv("INSTA_COOKIES", None)
UMODE         = os.getenv("UMODE", None)

# ── Mode flags ────────────────────────────────────────────────────────────────
FREE_BOT = os.getenv("FREE_BOT", "true").lower() == "true"
