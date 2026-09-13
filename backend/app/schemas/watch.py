"""
Pydantic schemas for monitored watch locations.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class WatchCreate(BaseModel):
    """Payload for creating a new monitored site."""

    name: str = Field(..., min_length=1, max_length=128)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(
        5.0, alias="radiusKm", serialization_alias="radiusKm", ge=0.5, le=50.0
    )
    frp_threshold: float = Field(
        ..., alias="frpThreshold", serialization_alias="frpThreshold", ge=0.0
    )
    risk_threshold: int = Field(
        50, alias="riskThreshold", serialization_alias="riskThreshold", ge=0, le=100
    )
    enabled: bool = True

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class WatchUpdate(BaseModel):
    """Payload for updating an existing monitored site."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    radius_km: Optional[float] = Field(
        None, alias="radiusKm", serialization_alias="radiusKm", ge=0.5, le=50.0
    )
    frp_threshold: Optional[float] = Field(
        None, alias="frpThreshold", serialization_alias="frpThreshold", ge=0.0
    )
    risk_threshold: Optional[int] = Field(
        None, alias="riskThreshold", serialization_alias="riskThreshold", ge=0, le=100
    )
    enabled: Optional[bool] = None

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class WatchResponse(BaseModel):
    """Response model representing a monitored site."""

    id: str
    name: str
    latitude: float
    longitude: float
    radius_km: float = Field(..., alias="radiusKm", serialization_alias="radiusKm")
    frp_threshold: float = Field(..., alias="frpThreshold", serialization_alias="frpThreshold")
    risk_threshold: int = Field(..., alias="riskThreshold", serialization_alias="riskThreshold")
    enabled: bool
    created_at: str = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt", serialization_alias="updatedAt")
    last_checked_at: Optional[str] = Field(
        None, alias="lastCheckedAt", serialization_alias="lastCheckedAt"
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
