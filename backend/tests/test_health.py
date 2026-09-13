"""
Tests for health endpoints.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_compat(client):
    """GET /api/health returns the legacy response shape."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "agnite"
    assert data["firms"] == "public-nasa-downloads"


@pytest.mark.asyncio
async def test_health_v1(client):
    """GET /api/v1/health returns extended status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert isinstance(data["database"], bool)
    assert isinstance(data["nasa_configured"], bool)
    assert isinstance(data["ml_classifier_loaded"], bool)
    assert isinstance(data["recurrence_model_loaded"], bool)
    assert isinstance(data["llm_enabled"], bool)
    assert isinstance(data["background_jobs_enabled"], bool)
    # Must never expose keys
    assert "api_key" not in str(data).lower()
    assert "password" not in str(data).lower()
