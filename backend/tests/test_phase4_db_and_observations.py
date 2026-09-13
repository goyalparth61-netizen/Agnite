"""
Phase 4 Tests: Database, Session, Observation Repository, and Ingestion.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.observation import ObservationModel
from app.db.repositories.observation_repository import ObservationRepository
from app.db.session import check_db_connection
from app.schemas.observation import Observation
from app.services.observation_service import ObservationService


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestDatabaseAndSession:
    def test_db_connection_check(self):
        """Database connection check returns True on valid connection."""
        assert check_db_connection() is True


class TestObservationRepository:
    def test_create_and_get_by_id(self, db_session):
        repo = ObservationRepository()
        obs = Observation(
            id="obs-1",
            latitude=21.1466,
            longitude=79.0889,
            observedAt="2026-09-13T12:00:00.000Z",
            frp=45.5,
            brightness=320.1,
            confidence="nominal",
            satellite="N20",
            sensor="noaa20",
            daynight="D",
            source="firms",
        )
        inserted, _ = repo.bulk_insert_ignore_duplicates(db_session, [obs])
        assert inserted == 1

        fetched = repo.get_by_id(db_session, "obs-1")
        assert fetched is not None
        assert fetched.id == "obs-1"
        assert fetched.frp == 45.5

    def test_bulk_insert_ignore_duplicates(self, db_session):
        repo = ObservationRepository()
        items = [
            Observation(
                id="obs-dup-1",
                latitude=21.1,
                longitude=79.1,
                observedAt="2026-09-13T10:00:00.000Z",
                frp=30.0,
                source="firms",
            ),
            Observation(
                id="obs-dup-2",
                latitude=21.2,
                longitude=79.2,
                observedAt="2026-09-13T11:00:00.000Z",
                frp=50.0,
                source="firms",
            ),
        ]
        inserted, dups = repo.bulk_insert_ignore_duplicates(db_session, items)
        assert inserted == 2
        assert dups == 0
        assert repo.count(db_session) == 2

        # Re-insert with 1 existing and 1 new
        items2 = [
            Observation(
                id="obs-dup-1",  # duplicate
                latitude=21.1,
                longitude=79.1,
                observedAt="2026-09-13T10:00:00.000Z",
                frp=30.0,
                source="firms",
            ),
            Observation(
                id="obs-dup-3",  # new
                latitude=21.3,
                longitude=79.3,
                observedAt="2026-09-13T12:00:00.000Z",
                frp=70.0,
                source="firms",
            ),
        ]
        inserted2, dups2 = repo.bulk_insert_ignore_duplicates(db_session, items2)
        assert inserted2 == 1
        assert dups2 == 1
        assert repo.count(db_session) == 3

    def test_get_near_location_haversine_filtering(self, db_session):
        repo = ObservationRepository()
        # Nagpur center
        center_lat, center_lon = 21.1466, 79.0889

        near_item = Observation(
            id="obs-near",
            latitude=21.1500,  # ~0.5 km away
            longitude=79.0900,
            observedAt="2026-09-13T12:00:00.000Z",
            frp=40.0,
            source="firms",
        )
        far_item = Observation(
            id="obs-far",
            latitude=21.5000,  # ~40 km away
            longitude=79.0889,
            observedAt="2026-09-13T12:00:00.000Z",
            frp=80.0,
            source="firms",
        )
        repo.bulk_insert_ignore_duplicates(db_session, [near_item, far_item])

        near_results = repo.get_near_location(
            db_session, latitude=center_lat, longitude=center_lon, radius_km=5.0
        )
        assert len(near_results) == 1
        assert near_results[0].id == "obs-near"

    def test_provenance_preservation(self, db_session):
        repo = ObservationRepository()
        items = [
            Observation(
                id="prov-manual",
                latitude=21.0,
                longitude=79.0,
                observedAt="2026-09-13T09:00:00.000Z",
                frp=15.0,
                source="manual",
            ),
            Observation(
                id="prov-imported",
                latitude=21.01,
                longitude=79.01,
                observedAt="2026-09-13T09:30:00.000Z",
                frp=25.0,
                source="imported",
            ),
            Observation(
                id="prov-demo",
                latitude=21.02,
                longitude=79.02,
                observedAt="2026-09-13T10:00:00.000Z",
                frp=35.0,
                source="demo",
            ),
        ]
        repo.bulk_insert_ignore_duplicates(db_session, items)
        for item in items:
            fetched = repo.get_by_id(db_session, item.id)
            assert fetched is not None
            assert fetched.source == item.source
            assert fetched.source != "firms"


@pytest.mark.asyncio
class TestObservationServiceAndRoutes:
    async def test_ingest_observations_api(self, client):
        import uuid
        test_id = f"ingest-api-{uuid.uuid4()}"
        payload = [
            {
                "id": test_id,
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-13T12:00:00.000Z",
                "frp": 55.0,
                "source": "imported",
            }
        ]
        resp = await client.post("/api/v1/observations", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["inserted"] >= 1

    async def test_manual_observation_api(self, client):
        import uuid
        test_id = f"manual-test-{uuid.uuid4()}"
        payload = {
            "id": test_id,
            "latitude": 22.5000,
            "longitude": 80.5000,
            "observedAt": "2026-09-13T14:30:00.000Z",
            "frp": 92.5,
            "brightness": 340.0,
            "source": "manual",
        }
        resp = await client.post("/api/v1/observations/manual", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "manual"
        assert data["frp"] == 92.5
        assert data["id"] == test_id

    async def test_get_observations_endpoint(self, client):
        resp = await client.get("/api/v1/observations?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
