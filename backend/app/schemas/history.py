"""
Pydantic schemas for long-term historical query endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisStatistics, HistoryTimelinePoint
from app.schemas.observation import Observation


class HistoryLocation(BaseModel):
    latitude: float
    longitude: float


class HistoryPeriod(BaseModel):
    from_date: str = Field(..., alias="from", serialization_alias="from")
    to_date: str = Field(..., alias="to", serialization_alias="to")

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class HistoryRecurrence(BaseModel):
    signal: str
    persistence_score: float = Field(..., alias="persistenceScore", serialization_alias="persistenceScore")
    coverage_ratio: float = Field(..., alias="coverageRatio", serialization_alias="coverageRatio")
    stability_factor: float = Field(..., alias="stabilityFactor", serialization_alias="stabilityFactor")
    unique_days: int = Field(..., alias="uniqueDays", serialization_alias="uniqueDays")
    distinct_times: int = Field(..., alias="distinctTimes", serialization_alias="distinctTimes")

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class HistoryQueryResponse(BaseModel):
    """Response model for GET /api/v1/history."""

    location: HistoryLocation
    radius_km: float = Field(..., alias="radiusKm", serialization_alias="radiusKm")
    period: HistoryPeriod
    observation_count: int = Field(..., alias="observationCount", serialization_alias="observationCount")
    observations: List[Observation]
    statistics: AnalysisStatistics
    timeline: List[HistoryTimelinePoint]
    recurrence: HistoryRecurrence
    provenance: Dict[str, int] = Field(
        default_factory=dict,
        description="Counts of observations grouped by source (firms, manual, imported, demo)",
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
