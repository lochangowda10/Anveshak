"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_name: str = "ANVESHAK"
    app_version: str = "1.0.0"
    database_url: str = "postgresql+asyncpg://anveshak:anveshak@localhost:5432/anveshak"
    secret_key: str = "change-me-to-a-random-string"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    trongrid_api_key: str = ""
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured CORS origins without empty entries."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()


settings = get_settings()
