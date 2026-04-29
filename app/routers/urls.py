"""POST /api/urls, create a short URL."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import URL
from app.db.session import get_db
from app.schemas.url import URLCreate, URLResponse
from app.services.shortener import generate_short_code

router = APIRouter()

# Try a few times in case of short-code collision (vanishingly rare at this scale).
MAX_COLLISION_RETRIES = 5


def _to_response(url: URL) -> URLResponse:
    """Convert ORM model to API response."""
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        short_url=f"{settings.app_base_url}/{url.short_code}",
        long_url=url.long_url,
        created_at=url.created_at,
        click_count=url.click_count,
    )


@router.post("", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_url(payload: URLCreate, db: AsyncSession = Depends(get_db)) -> URLResponse:
    """Create a short URL pointing at the supplied long URL."""
    long_url = str(payload.long_url)

    for _ in range(MAX_COLLISION_RETRIES):
        url = URL(short_code=generate_short_code(), long_url=long_url)
        db.add(url)
        try:
            await db.commit()
        except IntegrityError:
            # Short-code already taken, roll back and try again.
            await db.rollback()
            continue
        await db.refresh(url)
        return _to_response(url)

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique short code. Try again.",
    )
