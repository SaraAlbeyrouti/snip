"""Redis client + cache helpers for short_code -> long_url lookups.

Strategy: cache-aside.
    1. On redirect, check Redis first.
    2. On cache miss, fetch from Postgres and write the result back to Redis.
    3. We never manually invalidate. Instead, every entry has a 1-hour TTL
       (Time To Live), and Redis evicts expired keys automatically.

Why a TTL instead of explicit invalidation? Because for this app, short URLs
are immutable once created. The only way the long URL ever "changes" is if
we add an admin "edit URL" feature later — and even then, a 1-hour staleness
window is acceptable for a portfolio demo.

Lifecycle:
    The Redis client is opened once on app startup (see app/main.py's
    `lifespan` handler) and closed once on shutdown. We hold a single
    module-level client and share it across requests — opening a new
    connection per request would be wasteful.
"""

from typing import Optional

from redis.asyncio import Redis, from_url

from app.config import settings

# Module-level client. Initialized in `init_redis()` (called from app startup),
# torn down in `close_redis()` (called from app shutdown).
# Type is Optional so we can None it out cleanly during shutdown.
_client: Optional[Redis] = None

# Prefix for cache keys, so we can tell Snip's data apart from anything else
# that might share this Redis instance in production.
_CACHE_KEY_PREFIX = "url:"

# How long a cached entry lives, in seconds. 1 hour = 3600 s.
_CACHE_TTL_SECONDS = 60 * 60


async def init_redis() -> None:
    """Open the Redis connection. Called once on app startup."""
    global _client
    # `decode_responses=True` makes get/set return str instead of bytes — much
    # cleaner than calling .decode() everywhere.
    _client = from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close the Redis connection. Called once on app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _key(short_code: str) -> str:
    """Build the Redis key for a given short code."""
    return f"{_CACHE_KEY_PREFIX}{short_code}"


async def get_long_url(short_code: str) -> Optional[str]:
    """Return the cached long URL for a short code, or None on cache miss."""
    if _client is None:
        return None  # Cache not initialized — fall back to DB.
    # redis-py's stubs type .get() as returning Any. We assign to a typed
    # local so mypy knows the function's return type matches its annotation.
    cached: Optional[str] = await _client.get(_key(short_code))
    return cached


async def set_long_url(short_code: str, long_url: str) -> None:
    """Cache the long URL for a short code, with a TTL."""
    if _client is None:
        return  # Cache not initialized — silent no-op, DB still has the data.
    await _client.setex(_key(short_code), _CACHE_TTL_SECONDS, long_url)
