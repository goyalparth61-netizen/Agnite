"""
Spatial context service for OpenStreetMap infrastructure enrichment.

Provides abstract SpatialContextProvider protocol and concrete OSMSpatialContextProvider.
Implements in-memory coordinate grid caching, feature aggregation, context confidence scoring,
and zero-failure graceful degradation when upstream Overpass is unreachable.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable

from app.core.config import get_settings
from app.core.constants import (
    CONTEXT_SOURCE_OSM,
    CONTEXT_SOURCE_UNKNOWN,
    DEFAULT_OSM_SEARCH_RADIUS_KM,
)
from app.providers.osm.client import OsmClient, OsmProviderError
from app.providers.osm.parser import parse_overpass_json
from app.schemas.context import OsmFeature, SpatialContext
from app.utils.dates import utc_now_iso

logger = logging.getLogger("app.services.spatial_context_service")


@runtime_checkable
class SpatialContextProvider(Protocol):
    """Protocol for spatial context providers (OSM, Bhuvan, Government GIS)."""

    async def get_context(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = DEFAULT_OSM_SEARCH_RADIUS_KM,
    ) -> SpatialContext:
        """Retrieve normalized spatial context around target coordinates."""
        ...


class OSMSpatialContextProvider:
    """Production provider connecting to OpenStreetMap via Overpass."""

    def __init__(
        self,
        osm_client: Optional[OsmClient] = None,
        cache_ttl_seconds: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.osm_client = osm_client or OsmClient()
        self.cache_ttl_seconds = (
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else settings.osm_cache_ttl_seconds
        )
        self._cache: Dict[str, Tuple[SpatialContext, float]] = {}

    def _get_cache_key(self, lat: float, lon: float, radius: float) -> str:
        """Grid cache key: round coordinates to 2 decimal places (~1.1 km)."""
        return f"{lat:.2f}:{lon:.2f}:{radius:.1f}"

    def clear_cache(self) -> None:
        """Clear in-memory context cache."""
        self._cache.clear()

    async def get_context(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = DEFAULT_OSM_SEARCH_RADIUS_KM,
    ) -> SpatialContext:
        """
        Query Overpass and return normalized SpatialContext.

        Checks coordinate grid cache first. If Overpass fails or times out,
        gracefully returns degraded context with warnings instead of failing.
        """
        cache_key = self._get_cache_key(latitude, longitude, radius_km)
        now = time.time()

        # 1. Check cache
        if cache_key in self._cache:
            cached_ctx, cached_at = self._cache[cache_key]
            if now - cached_at < self.cache_ttl_seconds:
                logger.info("Spatial context cache hit for key %s", cache_key)
                # Return copy with cached=True
                ctx_copy = cached_ctx.model_copy()
                ctx_copy.cached = True
                return ctx_copy

        # 2. Query Overpass API
        try:
            raw_data = await self.osm_client.fetch_infrastructure(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
            )

            features, nearest_summary = parse_overpass_json(
                raw_data=raw_data,
                query_lat=latitude,
                query_lon=longitude,
                radius_km=radius_km,
            )

            # 3. Analyze features locally in Python
            industrial_count = len(features)
            count_1km = sum(1 for f in features if f.distance_km <= 1.0)
            count_5km = sum(1 for f in features if f.distance_km <= 5.0)
            count_10km = sum(1 for f in features if f.distance_km <= 10.0)
            within_1km = count_1km > 0
            within_5km = count_5km > 0
            within_10km = count_10km > 0

            power_nearby = any(
                f.feature_type in ("power_plant", "power_substation")
                for f in features
            )
            flare_nearby = any(f.feature_type == "flare" for f in features)
            chimney_nearby = any(f.feature_type == "chimney" for f in features)

            ind_dist: Optional[float] = None
            if nearest_summary is not None:
                ind_dist = nearest_summary.distance_km

            # Confidence calculation (0-100)
            warnings: List[str] = [
                "OpenStreetMap coverage is community-contributed and may be incomplete."
            ]

            if features:
                # Base confidence for having mapped objects
                named_count = sum(1 for f in features if f.name)
                high_heat_count = sum(
                    1
                    for f in features
                    if f.feature_type
                    in ("flare", "chimney", "power_plant", "refinery", "metal_works")
                )
                score = (
                    50.0
                    + min(20.0, industrial_count * 3.0)
                    + min(15.0, named_count * 5.0)
                    + min(15.0, high_heat_count * 7.5)
                )
                confidence = round(max(40.0, min(100.0, score)), 1)
            else:
                # Absence in OSM is not proof of absence in reality
                confidence = 25.0
                warnings.append(
                    "No relevant mapped industrial infrastructure was found within the search radius. "
                    "This does not establish that none exists."
                )

            provenance: Dict[str, str] = {
                "industrialDistanceKm": "osm" if ind_dist is not None else "osm_empty",
                "nearestIndustrialFeature": "osm" if nearest_summary is not None else "osm_empty",
                "industrialFeatureCount": "osm",
                "countWithin1Km": "osm",
                "countWithin5Km": "osm",
                "countWithin10Km": "osm",
                "industrialWithin1Km": "osm",
                "industrialWithin5Km": "osm",
                "industrialWithin10Km": "osm",
                "powerInfrastructureNearby": "osm",
                "mappedFlareNearby": "osm",
                "mappedChimneyNearby": "osm",
            }

            context = SpatialContext(
                latitude=latitude,
                longitude=longitude,
                searchRadiusKm=radius_km,
                industrialDistanceKm=ind_dist,
                nearestIndustrialFeature=nearest_summary,
                industrialFeatureCount=industrial_count,
                industrialWithin1Km=within_1km,
                industrialWithin5Km=within_5km,
                industrialWithin10Km=within_10km,
                countWithin1Km=count_1km,
                countWithin5Km=count_5km,
                countWithin10Km=count_10km,
                powerInfrastructureNearby=power_nearby,
                mappedFlareNearby=flare_nearby,
                mappedChimneyNearby=chimney_nearby,
                contextConfidence=confidence,
                source=CONTEXT_SOURCE_OSM,
                retrievedAt=utc_now_iso(),
                cached=False,
                provenance=provenance,
                features=features,
                warnings=warnings,
            )

            # Save in cache
            self._cache[cache_key] = (context, now)
            return context

        except OsmProviderError as exc:
            logger.warning(
                "Overpass spatial query unavailable (%s); degrading gracefully.", exc
            )
            return SpatialContext(
                latitude=latitude,
                longitude=longitude,
                searchRadiusKm=radius_km,
                industrialDistanceKm=None,
                nearestIndustrialFeature=None,
                industrialFeatureCount=0,
                industrialWithin1Km=False,
                industrialWithin5Km=False,
                industrialWithin10Km=False,
                countWithin1Km=0,
                countWithin5Km=0,
                countWithin10Km=0,
                powerInfrastructureNearby=False,
                mappedFlareNearby=False,
                mappedChimneyNearby=False,
                contextConfidence=0.0,
                source=CONTEXT_SOURCE_UNKNOWN,
                retrievedAt=utc_now_iso(),
                cached=False,
                provenance={
                    "industrialDistanceKm": "unavailable",
                    "nearestIndustrialFeature": "unavailable",
                    "industrialFeatureCount": "unavailable",
                },
                features=[],
                warnings=[
                    f"OpenStreetMap spatial query unavailable ({exc.message}). "
                    "Proceeding with thermal evidence only."
                ],
            )
        except Exception as exc:
            logger.error("Unexpected error in spatial context provider: %s", exc)
            return SpatialContext(
                latitude=latitude,
                longitude=longitude,
                searchRadiusKm=radius_km,
                industrialDistanceKm=None,
                nearestIndustrialFeature=None,
                industrialFeatureCount=0,
                industrialWithin1Km=False,
                industrialWithin5Km=False,
                industrialWithin10Km=False,
                countWithin1Km=0,
                countWithin5Km=0,
                countWithin10Km=0,
                powerInfrastructureNearby=False,
                mappedFlareNearby=False,
                mappedChimneyNearby=False,
                contextConfidence=0.0,
                source=CONTEXT_SOURCE_UNKNOWN,
                retrievedAt=utc_now_iso(),
                cached=False,
                provenance={
                    "industrialDistanceKm": "error",
                    "nearestIndustrialFeature": "error",
                    "industrialFeatureCount": "error",
                },
                features=[],
                warnings=[
                    "Spatial context retrieval encountered an unexpected error. "
                    "Proceeding with thermal evidence only."
                ],
            )


# Module-level singleton provider
_SPATIAL_PROVIDER: Optional[SpatialContextProvider] = None


def get_spatial_context_provider() -> SpatialContextProvider:
    """Return active spatial context provider singleton."""
    global _SPATIAL_PROVIDER
    if _SPATIAL_PROVIDER is None:
        _SPATIAL_PROVIDER = OSMSpatialContextProvider()
    return _SPATIAL_PROVIDER


def set_spatial_context_provider(provider: Optional[SpatialContextProvider]) -> None:
    """Override spatial provider (useful for testing)."""
    global _SPATIAL_PROVIDER
    _SPATIAL_PROVIDER = provider
