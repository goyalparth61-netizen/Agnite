"""
Unit tests for AssistantContextService in AGNITE Phase 5A.

Verifies:
- Context resolution priority: analysisId -> selectedObservationId -> coordinates
- Snapshot preservation from analysisId
- Observation and historical DB aggregation
- Spatial OSM context attachment
- Watch monitoring and alert integration
- Safe handling of missing references
"""

from __future__ import annotations

import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.alert import AlertModel
from app.db.models.analysis import AnalysisRecordModel
from app.db.models.observation import ObservationModel
from app.db.models.watch import WatchModel
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.observation_repository import ObservationRepository
from app.db.repositories.watch_repository import WatchRepository
from app.schemas.analysis import (
    AnalysisResult,
    AnalysisStatistics,
    Coordinates,
    ModelInfo,
    RiskResult,
)
from app.schemas.context import SpatialContext
from app.schemas.features import PersistenceResult
from app.schemas.observation import Observation
from app.schemas.watch import WatchCreate
from app.services.assistant_context_service import AssistantContextService


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_analysis_result():
    """A realistic AnalysisResult for testing."""
    return AnalysisResult(
        model=ModelInfo(
            name="agnite-heuristic-v1",
            version="1.0",
            method="heuristic",
            training_source="heuristic",
            sample_count=100,
            synthetic_validation_accuracy=0.88,
            limitations=["Requires ground-truth verification", "Weather telemetry not fetched automatically"],
        ),
        classification="Persistent Industrial Heat",
        status="classified",
        confidence=88.5,
        risk=RiskResult(
            index=35,
            level="Low",
            method="heuristic",
            factors=["Continuous low-variance thermal emission", "Proximity to mapped industrial facility"],
        ),
        summary="Persistent thermal detection consistent with continuous industrial operations.",
        statistics=AnalysisStatistics(
            included=5,
            excluded=0,
            distinct_times=5,
            span_hours=48.0,
            current_frp=28.0,
            baseline_frp=25.0,
            change_percent=12.0,
            persistence=85.0,
            center=Coordinates(latitude=21.1466, longitude=79.0889),
        ),
        persistence=PersistenceResult(
            score=85.0,
            status="HIGH_PERSISTENCE",
            coverage_ratio=0.8,
            stability_factor=0.9,
            details="Stable industrial source",
        ),
        recurrence_signal="daily_recurring",
        spatial_context=SpatialContext(
            latitude=21.1466,
            longitude=79.0889,
            search_radius_km=5.0,
            industrial_distance_km=0.75,
            industrial_feature_count=3,
            industrial_within_5km=True,
            source="OpenStreetMap",
            retrieved_at="2026-09-13T12:00:00Z",
        ),
    )


