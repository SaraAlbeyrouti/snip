"""GET /{short_code} — follow a short URL to its long URL.

Cache-aside flow on each request:
    1. Look up `short_code` in Redis.
       - On hit: we have the long URL, skip the DB SELECT.
       - On miss: fall through to step 2.
    2. Query Postgres for the URL row.
       - If the row doesn't exist or is inactive: 404.
       - Otherwise: write the long URL into Redis with a TTL for next time.
    3. Increment click_count in Postgres.
    4. Return a 301 redirect to the long URL.

"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import redis_client
from app.db.models import URL
from app.db.session import get_db

router = APIRouter()


@router.get("/{short_code}")
async def follow(
    short_code: str,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Look up `short_code` and 301-redirect to its long URL."""

    # Step 1: try the cache first.
    long_url = await redis_client.get_long_url(short_code)

    if long_url is None:
        # Step 2: cache miss — fetch from Postgres.
        result = await db.execute(
            select(URL).where(URL.short_code == short_code, URL.is_active.is_(True))
        )
        url_row = result.scalar_one_or_none()

        if url_row is None:
            # No row, or row is soft-deleted — return 404.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found",
            )

        long_url = url_row.long_url

        # Populate the cache so the next request for this short_code is fast.
        await redis_client.set_long_url(short_code, long_url)

    # Step 3: bump the click counter. We use the short_code in the WHERE clause
    # because on a cache hit we don't have the URL row's id.
    await db.execute(
        update(URL).where(URL.short_code == short_code).values(click_count=URL.click_count + 1)
    )
    await db.commit()

    # Step 4: redirect.
    return RedirectResponse(
        url=long_url,
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )
