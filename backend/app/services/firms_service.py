"""
FIRMS feed service — caching, stale-fallback, and deduplication.

This is the central service layer between API routes and the NASA
provider.  Routes call ``FirmsService.get()`` and receive a dict
ready to be serialized as the ``FirmsFeedResponse``.

The caching and stale-fallback logic is a faithful port of the
Node server's ``createFirmsService``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.constants import COVERAGE_LABEL, SENSOR_PATHS, WINDOW_LABELS
from app.core.exceptions import FirmsError
from app.providers.nasa.client import build_source_url, download_firms_csv
from app.providers.nasa.parser import parse_firms_csv

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    """A cached FIRMS feed result with its fetch timestamp."""

    timestamp_ms: int
    result: dict[str, Any]


class FirmsService:
    """
    Manages NASA FIRMS feed retrieval with in-memory caching.

    - Cache TTL is configurable (default 10 minutes).
    - On NASA failure, returns stale cached data with a warning.
    - Deduplicates concurrent requests for the same sensor/window.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        cache_ttl_seconds: int = 600,
    ) -> None:
        self._client = http_client
        self._cache_ttl_ms = cache_ttl_seconds * 1000
        self._cache: dict[str, _CacheEntry] = {}
        self._pending: dict[str, asyncio.Task[dict[str, Any]]] = {}

    async def get(
        self,
        sensor: str = "snpp",
        hours: int = 24,
    ) -> dict[str, Any]:
        """
        Retrieve the FIRMS feed for a sensor/window combination.

        Returns a dict matching the ``FirmsFeedResponse`` schema.
        """
        # Validate inputs
        if sensor not in SENSOR_PATHS:
            raise FirmsError(
                "Use hours=24, 48, or 168 and sensor=snpp, noaa20, or modis.",
                status_code=400,
            )
        if hours not in WINDOW_LABELS:
            raise FirmsError(
                "Use hours=24, 48, or 168 and sensor=snpp, noaa20, or modis.",
                status_code=400,
            )

        key = f"{sensor}:{hours}"
        now_ms = int(time.time() * 1000)

        # Cache hit?
        previous = self._cache.get(key)
        if previous and (now_ms - previous.timestamp_ms) < self._cache_ttl_ms:
            logger.info("NASA cache hit: %s", key)
            return {**previous.result, "cached": True}

        # Dedup concurrent requests
        if key in self._pending:
            logger.info("NASA request dedup: %s", key)
            return await self._pending[key]

        # Start a new fetch
        task = asyncio.create_task(self._fetch(sensor, hours, key, previous))
        self._pending[key] = task
        try:
            return await task
        finally:
            self._pending.pop(key, None)

    async def _fetch(
        self,
        sensor: str,
        hours: int,
        key: str,
        previous: _CacheEntry | None,
    ) -> dict[str, Any]:
        """Download, parse, cache, and return — with stale fallback."""
        source_url = build_source_url(sensor, hours)

        try:
            csv_text = await download_firms_csv(self._client, sensor, hours)
            fetched_ms = int(time.time() * 1000)

            parsed = parse_firms_csv(
                csv_text, sensor=sensor, hours=hours, now_ms=fetched_ms
            )

            fetched_at = datetime.fromtimestamp(
                fetched_ms / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.") + f"{fetched_ms % 1000:03d}Z"

            # Strip internal 'skipped' before returning to frontend
            warning = parsed.get("warning")

            result: dict[str, Any] = {
                "observations": parsed["observations"],
                "fetchedAt": fetched_at,
                "latestObservation": parsed["latestObservation"],
                "sourceUrl": source_url,
                "sensor": sensor,
                "windowHours": hours,
                "coverage": COVERAGE_LABEL,
                "stale": False,
                "cached": False,
            }
            if warning:
                result["warning"] = warning

            # Update cache
            self._cache[key] = _CacheEntry(
                timestamp_ms=fetched_ms, result=result
            )

            logger.info(
                "NASA FIRMS fetched: %s — %d observations",
                key,
                len(parsed["observations"]),
            )
            return result

        except FirmsError as exc:
            reason = exc.message
        except Exception as exc:
            logger.exception("Unexpected error fetching NASA FIRMS: %s", key)
            reason = "NASA FIRMS could not be reached."

        # ── Stale fallback ────────────────────────────────────────
        if previous:
            warning_parts = [reason]
            warning_parts.append(
                f"Showing cached observations fetched at "
                f"{previous.result['fetchedAt']}."
            )
            if previous.result.get("warning"):
                warning_parts.append(previous.result["warning"])
            logger.warning("NASA stale fallback: %s", key)
            return {
                **previous.result,
                "cached": True,
                "stale": True,
                "warning": " ".join(warning_parts),
            }

        # No cache at all — propagate the error
        raise FirmsError(
            f"{reason} No cached observations are available. Retry shortly."
        )
