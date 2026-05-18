# Snip

A URL shortener built to demonstrate production-grade backend patterns: async FastAPI, Redis cache-aside, Postgres with Alembic migrations, a multi-stage Docker build, and a CI pipeline that runs lint, format check, type check, and tests against real service containers.

**Stack:** Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Redis · Alembic · Docker · GitHub Actions · pytest · mypy · ruff · black

## What's interesting in the code

- **Cache-aside redirect path.** `GET /{short_code}` checks Redis first; on miss it queries Postgres and back-fills the cache with a 1-hour TTL. The choice of TTL over manual invalidation is documented in [`app/cache/redis_client.py`](app/cache/redis_client.py); the flow lives in [`app/routers/redirect.py`](app/routers/redirect.py).
- **Async all the way down.** FastAPI async handlers, SQLAlchemy 2.0 async sessions with `asyncpg`, and `redis.asyncio`. No blocking I/O on the request path. Redis is opened once on startup and closed on shutdown via FastAPI's `lifespan`.
- **Multi-stage Dockerfile.** A builder stage compiles dependencies; a slim runtime stage ships only the venv and app source, running as a non-root user. See [`Dockerfile`](Dockerfile).
- **CI mirrors prod.** GitHub Actions spins up the same Postgres 16 and Redis 7 containers as `docker-compose.yml`, then runs `ruff`, `black --check`, `mypy`, and `pytest` on every push and PR. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **Collision-safe short codes.** `secrets.token_urlsafe(7)` for cryptographically random codes, with a retry loop on `IntegrityError` rather than a race-prone pre-check.
- **Route ordering as a correctness concern.** `/health` and `/api/*` are registered before the catch-all `/{short_code}` so the redirect router doesn't swallow them. Documented inline in [`app/main.py`](app/main.py).

## Architecture

```
            ┌──────────────┐
            │    Client    │
            └──────┬───────┘
                   │ GET /{short_code}
                   ▼
            ┌──────────────┐    hit    ┌──────────────┐
            │   FastAPI    │──────────▶│    Redis     │
            │   (async)    │◀──────────│  (1h TTL)    │
            └──────┬───────┘           └──────────────┘
                   │ miss
                   ▼
            ┌──────────────┐
            │  PostgreSQL  │
            │   (asyncpg)  │
            └──────────────┘
```

## Quick try

```bash
docker compose up -d                                  # postgres + redis
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Create a short URL
curl -X POST http://localhost:8000/api/urls \
     -H "Content-Type: application/json" \
     -d '{"long_url": "https://example.com"}'
# → {"short_code": "Xq3-aBc", "short_url": "http://localhost:8000/Xq3-aBc", ...}

# Follow it (301 redirect)
curl -I http://localhost:8000/Xq3-aBc
# → HTTP/1.1 301 Moved Permanently
# → location: https://example.com
```

## Endpoints

| Method | Path                | Purpose                          |
| ------ | ------------------- | -------------------------------- |
| POST   | `/api/urls`         | Create a short URL               |
| GET    | `/{short_code}`     | Redirect to the long URL (301)   |
| GET    | `/health`           | Liveness probe                   |
| GET    | `/docs`             | Swagger UI                       |

## Not yet in v0.1

- TypeScript frontend (CORS is wired up; UI is next)
- Authentication and per-user URL ownership
- Rate limiting
- Custom short codes / collision-avoiding namespaces
- Analytics dashboard (click_count is already stored)

---

## Full setup

### Prerequisites

- **Python 3.11+** — `python --version`
- **Docker Desktop** — running, for the local Postgres + Redis containers
- **Git**

### First-time setup

Open a terminal in this folder.

**1. Start Postgres and Redis**

```bash
docker compose up -d
docker compose ps   # should show snip-postgres and snip-redis as Up
```

**2. Create a Python virtual environment**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

**3. Install dependencies**

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

Editable mode (`-e`) means code changes are picked up without reinstalling.

**4. Set up your environment file**

Windows: `copy .env.example .env`
macOS / Linux: `cp .env.example .env`

Defaults are fine for local dev.

**5. Create the database schema**

```bash
alembic upgrade head
```

This applies the existing migration (under `app/db/migrations/versions/`) to your running Postgres and creates the `urls` table.

**6. Run the server**

```bash
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> for the Swagger UI.

### Run the tests

```bash
pytest
```

You should see 4 tests passing.

## Day-to-day commands

```bash
# Activate venv (Windows)
.venv\Scripts\Activate.ps1
# Activate venv (macOS/Linux)
source .venv/bin/activate

# Start services (if not running)
docker compose up -d

# Run server
uvicorn app.main:app --reload

# Run tests
pytest

# Stop services
docker compose down

# Wipe the database (start fresh)
docker compose down -v
```

## Project layout

```
snip/
├── app/
│   ├── main.py                  FastAPI app entrypoint + lifespan + routing
│   ├── config.py                Settings loaded from .env via pydantic-settings
│   ├── cache/
│   │   └── redis_client.py      Cache-aside helpers (get/set with TTL)
│   ├── db/
│   │   ├── base.py              SQLAlchemy DeclarativeBase
│   │   ├── session.py           Async engine + session factory
│   │   ├── models.py            URL ORM model
│   │   └── migrations/          Alembic migrations
│   ├── schemas/url.py           Pydantic request/response shapes
│   ├── services/shortener.py    Short-code generation (pure function)
│   └── routers/
│       ├── urls.py              POST /api/urls
│       └── redirect.py          GET /{short_code}  (cache-aside + click count)
├── tests/unit/                  Pytest unit tests
├── .github/workflows/ci.yml     Lint, format, type check, tests
├── docker-compose.yml           Postgres + Redis for local dev
├── Dockerfile                   Multi-stage production image
├── alembic.ini
├── pyproject.toml
└── .env.example
```
