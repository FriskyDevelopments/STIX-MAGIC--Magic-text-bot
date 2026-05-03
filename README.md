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

  Currently deployed via `Procfile` (Heroku-compatible). A Dockerfile is planned — see [issue #1].

  ## Architecture

  - `main.py` — Bot entry point and Telegram handler registration
  - `stix_core.py` — Core NLP/text processing logic
  - `bot/` — Additional bot command handlers

  ## Related repos

  - [stixmagic-web](https://github.com/FriskyDevelopments/stixmagic-web) — Web platform
  - [stixmagic-bot](https://github.com/FriskyDevelopments/stixmagic-bot) — Sticker bot
  