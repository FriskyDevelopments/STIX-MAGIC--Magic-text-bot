# STIX MAGIC Text Bot

  A Telegram bot that processes text messages using STIX MAGIC's NLP pipeline.

  ## What it does

  - Receives text messages via Telegram
  - Processes them through `stix_core.py` for AI-powered text transformation
  - Returns enhanced/tagged output to the user

  ## Supported commands

  | Command | Description |
  |---------|-------------|
  | `/start` | Initialize the bot and display welcome message |
  | `/help` | Show available commands |
  | `/process <text>` | Process text through STIX MAGIC pipeline |

  ## Setup

  ```bash
  cp .env.example .env
  # Fill in your credentials
  pip install -r requirements.txt
  python main.py
  ```

  ## Environment variables

  See `.env.example` for all required variables.

  ## Deployment

  **RackNerd VPS (recommended)** — no Oracle capacity wait; KVM + SSH.

  1. Order an Ubuntu VPS at RackNerd; note the **IP** and **root password** (or SSH key).
  2. On the server (as root): `bash scripts/racknerd-bootstrap.sh`
  3. Edit `/etc/pupbot/pupbot.env` — set `TELEGRAM_BOT_TOKEN`, then `systemctl start pupbot`
  4. From your machine or GitHub Actions: set secrets `RACKNERD_HOST`, `RACKNERD_SSH_KEY`, run `scripts/racknerd-deploy.sh`

  GitHub: workflow **Deploy Pupbot (RackNerd)** on push to `main` (disable with repo variable `RACKNERD_DEPLOY_ENABLED=false`).

  Legacy: `Procfile` / Heroku; OCI A1 watchdog is deprecated (see `scripts/oci-a1-watchdog.sh`).

  ## Architecture

  - `main.py` — Bot entry point and Telegram handler registration
  - `stix_core.py` — Core NLP/text processing logic
  - `bot/` — Additional bot command handlers

  ## Related repos

  - [stixmagic-web](https://github.com/FriskyDevelopments/stixmagic-web) — Web platform
  - [stixmagic-bot](https://github.com/FriskyDevelopments/stixmagic-bot) — Sticker bot
  