"""
API routes for monitoring alerts.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models.alert import AlertModel
from app.db.repositories.alert_repository import AlertRepository
from app.db.session import get_db
from app.schemas.alert import AlertListResponse, AlertResponse

logger = logging.getLogger("app.api.routes.alerts")

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def model_to_response(model: AlertModel) -> AlertResponse:
    """Map AlertModel to Pydantic response."""
    return AlertResponse(
        id=model.id,
        watchId=model.watch_id,
        watchName=model.watch.name if model.watch else None,
        observationId=model.observation_id,
        analysisId=model.analysis_id,
        type=model.type,
        severity=model.severity,  # type: ignore[arg-type]
        title=model.title,
        message=model.message,
        latitude=model.latitude,
        longitude=model.longitude,
        frp=model.frp,
        risk=model.risk,
        confidence=model.confidence,
        fingerprint=model.fingerprint,
        acknowledged=model.acknowledged,
        createdAt=model.created_at.isoformat().replace("+00:00", "Z"),
    )


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List monitoring alerts with optional filtering",
)
def list_alerts(
    watch_id: Optional[str] = Query(None, alias="watchId", description="Filter by watch site ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, LOW, MODERATE, HIGH, CRITICAL)"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged state"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    """Retrieve filtered alerts."""
    alerts, total, unack_count = AlertRepository.list_alerts(
        db=db,
        watch_id=watch_id,
        severity=severity,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )
    return AlertListResponse(
        alerts=[model_to_response(a) for a in alerts],
        total=total,
        unacknowledgedCount=unack_count,
    )


@router.get(
    "/{id}",
    response_model=AlertResponse,
    summary="Get alert by ID",
)
def get_alert(id: str, db: Session = Depends(get_db)) -> AlertResponse:
    """Get single alert."""
    model = AlertRepository.get_by_id(db, id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return model_to_response(model)


@router.patch(
    "/{id}/acknowledge",
    response_model=AlertResponse,
    summary="Acknowledge alert",
)
def acknowledge_alert(id: str, db: Session = Depends(get_db)) -> AlertResponse:
    """Mark alert as acknowledged."""
    model = AlertRepository.acknowledge(db, id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return model_to_response(model)
