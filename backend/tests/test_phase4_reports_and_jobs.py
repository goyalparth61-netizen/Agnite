"""
Phase 4 Tests: Saved Reports, Analysis Records, Background Jobs, and Resilience.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.report import SavedReportModel
from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.report_repository import ReportRepository
from app.jobs.firms_sync import run_firms_sync
from app.jobs.watch_scanner import run_watch_scanner
from app.schemas.report import ReportCreate


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


class TestReportRepositoryAndAnalyses:
    def test_report_crud_and_json_integrity(self, db_session):
        repo = ReportRepository()
        report_in = ReportCreate(
            id="report-test-1",
            label="21.1466, 79.0889",
            latitude=21.1466,
            longitude=79.0889,
            classification="Persistent Industrial Heat",
            confidence=0.86,
            risk=42,
            summary="Identified recurring industrial thermal source.",
            report={
                "statistics": {"currentFrp": 45.0, "baselineFrp": 38.0},
                "evidence": [{"label": "FRP", "value": "45.0 MW"}],
            },
            context={"landCover": "industrial", "industrialDistanceKm": 0.5},
            observations=[
                {
                    "id": "obs-1",
                    "latitude": 21.1466,
                    "longitude": 79.0889,
                    "observedAt": "2026-09-13T12:00:00.000Z",
                    "frp": 45.0,
                    "source": "firms",
                }
            ],
        )

        created = repo.create(db_session, report_in)
        assert created.id == "report-test-1"
        assert created.schema_version == "1.0"
        assert created.classification == "Persistent Industrial Heat"

        fetched = repo.get_by_id(db_session, "report-test-1")
        assert fetched is not None
        assert fetched.summary == report_in.summary

        # Delete
        assert repo.delete(db_session, "report-test-1") is True
        assert repo.get_by_id(db_session, "report-test-1") is None

    def test_analysis_record_persistence(self, db_session):
        from app.schemas.analysis import (
            AnalysisResult,
            AnalysisStatistics,
            Coordinates,
            ModelInfo,
            RiskResult,
        )
        repo = AnalysisRepository()
        result = AnalysisResult(
            model=ModelInfo(
                name="agnite-heuristic-v1",
                version="1.0",
                training_source="heuristic",
                sample_count=100,
                synthetic_validation_accuracy=0.88,
                limitations=[],
            ),
            classification="Persistent Industrial Heat",
            status="classified",
            confidence=0.88,
            risk=RiskResult(index=45, level="Moderate", method="heuristic"),
            summary="Persistent thermal detection.",
            statistics=AnalysisStatistics(
                included=5,
                excluded=0,
                distinct_times=5,
                span_hours=24.0,
                current_frp=45.0,
                baseline_frp=38.0,
                change_percent=18.4,
                persistence=85.0,
                center=Coordinates(latitude=21.1466, longitude=79.0889),
            ),
        )
        record = repo.create(db_session, result, selected_observation_id="obs-123")
        assert record.id is not None
        assert record.selected_observation_id == "obs-123"

        fetched = repo.get_by_id(db_session, record.id)
        assert fetched is not None
        assert fetched.classification == "Persistent Industrial Heat"


@pytest.mark.asyncio
class TestReportsApi:
    async def test_report_api_lifecycle(self, client):
        payload = {
            "id": "api-rep-1",
            "label": "21.1466, 79.0889",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "classification": "Industrial Fire",
            "confidence": 0.91,
            "risk": 75,
            "summary": "Sudden high-FRP spike detected.",
            "report": {"classification": "Industrial Fire"},
            "context": {"landCover": "industrial"},
            "observations": [],
        }

        # Create
        res = await client.post("/api/v1/reports", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == "api-rep-1"

        # List
        res = await client.get("/api/v1/reports")
        assert res.status_code == 200
        reports = res.json()["reports"]
        assert any(r["id"] == "api-rep-1" for r in reports)

        # Get
        res = await client.get("/api/v1/reports/api-rep-1")
        assert res.status_code == 200
        assert res.json()["classification"] == "Industrial Fire"

        # Delete
        res = await client.delete("/api/v1/reports/api-rep-1")
        assert res.status_code == 204

        # 404 after delete
        res = await client.get("/api/v1/reports/api-rep-1")
        assert res.status_code == 404


@pytest.mark.asyncio
class TestBackgroundJobsAndHealth:
    async def test_health_reports_database_true(self, client):
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["database"] is True

    async def test_firms_sync_job(self):
        result = await run_firms_sync(sensor="noaa20", hours=24)
        assert "fetched" in result
        assert "inserted" in result
        assert "duplicates" in result
        assert "errors" in result


class TestWatchScannerSync:
    def test_watch_scanner_job(self):
        result = run_watch_scanner()
        assert "alerts_generated" in result
        assert result["status"] == "completed"
