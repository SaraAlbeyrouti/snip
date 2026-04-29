# Snip -  URL Shortener

Working endpoints:
- `POST /api/urls` — create a short URL
- `GET /{short_code}` — redirect to the long URL
- `GET /health` — liveness check


## Prerequisites

You need these installed before you start:

- **Python 3.11+** — check with `python --version`. If you don't have it, install from [python.org](https://www.python.org/downloads/).
- **Docker Desktop** — for the local Postgres database. Install from [docker.com](https://www.docker.com/products/docker-desktop/). **Make sure it's running** before you continue (icon in your system tray).
- **Git** — you have it.

That's it. No Node.js needed yet.

---

## First-time setup (do this once)

Open a terminal in this folder (`snip/`).

### 1. Start Postgres

```bash
docker compose up -d
```

Verify it's running:

```bash
docker compose ps
```

You should see `snip-postgres` with status `Up`.

### 2. Create a Python virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

This installs FastAPI, SQLAlchemy, Alembic, pytest, ruff, etc. (Editable mode — `-e` — means code changes are picked up without reinstalling.)

### 4. Set up your environment file

**Windows (PowerShell):**
```powershell
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

Defaults are fine for local dev. No edits needed.

### 5. Create the database schema (Alembic migration)

```bash
alembic revision --autogenerate -m "create urls table"
alembic upgrade head
```

The first command generates a migration file under `app/db/migrations/versions/`. The second applies it to the running Postgres. You now have a `urls` table.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs in your browser. You should see a Swagger UI with two endpoints: `POST /api/urls` and `GET /{short_code}`.

---

## Try it out

1. In Swagger UI, expand `POST /api/urls`, click **Try it out**.
2. Paste this body:
   ```json
   { "long_url": "https://example.com" }
   ```
3. Click **Execute**. You'll get back something like:
   ```json
   {
     "id": 1,
     "short_code": "Xq3-aBc",
     "short_url": "http://localhost:8000/Xq3-aBc",
     "long_url": "https://example.com/",
     "created_at": "2026-04-26T...",
     "click_count": 0
   }
   ```
4. Open `http://localhost:8000/Xq3-aBc` in a new tab — you'll be redirected to https://example.com.
5. Re-fetch the URL via `POST /api/urls` with the same code path — `click_count` is now 1.

---

## Run the tests

```bash
pytest
```

You should see 4 tests passing.

---

## Day-to-day commands

```bash
# Activate venv (Windows)
.venv\Scripts\Activate.ps1

# Activate venv (macOS/Linux)
source .venv/bin/activate

# Start postgres (if not running)
docker compose up -d

# Run server
uvicorn app.main:app --reload

# Run tests
pytest

# Stop postgres
docker compose down

# Wipe the database (start fresh)
docker compose down -v
```


## Project layout

```
snip/
├── app/
│   ├── main.py              FastAPI app entrypoint
│   ├── config.py            Settings loaded from .env
│   ├── db/
│   │   ├── base.py          SQLAlchemy DeclarativeBase
│   │   ├── session.py       Async engine + session factory
│   │   ├── models.py        URL ORM model
│   │   └── migrations/      Alembic migrations
│   ├── schemas/url.py       Pydantic request/response shapes
│   ├── services/shortener.py  Pure short-code generation logic
│   └── routers/
│       ├── urls.py          POST /api/urls
│       └── redirect.py      GET /{short_code}
├── tests/unit/test_shortener.py
├── docker-compose.yml       Postgres in Docker
├── alembic.ini
├── pyproject.toml
└── .env.example
```
