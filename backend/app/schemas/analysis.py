"""
Analysis request and response schemas for Phase 2.

Matches the exact frontend contract defined in backend/docs/phase2-contract.md.
All fields serialize to camelCase aliases matching TypeScript's AnalysisResult.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_SEARCH_RADIUS_KM
from app.schemas.features import PersistenceResult
from app.schemas.observation import Observation
from app.schemas.prediction import ClassScore


class AnalysisContext(BaseModel):
    """Contextual metadata supplied for site analysis."""

    industrial_distance_km: Optional[float] = Field(
        None,
        alias="industrialDistanceKm",
        serialization_alias="industrialDistanceKm",
        ge=0,
    )
    land_cover: Literal["forest", "urban", "industrial", "other", "unknown"] = Field(
        "unknown",
        alias="landCover",
        serialization_alias="landCover",
    )
    wind_kph: Optional[float] = Field(
        None,
        alias="windKph",
        serialization_alias="windKph",
        ge=0,
        le=500,
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class AnalysisRequest(BaseModel):
    """Payload sent to POST /api/v1/analysis/run."""

    selected_observation: Optional[Observation] = Field(
        None,
        alias="selectedObservation",
        serialization_alias="selectedObservation",
        description="Reference observation for site center; if omitted, latest observation is used",
    )
    observations: List[Observation] = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Observations to analyze (FIRMS, manual, imported, or demo)",
    )
    radius_km: float = Field(
        DEFAULT_SEARCH_RADIUS_KM,
        alias="radiusKm",
        serialization_alias="radiusKm",
        gt=0,
        le=100.0,
        description="Search radius in kilometers",
    )
    context: Optional[AnalysisContext] = Field(
        default_factory=AnalysisContext,
        description="Optional environmental and land-use context",
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class ModelInfo(BaseModel):
    """Generic model metadata supporting both heuristic rules and ML models."""

    name: str = "agnite-heuristic-v1"
    version: str = "1.0"
    method: Literal["heuristic", "ml"] = "heuristic"
    training_source: Optional[str] = Field(
        None,
        alias="trainingSource",
        serialization_alias="trainingSource",
    )
    metrics: Optional[Dict[str, float]] = None
    sample_count: Optional[int] = Field(
        None,
        alias="sampleCount",
        serialization_alias="sampleCount",
    )
    synthetic_validation_accuracy: Optional[float] = Field(
        None,
        alias="syntheticValidationAccuracy",
        serialization_alias="syntheticValidationAccuracy",
    )
    limitations: List[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class RiskResult(BaseModel):
    """Risk scoring details."""

    index: int = Field(..., ge=0, le=100, description="Risk index 0-100")
    level: Literal["Low", "Moderate", "High", "Critical"]
    method: str
    factors: Optional[List[str]] = None

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class EvidenceItem(BaseModel):
    """Single item in observation evidence list."""

    label: str
    value: str
    detail: str


class FeatureContribution(BaseModel):
    """Feature contribution bar showing influence on leading class vs runner-up."""

    feature: str
    value: float
    contribution: float
    direction: Literal["supports", "opposes"]


class HistoryTimelinePoint(BaseModel):
    """Time-series point for historical chart."""

    observed_at: str = Field(
        ...,
        alias="observedAt",
        serialization_alias="observedAt",
    )
    frp: float
    baseline: Optional[float] = None

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class AnalysisStatistics(BaseModel):
    """Summary statistics for analyzed site."""

    included: int
    excluded: int
    distinct_times: int = Field(
        ...,
        alias="distinctTimes",
        serialization_alias="distinctTimes",
    )
    span_hours: float = Field(
        ...,
        alias="spanHours",
        serialization_alias="spanHours",
    )
    current_frp: float = Field(
        ...,
        alias="currentFrp",
        serialization_alias="currentFrp",
    )
    baseline_frp: Optional[float] = Field(
        None,
        alias="baselineFrp",
        serialization_alias="baselineFrp",
    )
    change_percent: Optional[float] = Field(
        None,
        alias="changePercent",
        serialization_alias="changePercent",
    )
    persistence: float
    center: Coordinates

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class RiskScenario(BaseModel):
    """What-if risk scenario range based on current conditions — NOT a future prediction."""

    horizon: Literal["24h", "48h", "7d"]
    low: int
    central: int
    high: int
    label: str = "WHAT-IF heuristic index range"
    assumption: str

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class AnalysisResult(BaseModel):
    """Complete backend analysis result matching frontend expectations."""

    model: ModelInfo
    classification: str
    status: Literal["classified", "abstained"]
    model_score: Optional[float] = Field(
        None,
        alias="modelScore",
        serialization_alias="modelScore",
    )
    scores: List[ClassScore] = Field(default_factory=list)
    risk: RiskResult
    summary: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    contributions: List[FeatureContribution] = Field(default_factory=list)
    history: List[HistoryTimelinePoint] = Field(default_factory=list)
    statistics: AnalysisStatistics
    scenarios: List[RiskScenario] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Phase 2 Enhanced Intelligence fields
    method: Optional[str] = "heuristic"
    confidence: Optional[float] = Field(None, ge=0, le=100)
    persistence: Optional[PersistenceResult] = None
    recurrence_signal: Optional[str] = Field(
        None,
        alias="recurrenceSignal",
        serialization_alias="recurrenceSignal",
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
        "protected_namespaces": (),
    }
