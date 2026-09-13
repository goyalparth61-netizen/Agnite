"""
SQLAlchemy model for persistent thermal analysis snapshots.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalysisRecordModel(Base):
    """
    Persistent snapshot of an executed thermal intelligence analysis.

    Enables auditability, report derivation, grounding for future AI workflows,
    and alert traceability.
    """

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    selected_observation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    method: Mapped[str] = mapped_column(String(32), default="heuristic")
    model_name: Mapped[str] = mapped_column(String(64), default="agnite-heuristic-v1")
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0")
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    __table_args__ = (
        Index("ix_analyses_coords", "latitude", "longitude"),
    )
