"""
Health check routes.

GET /api/health      — compatibility endpoint (matches Node server)
GET /api/v1/health   — versioned endpoint with extended status
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.config import Settings
from app.db.session import check_db_connection

router = APIRouter()


@router.get("/api/health")
async def health_compat():
    """
    Compatibility health endpoint matching the Node server's response.

    The frontend status indicator checks this on startup.
    """
    return {
        "status": "ok",
        "service": "agnite",
        "firms": "public-nasa-downloads",
    }


@router.get("/api/v1/health")
async def health_v1(request: Request):
    """
    Extended health endpoint reporting subsystem availability.

    Never exposes secrets or credentials.
    """
    settings: Settings = request.app.state.settings
    db_active = check_db_connection()
    return {
        "status": "ok",
        "version": settings.app_version,
        "database": db_active,
        "nasa_configured": settings.nasa_configured,
        "ml_classifier_loaded": settings.enable_ml_classifier,
        "recurrence_model_loaded": settings.enable_recurrence_model,
        "llm_enabled": settings.enable_llm,
        "background_jobs_enabled": settings.enable_background_jobs,
    }
