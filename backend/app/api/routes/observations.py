"""
API routes for observation ingestion and querying.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.observation import Observation
from app.services.observation_service import ObservationService

logger = logging.getLogger("app.api.routes.observations")

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk ingest thermal observations",
    description="Bulk ingests thermal observations into persistent database storage, ignoring duplicates.",
)
def bulk_ingest_observations(
    observations: List[Observation],
    db: Session = Depends(get_db),
) -> dict:
    """Bulk ingest observations into database."""
    if not observations:
        return {"inserted": 0, "duplicates": 0, "message": "No observations provided."}

    inserted, duplicates = ObservationService.ingest_observations(db, observations)
    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "total": len(observations),
        "status": "success",
    }


@router.post(
    "/manual",
    status_code=status.HTTP_201_CREATED,
    response_model=Observation,
    summary="Ingest single manual observation",
    description="Stores an individual ground truth or manual observation, preserving provenance.",
)
def ingest_manual_observation(
    observation: Observation,
    db: Session = Depends(get_db),
) -> Observation:
    """Store single manual observation."""
    return ObservationService.ingest_manual_observation(db, observation)


@router.get(
    "",
    response_model=List[Observation],
    summary="Get recent stored observations",
)
def get_recent_observations(
    hours: int = Query(48, ge=1, le=720, description="Hours to look back"),
    limit: int = Query(500, ge=1, le=2000, description="Maximum observations to return"),
    db: Session = Depends(get_db),
) -> List[Observation]:
    """Retrieve recent stored observations across all locations."""
    return ObservationService.get_recent(db, hours=hours, limit=limit)
