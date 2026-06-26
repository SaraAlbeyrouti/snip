# Snip

> **Live demo:** [snip-sara.vercel.app](https://snip-sara.vercel.app) · **Backend:** [snip-sara.fly.dev](https://snip-sara.fly.dev)

A full-stack URL shortener built to demonstrate production-grade patterns: async FastAPI with Redis cache-aside, PostgreSQL with Alembic migrations, a typed React + TypeScript frontend, multi-stage Docker, and a CI pipeline that runs lint, format check, type check, and tests against real service containers.

**Backend stack:** Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL · Redis · Alembic · Docker · GitHub Actions · pytest · mypy · ruff · black

**Frontend stack:** TypeScript · React 19 · Vite · Tailwind CSS

**Hosting:** Fly.io (backend) · Neon (managed Postgres) · Upstash (managed Redis) · Vercel (frontend)

## What's interesting in the code

### Backend

- **Cache-aside redirect path.** `GET /{short_code}` checks Redis first; on miss it queries Postgres and back-fills the cache with a 1-hour TTL. The choice of TTL over manual invalidation is documented in [`app/cache/redis_client.py`](app/cache/redis_client.py); the flow lives in [`app/routers/redirect.py`](app/routers/redirect.py).
- **Async all the way down.** FastAPI async handlers, SQLAlchemy 2.0 async sessions with `asyncpg`, and `redis.asyncio`. No blocking I/O on the request path. Redis is opened once on startup and closed on shutdown via FastAPI's `lifespan`.
- **Multi-stage Dockerfile.** A builder stage compiles dependencies; a slim runtime stage ships only the venv and app source, running as a non-root user. See [`Dockerfile`](Dockerfile).
- **CI mirrors prod.** GitHub Actions spins up the same Postgres 16 and Redis 7 containers as `docker-compose.yml`, then runs `ruff`, `black --check`, `mypy`, and `pytest` on every push and PR. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **Collision-safe short codes.** `secrets.token_urlsafe(7)` for cryptographically random codes, with a retry loop on `IntegrityError` rather than a race-prone pre-check.
- **Route ordering as a correctness concern.** `/health` and `/api/*` are registered before the catch-all `/{short_code}` so the redirect router doesn't swallow them. Documented inline in [`app/main.py`](app/main.py).

### Frontend

- **Discriminated-union UI state.** Instead of multiple `isLoading` / `hasError` / `hasResult` booleans, the UI state is a single discriminated union: `{ kind: 'idle' | 'loading' | 'success' | 'error', ... }`. TypeScript enforces that `state.result` only exists when `state.kind === 'success'`, so invalid combinations like "loading AND showing a result" are unrepresentable at compile time. See [`web/src/App.tsx`](web/src/App.tsx).
- **Typed API client.** Request and response shapes mirror the backend's Pydantic schemas one-to-one in [`web/src/types/api.ts`](web/src/types/api.ts). The fetch wrapper in [`web/src/api/snip.ts`](web/src/api/snip.ts) normalizes network failures, HTTP errors, and Pydantic validation errors into a single `SnipAPIError` class so components only handle one error type.
- **Client-side URL validation.** The form uses the browser's built-in `URL` constructor to validate before submitting — catches obvious garbage without a round-trip to the server, while still treating the server as the source of truth.
- **Production API URL via env.** `VITE_API_BASE_URL` baked at build time points the frontend at `snip-sara.fly.dev` in production and `localhost:8000` in dev — no hard-coded URLs in component code.

## Architecture

```
                    ┌──────────────────────┐
                    │   React + TS SPA     │
                    │   (Vercel)           │
                    └──────────┬───────────┘
                               │ HTTPS / JSON
                               ▼
┌──────────────────────────────────────────────────────┐
│            FastAPI backend (Fly.io)                  │
│   Routers: /health · /api/urls · /{short_code}       │
└──────┬─────────────────────┬─────────────────────────┘
       │ SQL (async)         │ GET/SET (TTL = 1h)
       ▼                     ▼
┌────────────────┐   ┌────────────────┐
│   PostgreSQL   │   │     Redis      │
│    (Neon)      │   │   (Upstash)    │
└────────────────┘   └────────────────┘
```

## Quick try

Hit the live API directly:

```bash
curl -X POST https://snip-sara.fly.dev/api/urls \
     -H "Content-Type: application/json" \
     -d '{"long_url": "https://example.com"}'
# → {"short_code": "Xq3-aBc", "short_url": "https://snip-sara.fly.dev/Xq3-aBc", ...}

curl -I https://snip-sara.fly.dev/Xq3-aBc
# → HTTP/1.1 301 Moved Permanently
# → location: https://example.com
```

Or run it locally (full setup below):

```bash
docker compose up -d              # postgres + redis
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload     # backend on :8000

cd web && npm install && npm run dev   # frontend on :5173
```

## Endpoints

| Method | Path                | Purpose                          |
| ------ | ------------------- | -------------------------------- |
| POST   | `/api/urls`         | Create a short URL               |
| GET    | `/{short_code}`     | Redirect to the long URL (301)   |
| GET    | `/health`           | Liveness probe                   |
| GET    | `/docs`             | Swagger UI                       |

## Not yet

- Authentication and per-user URL ownership
- Rate limiting
- Custom short codes / vanity URLs
- Analytics dashboard (click_count is already stored — UI is the next iteration)
- Background-task click ingestion (currently sync inside the redirect handler)

---

## Full setup

### Prerequisites

- **Python 3.11+** — `python --version`
- **Node.js 20+** — `node --version`
- **Docker Desktop** — running, for local Postgres + Redis
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

**3. Install backend dependencies**

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

**4. Set up your environment file**

Windows: `copy .env.example .env`
macOS / Linux: `cp .env.example .env`

Defaults are fine for local dev.

**5. Create the database schema**

```bash
alembic upgrade head
```

**6. Run the backend**

```bash
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> for the Swagger UI.

**7. Install and run the frontend (in a separate terminal)**

```bash
cd web
npm install
cp .env.example .env.local   # or `copy` on Windows
npm run dev
```

Open <http://localhost:5173> for the Snip UI.

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

# Run backend
uvicorn app.main:app --reload

# Run frontend (from web/)
npm run dev

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
├── app/                         FastAPI backend
│   ├── main.py                  app entrypoint + lifespan + routing
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
├── web/                         React + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx              UI state machine (discriminated union)
│   │   ├── main.tsx             React entrypoint
│   │   ├── index.css            Tailwind import
│   │   ├── api/snip.ts          Typed fetch wrapper + SnipAPIError
│   │   ├── types/api.ts         Request/response types
│   │   └── components/
│   │       ├── ShortenForm.tsx  Input + client-side URL validation
│   │       ├── ResultCard.tsx   Short URL display + copy-to-clipboard
│   │       └── ErrorBanner.tsx  Inline error display
│   └── vite.config.ts           Vite + Tailwind plugin
├── tests/unit/                  Pytest unit tests
├── .github/workflows/ci.yml     Lint, format check, type check, tests
├── docker-compose.yml           Postgres + Redis for local dev
├── Dockerfile                   Multi-stage production image
├── fly.toml                     Fly.io deployment config
├── alembic.ini
├── pyproject.toml
└── .env.example
```
