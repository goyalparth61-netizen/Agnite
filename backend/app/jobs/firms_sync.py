"""
Background job for synchronizing NASA FIRMS satellite observations into persistent storage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.db.repositories.observation_repository import ObservationRepository
from app.db.session import SessionLocal
from app.providers.nasa.client import download_firms_csv
from app.providers.nasa.parser import parse_firms_csv

logger = logging.getLogger("app.jobs.firms_sync")


async def run_firms_sync(
    sensor: str = "noaa20",
    hours: int = 24,
    http_client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """
    Fetch active FIRMS feed, parse observations, and persist unseen records.
    Returns summary: {'fetched': N, 'inserted': M, 'duplicates': D, 'errors': E}.
    """
    logger.info("Starting FIRMS sync job for sensor=%s hours=%d", sensor, hours)
    summary = {
        "fetched": 0,
        "inserted": 0,
        "duplicates": 0,
        "errors": 0,
        "sensor": sensor,
        "hours": hours,
    }

    client = http_client or httpx.AsyncClient(timeout=30.0)
    should_close = http_client is None

    try:
        csv_text = await download_firms_csv(client, sensor=sensor, hours=hours)
        observations = parse_firms_csv(csv_text, sensor=sensor)
        summary["fetched"] = len(observations)

        db = SessionLocal()
        try:
            inserted, duplicates = ObservationRepository.bulk_insert_ignore_duplicates(
                db, observations
            )
            summary["inserted"] = inserted
            summary["duplicates"] = duplicates
            logger.info(
                "FIRMS sync complete: %d fetched, %d inserted, %d duplicates",
                len(observations),
                inserted,
                duplicates,
            )
        finally:
            db.close()

    except Exception as exc:
        logger.warning("FIRMS sync job encountered error: %s", exc)
        summary["errors"] += 1
    finally:
        if should_close:
            await client.aclose()

    return summary
