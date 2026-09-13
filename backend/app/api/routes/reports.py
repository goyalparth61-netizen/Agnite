"""
API routes for persistent saved analysis reports.
Matches frontend SavedReport contract.
"""

from __future__ import annotations

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.models.report import SavedReportModel
from app.db.repositories.report_repository import ReportRepository
from app.db.session import get_db
from app.schemas.report import ReportCreate, ReportListResponse, ReportResponse

logger = logging.getLogger("app.api.routes.reports")

router = APIRouter(prefix="/reports", tags=["Reports"])


def model_to_response(model: SavedReportModel) -> ReportResponse:
    """Map SavedReportModel to Pydantic response."""
    return ReportResponse(
        id=model.id,
        label=model.label,
        latitude=model.latitude,
        longitude=model.longitude,
        classification=model.classification,
        confidence=model.confidence,
        risk=model.risk,
        summary=model.summary,
        report=json.loads(model.analysis_json),
        context=json.loads(model.context_json) if model.context_json else None,
        observations=json.loads(model.observations_json) if model.observations_json else [],
        createdAt=model.created_at.isoformat().replace("+00:00", "Z"),
    )


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save an analysis report to backend storage",
)
def save_report(data: ReportCreate, db: Session = Depends(get_db)) -> ReportResponse:
    """Save an analysis report."""
    model = ReportRepository.create(db, data)
    return model_to_response(model)


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List saved analysis reports",
)
def list_reports(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ReportListResponse:
    """List saved reports."""
    reports, total = ReportRepository.list_reports(db, limit=limit, offset=offset)
    return ReportListResponse(
        reports=[model_to_response(r) for r in reports],
        total=total,
    )


@router.get(
    "/{id}",
    response_model=ReportResponse,
    summary="Get saved analysis report by ID",
)
def get_report(id: str, db: Session = Depends(get_db)) -> ReportResponse:
    """Get single saved report."""
    model = ReportRepository.get_by_id(db, id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return model_to_response(model)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete saved analysis report",
)
def delete_report(id: str, db: Session = Depends(get_db)) -> Response:
    """Delete saved report."""
    success = ReportRepository.delete(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
