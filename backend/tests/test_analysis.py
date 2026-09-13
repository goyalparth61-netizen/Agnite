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


@pytest.mark.asyncio
async def test_analysis_run_spatial_context_attached_and_provenance(client: AsyncClient):
    """Verify Phase 3: spatialContext is attached to AnalysisResult with field-aware provenance."""
    from unittest.mock import AsyncMock
    from app.schemas.context import SpatialContext
    from app.services.spatial_context_service import set_spatial_context_provider
    from app.utils.dates import utc_now_iso

    mock_provider = AsyncMock()
    mock_provider.get_context.return_value = SpatialContext(
        latitude=21.1466,
        longitude=79.0889,
        searchRadiusKm=10.0,
        industrialDistanceKm=0.35,
        nearestIndustrialFeature={
            "name": "Nagpur Smelter",
            "featureType": "metal_works",
            "distanceKm": 0.35,
        },
        industrialFeatureCount=4,
        industrialWithin1Km=True,
        industrialWithin5Km=True,
        industrialWithin10Km=True,
        countWithin1Km=2,
        countWithin5Km=4,
        countWithin10Km=4,
        powerInfrastructureNearby=True,
        mappedFlareNearby=True,
        mappedChimneyNearby=False,
        contextConfidence=80.0,
        source="osm",
        retrievedAt=utc_now_iso(),
        cached=False,
        provenance={"industrialDistanceKm": "osm"},
        features=[],
        warnings=["OpenStreetMap coverage is community-contributed."],
    )

    set_spatial_context_provider(mock_provider)

    try:
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
                # industrialDistanceKm left None to test automatic OSM enrichment
                "windKph": 12.0,
            },
        }

        response = await client.post("/api/v1/analysis/run", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Phase 3 spatialContext field checks
        assert "spatialContext" in data
        s_ctx = data["spatialContext"]
        assert s_ctx is not None
        assert s_ctx["industrialDistanceKm"] == 0.35
        assert s_ctx["industrialWithin1Km"] is True
        assert s_ctx["countWithin1Km"] == 2
        assert s_ctx["countWithin5Km"] == 4
        assert s_ctx["mappedFlareNearby"] is True
        assert s_ctx["contextConfidence"] == 80.0

        # Field-aware provenance
        assert "provenance" in s_ctx
        assert s_ctx["provenance"]["industrialDistanceKm"] == "osm"  # Enriched from OSM
        assert s_ctx["provenance"]["landCover"] == "manual"          # From user input
        assert s_ctx["provenance"]["windKph"] == "weather"           # From user weather input

        # Evidence checks
        evidence_labels = [e["label"] for e in data["evidence"]]
        assert "Spatial context" in evidence_labels
        assert "Industrial environment" in evidence_labels
        assert "Thermal infrastructure" in evidence_labels
        assert "Context source" in evidence_labels

    finally:
        set_spatial_context_provider(None)


@pytest.mark.asyncio
async def test_analysis_run_continues_when_overpass_unavailable(client: AsyncClient):
    """Verify Requirement 8: If Overpass is unavailable, analysis must continue successfully."""
    from unittest.mock import AsyncMock
    from app.providers.osm.client import OsmProviderError
    from app.services.spatial_context_service import OSMSpatialContextProvider, set_spatial_context_provider

    mock_client = AsyncMock()
    mock_client.fetch_infrastructure.side_effect = OsmProviderError("504 Gateway Timeout", status_code=504)

    provider = OSMSpatialContextProvider(osm_client=mock_client)
    set_spatial_context_provider(provider)

    try:
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
                "industrialDistanceKm": 1.2,
            },
        }

        # Analysis must not fail (must return 200)
        response = await client.post("/api/v1/analysis/run", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "classification" in data
        assert "risk" in data
        assert "spatialContext" in data
        s_ctx = data["spatialContext"]
        assert s_ctx is not None
        assert any("unavailable" in w.lower() for w in s_ctx["warnings"])
        assert any("unavailable" in w.lower() for w in data["warnings"])

    finally:
        set_spatial_context_provider(None)
