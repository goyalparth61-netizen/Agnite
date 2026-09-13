"""
Repository for persistent thermal analysis records.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.analysis import AnalysisRecordModel
from app.schemas.analysis import AnalysisResult


class AnalysisRepository:
    """Repository handling database operations for analysis snapshots."""

    @staticmethod
    def create(
        db: Session,
        result: AnalysisResult,
        selected_observation_id: Optional[str] = None,
    ) -> AnalysisRecordModel:
        """Persist AnalysisResult as an auditable AnalysisRecordModel."""
        center_lat = result.statistics.center.latitude
        center_lon = result.statistics.center.longitude
        analysis_id = str(uuid.uuid4())

        model = AnalysisRecordModel(
            id=analysis_id,
            selected_observation_id=selected_observation_id,
            latitude=center_lat,
            longitude=center_lon,
            classification=result.classification,
            confidence=result.confidence,
            risk_index=result.risk.index,
            risk_level=result.risk.level,
            method=result.method or "heuristic",
            model_name=result.model.name,
            schema_version="1.0",
            analysis_json=result.model_dump_json(),
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[AnalysisRecordModel]:
        """Find analysis record by ID."""
        return db.scalar(select(AnalysisRecordModel).where(AnalysisRecordModel.id == id))

    @staticmethod
    def list_recent(db: Session, limit: int = 50) -> List[AnalysisRecordModel]:
        """List most recent analyses."""
        stmt = (
            select(AnalysisRecordModel)
            .order_by(AnalysisRecordModel.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
