"""
FastAPI dependencies for dependency injection.

Services are created once at startup (in ``main.py`` lifespan) and
stored on ``app.state``.  Dependencies retrieve them here so that
route handlers receive ready-to-use service instances.
"""

from __future__ import annotations

from fastapi import Request

from app.services.firms_service import FirmsService


def get_firms_service(request: Request) -> FirmsService:
    """Retrieve the FIRMS service singleton from app state."""
    return request.app.state.firms_service
