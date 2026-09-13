"""
Unit tests for OSMSpatialContextProvider and spatial context caching.
Tests cache keys with radius, separate radii behavior, 1km/5km/10km counts,
confidence scoring, field-aware provenance, and graceful degradation.
"""

from unittest.mock import AsyncMock, patch
import pytest
from app.providers.osm.client import OsmProviderError
from app.services.spatial_context_service import OSMSpatialContextProvider


@pytest.mark.asyncio
async def test_spatial_context_cache_and_radius_isolation():
    """Verify that different radiusKm produce different cache keys and never share incorrect cached results."""
    mock_client = AsyncMock()
    mock_client.fetch_infrastructure.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 21.147,
                "lon": 79.089,
                "tags": {"industrial": "factory", "name": "Nagpur Forge"},
            }
        ]
    }

    provider = OSMSpatialContextProvider(osm_client=mock_client, cache_ttl_seconds=3600)

    # 1. First call at radius 10 km -> cache miss
    ctx_10km = await provider.get_context(21.1466, 79.0889, radius_km=10.0)
    assert ctx_10km.cached is False
    assert mock_client.fetch_infrastructure.call_count == 1
    assert ctx_10km.search_radius_km == 10.0

    # 2. Second call with SAME coordinates and SAME radius -> cache hit
    ctx_10km_cached = await provider.get_context(21.1466, 79.0889, radius_km=10.0)
    assert ctx_10km_cached.cached is True
    assert mock_client.fetch_infrastructure.call_count == 1  # No additional network call

    # 3. Third call with SAME coordinates but DIFFERENT radius (5.0 km) -> MUST query separately
    ctx_5km = await provider.get_context(21.1466, 79.0889, radius_km=5.0)
    assert ctx_5km.cached is False
    assert mock_client.fetch_infrastructure.call_count == 2  # Queried again because radius changed!
    assert ctx_5km.search_radius_km == 5.0


@pytest.mark.asyncio
async def test_spatial_context_distance_counts_and_booleans():
    """Verify within-1km, 5km, and 10km counts and boolean flags derived locally in Python."""
    mock_client = AsyncMock()
    # 3 elements at varying distances:
    # elem 1: ~100m away (<= 1km)
    # elem 2: ~3km away (> 1km, <= 5km)
    # elem 3: ~8km away (> 5km, <= 10km)
    mock_client.fetch_infrastructure.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 10,
                "lat": 21.147,
                "lon": 79.089,
                "tags": {"man_made": "flare", "name": "Gas Flare"},
            },
            {
                "type": "node",
                "id": 20,
                "lat": 21.170,
                "lon": 79.095,
                "tags": {"power": "plant", "name": "Thermal Power Plant"},
            },
            {
                "type": "node",
                "id": 30,
                "lat": 21.210,
                "lon": 79.110,
                "tags": {"landuse": "industrial"},
            },
        ]
    }

    provider = OSMSpatialContextProvider(osm_client=mock_client)
    ctx = await provider.get_context(21.1466, 79.0889, radius_km=10.0)

    # Local Python counts
    assert ctx.industrial_feature_count == 3
    assert ctx.count_within_1km == 1
    assert ctx.count_within_5km == 2
    assert ctx.count_within_10km == 3

    assert ctx.industrial_within_1km is True
    assert ctx.industrial_within_5km is True
    assert ctx.industrial_within_10km is True

    assert ctx.mapped_flare_nearby is True
    assert ctx.power_infrastructure_nearby is True
    assert ctx.mapped_chimney_nearby is False

    assert ctx.industrial_distance_km is not None
    assert ctx.industrial_distance_km < 0.2
    assert ctx.nearest_industrial_feature is not None
    assert ctx.nearest_industrial_feature.name == "Gas Flare"


@pytest.mark.asyncio
async def test_spatial_context_field_aware_provenance():
    """Verify field-aware provenance is attached to SpatialContext."""
    mock_client = AsyncMock()
    mock_client.fetch_infrastructure.return_value = {
        "elements": [
            {
                "type": "node",
                "id": 10,
                "lat": 21.147,
                "lon": 79.089,
                "tags": {"man_made": "works"},
            }
        ]
    }

    provider = OSMSpatialContextProvider(osm_client=mock_client)
    ctx = await provider.get_context(21.1466, 79.0889)

    assert "industrialDistanceKm" in ctx.provenance
    assert ctx.provenance["industrialDistanceKm"] == "osm"
    assert ctx.provenance["countWithin1Km"] == "osm"
    assert ctx.provenance["countWithin5Km"] == "osm"
    assert ctx.provenance["powerInfrastructureNearby"] == "osm"


@pytest.mark.asyncio
async def test_spatial_context_graceful_degradation_on_error():
    """Verify provider does not throw when Overpass fails, but returns degraded context with warnings."""
    mock_client = AsyncMock()
    mock_client.fetch_infrastructure.side_effect = OsmProviderError("503 Service Unavailable", status_code=503)

    provider = OSMSpatialContextProvider(osm_client=mock_client)
    ctx = await provider.get_context(21.1466, 79.0889)

    assert ctx.industrial_distance_km is None
    assert ctx.nearest_industrial_feature is None
    assert ctx.industrial_feature_count == 0
    assert ctx.context_confidence == 0.0
    assert len(ctx.warnings) > 0
    assert "unavailable" in ctx.warnings[0].lower()
    assert ctx.provenance.get("industrialDistanceKm") == "unavailable"
