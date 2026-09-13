"""
FIRMS feed response schemas.

These must produce JSON that passes the React frontend's strict
validation in useFirmsFeed.ts (lines 14-16):

- observations must be Array
- fetchedAt must parse as a Date
- sensor must === requested sensor
- windowHours must === requested hours
- stale and cached must be boolean
- every observation.source must be "firms"
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FirmsObservation(BaseModel):
    """
    Single observation in the FIRMS feed response.

    Field names are camelCase to match the frontend's TypeScript Observation
    interface extended with sensor/confidence.
    """

    id: str
    latitude: float
    longitude: float
    observed_at: str = Field(serialization_alias="observedAt")
    frp: float
    brightness: Optional[float] = None
    source: str = "firms"
    sensor: str = ""
    confidence: Optional[str | float] = None

    model_config = {
        "populate_by_name": True,
    }


class FirmsFeedResponse(BaseModel):
    """
    Complete FIRMS feed response.

    Every field name uses camelCase serialization aliases so the JSON
    output matches what useFirmsFeed.ts validates.
    """

    observations: list[FirmsObservation]
    fetched_at: str = Field(serialization_alias="fetchedAt")
    latest_observation: Optional[str] = Field(
        default=None, serialization_alias="latestObservation"
    )
    source_url: str = Field(serialization_alias="sourceUrl")
    sensor: str
    window_hours: int = Field(serialization_alias="windowHours")
    coverage: str
    stale: bool
    cached: bool
    warning: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }
