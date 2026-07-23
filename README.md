# English Tutor Bot

Personal Telegram AI English tutor: daily voice conversation practice,
adaptive lessons, interview coaching, and a RU/EN/ZH/UZ translator — built
around the Claude API.

Full architecture, tech-stack decisions and the module-by-module roadmap
live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Read that first.

## Status

Phase 0 (foundations) is in progress. Not yet functional as a bot.

## Local setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
copy .env.example .env   # then fill in real values
```

Fill in `.env`:
- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `ADMIN_TELEGRAM_ID` — your own Telegram numeric user id (the bot ignores
  everyone else — every reply costs API money)
- `ANTHROPIC_API_KEY` — from the Anthropic console
- `GROQ_API_KEY` — from console.groq.com (free tier, used for STT)
- `DATABASE_URL` / `REDIS_URL` — defaults match `docker/docker-compose.yml`

## Running with Docker

```powershell
docker compose -f docker/docker-compose.yml up --build
```

## Running locally without Docker

Requires a local PostgreSQL and Redis matching `.env`.

```powershell
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m src.bot.main
```

## Tests / lint

```powershell
.\.venv\Scripts\pytest
.\.venv\Scripts\ruff check src tests
.\.venv\Scripts\mypy src
```
