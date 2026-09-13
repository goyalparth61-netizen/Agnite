"""
Observation service for ingestion, querying, and persistent lifecycle management.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models.observation import ObservationModel
from app.db.repositories.observation_repository import ObservationRepository
from app.schemas.observation import Observation

logger = logging.getLogger("app.services.observation_service")


def model_to_observation(model: ObservationModel) -> Observation:
    """Convert database model to Pydantic Observation."""
    return Observation(
        id=model.id,
        latitude=model.latitude,
        longitude=model.longitude,
        observedAt=model.observed_at.isoformat().replace("+00:00", "Z"),
        frp=model.frp,
        brightness=model.brightness,
        confidence=float(model.confidence) if model.confidence and model.confidence.replace(".", "", 1).isdigit() else model.confidence,
        satellite=model.satellite,
        sensor=model.sensor,
        daynight=model.daynight,
        source=model.source,  # type: ignore[arg-type]
    )


class ObservationService:
    """Service layer for thermal observations."""

    @staticmethod
    def ingest_observations(
        db: Session, observations: List[Observation]
    ) -> Tuple[int, int]:
        """Bulk ingest observations into database, ignoring duplicates."""
        return ObservationRepository.bulk_insert_ignore_duplicates(db, observations)

    @staticmethod
    def ingest_manual_observation(db: Session, observation: Observation) -> Observation:
        """Store a single manual or imported observation preserving provenance."""
        # Ensure provenance is strictly manual or imported
        if observation.source not in ("manual", "imported", "demo"):
            observation.source = "manual"
        model = ObservationRepository.create(db, observation)
        return model_to_observation(model)

    @staticmethod
    def get_near_location(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Observation]:
        """Retrieve observations within radius_km of location."""
        models = ObservationRepository.get_near_location(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )
        return [model_to_observation(m) for m in models]

    @staticmethod
    def get_recent(db: Session, hours: int = 48, limit: int = 2000) -> List[Observation]:
        """Retrieve recent observations across all locations."""
        models = ObservationRepository.get_recent(db, hours=hours, limit=limit)
        return [model_to_observation(m) for m in models]
