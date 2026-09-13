"""
SQLAlchemy model for monitored alerts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AlertModel(Base):
    """
    Generated alert representing abnormal thermal activity at a watched site.

    Duplicate alert generation is strictly prevented via unique fingerprint.
    """

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    watch_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("watches.id", ondelete="CASCADE"), index=True
    )
    observation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    analysis_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    frp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    watch = relationship("WatchModel", backref="alerts")

    __table_args__ = (
        Index("ix_alerts_watch_ack", "watch_id", "acknowledged"),
    )
