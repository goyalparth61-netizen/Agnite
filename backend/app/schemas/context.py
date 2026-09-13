"""
Schemas for OpenStreetMap / Overpass spatial context integration.

Matches the domain model defined in Phase 3 instructions, serializing to camelCase
for API and frontend compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.core.constants import CONTEXT_SOURCE_OSM, DEFAULT_OSM_SEARCH_RADIUS_KM


class OsmFeature(BaseModel):
    """Normalized OpenStreetMap feature representing nearby infrastructure."""

    osm_id: str = Field(..., alias="osmId", serialization_alias="osmId")
    osm_type: Literal["node", "way", "relation"] = Field(
        ..., alias="osmType", serialization_alias="osmType"
    )
    feature_type: str = Field(
        ...,
        alias="featureType",
        serialization_alias="featureType",
        description="Categorized infrastructure type (e.g., factory, industrial_area, power_plant, chimney, flare)",
    )
    name: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    distance_km: float = Field(
        ...,
        alias="distanceKm",
        serialization_alias="distanceKm",
        ge=0,
        description="Distance from query coordinates in kilometres",
    )
    tags: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class NearestFeatureSummary(BaseModel):
    """Summary of the closest mapped industrial/infrastructure feature."""

    name: Optional[str] = None
    feature_type: str = Field(
        ..., alias="featureType", serialization_alias="featureType"
    )
    distance_km: float = Field(
        ..., alias="distanceKm", serialization_alias="distanceKm", ge=0
    )
    osm_id: Optional[str] = Field(
        None, alias="osmId", serialization_alias="osmId"
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class SpatialContext(BaseModel):
    """Normalized spatial context around a hotspot coordinate."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    search_radius_km: float = Field(
        DEFAULT_OSM_SEARCH_RADIUS_KM,
        alias="searchRadiusKm",
        serialization_alias="searchRadiusKm",
    )
    industrial_distance_km: Optional[float] = Field(
        None,
        alias="industrialDistanceKm",
        serialization_alias="industrialDistanceKm",
        description="Distance to nearest industrial feature in km, or None if none mapped",
    )
    nearest_industrial_feature: Optional[NearestFeatureSummary] = Field(
        None,
        alias="nearestIndustrialFeature",
        serialization_alias="nearestIndustrialFeature",
    )
    industrial_feature_count: int = Field(
        0,
        alias="industrialFeatureCount",
        serialization_alias="industrialFeatureCount",
        ge=0,
    )
    industrial_within_1km: bool = Field(
        False,
        alias="industrialWithin1Km",
        serialization_alias="industrialWithin1Km",
    )
    industrial_within_5km: bool = Field(
        False,
        alias="industrialWithin5Km",
        serialization_alias="industrialWithin5Km",
    )
    industrial_within_10km: bool = Field(
        False,
        alias="industrialWithin10Km",
        serialization_alias="industrialWithin10Km",
    )
    count_within_1km: int = Field(
        0,
        alias="countWithin1Km",
        serialization_alias="countWithin1Km",
        ge=0,
        description="Number of industrial features within 1 km",
    )
    count_within_5km: int = Field(
        0,
        alias="countWithin5Km",
        serialization_alias="countWithin5Km",
        ge=0,
        description="Number of industrial features within 5 km",
    )
    count_within_10km: int = Field(
        0,
        alias="countWithin10Km",
        serialization_alias="countWithin10Km",
        ge=0,
        description="Number of industrial features within 10 km",
    )
    power_infrastructure_nearby: bool = Field(
        False,
        alias="powerInfrastructureNearby",
        serialization_alias="powerInfrastructureNearby",
    )
    mapped_flare_nearby: bool = Field(
        False,
        alias="mappedFlareNearby",
        serialization_alias="mappedFlareNearby",
    )
    mapped_chimney_nearby: bool = Field(
        False,
        alias="mappedChimneyNearby",
        serialization_alias="mappedChimneyNearby",
    )
    context_confidence: float = Field(
        0.0,
        alias="contextConfidence",
        serialization_alias="contextConfidence",
        ge=0,
        le=100,
        description="Confidence in spatial context completeness and tag specificity (0-100)",
    )
    source: str = CONTEXT_SOURCE_OSM
    retrieved_at: str = Field(
        ..., alias="retrievedAt", serialization_alias="retrievedAt"
    )
    cached: bool = False
    provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="Field-aware provenance mapping indicating data source per context field (e.g. {'industrialDistanceKm': 'osm', 'landCover': 'manual', 'windKph': 'weather'})",
    )
    features: List[OsmFeature] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
