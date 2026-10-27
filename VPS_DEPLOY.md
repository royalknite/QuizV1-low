# 🚀 QuizBot — VPS Deployment Guide

Step-by-step copy-paste guide to run **both bots 24/7** on any Linux VPS
(Ubuntu 22.04 / Debian 12 / similar). Tested on a fresh 1 GB RAM droplet.

> **Repo:** https://github.com/Suraj08832/quizbot1

---

## ⚡ TL;DR — one-shot install

If you already have your `.env` values ready, paste this whole block as
**root** on a fresh Ubuntu/Debian VPS — it sets up everything except the
`.env` (you'll be dropped into nano to fill it in):

```bash
apt update && apt install -y python3 python3-venv python3-pip git curl && \
useradd -m -s /bin/bash quizbot 2>/dev/null; \
mkdir -p /opt/quizbot && chown quizbot:quizbot /opt/quizbot && \
sudo -u quizbot git clone https://github.com/Suraj08832/quizbot1.git /opt/quizbot && \
sudo -u quizbot python3 -m venv /opt/quizbot/.venv && \
sudo -u quizbot /opt/quizbot/.venv/bin/pip install --upgrade pip && \
sudo -u quizbot /opt/quizbot/.venv/bin/pip install -r /opt/quizbot/requirements.txt && \
sudo -u quizbot cp /opt/quizbot/.env.example /opt/quizbot/.env && \
chmod 600 /opt/quizbot/.env && \
cp /opt/quizbot/deploy/quizbot.service /etc/systemd/system/quizbot.service && \
systemctl daemon-reload && \
sudo -u quizbot nano /opt/quizbot/.env && \
systemctl enable --now quizbot && \
systemctl status quizbot --no-pager
```

After that:

```bash
journalctl -u quizbot -f      # live logs
```

---

## Detailed walk-through (recommended for first-time setup)

---

## What you'll set up

- A dedicated `quizbot` user
- The repo at `/opt/quizbot`
- A Python 3.12 virtual-env with all dependencies
- A `systemd` service that auto-starts on boot, auto-restarts on crash,
  and runs **both bots** (`main.py` + `bot.py`) under one supervisor (`web.py`)
- One-line update / restart / logs commands

Total time: **5–10 minutes**.

---

## 0. Before you start — collect these values

You'll paste these into `.env` later. Get them ready:

| Variable | Where to get it |
| --- | --- |
| `API_ID`, `API_HASH` | https://my.telegram.org → API development tools |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `MONGO_URI`, `MONGO_URI_2`, `MONGO_URIX` | MongoDB Atlas / your Mongo server connection strings |
| `OWNER_ID` | Your Telegram user ID (from [@userinfobot](https://t.me/userinfobot)) |

---

## 1. SSH into your VPS

```bash
ssh root@YOUR_VPS_IP
```

---

## 2. Install system packages

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git curl
```

> If your distro doesn't ship Python 3.10+, install `python3.12` from
> deadsnakes (Ubuntu) or use `pyenv`.

---

## 3. Create a dedicated `quizbot` user

Running bots as `root` is a bad idea. Make a low-privilege user:

```bash
useradd -m -s /bin/bash quizbot
```

---

## 4. Clone the repo

```bash
mkdir -p /opt/quizbot
chown quizbot:quizbot /opt/quizbot
sudo -u quizbot git clone https://github.com/Suraj08832/quizbot1.git /opt/quizbot
cd /opt/quizbot
```

---

## 5. Create the virtual-env and install dependencies

```bash
sudo -u quizbot python3 -m venv /opt/quizbot/.venv
sudo -u quizbot /opt/quizbot/.venv/bin/pip install --upgrade pip
sudo -u quizbot /opt/quizbot/.venv/bin/pip install -r /opt/quizbot/requirements.txt
```

---

## 6. Create your `.env`

```bash
sudo -u quizbot cp /opt/quizbot/.env.example /opt/quizbot/.env
sudo -u quizbot nano /opt/quizbot/.env
```

Fill in **all the required values** from step 0, save (`Ctrl+O`, `Enter`,
`Ctrl+X`), then lock the file down:

```bash
chmod 600 /opt/quizbot/.env
chown quizbot:quizbot /opt/quizbot/.env
```

---

## 7. Install the systemd service

```bash
cp /opt/quizbot/deploy/quizbot.service /etc/systemd/system/quizbot.service
systemctl daemon-reload
systemctl enable --now quizbot
```

That's it — both bots are now running and will:

- ✅ Auto-start on every reboot
- ✅ Auto-restart within 5 seconds if either bot crashes
- ✅ Log everything to `journald`

---

## 8. Verify it's working

**Service status:**

```bash
systemctl status quizbot
```

You should see `active (running)`.

**Live logs (Ctrl+C to exit):**

```bash
journalctl -u quizbot -f
```

You should see lines like:

```
[main]      pyrogram.session.session - INFO - Session started
[scheduler] ✓ Primary database connected
[scheduler] ✓ Database initialization complete
[web]       Health server listening on 0.0.0.0:10000
```

**Open Telegram → message your bot → it should reply.** 🎉

---

## 9. Day-to-day commands

| Action | Command |
| --- | --- |
| Show status | `systemctl status quizbot` |
| Live logs | `journalctl -u quizbot -f` |
| Last 200 log lines | `journalctl -u quizbot -n 200 --no-pager` |
| Restart bots | `systemctl restart quizbot` |
| Stop bots | `systemctl stop quizbot` |
| Start bots | `systemctl start quizbot` |
| Disable auto-start | `systemctl disable quizbot` |

---

## 10. Updating the bot (after pushing new code)

```bash
cd /opt/quizbot
sudo -u quizbot git pull
sudo -u quizbot /opt/quizbot/.venv/bin/pip install -r requirements.txt
systemctl restart quizbot
```

---

## 11. Optional — open the health-check port

`web.py` exposes a tiny HTTP page at port `10000` (override with `PORT`
in `.env`). It's used internally to keep things alive on Render and
isn't required for the bots to work — but if you want to hit it from a
browser to verify, open the port:

```bash
ufw allow 10000/tcp
```

Then visit `http://YOUR_VPS_IP:10000/` — you'll see:

```
QuizBot alive — main=up, scheduler=up
```

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Failed to start quizbot.service` | `journalctl -u quizbot -n 50` — usually a typo in `.env` or wrong `WorkingDirectory` in the unit file |
| `pyrogram` errors about session | Make sure `API_ID` is a number and `API_HASH` is a 32-char hex string |
| `pymongo.errors.ConfigurationError` | Your `MONGO_URI` is wrong — copy it again from Atlas, URL-encode any `@` / `:` / `/` in the password |
| Bot starts but doesn't respond | Check `OWNER_ID` is your real Telegram ID; check `FORCE_SUB`/`LOG_GROUP` aren't blocking |
| Wants to run on a different path/user | Edit `User=`, `WorkingDirectory=`, `EnvironmentFile=` and `ExecStart=` in `/etc/systemd/system/quizbot.service`, then `systemctl daemon-reload && systemctl restart quizbot` |

---

## Uninstall

```bash
systemctl disable --now quizbot
rm /etc/systemd/system/quizbot.service
systemctl daemon-reload
rm -rf /opt/quizbot
userdel -r quizbot
```

---

**Done!** Your bots are running 24/7 with auto-restart, isolated user,
locked-down `.env`, and one-command updates. 🛡️
