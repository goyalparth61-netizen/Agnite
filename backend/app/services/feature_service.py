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


from app.schemas.context import SpatialContext


def extract_base_features(
    history: HotspotHistory,
    nearby_observations: List[Observation],
    selected_observation: Observation,
    context: Optional[AnalysisContext] = None,
    spatial_context: Optional[SpatialContext] = None,
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

    # Precedence: user/manual input takes priority; fallback to OSM spatial context
    ind_dist = ctx.industrial_distance_km
    if ind_dist is None and spatial_context and spatial_context.industrial_distance_km is not None:
        ind_dist = spatial_context.industrial_distance_km

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
        industrial_distance_km=ind_dist,
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
    spatial_context: Optional[SpatialContext] = None,
) -> HotspotFeatures:
    """
    Central pipeline for feature generation.

    1. Computes BaseHotspotFeatures (incorporating spatial_context if available)
    2. Runs persistence_service to get PersistenceResult
    3. Derives recurrence signal
    4. Emits final HotspotFeatures with OSM and environmental fields
    """
    base = extract_base_features(
        history=history,
        nearby_observations=nearby_observations,
        selected_observation=selected_observation,
        context=context,
        spatial_context=spatial_context,
    )
    persistence = calculate_persistence(base)
    recurrence_sig = derive_recurrence_signal(base, persistence)

    # Extract spatial context attributes if present
    ind_feat_count = spatial_context.industrial_feature_count if spatial_context else 0
    ind_w_1km = spatial_context.industrial_within_1km if spatial_context else False
    ind_w_5km = spatial_context.industrial_within_5km if spatial_context else False
    ind_w_10km = spatial_context.industrial_within_10km if spatial_context else False
    c_1km = spatial_context.count_within_1km if spatial_context else 0
    c_5km = spatial_context.count_within_5km if spatial_context else 0
    c_10km = spatial_context.count_within_10km if spatial_context else 0
    nearest_name = (
        spatial_context.nearest_industrial_feature.name
        if spatial_context and spatial_context.nearest_industrial_feature
        else None
    )
    nearest_type = (
        spatial_context.nearest_industrial_feature.feature_type
        if spatial_context and spatial_context.nearest_industrial_feature
        else None
    )
    power_nearby = spatial_context.power_infrastructure_nearby if spatial_context else False
    flare_nearby = spatial_context.mapped_flare_nearby if spatial_context else False
    chimney_nearby = spatial_context.mapped_chimney_nearby if spatial_context else False
    ctx_conf = spatial_context.context_confidence if spatial_context else 0.0
    ctx_src = spatial_context.source if spatial_context else "unknown"
    ctx_prov = spatial_context.provenance if spatial_context else {}

    base_dict = base.model_dump()
    return HotspotFeatures(
        **base_dict,
        persistence_score=persistence.score,
        persistence_status=persistence.status,
        persistence_details=persistence.details,
        recurrence_signal=recurrence_sig,
        industrial_feature_count=ind_feat_count,
        industrial_within_1km=ind_w_1km,
        industrial_within_5km=ind_w_5km,
        industrial_within_10km=ind_w_10km,
        count_within_1km=c_1km,
        count_within_5km=c_5km,
        count_within_10km=c_10km,
        nearest_industrial_name=nearest_name,
        nearest_industrial_type=nearest_type,
        power_infrastructure_nearby=power_nearby,
        mapped_flare_nearby=flare_nearby,
        mapped_chimney_nearby=chimney_nearby,
        context_confidence=ctx_conf,
        context_source=ctx_src,
        context_provenance=ctx_prov,
    )
