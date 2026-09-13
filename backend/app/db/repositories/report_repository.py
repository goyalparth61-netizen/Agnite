"""
Repository for persistent saved analysis reports.
"""

from __future__ import annotations

import json
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.report import SavedReportModel
from app.schemas.report import ReportCreate


class ReportRepository:
    """Repository handling CRUD operations for saved analysis reports."""

    @staticmethod
    def create(db: Session, data: ReportCreate) -> SavedReportModel:
        """Persist a new analysis report."""
        report_id = data.id or str(uuid.uuid4())
        model = SavedReportModel(
            id=report_id,
            label=data.label,
            latitude=data.latitude,
            longitude=data.longitude,
            classification=data.classification,
            confidence=data.confidence,
            risk=data.risk,
            summary=data.summary,
            schema_version="1.0",
            analysis_json=json.dumps(data.report),
            context_json=json.dumps(data.context) if data.context else None,
            observations_json=json.dumps(data.observations) if data.observations else None,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[SavedReportModel]:
        """Find report by ID."""
        return db.scalar(select(SavedReportModel).where(SavedReportModel.id == id))

    @staticmethod
    def list_reports(
        db: Session, limit: int = 50, offset: int = 0
    ) -> Tuple[List[SavedReportModel], int]:
        """List saved reports with total count."""
        total = db.scalar(select(func.count(SavedReportModel.id))) or 0
        stmt = (
            select(SavedReportModel)
            .order_by(SavedReportModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        reports = list(db.scalars(stmt).all())
        return reports, total

    @staticmethod
    def delete(db: Session, id: str) -> bool:
        """Delete saved report."""
        model = db.scalar(select(SavedReportModel).where(SavedReportModel.id == id))
        if not model:
            return False
        db.delete(model)
        db.commit()
        return True
