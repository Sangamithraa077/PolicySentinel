"""Project settings and configuration loader.

Single source of truth for environment-driven configuration. Values are
read from process environment variables, falling back to a local .env
file (see root .env.example) when present. No business logic lives here —
this module only declares and loads configuration.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "PolicySentinel"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "changeme"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"

    # --- Backend / API ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    # --- PostgreSQL ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "policysentinel"
    POSTGRES_USER: str = "policysentinel"
    POSTGRES_PASSWORD: str = "changeme"
    DATABASE_URL: str = "postgresql://policysentinel:changeme@localhost:5432/policysentinel"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_ECHO: bool = False

    # --- Neo4j ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "changeme"

    # --- JWT Auth ---
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Claude API ---
    ANTHROPIC_API_KEY: str = "changeme"
    CLAUDE_MODEL: str = "claude-sonnet-5"

    # --- File Uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    @property
    def cors_origins(self) -> list[str]:
        """CORS_ALLOWED_ORIGINS as a parsed list, e.g. 'a,b' -> ['a', 'b']."""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached Settings singleton — safe to call repeatedly (e.g. via Depends)."""
    return Settings()
