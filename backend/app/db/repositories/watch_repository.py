"""
Repository for monitored watch locations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.watch import WatchModel
from app.schemas.watch import WatchCreate, WatchUpdate


class WatchRepository:
    """Repository handling CRUD operations for monitored watch locations."""

    @staticmethod
    def create(db: Session, data: WatchCreate) -> WatchModel:
        """Create new watch site."""
        model = WatchModel(
            id=str(uuid.uuid4()),
            name=data.name,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_km=data.radius_km,
            frp_threshold=data.frp_threshold,
            risk_threshold=data.risk_threshold,
            enabled=data.enabled,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[WatchModel]:
        """Find watch by ID."""
        return db.scalar(select(WatchModel).where(WatchModel.id == id))

    @staticmethod
    def list_all(db: Session, enabled_only: bool = False) -> List[WatchModel]:
        """List all watch sites."""
        stmt = select(WatchModel)
        if enabled_only:
            stmt = stmt.where(WatchModel.enabled.is_(True))
        stmt = stmt.order_by(WatchModel.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def update(db: Session, id: str, data: WatchUpdate) -> Optional[WatchModel]:
        """Update existing watch."""
        model = db.scalar(select(WatchModel).where(WatchModel.id == id))
        if not model:
            return None

        if data.name is not None:
            model.name = data.name
        if data.radius_km is not None:
            model.radius_km = data.radius_km
        if data.frp_threshold is not None:
            model.frp_threshold = data.frp_threshold
        if data.risk_threshold is not None:
            model.risk_threshold = data.risk_threshold
        if data.enabled is not None:
            model.enabled = data.enabled

        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def delete(db: Session, id: str) -> bool:
        """Delete watch site."""
        model = db.scalar(select(WatchModel).where(WatchModel.id == id))
        if not model:
            return False
        db.delete(model)
        db.commit()
        return True

    @staticmethod
    def update_last_checked(db: Session, id: str, checked_at: datetime) -> None:
        """Update last_checked_at timestamp."""
        model = db.scalar(select(WatchModel).where(WatchModel.id == id))
        if model:
            model.last_checked_at = checked_at
            db.commit()
