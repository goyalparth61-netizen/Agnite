"""
Phase 4 Tests: Monitored Watches, Monitoring Service, and Alert Generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.observation import ObservationModel
from app.db.models.watch import WatchModel
from app.db.repositories.alert_repository import AlertRepository
from app.db.repositories.watch_repository import WatchRepository
from app.schemas.watch import WatchCreate, WatchUpdate
from app.services.monitoring_service import MonitoringService


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestWatchRepository:
    def test_watch_crud_lifecycle(self, db_session):
        repo = WatchRepository()
        created = repo.create(
            db_session,
            WatchCreate(
                name="Nagpur Refinery",
                latitude=21.1466,
                longitude=79.0889,
                radius_km=5.0,
                frp_threshold=30.0,
                risk_threshold=60,
            ),
        )
        assert created.id is not None
        assert created.name == "Nagpur Refinery"
        assert created.enabled is True

        # Read
        fetched = repo.get_by_id(db_session, created.id)
        assert fetched is not None
        assert fetched.name == "Nagpur Refinery"

        # Update
        updated = repo.update(
            db_session,
            created.id,
            WatchUpdate(frp_threshold=45.0, enabled=False),
        )
        assert updated is not None
        assert updated.frp_threshold == 45.0
        assert updated.enabled is False

        # Delete
        assert repo.delete(db_session, created.id) is True
        assert repo.get_by_id(db_session, created.id) is None


class TestMonitoringAndAlertDeduplication:
    def test_alert_creation_and_fingerprint_deduplication(self, db_session):
        alert_repo = AlertRepository()

        # First insert succeeds
        first = alert_repo.create_if_not_exists(
            db=db_session,
            watch_id="watch-1",
            alert_type="FRP_THRESHOLD_EXCEEDED",
            severity="HIGH",
            title="High FRP Exceeded",
            message="FRP of 85.0 MW exceeded threshold 50.0 MW",
            latitude=21.1466,
            longitude=79.0889,
            fingerprint="watch-1:obs-100:FRP_THRESHOLD_EXCEEDED",
            observation_id="obs-100",
            frp=85.0,
            risk=70,
            confidence=0.85,
        )
        assert first is not None
        assert first.severity == "HIGH"
        assert first.fingerprint == "watch-1:obs-100:FRP_THRESHOLD_EXCEEDED"

        # Second insert with identical fingerprint is blocked
        second = alert_repo.create_if_not_exists(
            db=db_session,
            watch_id="watch-1",
            alert_type="FRP_THRESHOLD_EXCEEDED",
            severity="HIGH",
            title="High FRP Exceeded",
            message="FRP of 85.0 MW exceeded threshold 50.0 MW",
            latitude=21.1466,
            longitude=79.0889,
            fingerprint="watch-1:obs-100:FRP_THRESHOLD_EXCEEDED",
            observation_id="obs-100",
            frp=85.0,
            risk=70,
            confidence=0.85,
        )
        assert second is None

        # Total alerts remain 1
        alerts, total, _ = alert_repo.list_alerts(db_session)
        assert total == 1

    def test_monitoring_service_scanner(self, db_session):
        # 1. Create a watch
        watch = WatchModel(
            id="watch-test-1",
            name="Koradi Power Plant",
            latitude=21.2400,
            longitude=79.1600,
            radius_km=5.0,
            frp_threshold=40.0,
            risk_threshold=50,
            enabled=True,
        )
        db_session.add(watch)

        # 2. Add an observation exceeding threshold within radius
        now_utc = datetime.now(timezone.utc)
        obs_near_exceed = ObservationModel(
            id="obs-koradi-1",
            latitude=21.2420,
            longitude=79.1610,
            observed_at=now_utc,
            frp=75.0,
            source="firms",
        )
        # 3. Add an observation outside radius
        obs_far = ObservationModel(
            id="obs-far-1",
            latitude=21.8000,
            longitude=79.1600,
            observed_at=now_utc,
            frp=120.0,
            source="firms",
        )
        db_session.add_all([obs_near_exceed, obs_far])
        db_session.commit()

        # Run monitoring scanner
        result1 = MonitoringService.scan_all_watches(db_session)
        assert len(result1) >= 1

        # Second scan over identical observations produces 0 new alerts
        result2 = MonitoringService.scan_all_watches(db_session)
        assert len(result2) == 0


@pytest.mark.asyncio
class TestWatchesAndAlertsApi:
    async def test_watch_api_crud(self, client):
        # Create
        create_payload = {
            "name": "API Test Site",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "radiusKm": 5.0,
            "frpThreshold": 35.0,
            "riskThreshold": 50,
        }
        res = await client.post("/api/v1/watches", json=create_payload)
        assert res.status_code == 201
        watch_id = res.json()["id"]

        # List
        res = await client.get("/api/v1/watches")
        assert res.status_code == 200
        watches = res.json()
        assert any(w["id"] == watch_id for w in watches)

        # Update
        res = await client.patch(f"/api/v1/watches/{watch_id}", json={"enabled": False})
        assert res.status_code == 200
        assert res.json()["enabled"] is False

        # Delete
        res = await client.delete(f"/api/v1/watches/{watch_id}")
        assert res.status_code == 204

        # Verify deletion
        res = await client.get(f"/api/v1/watches/{watch_id}")
        assert res.status_code == 404

    async def test_alerts_api_list_and_acknowledge(self, client):
        res = await client.get("/api/v1/alerts")
        assert res.status_code == 200
        data = res.json()
        assert "alerts" in data
        assert "total" in data
