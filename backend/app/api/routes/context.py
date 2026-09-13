"""
Context API route for OpenStreetMap infrastructure queries.

Exposes GET /api/v1/context to retrieve normalized spatial context around target coordinates.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from app.core.constants import (
    DEFAULT_OSM_SEARCH_RADIUS_KM,
    MAX_OSM_SEARCH_RADIUS_KM,
    MIN_OSM_SEARCH_RADIUS_KM,
)
from app.schemas.context import SpatialContext
from app.services.spatial_context_service import get_spatial_context_provider
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.api.routes.context")

router = APIRouter(tags=["Context"])


@router.get(
    "/context",
    response_model=SpatialContext,
    summary="Get OpenStreetMap industrial and thermal infrastructure context",
    description=(
        "Queries OpenStreetMap via Overpass for industrial areas, power plants, works, "
        "chimneys, and flares within radiusKm (default 10 km) of target coordinates."
    ),
)
async def get_spatial_context_endpoint(
    latitude: float = Query(..., ge=-90, le=90, description="Target latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Target longitude (-180 to 180)"),
    radius_km: float = Query(
        DEFAULT_OSM_SEARCH_RADIUS_KM,
        alias="radiusKm",
        ge=MIN_OSM_SEARCH_RADIUS_KM,
        le=MAX_OSM_SEARCH_RADIUS_KM,
        description="Search radius in kilometres (0.5 to 25.0)",
    ),
) -> SpatialContext:
    """Retrieve normalized spatial context for given coordinates."""
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

    provider = get_spatial_context_provider()
    context = await provider.get_context(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
    return context
