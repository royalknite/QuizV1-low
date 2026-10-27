# QuizBot — Telegram Quiz Platform

## Overview
A two-process Telegram quiz bot platform built in Python.

- `main.py` — Pyrogram-based main bot (quiz creation, management, analytics, file imports, inline queries, broadcasts, assignments, HTML reports).
- `bot.py` — python-telegram-bot scheduler that runs/dispatches polls, handles concurrent quiz sessions, leaderboards, and result comparisons.
- `c.py`, `func.py` — Helper modules (HTML generation, parsing, utilities).
- `config.py` — Loads all configuration from environment variables (uses `python-dotenv`).

This is a pure backend project — there is no web frontend. The bots talk to Telegram via long polling and persist data to MongoDB.

## Tech Stack
- Python 3.12
- Pyrogram 2.0.106 + TgCrypto (Telegram MTProto client)
- python-telegram-bot 20.7 (Bot API client)
- MongoDB (pymongo + motor)
- PyMySQL (optional web panel sync)
- Pillow, sympy, beautifulsoup4, lxml, pycryptodome, playwright

## Workflows
- **Main Bot** — `python main.py` (console)
- **Scheduler Bot** — `python bot.py` (console)

Both run as console workflows; neither listens on an HTTP port.

## Environment Variables / Secrets
Required (already configured in Replit Secrets):
- `API_ID`, `API_HASH`, `BOT_TOKEN` — Pyrogram main bot credentials
- `BOT_TOKEN_2` — Secondary PTB scheduler bot token
- `MONGO_URI`, `MONGO_URI_2`, `MONGO_URIX` — MongoDB connection strings
- `OWNER_ID` — Space-separated owner Telegram IDs

Optional (enable extra features when set; default to 0/empty):
- `LOG_GROUP` — Log channel chat ID
- `FORCE_SUB` — Force-subscribe channel ID
- `BOT_GROUP` — Community group ID
- `CHANNEL_ID` — Announcement channel ID
- `MASTER_KEY`, `IV_KEY` — AES key + IV for quiz file encryption (needed for encrypted quiz import/export)
- `DB_NAME` (default `quiz_bot`)
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASS`, `MYSQL_DB` — Optional MySQL panel sync
- `FREEMIUM_LIMIT`, `PREMIUM_LIMIT` — Quiz limits
- `PAY_API`, `YT_COOKIES`, `INSTA_COOKIES`, `UMODE`, `FREE_BOT`

## Quiz Input Formats

### Format 1 — Classic (single-line question)
```
Question text?
Option A
Option B ✅
Option C
Option D
Ex: Explanation text
```

### Format 2 — 👇-separator (multi-line / statement-based question)
Use a 👇 emoji on its own line to separate the (multi-line) question from the options.
The A)/B)/C)/D) option labels are automatically stripped.
```
Question text?
I. Statement one.
II. Statement two.
Final sub-question?
👇 ─────────────────
A) Option A
B) Option B
C) Option C ✅
D) Option D
Ex: Explanation text
```
Both formats work in `.txt`/`.pdf` file uploads and in the inline `/edit` → update question / add question flows.

## Recent Changes
- 2026-05-04: Added **👇-separator input format** support. The bot now detects a line containing 👇 as the divider between a multi-line question block and its options. A)/B)/C)/D) prefixes are stripped automatically. ✅ marks the correct option; `Ex:` adds an explanation. Supported in both file-upload parsing (`_process_txt_file`) and inline question entry (`_parse_inline_question` helper used by edit/add flows).
- 2026-05-02: **PDF format completely reworked** to match the quiz report style (leaderboard + Q&A). New `pdf_report.py` generates: (1) page 1 with quiz banner header + ranked leaderboard table, (2) subsequent pages with all questions in a 2-column layout showing question text, A/B/C/D options (correct answer highlighted in green), and explanation. Fixes: all questions now included regardless of quiz size; per-question error handling ensures one bad question never aborts the PDF. **Question shuffle**: when a quiz has `shuffle: true`, questions are now randomised before polls are sent (both in group and private mode) and in the PDF. Leaderboard data is passed from `end_group_quiz` / `end_private_quiz` through `send_quiz_result_pdf` to `generate_mock_test_pdf`.

- 2026-04-29: **Scanned PDF → quiz** support. When a PDF has no embedded text, `ai_quiz.py` now rasterizes each page (PyMuPDF / `fitz`) and OCRs them through the same vision provider chain (Gemini vision → Pollinations vision), then feeds the joined text into the question-generation step. Caps: `AI_QUIZ_PDF_OCR_MAX_PAGES=10`, `AI_QUIZ_PDF_OCR_DPI=180`. Added `pymupdf` to `requirements.txt`.
- 2026-04-29: **Image → quiz** support added to `/aicreate`. Users can now send a photo (or image file: jpg/png/webp/etc.) and the AI vision model OCRs the image into text, then runs the standard MCQ-generation pipeline. New helpers in `ai_quiz.py`: `extract_text_from_image()`, `is_image_file()`. Vision provider chain: 1) user's Gemini key (`gemini-2.5-flash` vision with retries+model fallback), 2) Pollinations vision (free OpenAI-compatible). Sandeep is text-only, so it kicks in for the question-generation step after OCR. New `@app.on_message(filters.photo & filters.private)` handler in `main.py` accepts plain photos.
- 2026-04-29: Re-imported into Replit. Bumped `python-telegram-bot` pin to `>=21,<22` so it can share `httpx>=0.28` with `google-genai`. Configured two console workflows (`Main Bot`, `Scheduler Bot`).
- 2026-04-29: AI provider chain reworked. `/aicreate` now uses the **free Sandeep public copilot API** by default (`https://copilotbysandeep.replit.app/chat`). Users can register their **own Gemini API key** via the new `/gemini <key>` command — when set, that key is used instead. The bot no longer requires the Replit AI Integration env vars.
- 2026-04-29: Added AI-powered quiz creation via `/aicreate`. New `ai_quiz.py` module reads PDF/TXT and turns it into MCQs in the bot's native `.txt` block format, then feeds them through the existing `_process_txt_file` pipeline. Added `google-genai` package (used only when the user supplies their own Gemini key).
- 2026-04-26: Initial Replit import. Installed Python dependencies pinned in `requirements.txt`. Configured two console workflows (`Main Bot`, `Scheduler Bot`). Verified both bots authenticate with Telegram and connect to MongoDB.

