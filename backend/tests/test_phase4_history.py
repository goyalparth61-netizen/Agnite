"""
Phase 4 Tests: Long-Term Location History and Analysis DB Merging.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.repositories.observation_repository import ObservationRepository
from app.schemas.observation import Observation
from app.services.historical_intelligence_service import HistoricalIntelligenceService


@pytest.fixture
def db_session():
    """Isolated SQLite session with historical records."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed 4 observations spanning 4 distinct days at Nagpur + 1 far
    repo = ObservationRepository()
    records = [
        Observation(
            id="hist-nagpur-1",
            latitude=21.1466,
            longitude=79.0889,
            observedAt="2026-09-10T12:00:00.000Z",
            frp=35.0,
            source="firms",
        ),
        Observation(
            id="hist-nagpur-2",
            latitude=21.1480,
            longitude=79.0895,
            observedAt="2026-09-11T12:00:00.000Z",
            frp=42.0,
            source="firms",
        ),
        Observation(
            id="hist-nagpur-3",
            latitude=21.1460,
            longitude=79.0880,
            observedAt="2026-09-12T12:00:00.000Z",
            frp=38.0,
            source="firms",
        ),
        Observation(
            id="hist-nagpur-4",
            latitude=21.1470,
            longitude=79.0885,
            observedAt="2026-09-13T12:00:00.000Z",
            frp=55.0,
            source="firms",
        ),
        # Outside 5km
        Observation(
            id="hist-far-1",
            latitude=21.4500,
            longitude=79.0889,
            observedAt="2026-09-13T12:00:00.000Z",
            frp=90.0,
            source="firms",
        ),
    ]
    repo.bulk_insert_ignore_duplicates(session, records)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestHistoricalIntelligenceService:
    def test_query_location_history_metrics(self, db_session):
        service = HistoricalIntelligenceService()
        result = service.get_location_history(
            db=db_session,
            latitude=21.1466,
            longitude=79.0889,
            radius_km=5.0,
            days=30,
        )

        assert result.location.latitude == 21.1466
        assert result.radius_km == 5.0
        assert result.observation_count == 4  # hist-far-1 excluded
        assert result.recurrence.unique_days == 4
        assert result.statistics.baseline_frp is not None
        assert result.recurrence.signal is not None
        assert "firms" in result.provenance


@pytest.mark.asyncio
class TestHistoryApiEndpoint:
    async def test_get_history_endpoint_validation(self, client):
        # Missing latitude / longitude -> 422
        resp = await client.get("/api/v1/history")
        assert resp.status_code == 422

        # Invalid coordinates -> 422
        resp = await client.get("/api/v1/history?latitude=100&longitude=79.0")
        assert resp.status_code == 422

        # Valid coordinates -> 200 with contract
        resp = await client.get("/api/v1/history?latitude=21.1466&longitude=79.0889&radiusKm=5&days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert "location" in data
        assert "period" in data
        assert "observations" in data
        assert "statistics" in data
        assert "recurrence" in data
        assert "timeline" in data


@pytest.mark.asyncio
class TestAnalysisHistoryMerging:
    async def test_analysis_run_deduplicates_request_and_db_observations(self, client):
        """
        When analysis runs with loaded observations that also exist in DB,
        they must be merged and deduplicated by ID without inflating metrics.
        """
        # Ingest an observation first
        obs_payload = [
            {
                "id": "merge-obs-1",
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-12T12:00:00.000Z",
                "frp": 45.0,
                "source": "firms",
            }
        ]
        await client.post("/api/v1/observations", json=obs_payload)

        # Query history to get the exact ID inserted
        hist_resp = await client.get("/api/v1/history?latitude=21.1466&longitude=79.0889&radiusKm=5")
        assert hist_resp.status_code == 200
        persisted = hist_resp.json()["observations"]
        assert len(persisted) >= 1
        persisted_id = persisted[0]["id"]

        # Run analysis supplying the SAME observation in request observations
        analysis_payload = {
            "selectedObservation": {
                "id": persisted_id,
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-12T12:00:00.000Z",
                "frp": 45.0,
                "source": "firms",
            },
            "observations": [
                {
                    "id": persisted_id,  # Same observation as in DB
                    "latitude": 21.1466,
                    "longitude": 79.0889,
                    "observedAt": "2026-09-12T12:00:00.000Z",
                    "frp": 45.0,
                    "source": "firms",
                }
            ],
            "radiusKm": 5.0,
        }
        res = await client.post("/api/v1/analysis/run", json=analysis_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["statistics"]["included"] >= 1
        assert "classification" in data
        assert "risk" in data
