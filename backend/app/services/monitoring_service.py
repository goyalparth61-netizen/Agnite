"""
Monitoring service for evaluating watched sites and generating persistent alerts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.alert import AlertModel
from app.db.models.watch import WatchModel
from app.db.repositories.alert_repository import AlertRepository
from app.db.repositories.observation_repository import ObservationRepository
from app.db.repositories.watch_repository import WatchRepository
from app.utils.geo import haversine_km

logger = logging.getLogger("app.services.monitoring_service")


class MonitoringService:
    """Evaluates watch conditions against recent observations and produces alerts."""

    @staticmethod
    def scan_watch(db: Session, watch: WatchModel) -> List[AlertModel]:
        """Evaluate a single watch site and generate alerts for un-alerted detections."""
        now = datetime.now(timezone.utc)
        # Look back 48 hours for detections
        from_date = datetime.fromtimestamp(now.timestamp() - (48 * 3600), tz=timezone.utc)

        observations = ObservationRepository.get_near_location(
            db=db,
            latitude=watch.latitude,
            longitude=watch.longitude,
            radius_km=watch.radius_km,
            from_date=from_date,
            to_date=now,
            limit=50,
        )

        generated_alerts: List[AlertModel] = []

        for obs in observations:
            dist = haversine_km(watch.latitude, watch.longitude, obs.latitude, obs.longitude)
            if dist > watch.radius_km:
                continue

            # Check threshold exceeded
            if obs.frp >= watch.frp_threshold:
                alert_type = "FRP_THRESHOLD_EXCEEDED"
                # Determine severity
                if obs.frp >= 150.0:
                    severity = "CRITICAL"
                elif obs.frp >= 50.0 or obs.frp >= (watch.frp_threshold * 2.0):
                    severity = "HIGH"
                elif obs.frp >= 25.0:
                    severity = "MODERATE"
                else:
                    severity = "LOW"

                title = f"Thermal Intensity Threshold Exceeded at {watch.name}"
                message = (
                    f"Thermal observation of {obs.frp:.1f} MW detected {dist:.2f} km from site "
                    f"(configured threshold: {watch.frp_threshold:.1f} MW)."
                )

                fingerprint = f"{watch.id}:{obs.id}:{alert_type}"
                alert = AlertRepository.create_if_not_exists(
                    db=db,
                    watch_id=watch.id,
                    alert_type=alert_type,
                    severity=severity,
                    title=title,
                    message=message,
                    latitude=obs.latitude,
                    longitude=obs.longitude,
                    observation_id=obs.id,
                    frp=obs.frp,
                    fingerprint=fingerprint,
                )
                if alert:
                    generated_alerts.append(alert)
                    logger.info("Generated alert %s for watch %s", alert.id, watch.name)

            # Check general new thermal detection if threshold was not exceeded
            else:
                alert_type = "NEW_THERMAL_DETECTION"
                severity = "INFO"
                title = f"New Thermal Activity Detected near {watch.name}"
                message = (
                    f"Thermal detection with {obs.frp:.1f} MW observed at {dist:.2f} km from site center."
                )
                fingerprint = f"{watch.id}:{obs.id}:{alert_type}"
                alert = AlertRepository.create_if_not_exists(
                    db=db,
                    watch_id=watch.id,
                    alert_type=alert_type,
                    severity=severity,
                    title=title,
                    message=message,
                    latitude=obs.latitude,
                    longitude=obs.longitude,
                    observation_id=obs.id,
                    frp=obs.frp,
                    fingerprint=fingerprint,
                )
                if alert:
                    generated_alerts.append(alert)

        # Update last checked timestamp
        WatchRepository.update_last_checked(db, watch.id, now)
        return generated_alerts

    @staticmethod
    def scan_all_watches(db: Session) -> List[AlertModel]:
        """Scan all active watches and return all newly generated alerts."""
        watches = WatchRepository.list_all(db, enabled_only=True)
        all_alerts: List[AlertModel] = []
        for watch in watches:
            alerts = MonitoringService.scan_watch(db, watch)
            all_alerts.extend(alerts)
        return all_alerts
