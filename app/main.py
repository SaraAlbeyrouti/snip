from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache.redis_client import close_redis, init_redis
from app.routers import redirect, urls


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """

    We open the Redis connection on startup and close it on shutdown.
    Postgres uses lazy per-request sessions, so it doesn't need lifespan setup.
    """
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="Snip",
    description="Production URL shortener with analytics",
    version="0.1.0",
    lifespan=lifespan,
)


# CORS let the React frontend (which runs on a different origin during
# development, e.g. http://localhost:5173) make requests to this backend.
# In production, replace `allow_origins=["*"]` with the explicit Vercel URL
# for your frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# IMPORTANT: register /health and /api/* routers BEFORE the redirect router.
# The redirect router owns /{short_code} which would otherwise capture /health
# as short_code="health". FastAPI/Starlette matches routes in registration order,
# so more-specific routes must come first.
@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


app.include_router(urls.router, prefix="/api/urls", tags=["urls"])

# Redirect router has no prefix, it owns the root path /{short_code}.
# Registered LAST so the more specific routes above match first.
app.include_router(redirect.router, tags=["redirect"])
