"""
NASA FIRMS HTTP client.

Downloads public near-real-time CSV files from NASA FIRMS.
Phase 1 uses the public download URLs (no MAP_KEY required).
"""

from __future__ import annotations

import logging

import httpx

from app.core.constants import (
    MAX_BODY_BYTES,
    NASA_REQUEST_TIMEOUT_SECONDS,
    SENSOR_PATHS,
    WINDOW_LABELS,
)
from app.core.exceptions import FirmsError

logger = logging.getLogger(__name__)


def build_source_url(sensor: str, hours: int) -> str:
    """
    Build the public NASA FIRMS CSV download URL.

    Matches the Node server's ``sourceUrlFor`` exactly.
    """
    if sensor not in SENSOR_PATHS or hours not in WINDOW_LABELS:
        raise FirmsError(
            "Unsupported NASA FIRMS source or time window.", status_code=400
        )
    folder, prefix = SENSOR_PATHS[sensor]
    window = WINDOW_LABELS[hours]
    return (
        f"https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
        f"{folder}/csv/{prefix}_South_Asia_{window}.csv"
    )


async def download_firms_csv(
    client: httpx.AsyncClient,
    sensor: str,
    hours: int,
    timeout: float = NASA_REQUEST_TIMEOUT_SECONDS,
) -> str:
    """
    Download a NASA FIRMS CSV file.

    Returns the raw CSV text.  Raises ``FirmsError`` on any failure.
    """
    url = build_source_url(sensor, hours)
    logger.info("NASA FIRMS request started: %s", url)

    try:
        response = await client.get(
            url,
            timeout=timeout,
            follow_redirects=False,
            headers={
                "Accept": "text/csv",
                "User-Agent": "AGNITE/0.1 NASA-FIRMS-public-data",
            },
        )
    except httpx.TimeoutException:
        logger.warning("NASA FIRMS download timed out: %s", url)
        raise FirmsError("NASA FIRMS download timed out.")
    except httpx.RequestError as exc:
        logger.warning("NASA FIRMS request failed: %s — %s", url, exc)
        raise FirmsError("NASA FIRMS could not be reached.")

    if response.status_code != 200:
        logger.warning(
            "NASA FIRMS returned HTTP %s: %s", response.status_code, url
        )
        raise FirmsError(
            f"NASA FIRMS download returned HTTP {response.status_code}."
        )

    content_type = (response.headers.get("content-type") or "").lower()
    if any(bad in content_type for bad in ("text/html", "application/json", "application/xml")):
        logger.warning("NASA FIRMS returned unexpected content-type: %s", content_type)
        raise FirmsError("NASA FIRMS returned an unexpected response format.")

    body = response.text
    if len(body.encode("utf-8", errors="replace")) > MAX_BODY_BYTES:
        raise FirmsError("NASA FIRMS response exceeded the 10 MB safety limit.")

    logger.info(
        "NASA FIRMS request completed: %s — %d bytes",
        url,
        len(body),
    )
    return body
