from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env file.

    Each field has a sensible default for local dev. In production, these are
    overridden by environment variables set in the deploy environment.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection string (async driver).
    database_url: str = "postgresql+asyncpg://snip:snip_dev_password@localhost:5432/snip"

    # Redis connection string. The /0 at the end is the database index (Redis
    # has 16 numbered databases by default; we use 0).
    redis_url: str = "redis://localhost:6379/0"

    # Public-facing base URL of this app. Used to build the `short_url` field
    # in API responses ("http://localhost:8000/abc123").
    app_base_url: str = "http://localhost:8000"

    environment: str = "development"


settings = Settings()
