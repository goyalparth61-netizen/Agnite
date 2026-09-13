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
from app.utils.dates import iso_to_epoch_ms
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.services.analysis_service")


def run_hotspot_analysis(request: AnalysisRequest) -> AnalysisResult:
    """Execute the full thermal intelligence analysis workflow on request observations."""
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

    # 3. Spatial search: find nearby observations within radius_km
    nearby, all_unique, excluded_count = get_nearby_observations(
        selected_observation=selected,
        observations=observations,
        radius_km=radius,
    )

    if not nearby:
        raise ValueError(
            f"No observations were found within {radius:.1f} km of the selected site."
        )

    # 4. History calculation (overpass grouping + baseline)
    history = compute_history(nearby)

    # 5 & 6 & 7. Feature extraction + Persistence scoring + Consolidated features
    features = build_hotspot_features(
        history=history,
        nearby_observations=nearby,
        selected_observation=selected,
        context=context,
    )
    persistence_res = calculate_persistence(features)

    # 8. Classification
    prediction = classify_hotspot(features, context)

    # 9. Risk assessment & scenarios
    risk_result, scenarios = calculate_risk(features, context)

    # 10. Explainability & evidence
    evidence = generate_evidence(features, context)
    contributions = compute_contributions(features, context, prediction)
    summary = generate_summary(features, context, prediction, risk_result)
    warnings = generate_warnings(
        features=features,
        context=context,
        prediction=prediction,
        excluded_count=excluded_count,
        total_count=len(observations),
    )

    # 11. Statistics
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

    # 12. Model metadata
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

    return AnalysisResult(
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
    )
