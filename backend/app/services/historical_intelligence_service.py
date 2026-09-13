"""
Historical intelligence service for long-term multi-day location analytics.
Queries persistent observation storage and leverages existing thermal engines.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.repositories.observation_repository import ObservationRepository
from app.schemas.analysis import AnalysisStatistics, Coordinates, HistoryTimelinePoint
from app.schemas.history import (
    HistoryLocation,
    HistoryPeriod,
    HistoryQueryResponse,
    HistoryRecurrence,
)
from app.schemas.observation import Observation
from app.services.feature_service import derive_recurrence_signal, extract_base_features
from app.services.history_service import compute_history
from app.services.observation_service import model_to_observation
from app.services.persistence_service import calculate_persistence

logger = logging.getLogger("app.services.historical_intelligence_service")


class HistoricalIntelligenceService:
    """Orchestrates long-term location intelligence using persisted observations."""

    @staticmethod
    def get_location_history(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        days: int = 30,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> HistoryQueryResponse:
        """
        Query database for all observations at location within radius_km across date range,
        and calculate historical baseline, statistics, timeline, and recurrence.
        """
        now = datetime.now(timezone.utc)
        if to_date is None:
            to_date = now
        if from_date is None:
            from_date = datetime.fromtimestamp(now.timestamp() - (days * 86400), tz=timezone.utc)

        # Retrieve stored models
        models = ObservationRepository.get_near_location(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            from_date=from_date,
            to_date=to_date,
            limit=2000,
        )
        observations: List[Observation] = [model_to_observation(m) for m in models]

        # Calculate provenance breakdown
        provenance_counts: Dict[str, int] = {}
        for obs in observations:
            src = obs.source or "unknown"
            provenance_counts[src] = provenance_counts.get(src, 0) + 1

        period = HistoryPeriod(
            from_date=from_date.isoformat().replace("+00:00", "Z"),
            to_date=to_date.isoformat().replace("+00:00", "Z"),
        )
        location = HistoryLocation(latitude=latitude, longitude=longitude)

        if not observations:
            # Empty response when no observations are present
            empty_stats = AnalysisStatistics(
                included=0,
                excluded=0,
                distinctTimes=0,
                spanHours=0.0,
                currentFrp=0.0,
                baselineFrp=None,
                changePercent=None,
                persistence=0.0,
                center=Coordinates(latitude=latitude, longitude=longitude),
            )
            empty_recurrence = HistoryRecurrence(
                signal="INSUFFICIENT_HISTORY",
                persistenceScore=0.0,
                coverageRatio=0.0,
                stabilityFactor=0.0,
                uniqueDays=0,
                distinctTimes=0,
            )
            return HistoryQueryResponse(
                location=location,
                radiusKm=radius_km,
                period=period,
                observationCount=0,
                observations=[],
                statistics=empty_stats,
                timeline=[],
                recurrence=empty_recurrence,
                provenance=provenance_counts,
            )

        # Compute history through core thermal engine
        history = compute_history(observations)

        # Compute persistence & recurrence signal
        latest_obs = observations[-1]
        base_features = extract_base_features(
            history=history,
            nearby_observations=observations,
            selected_observation=latest_obs,
        )
        persistence_res = calculate_persistence(base_features)
        rec_signal = derive_recurrence_signal(base_features, persistence_res)

        statistics = AnalysisStatistics(
            included=len(observations),
            excluded=0,
            distinctTimes=history.distinct_passes_count,
            spanHours=history.span_hours,
            currentFrp=history.current_frp,
            baselineFrp=history.baseline_frp,
            changePercent=history.frp_change_percentage,
            persistence=persistence_res.coverage_ratio,
            center=Coordinates(latitude=latitude, longitude=longitude),
        )

        recurrence = HistoryRecurrence(
            signal=rec_signal,
            persistenceScore=persistence_res.score,
            coverageRatio=persistence_res.coverage_ratio,
            stabilityFactor=persistence_res.stability_factor,
            uniqueDays=history.unique_days_count,
            distinctTimes=history.distinct_passes_count,
        )

        return HistoryQueryResponse(
            location=location,
            radiusKm=radius_km,
            period=period,
            observationCount=len(observations),
            observations=observations,
            statistics=statistics,
            timeline=history.timeline,
            recurrence=recurrence,
            provenance=provenance_counts,
        )