## AI Quiz
- `/aicreate` — start an AI quiz session (default 25 questions per upload).
  - `/aicreate 50` → ask for 50 questions per upload (max 100).
  - Flow: send quiz name → upload `.pdf` or `.txt` → AI generates MCQs → `/done` to save.
- `/aiconfig` — configure AI generation settings for the current session:
  - `/aiconfig type <direct|statement|assertion|match|mixed>` — question type
  - `/aiconfig lang <language>` — output language (e.g. Hindi, Tamil, English)
  - `/aiconfig bilingual <on|off>` — bilingual mode (language + English on every line)
  - `/aiconfig pages <range|all>` — PDF page range e.g. `1-5`, `3`, `all`
  - `/aiconfig difficulty <easy|medium|hard>` — difficulty level
  - `/aiconfig count <number>` — change question count mid-session
  - `/aiconfig reset` — reset all settings to defaults
  - `/aiconfig` — show current settings
- `/gemini <api_key>` — save your own Gemini API key (stored on your user doc in MongoDB).
- `/gemini` — show whether a key is currently saved.
- `/gemini remove` — delete your saved key.
- Provider chain (auto-fallback if any provider is overloaded/down):
  1. **Your own Gemini key** (if `/gemini` set) — tries `gemini-2.5-flash`, then 2.0-flash, then 2.5-flash-lite, then flash-latest. Each model: 3 retries with 2/4/8 s backoff. Batched in chunks of 25 for big counts.
  2. **Pollinations AI** (free, no key) — OpenAI-compatible endpoint, 3 retries.
  3. **Sandeep AI** (free, no key) — URL-based copilot endpoint, 3 retries.
- Source-text caps per provider: 120 000 chars (Gemini) / 20 000 (Pollinations) / 6 000 (Sandeep, URL length limit). Override via `AI_QUIZ_GEMINI_MAX_CHARS` / `AI_QUIZ_POLLINATIONS_MAX_CHARS` / `AI_QUIZ_SANDEEP_MAX_CHARS`.

