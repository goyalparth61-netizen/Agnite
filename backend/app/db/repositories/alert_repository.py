"""
Repository for monitoring alerts.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.alert import AlertModel


class AlertRepository:
    """Repository handling CRUD and deduplication operations for alerts."""

    @staticmethod
    def create_if_not_exists(
        db: Session,
        watch_id: str,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        latitude: float,
        longitude: float,
        fingerprint: str,
        observation_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        frp: Optional[float] = None,
        risk: Optional[int] = None,
        confidence: Optional[float] = None,
    ) -> Optional[AlertModel]:
        """
        Create new alert if fingerprint does not already exist.
        Guarantees idempotence and duplicate prevention.
        """
        existing = db.scalar(select(AlertModel).where(AlertModel.fingerprint == fingerprint))
        if existing:
            return None

        model = AlertModel(
            id=str(uuid.uuid4()),
            watch_id=watch_id,
            observation_id=observation_id,
            analysis_id=analysis_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            latitude=latitude,
            longitude=longitude,
            frp=frp,
            risk=risk,
            confidence=confidence,
            fingerprint=fingerprint,
            acknowledged=False,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[AlertModel]:
        """Find alert by ID."""
        return db.scalar(select(AlertModel).where(AlertModel.id == id))

    @staticmethod
    def list_alerts(
        db: Session,
        watch_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AlertModel], int, int]:
        """
        List alerts with optional filters.
        Returns (alerts, total_filtered_count, unacknowledged_count).
        """
        stmt = select(AlertModel)
        if watch_id:
            stmt = stmt.where(AlertModel.watch_id == watch_id)
        if severity:
            stmt = stmt.where(AlertModel.severity == severity)
        if acknowledged is not None:
            stmt = stmt.where(AlertModel.acknowledged == acknowledged)

        # Count total matching query
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        # Unacknowledged count across query
        unack_stmt = select(func.count(AlertModel.id)).where(AlertModel.acknowledged.is_(False))
        if watch_id:
            unack_stmt = unack_stmt.where(AlertModel.watch_id == watch_id)
        unack_count = db.scalar(unack_stmt) or 0

        # Paginated results
        stmt = stmt.order_by(AlertModel.created_at.desc()).limit(limit).offset(offset)
        alerts = list(db.scalars(stmt).all())

        return alerts, total, unack_count

    @staticmethod
    def acknowledge(db: Session, id: str) -> Optional[AlertModel]:
        """Mark alert as acknowledged."""
        model = db.scalar(select(AlertModel).where(AlertModel.id == id))
        if model:
            model.acknowledged = True
            db.commit()
            db.refresh(model)
        return model
