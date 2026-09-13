"""
Timeline schemas for Phase 2.

Exposes chronological series and temporal aggregation for a selected hotspot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_SEARCH_RADIUS_KM
from app.schemas.analysis import AnalysisStatistics
from app.schemas.observation import Observation


class TimelineRequest(BaseModel):
    """Payload for POST /api/v1/timeline."""

    selected_observation: Optional[Observation] = Field(
        None,
        alias="selectedObservation",
        serialization_alias="selectedObservation",
    )
    observations: List[Observation] = Field(..., min_length=1, max_length=5000)
    radius_km: float = Field(
        DEFAULT_SEARCH_RADIUS_KM,
        alias="radiusKm",
        serialization_alias="radiusKm",
        gt=0,
        le=100.0,
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class TimelinePoint(BaseModel):
    """Single aggregated overpass point in the timeline."""

    observed_at: str = Field(
        ...,
        alias="observedAt",
        serialization_alias="observedAt",
    )
    frp: float
    brightness: Optional[float] = None
    sensor: Optional[str] = None
    baseline: Optional[float] = None
    pixel_count: int = Field(1, alias="pixelCount", serialization_alias="pixelCount")

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class TimelineResponse(BaseModel):
    """Aggregated timeline response."""

    timeline: List[TimelinePoint]
    statistics: AnalysisStatistics
    baseline_frp: Optional[float] = Field(
        None,
        alias="baselineFrp",
        serialization_alias="baselineFrp",
    )
    recurrence_metrics: Optional[Dict[str, Any]] = Field(
        None,
        alias="recurrenceMetrics",
        serialization_alias="recurrenceMetrics",
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
