"""
AGNITE backend configuration via environment variables.

Uses pydantic-settings so values can come from .env, system environment,
or constructor arguments during testing.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, loaded once at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────────────
    app_env: str = "development"
    app_version: str = "0.1.0"

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = "sqlite:///./agnite.db"

    # ── Frontend ──────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:5173"

    # ── NASA FIRMS ────────────────────────────────────────────────────
    nasa_firms_map_key: str = ""
    nasa_cache_ttl_seconds: int = 600

    # ── OpenStreetMap / Overpass ──────────────────────────────────────
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    osm_cache_ttl_seconds: int = 21600  # 6 hours
    osm_timeout_seconds: int = 15
    osm_max_response_bytes: int = 5 * 1024 * 1024  # 5 MB
    osm_user_agent: str = "AGNITE-Thermal-Intelligence/0.1.0 (SIH26162)"
    enable_osm_context: bool = True

    # ── ML / Models ───────────────────────────────────────────────────
    enable_ml_classifier: bool = False
    enable_recurrence_model: bool = False

    # ── LLM / AGNITE AI ──────────────────────────────────────────────
    enable_llm: bool = False
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # ── Background Jobs ──────────────────────────────────────────────
    enable_background_jobs: bool = False
    firms_sync_interval_seconds: int = 600
    watch_scan_interval_seconds: int = 300

    # ── Redis ─────────────────────────────────────────────────────────
    redis_url: str = ""

    @property
    def nasa_configured(self) -> bool:
        """Phase 1 uses public CSVs, so NASA is always configured."""
        return True


def get_settings() -> Settings:
    """Factory used by FastAPI Depends(); easily overridable in tests."""
    return Settings()
