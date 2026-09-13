"""
API route for long-term location history intelligence.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.history import HistoryQueryResponse
from app.services.historical_intelligence_service import HistoricalIntelligenceService
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.api.routes.history")

router = APIRouter(tags=["History"])


@router.get(
    "/history",
    response_model=HistoryQueryResponse,
    summary="Get multi-day location history intelligence",
    description=(
        "Queries persistent observation database around target coordinates within radiusKm, "
        "calculating historical passes, baseline FRP, trend, and recurrence metrics."
    ),
)
def get_location_history(
    latitude: float = Query(..., ge=-90, le=90, description="Target latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Target longitude (-180 to 180)"),
    radius_km: float = Query(
        5.0,
        alias="radiusKm",
        ge=0.5,
        le=50.0,
        description="Search radius in kilometres (0.5 to 50.0)",
    ),
    days: int = Query(
        30,
        ge=1,
        le=365,
        description="Days of history to analyze (1 to 365)",
    ),
    db: Session = Depends(get_db),
) -> HistoryQueryResponse:
    """Retrieve long-term historical intelligence for target location."""
    if not is_valid_coordinate(latitude, longitude):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_COORDINATES",
                    "message": f"Coordinates ({latitude}, {longitude}) are out of valid bounds.",
                    "retryable": False,
                }
            },
        )

    return HistoricalIntelligenceService.get_location_history(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        days=days,
    )
