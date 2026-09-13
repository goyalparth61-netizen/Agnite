"""
Feature schemas for AGNITE Phase 2.

Defines:
- BaseHotspotFeatures: Statistical, temporal, spatial, and contextual features extracted from history.
- PersistenceResult: Persistence metrics calculated by persistence_service.
- HotspotFeatures: Final central feature vector consumed by all downstream classifiers, risk engines, and explainability.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class BaseHotspotFeatures(BaseModel):
    """Features derived from hotspot spatial and historical observations."""

    # FRP Metrics (MW)
    current_frp: float = Field(..., ge=0, description="FRP of latest pass at site (MW)")
    maximum_frp: float = Field(..., ge=0, description="Highest FRP observed at site")
    minimum_frp: float = Field(..., ge=0, description="Lowest FRP observed at site")
    mean_frp: float = Field(..., ge=0, description="Mean FRP across observations")
    median_frp: float = Field(..., ge=0, description="Median FRP across observations")
    frp_std: float = Field(..., ge=0, description="Standard deviation of FRP")

    # Baseline & Dynamics
    baseline_frp: Optional[float] = Field(None, ge=0, description="Median FRP of passes older than 24h")
    frp_change: Optional[float] = Field(None, description="Absolute difference current_frp - baseline_frp")
    frp_change_percent: Optional[float] = Field(None, description="Percentage change relative to baseline")
    log_baseline_ratio: float = Field(0.0, description="log((current_frp + 1) / (baseline_frp + 1))")

    # Temporal Metrics
    observation_count: int = Field(..., ge=1, description="Total observations in nearby radius")
    distinct_passes_count: int = Field(..., ge=1, description="Number of distinct overpass timestamps")
    unique_days: int = Field(..., ge=1, description="Number of distinct calendar dates (UTC)")
    history_duration_days: float = Field(..., ge=0, description="Span from earliest to latest observation (days)")
    span_hours: float = Field(..., ge=0, description="Span from earliest to latest observation (hours)")
    detection_frequency: float = Field(..., ge=0, description="Detections per calendar day over span")
    days_since_previous: Optional[float] = Field(None, ge=0, description="Days between latest and prior detection")
    average_detection_interval_hours: Optional[float] = Field(None, ge=0, description="Mean interval between consecutive passes")

    # Spatial & Cluster Metrics
    thermal_variability: float = Field(..., ge=0, description="Coefficient of variation (std/mean) or 0")
    spatial_spread_km: float = Field(..., ge=0, description="Max distance between any observation and site center (km)")
    cluster_size: int = Field(..., ge=1, description="Count of observations in current cluster")

    # Contextual inputs (supplied or future automated)
    industrial_distance_km: Optional[float] = Field(None, ge=0)
    land_cover: Literal["forest", "urban", "industrial", "other", "unknown"] = "unknown"
    wind_kph: Optional[float] = Field(None, ge=0, le=500)

    # Provenance counts
    firms_count: int = 0
    manual_count: int = 0
    imported_count: int = 0
    demo_count: int = 0

    model_config = {
        "populate_by_name": True,
    }


class PersistenceResult(BaseModel):
    """Persistence score and status computed by persistence_service."""

    score: float = Field(..., ge=0, le=100, description="Persistence index from 0 to 100")
    status: Literal[
        "INSUFFICIENT_HISTORY",
        "LOW_PERSISTENCE",
        "MODERATE_PERSISTENCE",
        "HIGH_PERSISTENCE",
    ] = "INSUFFICIENT_HISTORY"
    coverage_ratio: float = Field(..., ge=0, le=1, description="Unique detection days / calendar span days")
    stability_factor: float = Field(..., ge=0, le=1, description="Inverse variability factor (1 / (1 + CV))")
    details: str = ""

    model_config = {
        "populate_by_name": True,
    }


class HotspotFeatures(BaseHotspotFeatures):
    """
    Final consolidated feature vector.

    Inherits all BaseHotspotFeatures and incorporates PersistenceResult metrics.
    All intelligence modules (classification, risk, recurrence, explainability)
    consume this exact schema.
    """

    persistence_score: float = Field(..., ge=0, le=100, description="Persistence score (0-100)")
    persistence_status: Literal[
        "INSUFFICIENT_HISTORY",
        "LOW_PERSISTENCE",
        "MODERATE_PERSISTENCE",
        "HIGH_PERSISTENCE",
    ] = "INSUFFICIENT_HISTORY"
    persistence_details: str = ""

    # Recurrence signal
    recurrence_signal: Literal["LOW", "MODERATE", "HIGH", "INSUFFICIENT_HISTORY"] = "INSUFFICIENT_HISTORY"

    # Spatial / OpenStreetMap context features
    industrial_feature_count: int = 0
    industrial_within_1km: bool = False
    industrial_within_5km: bool = False
    industrial_within_10km: bool = False
    count_within_1km: int = 0
    count_within_5km: int = 0
    count_within_10km: int = 0
    nearest_industrial_name: Optional[str] = None
    nearest_industrial_type: Optional[str] = None
    power_infrastructure_nearby: bool = False
    mapped_flare_nearby: bool = False
    mapped_chimney_nearby: bool = False
    context_confidence: float = Field(0.0, ge=0, le=100)
    context_source: str = "unknown"
    context_provenance: dict[str, str] = Field(default_factory=dict)

    # Future-ready placeholders for environmental/weather context
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None

    model_config = {
        "populate_by_name": True,
    }
