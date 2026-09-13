"""
End-to-end tests for POST /api/v1/analysis/run endpoint.
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


def sample_obs_list():
    return [
        {
            "id": "firms-1",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "observedAt": "2026-09-10T12:00:00.000Z",
            "frp": 20.0,
            "source": "firms",
        },
        {
            "id": "firms-2",
            "latitude": 21.1470,
            "longitude": 79.0890,
            "observedAt": "2026-09-11T12:00:00.000Z",
            "frp": 22.0,
            "source": "firms",
        },
        {
            "id": "firms-3",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "observedAt": "2026-09-12T12:00:00.000Z",
            "frp": 21.0,
            "source": "firms",
        },
        {
            "id": "firms-4",
            "latitude": 21.1465,
            "longitude": 79.0888,
            "observedAt": "2026-09-13T06:00:00.000Z",
            "frp": 25.0,
            "source": "firms",
        },
        {
            "id": "firms-5",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "observedAt": "2026-09-13T12:00:00.000Z",
            "frp": 28.0,
            "source": "firms",
        },
    ]


@pytest.mark.asyncio
async def test_analysis_run_valid_firms(client: AsyncClient):
    payload = {
        "selectedObservation": {
            "id": "firms-5",
            "latitude": 21.1466,
            "longitude": 79.0889,
            "observedAt": "2026-09-13T12:00:00.000Z",
            "frp": 28.0,
            "source": "firms",
        },
        "observations": sample_obs_list(),
        "radiusKm": 5.0,
        "context": {
            "landCover": "industrial",
            "industrialDistanceKm": 0.5,
            "windKph": 15.0,
        },
    }

    response = await client.post("/api/v1/analysis/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify essential frontend contract fields
    assert "model" in data
    assert data["model"]["name"] == "agnite-heuristic-v1"
    assert data["model"]["method"] == "heuristic"

    assert "classification" in data
    assert data["classification"] in (
        "Persistent Industrial Heat",
        "Industrial Fire",
        "Forest / Natural Fire",
        "Other Thermal Anomaly",
        "Insufficient evidence",
    )
    assert "status" in data
    assert "risk" in data
    assert 0 <= data["risk"]["index"] <= 100
    assert data["risk"]["level"] in ("Low", "Moderate", "High", "Critical")

    assert "evidence" in data
    assert isinstance(data["evidence"], list)
    assert len(data["evidence"]) > 0

    assert "history" in data
    assert len(data["history"]) == 5
    assert "observedAt" in data["history"][0]
    assert "frp" in data["history"][0]

    assert "statistics" in data
    assert data["statistics"]["included"] == 5
    assert data["statistics"]["distinctTimes"] == 5
    assert "center" in data["statistics"]

    assert "scenarios" in data
    assert len(data["scenarios"]) == 3

    assert "contributions" in data
    assert "warnings" in data
    assert "recurrenceSignal" in data


@pytest.mark.asyncio
async def test_analysis_run_imported_and_manual_sources(client: AsyncClient):
    obs = sample_obs_list()
    obs[0]["source"] = "manual"
    obs[1]["source"] = "imported"
    obs[2]["source"] = "demo"

    payload = {
        "observations": obs,
        "radiusKm": 5.0,
    }

    response = await client.post("/api/v1/analysis/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "abstained"  # missing context -> abstained
    assert any("DEMO / SIMULATION" in w for w in data["warnings"])
    assert any("Uploaded/manual" in w for w in data["warnings"])


@pytest.mark.asyncio
async def test_analysis_run_empty_observations_rejected(client: AsyncClient):
    payload = {
        "observations": [],
        "radiusKm": 5.0,
    }
    response = await client.post("/api/v1/analysis/run", json=payload)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_analysis_run_invalid_selected_coordinates(client: AsyncClient):
    payload = {
        "selectedObservation": {
            "id": "bad-coord",
            "latitude": 999.0,  # Invalid lat
            "longitude": 79.0889,
            "observedAt": "2026-09-13T12:00:00.000Z",
            "frp": 28.0,
            "source": "firms",
        },
        "observations": sample_obs_list(),
    }
    response = await client.post("/api/v1/analysis/run", json=payload)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_analysis_run_limit_exceeded(client: AsyncClient):
    # > 5000 observations rejected
    too_many = [sample_obs_list()[0] for _ in range(5001)]
    payload = {
        "observations": too_many,
    }
    response = await client.post("/api/v1/analysis/run", json=payload)
    assert response.status_code in (400, 422)
