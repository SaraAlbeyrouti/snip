from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class URLCreate(BaseModel):
    """Request body for POST /api/urls."""

    long_url: HttpUrl  # Pydantic validates this is a real http(s) URL.


class URLResponse(BaseModel):
    """Response body for URL-creation and URL-list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime
    click_count: int
