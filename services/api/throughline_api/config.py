"""Runtime settings (12-factor via env, prefix ``THROUGHLINE_``)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="THROUGHLINE_", env_file=".env", extra="ignore")

    # PostgreSQL is the single source of truth in prod; SQLite is the zero-setup default
    # for local dev + unit tests (the event-sourced core is storage-agnostic).
    database_url: str = "sqlite+pysqlite:///./throughline.db"
    app_name: str = "Throughline API"
    version: str = "0.1.0"


settings = Settings()
