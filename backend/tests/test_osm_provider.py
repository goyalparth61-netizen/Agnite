"""
Unit tests for OsmClient Overpass API client.
Tests query building, HTTP handling, timeout, 429 rate limit, 500 server error, and invalid JSON.
"""

import httpx
import pytest
from app.providers.osm.client import OsmClient, OsmProviderError, build_overpass_query


def test_build_overpass_query():
    query = build_overpass_query(21.1466, 79.0889, radius_km=10.0, limit=50)
    assert "[out:json]" in query
    assert "around:10000,21.1466,79.0889" in query
    assert 'nwr["landuse"="industrial"]' in query
    assert 'nwr["man_made"="flare"]' in query
    assert 'nwr["power"="plant"]' in query
    assert "out center tags 50;" in query


@pytest.mark.asyncio
async def test_osm_client_success():
    mock_elements = [
        {
            "type": "node",
            "id": 12345,
            "lat": 21.147,
            "lon": 79.089,
            "tags": {"man_made": "works", "name": "Test Factory"},
        }
    ]

    async def mock_handler(request: httpx.Request):
        return httpx.Response(200, json={"elements": mock_elements})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OsmClient(http_client=http_client)
        data = await client.fetch_infrastructure(21.1466, 79.0889, radius_km=5.0)
        assert "elements" in data
        assert len(data["elements"]) == 1
        assert data["elements"][0]["id"] == 12345


@pytest.mark.asyncio
async def test_osm_client_timeout():
    async def mock_handler(request: httpx.Request):
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OsmClient(http_client=http_client)
        with pytest.raises(OsmProviderError) as exc_info:
            await client.fetch_infrastructure(21.1466, 79.0889)
        assert "timed out" in exc_info.value.message


@pytest.mark.asyncio
async def test_osm_client_rate_limit_429():
    async def mock_handler(request: httpx.Request):
        return httpx.Response(429, text="Rate limit exceeded")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OsmClient(http_client=http_client)
        with pytest.raises(OsmProviderError) as exc_info:
            await client.fetch_infrastructure(21.1466, 79.0889)
        assert exc_info.value.status_code == 429
        assert "rate limit" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_osm_client_server_error_500():
    async def mock_handler(request: httpx.Request):
        return httpx.Response(504, text="Gateway Timeout")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OsmClient(http_client=http_client)
        with pytest.raises(OsmProviderError) as exc_info:
            await client.fetch_infrastructure(21.1466, 79.0889)
        assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_osm_client_malformed_json():
    async def mock_handler(request: httpx.Request):
        return httpx.Response(200, text="Not a JSON response")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = OsmClient(http_client=http_client)
        with pytest.raises(OsmProviderError) as exc_info:
            await client.fetch_infrastructure(21.1466, 79.0889)
        assert "malformed" in exc_info.value.message.lower()
