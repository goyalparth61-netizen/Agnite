"""
FIRMS feed routes.

GET /api/firms          — compatibility endpoint (matches Node server)
GET /api/v1/firms       — versioned endpoint (same logic)

Both endpoints validate query parameters and delegate to FirmsService.
The response JSON uses camelCase field names to match the strict
frontend validation in useFirmsFeed.ts.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.deps import get_firms_service
from app.core.constants import SENSOR_PATHS, WINDOW_LABELS
from app.core.exceptions import FirmsError
from app.services.firms_service import FirmsService

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Valid parameter values ────────────────────────────────────────────
VALID_SENSORS = set(SENSOR_PATHS.keys())
VALID_HOURS = set(WINDOW_LABELS.keys())


async def _handle_firms_request(
    sensor: str,
    hours: int,
    firms: FirmsService,
) -> JSONResponse:
    """
    Shared handler for both /api/firms and /api/v1/firms.

    Validates parameters, calls the service, and returns a JSON
    response that passes the frontend's strict checks.
    """
    # Validate sensor
    if sensor not in VALID_SENSORS:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Use hours=24, 48, or 168 and sensor=snpp, noaa20, or modis."
            },
        )

    # Validate hours
    if hours not in VALID_HOURS:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Use hours=24, 48, or 168 and sensor=snpp, noaa20, or modis."
            },
        )

    try:
        result = await firms.get(sensor=sensor, hours=hours)
        return JSONResponse(content=result)
    except FirmsError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message},
        )


@router.get("/api/firms")
async def firms_compat(
    sensor: str = Query(default="snpp"),
    hours: int = Query(default=24),
    firms: FirmsService = Depends(get_firms_service),
):
    """
    Compatibility FIRMS endpoint — exact drop-in for the Node server.

    The frontend's useFirmsFeed.ts calls:
        GET /api/firms?sensor=noaa20&hours=24

    and validates the response strictly.
    """
    return await _handle_firms_request(sensor, hours, firms)


@router.get("/api/v1/firms")
async def firms_v1(
    sensor: str = Query(default="snpp"),
    hours: int = Query(default=24),
    firms: FirmsService = Depends(get_firms_service),
):
    """Versioned FIRMS endpoint — same logic as compatibility route."""
    return await _handle_firms_request(sensor, hours, firms)