## Question Types (AI-generated)
All 5 types are compatible with Telegram polls and the bot's parser:

- **Direct** — standard MCQ with A)/B)/C)/D) options
- **Statement** — introductory text + I./II./III. statements + 👇 separator + options
- **Assertion-Reason** — `Assertion (A): ...` / `Reason (R): ...` + 4 standard AR options
- **Match the Following** — items with `→` arrows + `[ Poll : [N/T] ]` marker + options
- **Mixed** — auto-mix of all types across the quiz (default)

### Prompt Engine (ai_quiz.py)
- Comprehensive system prompt enforces: intelligent extraction vs generation, plain-text-only output, no markdown, answer randomization (correct answer not always A), bilingual support, PDF/OCR formatting recovery (normalizes `A.`/`A:`/`(A)`/`Option A` → `A)`), minimum 10 questions, and all Telegram poll compatibility rules.
- `QuizConfig` dataclass carries all generation parameters through the provider chain.
- Native plain-text output path for all providers (bypasses JSON for complex question types).
- JSON path retained for Gemini (highest fidelity) with automatic fallback to plain-text.

## Recent Changes
- 2026-05-17: **Quiz rendering overhaul (bot.py)**. New strict card format for statement, matching, and assertion-reason questions: `Question X/Y` header line → full question text with statements/arrows on separate lines → `[ Poll : [X/Y] ]` marker → plain A/B/C/D options. No emojis, no markdown, no ✅ in text card. New `needs_full_card()` detection covers Statement (I./II./III.), Match-the-Following (→ arrows / `[ Poll : [N/T] ]` marker), and Assertion-Reason (`Assertion (A):`) types. New `format_matching_question()` ensures arrow items are always displayed vertically. `prepare_poll_content()` now extracts the correct short question line for all rich question types (matching questions use the root question line, not an arrow item). **AI prompt (ai_quiz.py) updated** with explicit WRONG vs RIGHT examples for Statement and Match-the-Following types, preventing the AI from (a) embedding question text inside `[ Poll : [...] ]`, (b) using dash bullet points for options, and (c) listing 👇 as a bullet item. **AI prompt sections 14, 15, 16 added**: Telegram Bot Feature Awareness + PDF Import Recovery, Quiz Editing & Management Compatibility, Parser Safety Rules.
- 2026-05-17: **Bot username updated to `@Xd_Quiz_Bot`** everywhere in main.py (previously `@quizbot`).
- 2026-05-17: **Full inline button system for `/create` flow** in main.py. Every yes/no and preset selection step is now driven by inline buttons: statement-based (Yes/No), section choice (Yes/No), timer (10/15/20/30/45/60/90/120s + Custom), negative marking (0/¼/⅓/½ + Custom), shuffle questions (Yes/No), shuffle options (Yes/No), promo (Skip/Add Custom), quiz type (Free/Paid). Custom numeric entries (timer, neg marking) and custom promo text still use text input. New dedicated `handle_create_callback` handler (registered before the generic callback handler) processes all `cr|<step>|<value>` callbacks. New `_finalize_and_save_quiz` helper unifies quiz saving for both the callback path and any legacy text path. Helper keyboard functions: `_stmt_keyboard`, `_section_keyboard`, `_timer_keyboard`, `_neg_keyboard`, `_shuffq_keyboard`, `_shuffo_keyboard`, `_promo_keyboard`, `_type_keyboard`.
- 2026-05-17: **Comprehensive AI quiz prompt engine** added. New features in `ai_quiz.py`: (1) `QuizConfig` dataclass with language, bilingual, question_type, page_range, difficulty fields; (2) complete system prompt from competition-exam specification covering all 5 question types; (3) correct-answer randomization; (4) PDF/OCR format recovery; (5) page range extraction for PDFs; (6) minimum 10 questions enforcement; (7) `_clean_native_output()` normalizer; (8) enhanced plain-text parser for Statement/Assertion-Reason/Match-the-Following blocks. New `/aiconfig` command in `main.py` exposes all settings per session.
