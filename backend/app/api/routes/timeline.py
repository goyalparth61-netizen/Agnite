"""
Timeline API route for AGNITE Phase 2.

Exposes POST /api/v1/timeline for aggregated chronological history and baseline.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.constants import DEFAULT_SEARCH_RADIUS_KM
from app.schemas.analysis import AnalysisStatistics, Coordinates
from app.schemas.timeline import TimelinePoint, TimelineRequest, TimelineResponse
from app.services.history_service import compute_history
from app.services.hotspot_service import get_nearby_observations
from app.services.persistence_service import calculate_persistence
from app.services.feature_service import extract_base_features
from app.utils.dates import iso_to_epoch_ms
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.api.routes.timeline")

router = APIRouter(tags=["Timeline"])


@router.post(
    "/timeline",
    response_model=TimelineResponse,
    summary="Generate chronological hotspot timeline and baseline",
    description="Groups overpasses within search radius, computes pass means and historical baseline.",
)
async def generate_timeline_endpoint(request: TimelineRequest) -> TimelineResponse:
    """Generate chronological history timeline for selected site."""
    try:
        observations = request.observations
        if not observations:
            raise ValueError("Add at least one observation before generating timeline.")

        selected = request.selected_observation
        if selected is None:
            selected = max(observations, key=lambda x: iso_to_epoch_ms(x.observed_at))

        if not is_valid_coordinate(selected.latitude, selected.longitude):
            raise ValueError(
                f"Coordinates ({selected.latitude}, {selected.longitude}) are invalid."
            )

        radius = request.radius_km or DEFAULT_SEARCH_RADIUS_KM

        nearby, _, excluded_count = get_nearby_observations(
            selected_observation=selected,
            observations=observations,
            radius_km=radius,
        )

        if not nearby:
            raise ValueError(
                f"No observations were found within {radius:.1f} km of the site."
            )

        history = compute_history(nearby)
        base = extract_base_features(history, nearby, selected)
        persistence = calculate_persistence(base)

        timeline_points = [
            TimelinePoint(
                observedAt=p.observed_at,
                frp=round(p.mean_frp, 2),
                brightness=round(p.mean_brightness, 1) if p.mean_brightness else None,
                sensor=p.sensor,
                baseline=round(history.baseline_frp, 2) if history.baseline_frp else None,
                pixelCount=p.pixel_count,
            )
            for p in history.passes
        ]

        stats = AnalysisStatistics(
            included=len(nearby),
            excluded=excluded_count,
            distinctTimes=history.distinct_passes_count,
            spanHours=history.span_hours,
            currentFrp=history.current_frp,
            baselineFrp=history.baseline_frp,
            changePercent=history.frp_change_percentage,
            persistence=persistence.coverage_ratio,
            center=Coordinates(
                latitude=selected.latitude,
                longitude=selected.longitude,
            ),
        )

        recurrence_metrics = {
            "uniqueDays": history.unique_days_count,
            "calendarSpanDays": history.calendar_span_days,
            "detectionFrequency": history.detection_frequency,
            "persistenceScore": persistence.score,
            "persistenceStatus": persistence.status,
            "averageIntervalHours": history.average_detection_interval_hours,
        }

        return TimelineResponse(
            timeline=timeline_points,
            statistics=stats,
            baselineFrp=history.baseline_frp,
            recurrenceMetrics=recurrence_metrics,
        )
    except ValueError as val_err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_TIMELINE_REQUEST",
                    "message": str(val_err),
                    "retryable": False,
                }
            },
        )
    except Exception as exc:
        logger.error("Timeline generation error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "TIMELINE_FAILED",
                    "message": "Failed to generate timeline due to an internal error.",
                    "retryable": False,
                }
            },
        )
