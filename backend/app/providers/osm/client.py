"""
Async client for querying OpenStreetMap Overpass API.

Constructs bounded Overpass QL queries for industrial and power infrastructure,
enforces timeouts, response size limits, and polite User-Agent headers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core.constants import DEFAULT_OSM_SEARCH_RADIUS_KM

logger = logging.getLogger("app.providers.osm.client")


class OsmProviderError(Exception):
    """Raised when an Overpass query fails or returns an error."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def build_overpass_query(
    latitude: float,
    longitude: float,
    radius_km: float = DEFAULT_OSM_SEARCH_RADIUS_KM,
    limit: int = 50,
) -> str:
    """
    Build bounded Overpass QL query searching for industrial and thermal candidates.

    Uses `around:radius_m,lat,lon` and requests `out center tags limit` to fetch
    ways and relations with pre-computed centroids.
    """
    radius_meters = int(radius_km * 1000)
    query = f"""[out:json][timeout:12];
(
  nwr["landuse"="industrial"](around:{radius_meters},{latitude},{longitude});
  nwr["industrial"](around:{radius_meters},{latitude},{longitude});
  nwr["man_made"="works"](around:{radius_meters},{latitude},{longitude});
  nwr["power"="plant"](around:{radius_meters},{latitude},{longitude});
  nwr["power"="generator"](around:{radius_meters},{latitude},{longitude});
  nwr["man_made"="chimney"](around:{radius_meters},{latitude},{longitude});
  nwr["man_made"="flare"](around:{radius_meters},{latitude},{longitude});
  nwr["man_made"="storage_tank"](around:{radius_meters},{latitude},{longitude});
  nwr["amenity"="fuel"](around:{radius_meters},{latitude},{longitude});
  nwr["landuse"="quarry"](around:{radius_meters},{latitude},{longitude});
);
out center tags {limit};"""
    return query


class OsmClient:
    """Async client for Overpass API communication."""

    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        api_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self.api_url = api_url or settings.overpass_api_url
        self.timeout_seconds = timeout_seconds or settings.osm_timeout_seconds
        self.max_response_bytes = settings.osm_max_response_bytes
        self.user_agent = settings.osm_user_agent
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self._client

    async def fetch_infrastructure(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = DEFAULT_OSM_SEARCH_RADIUS_KM,
    ) -> Dict[str, Any]:
        """Query Overpass API for nearby infrastructure within radius_km."""
        query = build_overpass_query(latitude, longitude, radius_km)
        client = await self._get_client()

        logger.info(
            "Overpass request dispatched for (%.4f, %.4f) radius=%.1f km",
            latitude,
            longitude,
            radius_km,
        )

        try:
            response = await client.post(
                self.api_url,
                data={"data": query},
                headers={"User-Agent": self.user_agent},
            )

            if response.status_code == 429:
                raise OsmProviderError(
                    "Overpass API rate limit reached. Using cached or fallback context.",
                    status_code=429,
                )
            elif response.status_code >= 500:
                raise OsmProviderError(
                    f"Overpass upstream server error ({response.status_code}).",
                    status_code=response.status_code,
                )
            elif not response.is_success:
                raise OsmProviderError(
                    f"Overpass request failed with status {response.status_code}.",
                    status_code=response.status_code,
                )

            if len(response.content) > self.max_response_bytes:
                raise OsmProviderError("Overpass response payload exceeded maximum size limit.")

            data = response.json()
            logger.info(
                "Overpass response received: %d elements",
                len(data.get("elements", [])),
            )
            return data

        except httpx.TimeoutException as exc:
            logger.warning("Overpass request timed out after %ds", self.timeout_seconds)
            raise OsmProviderError("Overpass API request timed out.") from exc
        except httpx.RequestError as exc:
            logger.warning("Overpass network connection error: %s", exc)
            raise OsmProviderError(f"Network error connecting to Overpass: {exc}") from exc
        except ValueError as exc:
            logger.warning("Overpass invalid JSON response: %s", exc)
            raise OsmProviderError("Overpass returned malformed JSON.") from exc

    async def close(self) -> None:
        """Close underlying HTTP client if internally managed."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
