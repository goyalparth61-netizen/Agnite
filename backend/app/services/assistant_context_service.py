"""
Assistant Context Service for AGNITE AI.

Aggregates normalized, auditable context across:
- Persisted Analysis Records (preserving exact snapshots when analysisId is given)
- Raw / Ingested Observations & NASA FIRMS history
- Spatial context & OpenStreetMap proximity
- Active Watch sites & Triggered Alerts
- Heuristic and future ML Model metadata

Strict Resolution Priority:
    analysisId -> selectedObservationId -> coordinates
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.alert import AlertModel
from app.db.models.analysis import AnalysisRecordModel
from app.db.models.observation import ObservationModel
from app.db.models.watch import WatchModel
from app.db.repositories.alert_repository import AlertRepository
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.observation_repository import ObservationRepository
from app.db.repositories.watch_repository import WatchRepository
from app.schemas.analysis import AnalysisResult
from app.utils.geo import haversine_km, is_valid_coordinate

logger = logging.getLogger("app.services.assistant_context_service")


class AssistantContext(BaseModel):
    """
    Normalized, structured data contract for the AGNITE AI explanation layer.
    Strictly grounded in persisted and observed backend data.
    """

    resolved: bool = True
    reference_type: str = "none"  # "analysis", "observation", "coordinates", or "none"
    analysis_id: Optional[str] = None
    selected_observation_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Current / reference observation details
    current_frp: Optional[float] = None
    brightness: Optional[float] = None
    observed_at: Optional[str] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    observation_source: Optional[str] = None

    # Classification & Model
    classification: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_method: Optional[str] = None  # "heuristic" or "ml"
    model_name: Optional[str] = None
    model_limitations: List[str] = Field(default_factory=list)
    contributions: List[Dict[str, Any]] = Field(default_factory=list)

    # Risk Scoring
    risk_index: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: List[str] = Field(default_factory=list)
    scenarios: List[Dict[str, Any]] = Field(default_factory=list)

    # Historical & Baseline
    history_observation_count: int = 0
    distinct_times: int = 0
    span_hours: Optional[float] = None
    baseline_frp: Optional[float] = None
    frp_change_percent: Optional[float] = None

    # Persistence & Recurrence
    persistence_score: Optional[float] = None
    persistence_status: Optional[str] = None
    recurrence_signal: Optional[str] = None

    # Spatial Context / OSM
    industrial_distance_km: Optional[float] = None
    nearby_industrial_count: int = 0
    nearest_infrastructure_name: Optional[str] = None
    land_cover: Optional[str] = None
    osm_status: str = "unknown"  # "present", "none_found", "unavailable"
    nearby_features: List[Dict[str, Any]] = Field(default_factory=list)

    # Monitoring & Alerts
    watch_status: Optional[str] = None
    matching_watches: List[Dict[str, Any]] = Field(default_factory=list)
    recent_alerts: List[Dict[str, Any]] = Field(default_factory=list)

    # Audit, Provenance & Warnings
    sources: List[str] = Field(default_factory=list)
    evidence_items: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
        "protected_namespaces": (),
    }


class AssistantContextService:
    """Service that resolves and builds normalized AssistantContext."""

    @staticmethod
    def build_context(
        db: Session,
        analysis_id: Optional[str] = None,
        selected_observation_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> AssistantContext:
        """
        Build AssistantContext following strict resolution hierarchy:
        1. analysisId (exact immutable snapshot)
        2. selectedObservationId (observation lookup + linked analysis)
        3. coordinates (spatial lookup for nearby analyses & observations)
        """
        context = AssistantContext()
        missing: List[str] = []
        sources: List[str] = []

        # ── Priority 1: analysisId ────────────────────────────────────
        if analysis_id:
            record = AnalysisRepository.get_by_id(db, analysis_id)
            if record:
                context.resolved = True
                context.reference_type = "analysis"
                context.analysis_id = record.id
                context.selected_observation_id = record.selected_observation_id
                context.latitude = record.latitude
                context.longitude = record.longitude
                context.classification = record.classification
                context.classification_confidence = record.confidence
                context.classification_method = record.method or "heuristic"
                context.model_name = record.model_name
                context.risk_index = record.risk_index
                context.risk_level = record.risk_level

                sources.append("AGNITE historical database")
                if record.method == "ml":
                    sources.append(f"ML Classifier ({record.model_name})")
                else:
                    sources.append("AGNITE Heuristic Classification Engine")
                sources.append("AGNITE Risk Engine")

                # Parse immutable JSON snapshot
                try:
                    analysis_data = json.loads(record.analysis_json)
                    parsed_result = AnalysisResult.model_validate(analysis_data)
                    AssistantContextService._hydrate_from_analysis_result(context, parsed_result, sources)
                except Exception as exc:
                    logger.warning("Could not fully parse analysis_json for id=%s: %s", analysis_id, exc)

                # Try to enrich with raw observation details if available
                if record.selected_observation_id:
                    raw_obs = ObservationRepository.get_by_id(db, record.selected_observation_id)
                    if raw_obs:
                        AssistantContextService._hydrate_from_observation_model(context, raw_obs, sources)

                # Add watches and alerts for this location
                AssistantContextService._attach_monitoring_and_alerts(db, context, sources)
                AssistantContextService._finalize_context(context, missing, sources)
                return context
            else:
                missing.append(f"Analysis record with ID '{analysis_id}' was not found in the database.")

        # ── Priority 2: selectedObservationId ─────────────────────────
        if selected_observation_id:
            obs = ObservationRepository.get_by_id(db, selected_observation_id)
            if obs:
                context.resolved = True
                context.reference_type = "observation"
                context.selected_observation_id = obs.id
                context.latitude = obs.latitude
                context.longitude = obs.longitude
                AssistantContextService._hydrate_from_observation_model(context, obs, sources)

                # Check if there is an existing analysis created for this observation
                analysis_rec = db.scalar(
                    select(AnalysisRecordModel)
                    .where(AnalysisRecordModel.selected_observation_id == obs.id)
                    .order_by(AnalysisRecordModel.created_at.desc())
                )
                if not analysis_rec:
                    # Look for analysis nearby within 1 km
                    analysis_rec = AssistantContextService._find_nearest_analysis(db, obs.latitude, obs.longitude, max_km=1.0)

                if analysis_rec:
                    context.analysis_id = analysis_rec.id
                    context.classification = analysis_rec.classification
                    context.classification_confidence = analysis_rec.confidence
                    context.classification_method = analysis_rec.method or "heuristic"
                    context.model_name = analysis_rec.model_name
                    context.risk_index = analysis_rec.risk_index
                    context.risk_level = analysis_rec.risk_level

                    try:
                        analysis_data = json.loads(analysis_rec.analysis_json)
                        parsed_result = AnalysisResult.model_validate(analysis_data)
                        AssistantContextService._hydrate_from_analysis_result(context, parsed_result, sources)
                    except Exception as exc:
                        logger.warning("Could not parse analysis_json: %s", exc)
                else:
                    missing.append("No thermal analysis has been run yet for this observation.")

                # Attach history count near this observation
                AssistantContextService._attach_db_history(db, context, obs.latitude, obs.longitude, sources)
                AssistantContextService._attach_monitoring_and_alerts(db, context, sources)
                AssistantContextService._finalize_context(context, missing, sources)
                return context
            else:
                missing.append(f"Observation with ID '{selected_observation_id}' was not found in the database.")

        # ── Priority 3: coordinates ───────────────────────────────────
        if latitude is not None and longitude is not None:
            if is_valid_coordinate(latitude, longitude):
                context.resolved = True
                context.reference_type = "coordinates"
                context.latitude = latitude
                context.longitude = longitude

                # Find any recent analysis nearby (within 5 km)
                analysis_rec = AssistantContextService._find_nearest_analysis(db, latitude, longitude, max_km=5.0)
                if analysis_rec:
                    context.analysis_id = analysis_rec.id
                    context.classification = analysis_rec.classification
                    context.classification_confidence = analysis_rec.confidence
                    context.classification_method = analysis_rec.method or "heuristic"
                    context.model_name = analysis_rec.model_name
                    context.risk_index = analysis_rec.risk_index
                    context.risk_level = analysis_rec.risk_level

                    try:
                        analysis_data = json.loads(analysis_rec.analysis_json)
                        parsed_result = AnalysisResult.model_validate(analysis_data)
                        AssistantContextService._hydrate_from_analysis_result(context, parsed_result, sources)
                    except Exception as exc:
                        logger.warning("Could not parse analysis_json: %s", exc)
                else:
                    missing.append("No prior analysis found within 5 km of these coordinates.")

                AssistantContextService._attach_db_history(db, context, latitude, longitude, sources)
                AssistantContextService._attach_monitoring_and_alerts(db, context, sources)
                AssistantContextService._finalize_context(context, missing, sources)
                return context
            else:
                missing.append(f"Supplied coordinates ({latitude}, {longitude}) are geographically invalid.")

        # ── No valid references provided ──────────────────────────────
        context.resolved = False
        context.reference_type = "none"
        missing.append("No reference observation, analysis record, or valid coordinates were provided.")
        AssistantContextService._finalize_context(context, missing, sources)
        return context

    @staticmethod
    def _hydrate_from_analysis_result(
        context: AssistantContext,
        result: AnalysisResult,
        sources: List[str],
    ) -> None:
        """Hydrate AssistantContext fields from an immutable AnalysisResult."""
        if result.risk:
            context.risk_index = result.risk.index
            context.risk_level = result.risk.level
            if result.risk.factors:
                context.risk_factors = list(result.risk.factors)

        if result.statistics:
            context.current_frp = result.statistics.current_frp
            context.baseline_frp = result.statistics.baseline_frp
            context.frp_change_percent = result.statistics.change_percent
            context.distinct_times = result.statistics.distinct_times
            context.span_hours = result.statistics.span_hours
            context.persistence_score = result.statistics.persistence
            context.history_observation_count = result.statistics.included

        if result.persistence:
            context.persistence_score = result.persistence.score
            context.persistence_status = result.persistence.status

        if result.recurrence_signal:
            context.recurrence_signal = result.recurrence_signal

        if result.model:
            context.model_name = result.model.name
            context.classification_method = result.model.method
            if result.model.limitations:
                context.model_limitations = list(result.model.limitations)

        if result.contributions:
            context.contributions = [
                {
                    "feature": c.feature,
                    "value": c.value,
                    "contribution": c.contribution,
                    "direction": c.direction,
                }
                for c in result.contributions
            ]

        if result.evidence:
            context.evidence_items = [
                {"label": e.label, "value": e.value, "detail": e.detail}
                for e in result.evidence
            ]

        if result.warnings:
            context.warnings = list(result.warnings)

        if result.scenarios:
            context.scenarios = [
                {
                    "horizon": s.horizon,
                    "low": s.low,
                    "central": s.central,
                    "high": s.high,
                    "assumption": s.assumption,
                }
                for s in result.scenarios
            ]

        if result.spatial_context:
            sc = result.spatial_context
            sources.append(getattr(sc, "source", "OpenStreetMap") or "OpenStreetMap")
            context.industrial_distance_km = getattr(sc, "industrial_distance_km", None)
            count = getattr(sc, "industrial_feature_count", getattr(sc, "nearby_industrial_count", 0))
            context.nearby_industrial_count = count or 0
            context.land_cover = getattr(sc, "land_cover", None)
            
            nearest = getattr(sc, "nearest_industrial_feature", getattr(sc, "nearest_industrial", None))
            if nearest and getattr(nearest, "name", None):
                context.nearest_infrastructure_name = getattr(nearest, "name", None)

            features = getattr(sc, "features", [])
            if features:
                context.nearby_features = [
                    {
                        "name": getattr(f, "name", None) or getattr(f, "type", "feature"),
                        "type": getattr(f, "type", getattr(f, "feature_type", "industrial")),
                        "distance_km": getattr(f, "distance_km", 0.0),
                        "tags": getattr(f, "tags", {}),
                    }
                    for f in features[:5]
                ]

            is_degraded = getattr(sc, "degraded", False)
            has_ind = getattr(sc, "industrial_within_5km", getattr(sc, "has_industrial_nearby", False))
            if is_degraded:
                context.osm_status = "unavailable"
            elif has_ind or (count and count > 0):
                context.osm_status = "present"
            else:
                context.osm_status = "none_found"

    @staticmethod
    def _hydrate_from_observation_model(
        context: AssistantContext,
        obs: ObservationModel,
        sources: List[str],
    ) -> None:
        """Hydrate raw observation telemetry."""
        if context.current_frp is None:
            context.current_frp = obs.frp
        context.brightness = obs.brightness
        if obs.observed_at:
            context.observed_at = obs.observed_at.isoformat()
        context.satellite = obs.satellite
        context.sensor = obs.sensor
        context.observation_source = obs.source
        if obs.source == "firms":
            sources.append("NASA FIRMS")
        elif obs.source:
            sources.append(f"Observation Source ({obs.source})")

    @staticmethod
    def _attach_db_history(
        db: Session,
        context: AssistantContext,
        lat: float,
        lon: float,
        sources: List[str],
    ) -> None:
        """Count nearby observations in database history."""
        models = ObservationRepository.get_near_location(db, lat, lon, radius_km=5.0)
        if models:
            context.history_observation_count = max(context.history_observation_count, len(models))
            sources.append("AGNITE historical database")

    @staticmethod
    def _attach_monitoring_and_alerts(
        db: Session,
        context: AssistantContext,
        sources: List[str],
    ) -> None:
        """Check active watches and recent alerts for this location."""
        if context.latitude is None or context.longitude is None:
            return

        lat = context.latitude
        lon = context.longitude

        # 1. Check watches
        watches = WatchRepository.list_all(db, enabled_only=True)
        matched_watches = []
        for w in watches:
            dist = haversine_km(lat, lon, w.latitude, w.longitude)
            if dist <= (w.radius_km or 5.0):
                matched_watches.append({
                    "id": w.id,
                    "name": w.name,
                    "distance_km": round(dist, 2),
                    "threshold": w.frp_threshold,
                    "risk_threshold": w.risk_threshold,
                })

        context.matching_watches = matched_watches
        if matched_watches:
            context.watch_status = (
                f"Location is inside monitored watch zone '{matched_watches[0]['name']}' "
                f"(threshold: {matched_watches[0]['threshold']} MW, distance: {matched_watches[0]['distance_km']} km)."
            )
            sources.append("AGNITE Monitoring Engine")
        else:
            context.watch_status = "Not currently inside any active watch location."

        # 2. Check alerts
        alerts, _, _ = AlertRepository.list_alerts(db, limit=50)
        relevant_alerts = []
        for a in alerts:
            # Match by analysis_id, observation_id, or spatial proximity (5 km)
            is_match = False
            if context.analysis_id and a.analysis_id == context.analysis_id:
                is_match = True
            elif context.selected_observation_id and a.observation_id == context.selected_observation_id:
                is_match = True
            elif a.latitude and a.longitude:
                dist = haversine_km(lat, lon, a.latitude, a.longitude)
                if dist <= 5.0:
                    is_match = True

            if is_match:
                relevant_alerts.append({
                    "id": a.id,
                    "title": a.title,
                    "severity": a.severity,
                    "message": a.message,
                    "frp": a.frp,
                    "risk": a.risk,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "acknowledged": a.acknowledged,
                })

        context.recent_alerts = relevant_alerts[:5]
        if relevant_alerts:
            sources.append("AGNITE Alert System")

    @staticmethod
    def _find_nearest_analysis(
        db: Session,
        lat: float,
        lon: float,
        max_km: float = 5.0,
    ) -> Optional[AnalysisRecordModel]:
        """Find most recent analysis within max_km bounding box and Haversine."""
        delta = max_km / 111.0
        records = list(
            db.scalars(
                select(AnalysisRecordModel)
                .where(
                    AnalysisRecordModel.latitude.between(lat - delta, lat + delta),
                    AnalysisRecordModel.longitude.between(lon - delta, lon + delta),
                )
                .order_by(AnalysisRecordModel.created_at.desc())
                .limit(10)
            ).all()
        )
        for rec in records:
            dist = haversine_km(lat, lon, rec.latitude, rec.longitude)
            if dist <= max_km:
                return rec
        return None

    @staticmethod
    def _finalize_context(
        context: AssistantContext,
        missing: List[str],
        sources: List[str],
    ) -> None:
        """Deduplicate sources and identify missing evidence."""
        # Deduplicate sources preserving order
        unique_sources: List[str] = []
        for s in sources:
            if s and s not in unique_sources:
                unique_sources.append(s)
        context.sources = unique_sources

        # Detect specific missing evidence
        if context.classification is None:
            missing.append("Classification is not yet available; run site analysis first.")
        if context.baseline_frp is None:
            missing.append("Historical FRP baseline is not established (requires prior observations).")
        if context.history_observation_count < 2:
            missing.append("Insufficient multi-pass history (only 0 or 1 observation recorded).")
        if context.osm_status in ("unknown", "unavailable"):
            missing.append("OpenStreetMap industrial spatial context is unavailable or unqueried.")
        if context.risk_index is None:
            missing.append("Quantitative risk scoring is not available.")

        # Deduplicate missing evidence list
        deduped_missing: List[str] = []
        for m in missing:
            if m not in deduped_missing:
                deduped_missing.append(m)
        context.missing_evidence = deduped_missing