class TestAssistantContextResolution:
    def test_priority_1_analysis_id_exact_snapshot(self, db_session, sample_analysis_result):
        """Priority 1: analysisId resolves exact snapshot without replacing values."""
        record = AnalysisRepository.create(
            db=db_session,
            result=sample_analysis_result,
            selected_observation_id="obs-abc-1",
        )

        ctx = AssistantContextService.build_context(
            db=db_session,
            analysis_id=record.id,
            selected_observation_id="unrelated-obs",
            latitude=12.0,
            longitude=77.0,
        )

        assert ctx.resolved is True
        assert ctx.reference_type == "analysis"
        assert ctx.analysis_id == record.id
        assert ctx.classification == "Persistent Industrial Heat"
        assert ctx.risk_index == 35
        assert ctx.risk_level == "Low"
        assert ctx.current_frp == 28.0
        assert ctx.baseline_frp == 25.0
        assert ctx.frp_change_percent == 12.0
        assert ctx.industrial_distance_km == 0.75
        assert ctx.persistence_score == 85.0
        assert ctx.classification_method == "heuristic"
        assert "OpenStreetMap" in ctx.sources
        assert "AGNITE historical database" in ctx.sources

    def test_priority_2_selected_observation_id(self, db_session):
        """Priority 2: selectedObservationId resolves observation details and linked analysis."""
        obs = Observation(
            id="obs-xyz-99",
            latitude=21.1466,
            longitude=79.0889,
            observed_at="2026-09-13T12:00:00.000Z",
            frp=65.4,
            brightness=340.2,
            satellite="N20",
            sensor="noaa20",
            source="firms",
        )
        ObservationRepository.create(db_session, obs)

        ctx = AssistantContextService.build_context(
            db=db_session,
            selected_observation_id="obs-xyz-99",
            latitude=15.0,
            longitude=75.0,
        )

        assert ctx.resolved is True
        assert ctx.reference_type == "observation"
        assert ctx.selected_observation_id == "obs-xyz-99"
        assert ctx.current_frp == 65.4
        assert ctx.brightness == 340.2
        assert ctx.satellite == "N20"
        assert "NASA FIRMS" in ctx.sources

    def test_priority_3_coordinates(self, db_session, sample_analysis_result):
        """Priority 3: Coordinates resolve nearest recent analysis and DB history."""
        # Create an analysis at (21.1466, 79.0889)
        record = AnalysisRepository.create(db=db_session, result=sample_analysis_result)

        # Query slightly nearby within 1 km
        ctx = AssistantContextService.build_context(
            db=db_session,
            latitude=21.1480,
            longitude=79.0895,
        )

        assert ctx.resolved is True
        assert ctx.reference_type == "coordinates"
        assert ctx.analysis_id == record.id
        assert ctx.classification == "Persistent Industrial Heat"

    def test_missing_all_references_safe_handling(self, db_session):
        """When no reference is given, returns resolved=False with explicit missing evidence."""
        ctx = AssistantContextService.build_context(db=db_session)
        assert ctx.resolved is False
        assert ctx.reference_type == "none"
        assert any("No reference observation" in m for m in ctx.missing_evidence)

    def test_invalid_coordinates_handled_safely(self, db_session):
        """Invalid coordinates produce clear missing evidence."""
        ctx = AssistantContextService.build_context(
            db=db_session,
            latitude=999.0,
            longitude=79.0,
        )
        assert ctx.resolved is False
        assert any("geographically invalid" in m for m in ctx.missing_evidence)


class TestMonitoringAndAlertIntegration:
    def test_watch_location_detected(self, db_session, sample_analysis_result):
        """Verifies context identifies when location falls within a watched site."""
        WatchRepository.create(
            db=db_session,
            data=WatchCreate(
                name="Nagpur Refinery Watch",
                latitude=21.1466,
                longitude=79.0889,
                radius_km=5.0,
                frp_threshold=30.0,
            ),
        )

        record = AnalysisRepository.create(db=db_session, result=sample_analysis_result)
        ctx = AssistantContextService.build_context(db=db_session, analysis_id=record.id)

        assert "Nagpur Refinery Watch" in (ctx.watch_status or "")
        assert len(ctx.matching_watches) >= 1
        assert "AGNITE Monitoring Engine" in ctx.sources

    def test_active_alerts_attached_to_context(self, db_session, sample_analysis_result):
        """Verifies context attaches alerts triggered near the hotspot."""
        record = AnalysisRepository.create(db=db_session, result=sample_analysis_result)

        # Insert matching alert
        alert = AlertModel(
            id="alert-1",
            watch_id="watch-1",
            analysis_id=record.id,
            type="threshold_exceeded",
            severity="warning",
            title="Thermal Threshold Exceeded",
            message="FRP of 45 MW exceeded watch threshold 30 MW.",
            latitude=21.1466,
            longitude=79.0889,
            frp=45.0,
            risk=70,
            fingerprint="fp-1",
            acknowledged=False,
        )
        db_session.add(alert)
        db_session.commit()

        ctx = AssistantContextService.build_context(db=db_session, analysis_id=record.id)
        assert len(ctx.recent_alerts) == 1
        assert ctx.recent_alerts[0]["title"] == "Thermal Threshold Exceeded"
        assert "AGNITE Alert System" in ctx.sources
