"""
Central feature engineering service for AGNITE.

Extracts BaseHotspotFeatures from spatial and temporal history, invokes
persistence_service, and compiles the final consolidated HotspotFeatures vector.
Ensures all intelligence components consume identical feature definitions.
"""

from __future__ import annotations

from typing import List, Optional

from app.core.constants import (
    RECURRENCE_SIGNAL_HIGH,
    RECURRENCE_SIGNAL_INSUFFICIENT,
    RECURRENCE_SIGNAL_LOW,
    RECURRENCE_SIGNAL_MODERATE,
)
from app.schemas.analysis import AnalysisContext
from app.schemas.features import (
    BaseHotspotFeatures,
    HotspotFeatures,
    PersistenceResult,
)
from app.schemas.observation import Observation
from app.services.history_service import HotspotHistory
from app.services.persistence_service import calculate_persistence
from app.utils.geo import haversine_km


def extract_base_features(
    history: HotspotHistory,
    nearby_observations: List[Observation],
    selected_observation: Observation,
    context: Optional[AnalysisContext] = None,
) -> BaseHotspotFeatures:
    """Extract model-ready base features from history, observations, and context."""
    center_lat = selected_observation.latitude
    center_lon = selected_observation.longitude

    # Spatial spread: maximum distance from center to any nearby observation
    distances = [
        haversine_km(center_lat, center_lon, obs.latitude, obs.longitude)
        for obs in nearby_observations
    ]
    spatial_spread = max(distances) if distances else 0.0

    # Coefficient of variation for thermal variability
    thermal_var = (
        history.frp_std / history.mean_frp if history.mean_frp > 0 else 0.0
    )

    # Provenance counts
    firms_count = sum(1 for o in nearby_observations if o.source == "firms")
    manual_count = sum(1 for o in nearby_observations if o.source == "manual")
    imported_count = sum(1 for o in nearby_observations if o.source == "imported")
    demo_count = sum(1 for o in nearby_observations if o.source == "demo")

    ctx = context or AnalysisContext()

    return BaseHotspotFeatures(
        current_frp=history.current_frp,
        maximum_frp=history.maximum_frp,
        minimum_frp=history.minimum_frp,
        mean_frp=history.mean_frp,
        median_frp=history.median_frp,
        frp_std=history.frp_std,
        baseline_frp=history.baseline_frp,
        frp_change=history.frp_change,
        frp_change_percent=history.frp_change_percentage,
        log_baseline_ratio=history.log_baseline_ratio,
        observation_count=history.observation_count,
        distinct_passes_count=history.distinct_passes_count,
        unique_days=history.unique_days_count,
        history_duration_days=history.historical_duration_days,
        span_hours=history.span_hours,
        detection_frequency=history.detection_frequency,
        days_since_previous=history.days_since_previous,
        average_detection_interval_hours=history.average_detection_interval_hours,
        thermal_variability=round(thermal_var, 3),
        spatial_spread_km=round(spatial_spread, 3),
        cluster_size=len(nearby_observations),
        industrial_distance_km=ctx.industrial_distance_km,
        land_cover=ctx.land_cover,
        wind_kph=ctx.wind_kph,
        firms_count=firms_count,
        manual_count=manual_count,
        imported_count=imported_count,
        demo_count=demo_count,
    )


def derive_recurrence_signal(
    base: BaseHotspotFeatures, persistence: PersistenceResult
) -> str:
    """Calculate recurrence signal tier without fabricating a future date."""
    if base.distinct_passes_count < 2 or base.span_hours < 12.0:
        return RECURRENCE_SIGNAL_INSUFFICIENT
    if persistence.score >= 65.0 or base.unique_days >= 4:
        return RECURRENCE_SIGNAL_HIGH
    if persistence.score >= 35.0 or base.unique_days >= 2:
        return RECURRENCE_SIGNAL_MODERATE
    return RECURRENCE_SIGNAL_LOW


def build_hotspot_features(
    history: HotspotHistory,
    nearby_observations: List[Observation],
    selected_observation: Observation,
    context: Optional[AnalysisContext] = None,
) -> HotspotFeatures:
    """
    Central pipeline for feature generation.

    1. Computes BaseHotspotFeatures
    2. Runs persistence_service to get PersistenceResult
    3. Derives recurrence signal
    4. Emits final HotspotFeatures
    """
    base = extract_base_features(
        history=history,
        nearby_observations=nearby_observations,
        selected_observation=selected_observation,
        context=context,
    )
    persistence = calculate_persistence(base)
    recurrence_sig = derive_recurrence_signal(base, persistence)

    # Combine into full HotspotFeatures
    base_dict = base.model_dump()
    return HotspotFeatures(
        **base_dict,
        persistence_score=persistence.score,
        persistence_status=persistence.status,
        persistence_details=persistence.details,
        recurrence_signal=recurrence_sig,
    )
