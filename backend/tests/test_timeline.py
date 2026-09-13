"""
Tests for POST /api/v1/timeline endpoint.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_timeline_endpoint(client: AsyncClient):
    payload = {
        "observations": [
            {
                "id": "t1",
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-10T12:00:00.000Z",
                "frp": 15.0,
                "source": "firms",
            },
            {
                "id": "t2",
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-12T12:00:00.000Z",
                "frp": 25.0,
                "source": "firms",
            },
            {
                "id": "t3",
                "latitude": 21.1466,
                "longitude": 79.0889,
                "observedAt": "2026-09-13T12:00:00.000Z",
                "frp": 35.0,
                "source": "firms",
            },
        ],
        "radiusKm": 5.0,
    }

    response = await client.post("/api/v1/timeline", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "timeline" in data
    assert len(data["timeline"]) == 3
    assert data["timeline"][0]["frp"] == 15.0
    assert data["timeline"][2]["frp"] == 35.0
    assert "statistics" in data
    assert data["statistics"]["distinctTimes"] == 3
    assert "recurrenceMetrics" in data
    assert data["recurrenceMetrics"]["uniqueDays"] == 3
