"""
Central analysis orchestrator service for AGNITE Phase 2.

Coordinates the complete thermal intelligence pipeline:
Input Validation
    ↓
Hotspot Spatial Search (5 km radius)
    ↓
History & Baseline Calculation
    ↓
Base Feature Extraction
    ↓
Persistence Scoring
    ↓
Consolidated HotspotFeatures Assembly
    ↓
Classification (FallbackClassifier / MLClassifier)
    ↓
Risk Scoring & What-If Scenarios
    ↓
Explainability, Contributions & Evidence
    ↓
AnalysisResult
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from app.core.constants import (
    CONTEXT_SOURCE_UNKNOWN,
    DEFAULT_OSM_SEARCH_RADIUS_KM,
    DEFAULT_SEARCH_RADIUS_KM,
    MAX_ANALYSIS_OBSERVATIONS,
    MAX_SEARCH_RADIUS_KM,
    MIN_SEARCH_RADIUS_KM,
)
from app.schemas.analysis import (
    AnalysisContext,
    AnalysisRequest,
    AnalysisResult,
    AnalysisStatistics,
    Coordinates,
    ModelInfo,
)
from app.schemas.context import SpatialContext
from app.schemas.observation import Observation
from app.services.classification_service import classify_hotspot
from app.services.explainability_service import (
    compute_contributions,
    generate_evidence,
    generate_summary,
    generate_warnings,
)
from app.services.feature_service import build_hotspot_features
from app.services.history_service import compute_history
from app.services.hotspot_service import get_nearby_observations
from app.services.persistence_service import calculate_persistence
from app.services.risk_service import calculate_risk
from app.services.spatial_context_service import (
    SpatialContextProvider,
    get_spatial_context_provider,
)
from app.utils.dates import iso_to_epoch_ms, utc_now_iso
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.services.analysis_service")


async def run_hotspot_analysis(
    request: AnalysisRequest,
    spatial_provider: Optional[SpatialContextProvider] = None,
) -> AnalysisResult:
    """
    Execute the full thermal intelligence analysis workflow on request observations.

    Thermal analysis (clustering, history, baseline, persistence) and external spatial
    context retrieval (OSM Overpass) are conceptually decoupled. If Overpass fails or times
    out, degraded context with warnings is attached without failing the overall analysis.
    """
    start_time = time.perf_counter()

    # 1. Validation
    observations = request.observations
    if not observations:
        raise ValueError("Add at least one observation before analysis.")
    if len(observations) > MAX_ANALYSIS_OBSERVATIONS:
        raise ValueError(
            f"Analyze at most {MAX_ANALYSIS_OBSERVATIONS} observations at a time."
        )

    radius = request.radius_km or DEFAULT_SEARCH_RADIUS_KM
    if radius < MIN_SEARCH_RADIUS_KM or radius > MAX_SEARCH_RADIUS_KM:
        raise ValueError(
            f"Radius must be between {MIN_SEARCH_RADIUS_KM} and {MAX_SEARCH_RADIUS_KM} km."
        )

    context = request.context or AnalysisContext()

    # 2. Resolve selected observation / site center
    selected = request.selected_observation
    if selected is None:
        # Default to observation with the latest timestamp
        selected = max(observations, key=lambda x: iso_to_epoch_ms(x.observed_at))

    if not is_valid_coordinate(selected.latitude, selected.longitude):
        raise ValueError(
            f"Site center coordinate ({selected.latitude}, {selected.longitude}) is invalid."
        )

    # 3. Combine request observations + database persistent observations (Requirement 14 & 15)
    # Deduplicate strictly by id so nothing is double-counted
    merged_obs_by_id: dict[str, Observation] = {obs.id: obs for obs in observations}
    try:
        from app.db.repositories.observation_repository import ObservationRepository
        from app.db.session import SessionLocal
        from app.services.observation_service import model_to_observation

        db = SessionLocal()
        try:
            db_models = ObservationRepository.get_near_location(
                db=db,
                latitude=selected.latitude,
                longitude=selected.longitude,
                radius_km=radius,
                limit=1000,
            )
            for m in db_models:
                if m.id not in merged_obs_by_id:
                    merged_obs_by_id[m.id] = model_to_observation(m)
        finally:
            db.close()
    except Exception as db_exc:
        logger.warning(
            "Database historical observations query failed (non-fatal); using request observations: %s",
            db_exc,
        )

    combined_observations = list(merged_obs_by_id.values())

    # 4. Spatial search: find nearby observations within radius_km (pure thermal domain)
    nearby, all_unique, excluded_count = get_nearby_observations(
        selected_observation=selected,
        observations=combined_observations,
        radius_km=radius,
    )

    if not nearby:
        raise ValueError(
            f"No observations were found within {radius:.1f} km of the selected site."
        )

    # 4. History calculation: overpass grouping + baseline (pure thermal domain)
    history = compute_history(nearby)

    # 5. External spatial context retrieval (conceptually decoupled from thermal pipeline)
    provider = spatial_provider or get_spatial_context_provider()
    try:
        spatial_context = await provider.get_context(
            latitude=selected.latitude,
            longitude=selected.longitude,
            radius_km=DEFAULT_OSM_SEARCH_RADIUS_KM,
        )
    except Exception as exc:
        logger.warning(
            "Spatial context provider failed (%s); continuing with thermal evidence only.",
            exc,
        )
        spatial_context = SpatialContext(
            latitude=selected.latitude,
            longitude=selected.longitude,
            searchRadiusKm=DEFAULT_OSM_SEARCH_RADIUS_KM,
            industrialDistanceKm=None,
            nearestIndustrialFeature=None,
            industrialFeatureCount=0,
            industrialWithin1Km=False,
            industrialWithin5Km=False,
            industrialWithin10Km=False,
            countWithin1Km=0,
            countWithin5Km=0,
            countWithin10Km=0,
            powerInfrastructureNearby=False,
            mappedFlareNearby=False,
            mappedChimneyNearby=False,
            contextConfidence=0.0,
            source=CONTEXT_SOURCE_UNKNOWN,
            retrievedAt=utc_now_iso(),
            cached=False,
            provenance={"industrialDistanceKm": "unavailable"},
            features=[],
            warnings=[
                "External spatial context was unavailable; continuing with thermal measurements."
            ],
        )

    # Reconcile field-aware provenance and effective context
    effective_context = context.model_copy()
    reconciled_provenance: dict[str, str] = dict(spatial_context.provenance)

    if context.industrial_distance_km is not None:
        effective_context.industrial_distance_km = context.industrial_distance_km
        reconciled_provenance["industrialDistanceKm"] = "manual"
    elif spatial_context.industrial_distance_km is not None:
        effective_context.industrial_distance_km = spatial_context.industrial_distance_km
        reconciled_provenance["industrialDistanceKm"] = "osm"
    else:
        reconciled_provenance["industrialDistanceKm"] = "none"

    if context.land_cover != "unknown":
        reconciled_provenance["landCover"] = "manual"
    else:
        reconciled_provenance["landCover"] = "unknown"

    if context.wind_kph is not None:
        reconciled_provenance["windKph"] = "weather"
    else:
        reconciled_provenance["windKph"] = "none"

    spatial_context.provenance = reconciled_provenance

    # 6. Feature extraction + Persistence scoring + Consolidated features
    features = build_hotspot_features(
        history=history,
        nearby_observations=nearby,
        selected_observation=selected,
        context=effective_context,
        spatial_context=spatial_context,
    )
    persistence_res = calculate_persistence(features)

    # 7. Classification
    prediction = classify_hotspot(features, effective_context)

    # 8. Risk assessment & scenarios
    risk_result, scenarios = calculate_risk(features, effective_context)

    # 9. Explainability & evidence
    evidence = generate_evidence(features, effective_context)
    contributions = compute_contributions(features, effective_context, prediction)
    summary = generate_summary(features, effective_context, prediction, risk_result)
    warnings = generate_warnings(
        features=features,
        context=effective_context,
        prediction=prediction,
        excluded_count=excluded_count,
        total_count=len(observations),
    )
    if spatial_context and spatial_context.warnings:
        for w in spatial_context.warnings:
            if w not in warnings:
                warnings.append(w)

    # 10. Statistics
    statistics = AnalysisStatistics(
        included=len(nearby),
        excluded=excluded_count,
        distinctTimes=history.distinct_passes_count,
        spanHours=history.span_hours,
        currentFrp=history.current_frp,
        baselineFrp=history.baseline_frp,
        changePercent=history.frp_change_percentage,
        persistence=persistence_res.coverage_ratio,
        center=Coordinates(
            latitude=selected.latitude,
            longitude=selected.longitude,
        ),
    )

    # 11. Model metadata
    model_info = ModelInfo(
        name=prediction.model_name,
        version=prediction.model_version,
        method=prediction.method,
        trainingSource=prediction.training_source,
        metrics=prediction.metrics,
        sampleCount=prediction.sample_count,
        syntheticValidationAccuracy=None,
        limitations=prediction.limitations,
    )

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Hotspot analysis completed in %.2f ms | Class: %s (Method: %s, Conf: %.1f%%) | Risk: %s (%d/100) | Nearby: %d/%d",
        duration_ms,
        prediction.classification,
        prediction.method,
        prediction.confidence,
        risk_result.level,
        risk_result.index,
        len(nearby),
        len(observations),
    )

    result = AnalysisResult(
        model=model_info,
        classification=prediction.classification,
        status=prediction.status,
        modelScore=prediction.model_score,
        scores=prediction.scores,
        risk=risk_result,
        summary=summary,
        evidence=evidence,
        contributions=contributions,
        history=history.timeline,
        statistics=statistics,
        scenarios=scenarios,
        warnings=warnings,
        method=prediction.method,
        confidence=prediction.confidence,
        persistence=persistence_res,
        recurrenceSignal=features.recurrence_signal,
        spatialContext=spatial_context,
    )

    # Persist analysis record to DB (Requirement 26) - non-blocking & non-fatal
    try:
        from app.db.repositories.analysis_repository import AnalysisRepository
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            AnalysisRepository.create(
                db=db,
                result=result,
                selected_observation_id=selected.id if selected else None,
            )
        finally:
            db.close()
    except Exception as db_exc:
        logger.warning("Analysis record persistence failed (non-fatal): %s", db_exc)

    return result
