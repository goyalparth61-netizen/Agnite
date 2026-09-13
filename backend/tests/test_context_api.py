"""
End-to-end tests for GET /api/v1/context endpoint.
"""

from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.context import SpatialContext
from app.services.spatial_context_service import set_spatial_context_provider
from app.utils.dates import utc_now_iso


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
async def test_get_context_success(client: AsyncClient):
    mock_provider = AsyncMock()
    mock_provider.get_context.return_value = SpatialContext(
        latitude=21.1466,
        longitude=79.0889,
        searchRadiusKm=10.0,
        industrialDistanceKm=0.45,
        nearestIndustrialFeature={
            "name": "Steel Mill",
            "featureType": "metal_works",
            "distanceKm": 0.45,
            "osmId": "node/123",
        },
        industrialFeatureCount=2,
        industrialWithin1Km=True,
        industrialWithin5Km=True,
        industrialWithin10Km=True,
        countWithin1Km=1,
        countWithin5Km=2,
        countWithin10Km=2,
        powerInfrastructureNearby=False,
        mappedFlareNearby=False,
        mappedChimneyNearby=False,
        contextConfidence=75.0,
        source="osm",
        retrievedAt=utc_now_iso(),
        cached=False,
        provenance={"industrialDistanceKm": "osm"},
        features=[],
        warnings=[],
    )

    set_spatial_context_provider(mock_provider)

    try:
        response = await client.get("/api/v1/context?latitude=21.1466&longitude=79.0889&radiusKm=10.0")
        assert response.status_code == 200
        data = response.json()

        assert data["latitude"] == 21.1466
        assert data["longitude"] == 79.0889
        assert data["searchRadiusKm"] == 10.0
        assert data["industrialDistanceKm"] == 0.45
        assert data["industrialWithin1Km"] is True
        assert data["countWithin1Km"] == 1
        assert data["countWithin5Km"] == 2
        assert data["countWithin10Km"] == 2
        assert data["contextConfidence"] == 75.0
        assert data["source"] == "osm"
        assert "provenance" in data
        assert data["provenance"]["industrialDistanceKm"] == "osm"
        assert data["nearestIndustrialFeature"]["name"] == "Steel Mill"
    finally:
        set_spatial_context_provider(None)


@pytest.mark.asyncio
async def test_get_context_invalid_coordinates(client: AsyncClient):
    # Latitude > 90
    response = await client.get("/api/v1/context?latitude=999.0&longitude=79.0889")
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_get_context_radius_bounds(client: AsyncClient):
    # Radius > 25.0 km should fail validation (422)
    response = await client.get("/api/v1/context?latitude=21.1466&longitude=79.0889&radiusKm=50.0")
    assert response.status_code == 422

    # Radius < 0.5 km should fail validation (422)
    response = await client.get("/api/v1/context?latitude=21.1466&longitude=79.0889&radiusKm=0.1")
    assert response.status_code == 422
