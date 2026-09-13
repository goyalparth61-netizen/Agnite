"""
API endpoint tests for POST /api/v1/assistant/chat in AGNITE Phase 5A.

Verifies:
- 200 OK responses with matching schema contract
- Resolution via analysisId, selectedObservationId, coordinates
- Validation rejection of empty, whitespace, or oversized questions
- Conversation history ingestion
- Missing context handling without crashing
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.repositories.analysis_repository import AnalysisRepository
from app.db.repositories.observation_repository import ObservationRepository
from app.db.session import SessionLocal
from app.schemas.analysis import (
    AnalysisResult,
    AnalysisStatistics,
    Coordinates,
    ModelInfo,
    RiskResult,
)
from app.schemas.observation import Observation


@pytest.fixture
def persisted_analysis_id():
    """Create a sample analysis in the test database and return its ID."""
    db = SessionLocal()
    try:
        result = AnalysisResult(
            model=ModelInfo(
                name="agnite-heuristic-v1",
                version="1.0",
                method="heuristic",
            ),
            classification="Persistent Industrial Heat",
            status="classified",
            confidence=89.0,
            risk=RiskResult(index=40, level="Moderate", method="heuristic", factors=["Baseline variance within threshold"]),
            summary="Persistent thermal activity at industrial facility.",
            statistics=AnalysisStatistics(
                included=5,
                excluded=0,
                distinct_times=5,
                span_hours=48.0,
                current_frp=32.0,
                baseline_frp=30.0,
                change_percent=6.7,
                persistence=82.0,
                center=Coordinates(latitude=21.1466, longitude=79.0889),
            ),
        )
        record = AnalysisRepository.create(db, result=result, selected_observation_id="test-obs-api")
        return record.id
    finally:
        db.close()


@pytest.mark.asyncio
class TestAssistantApiEndpoints:
    async def test_chat_with_analysis_id_success(self, client: AsyncClient, persisted_analysis_id: str):
        """Successfully query assistant using analysisId."""
        payload = {
            "question": "Why did AGNITE classify this hotspot as Persistent Industrial Heat?",
            "analysisId": persisted_analysis_id,
        }
        res = await client.post("/api/v1/assistant/chat", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "answer" in data
        assert data["mode"] == "deterministic"
        assert data["grounded"] is True
        assert data["analysisId"] == persisted_analysis_id
        assert data["classification"] == "Persistent Industrial Heat"
        assert data["risk"] == 40
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
        assert isinstance(data["evidenceUsed"], list)
        assert isinstance(data["suggestedQuestions"], list)

    async def test_chat_with_coordinates_success(self, client: AsyncClient):
        """Query assistant with geographical coordinates."""
        payload = {
            "question": "What is the historical baseline around here?",
            "latitude": 21.1466,
            "longitude": 79.0889,
        }
        res = await client.post("/api/v1/assistant/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "answer" in data
        assert data["grounded"] is True

    async def test_chat_with_conversation_history(self, client: AsyncClient, persisted_analysis_id: str):
        """Query assistant including prior conversation history turns."""
        payload = {
            "question": "What precautions should authorities take?",
            "analysisId": persisted_analysis_id,
            "conversationHistory": [
                {"role": "user", "text": "Why is the risk moderate?"},
                {"role": "assistant", "text": "The risk index is 40/100 due to baseline variance."},
            ],
        }
        res = await client.post("/api/v1/assistant/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "precautions" in data["answer"].lower() or "personnel" in data["answer"].lower()

    async def test_empty_question_rejected(self, client: AsyncClient):
        """Empty question string returns 422 Unprocessable Entity."""
        res = await client.post("/api/v1/assistant/chat", json={"question": ""})
        assert res.status_code == 422

    async def test_whitespace_question_rejected(self, client: AsyncClient):
        """Whitespace-only question string returns 422."""
        res = await client.post("/api/v1/assistant/chat", json={"question": "   \n\t  "})
        assert res.status_code == 422

    async def test_overlength_question_rejected(self, client: AsyncClient):
        """Question exceeding 1,000 characters returns 422."""
        res = await client.post("/api/v1/assistant/chat", json={"question": "a" * 1001})
        assert res.status_code == 422

    async def test_invalid_coordinates_rejected(self, client: AsyncClient):
        """Latitude out of range returns 422."""
        res = await client.post(
            "/api/v1/assistant/chat",
            json={"question": "Check this location", "latitude": 95.0, "longitude": 79.0},
        )
        assert res.status_code == 422

    async def test_unresolved_reference_returns_grounded_message(self, client: AsyncClient):
        """When no reference is given, returns 200 with clear guidance rather than failing."""
        res = await client.post("/api/v1/assistant/chat", json={"question": "Explain this site"})
        assert res.status_code == 200
        data = res.json()
        assert "does not currently have a selected hotspot" in data["answer"]
        assert data["grounded"] is True
