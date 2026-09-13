"""
Background job for scanning monitored sites and generating alerts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.db.session import SessionLocal
from app.services.monitoring_service import MonitoringService

logger = logging.getLogger("app.jobs.watch_scanner")


def run_watch_scanner() -> Dict[str, Any]:
    """
    Evaluate all active watches and generate alerts.
    Guaranteed idempotent via fingerprint uniqueness.
    """
    logger.info("Starting watch scanner job")
    db = SessionLocal()
    try:
        new_alerts = MonitoringService.scan_all_watches(db)
        summary = {
            "alerts_generated": len(new_alerts),
            "alert_ids": [a.id for a in new_alerts],
            "status": "completed",
        }
        logger.info("Watch scanner complete: %d alerts generated", len(new_alerts))
        return summary
    except Exception as exc:
        logger.error("Watch scanner failed: %s", exc)
        return {
            "alerts_generated": 0,
            "error": str(exc),
            "status": "failed",
        }
    finally:
        db.close()
