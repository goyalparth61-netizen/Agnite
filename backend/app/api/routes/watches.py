"""
API routes for monitored watch locations.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.models.watch import WatchModel
from app.db.repositories.watch_repository import WatchRepository
from app.db.session import get_db
from app.schemas.watch import WatchCreate, WatchResponse, WatchUpdate
from app.utils.geo import is_valid_coordinate

logger = logging.getLogger("app.api.routes.watches")

router = APIRouter(prefix="/watches", tags=["Watches"])


def model_to_response(model: WatchModel) -> WatchResponse:
    """Map SQLAlchemy model to Pydantic response."""
    return WatchResponse(
        id=model.id,
        name=model.name,
        latitude=model.latitude,
        longitude=model.longitude,
        radiusKm=model.radius_km,
        frpThreshold=model.frp_threshold,
        riskThreshold=model.risk_threshold,
        enabled=model.enabled,
        createdAt=model.created_at.isoformat().replace("+00:00", "Z"),
        updatedAt=model.updated_at.isoformat().replace("+00:00", "Z"),
        lastCheckedAt=model.last_checked_at.isoformat().replace("+00:00", "Z") if model.last_checked_at else None,
    )


@router.post(
    "",
    response_model=WatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new monitored watch site",
)
def create_watch(data: WatchCreate, db: Session = Depends(get_db)) -> WatchResponse:
    """Create watch site."""
    if not is_valid_coordinate(data.latitude, data.longitude):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coordinates ({data.latitude}, {data.longitude}) are out of valid bounds.",
        )
    model = WatchRepository.create(db, data)
    return model_to_response(model)


@router.get(
    "",
    response_model=List[WatchResponse],
    summary="List all monitored watch sites",
)
def list_watches(db: Session = Depends(get_db)) -> List[WatchResponse]:
    """List all watches."""
    models = WatchRepository.list_all(db)
    return [model_to_response(m) for m in models]


@router.get(
    "/{id}",
    response_model=WatchResponse,
    summary="Get watch site by ID",
)
def get_watch(id: str, db: Session = Depends(get_db)) -> WatchResponse:
    """Get single watch site."""
    model = WatchRepository.get_by_id(db, id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch site not found.")
    return model_to_response(model)


@router.patch(
    "/{id}",
    response_model=WatchResponse,
    summary="Update monitored watch site",
)
def update_watch(id: str, data: WatchUpdate, db: Session = Depends(get_db)) -> WatchResponse:
    """Update watch site."""
    model = WatchRepository.update(db, id, data)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch site not found.")
    return model_to_response(model)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete monitored watch site",
)
def delete_watch(id: str, db: Session = Depends(get_db)) -> Response:
    """Delete watch site."""
    success = WatchRepository.delete(db, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watch site not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
