"""
SQLAlchemy model for persistent thermal observations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ObservationModel(Base):
    """
    Persistent thermal observation record.

    Stores normalized observations from NASA FIRMS, manual entry, or file imports.
    Deduplication is guaranteed via unique primary key `id`.
    """

    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="firms", index=True)
    sensor: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    frp: Mapped[float] = mapped_column(Float, nullable=False)
    brightness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    satellite: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    instrument: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    daynight: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_observations_lat_lon", "latitude", "longitude"),
        Index("ix_observations_observed_at_frp", "observed_at", "frp"),
    )
