"""
Base Observation schema used throughout the AGNITE backend.

This is the normalized internal domain model that all providers
(NASA, OSM, CSV import, manual entry) must produce.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """
    Normalized thermal observation.

    All field names use camelCase aliases to match the React frontend's
    TypeScript interfaces.  Python code uses snake_case internally.
    """

    id: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    observed_at: str = Field(alias="observedAt", serialization_alias="observedAt")
    frp: float = Field(ge=0, le=1_000_000)
    brightness: Optional[float] = None
    source: Literal["demo", "imported", "manual", "firms"]
    sensor: Optional[str] = None
    confidence: Optional[str | float] = None

    # Future normalized fields (Phase 2+)
    satellite: Optional[str] = None
    instrument: Optional[str] = None
    daynight: Optional[str] = None
    metadata: Optional[dict] = None

    model_config = {
        "populate_by_name": True,
    }
