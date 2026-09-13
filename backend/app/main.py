"""
AGNITE FastAPI application entry point.

Creates the app, configures CORS, registers exception handlers,
initializes services at startup (FIRMS provider, ML model loader),
and registers all compatibility and versioned API route modules.

Start with:
    uvicorn app.main:app --reload --port 8787
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, firms, health, timeline
from app.core.config import Settings, get_settings
from app.core.exceptions import FirmsError, ValidationError
from app.core.logging import setup_logging
from app.ml.model_loader import load_classification_provider
from app.services.firms_service import FirmsService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Creates shared resources (HTTP client, services, ML classification provider)
    at startup and tears them down cleanly at shutdown.
    """
    settings = get_settings()
    app.state.settings = settings

    setup_logging("DEBUG" if settings.app_env == "development" else "INFO")

    logger.info(
        "AGNITE backend starting — env=%s version=%s",
        settings.app_env,
        settings.app_version,
    )

    # ── Shared HTTP client ────────────────────────────────────────
    http_client = httpx.AsyncClient(
        follow_redirects=False,
        timeout=30.0,
    )

    # ── FIRMS service ─────────────────────────────────────────────
    app.state.firms_service = FirmsService(
        http_client=http_client,
        cache_ttl_seconds=settings.nasa_cache_ttl_seconds,
    )

    # ── Classification provider initialization ────────────────────
    provider = load_classification_provider()
    app.state.classification_provider = provider
    logger.info(
        "Classification provider ready: %s (version=%s, method=%s)",
        provider.name,
        provider.version,
        provider.method,
    )

    logger.info("AGNITE backend ready on port 8787")
    yield

    # ── Shutdown ──────────────────────────────────────────────────
    await http_client.aclose()
    logger.info("AGNITE backend shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="AGNITE — AI-Powered Thermal Intelligence",
        description="Backend API for satellite thermal detection analysis",
        version=settings.app_version,
        docs_url="/api/docs" if settings.app_env == "development" else None,
        redoc_url="/api/redoc" if settings.app_env == "development" else None,
        openapi_url="/api/openapi.json" if settings.app_env == "development" else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────
    @app.exception_handler(FirmsError)
    async def firms_error_handler(request: Request, exc: FirmsError):
        """Return ``{ "error": "..." }`` matching frontend expectations."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": exc.message},
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "The server could not complete this request."},
        )

    # ── Routes ────────────────────────────────────────────────────
    # Phase 1 health and FIRMS feed routes (compat + v1)
    app.include_router(health.router, tags=["health"])
    app.include_router(firms.router, tags=["firms"])

    # Phase 2 Thermal Intelligence routes
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(timeline.router, prefix="/api/v1")

    return app


# ── Module-level app instance for uvicorn ─────────────────────────────
app = create_app()
