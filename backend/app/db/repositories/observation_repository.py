"""
Repository for persistent thermal observations.
Dialect-agnostic: works on SQLite and PostgreSQL/Supabase.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.observation import ObservationModel
from app.schemas.observation import Observation
from app.utils.dates import epoch_ms_to_iso, iso_to_epoch_ms
from app.utils.geo import haversine_km


class ObservationRepository:
    """Repository handling database operations for thermal observations."""

    @staticmethod
    def bulk_insert_ignore_duplicates(
        db: Session, observations: Union[List[Observation], List[Dict[str, Any]]]
    ) -> Tuple[int, int]:
        """
        Bulk insert observations, ignoring duplicates based on primary key `id`.
        Accepts either Pydantic Observation models or raw dictionaries.
        Returns (inserted_count, duplicate_count).
        """
        if not observations:
            return 0, 0

        def get_val(item: Any, key: str, alt_key: Optional[str] = None, default: Any = None) -> Any:
            if isinstance(item, dict):
                if key in item:
                    return item[key]
                if alt_key and alt_key in item:
                    return item[alt_key]
                return default
            val = getattr(item, key, None)
            if val is not None:
                return val
            if alt_key:
                val = getattr(item, alt_key, None)
                if val is not None:
                    return val
            return default

        ids = [get_val(obs, "id") for obs in observations if get_val(obs, "id")]
        # Query existing IDs in chunks of 500 to adhere to query parameter limits
        existing_ids: Set[str] = set()
        chunk_size = 500
        for i in range(0, len(ids), chunk_size):
            chunk = ids[i : i + chunk_size]
            rows = db.scalars(select(ObservationModel.id).where(ObservationModel.id.in_(chunk))).all()
            existing_ids.update(rows)

        new_models = []
        for obs in observations:
            obs_id = get_val(obs, "id")
            if not obs_id or obs_id in existing_ids:
                continue

            observed_at_str = str(get_val(obs, "observed_at", "observedAt", ""))
            try:
                dt = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

            conf = get_val(obs, "confidence")
            model = ObservationModel(
                id=obs_id,
                source=get_val(obs, "source", default="firms"),
                sensor=get_val(obs, "sensor"),
                latitude=float(get_val(obs, "latitude")),
                longitude=float(get_val(obs, "longitude")),
                observed_at=dt,
                frp=float(get_val(obs, "frp", default=0.0)),
                brightness=get_val(obs, "brightness"),
                confidence=str(conf) if conf is not None else None,
                satellite=get_val(obs, "satellite"),
                instrument=get_val(obs, "instrument"),
                daynight=get_val(obs, "daynight"),
            )
            new_models.append(model)
            existing_ids.add(obs_id)

        if new_models:
            db.add_all(new_models)
            db.commit()

        inserted = len(new_models)
        duplicates = len(observations) - inserted
        return inserted, duplicates

    @staticmethod
    def create(db: Session, obs: Union[Observation, Dict[str, Any]]) -> ObservationModel:
        """Create single observation record idempotently."""
        def get_val(item: Any, key: str, alt_key: Optional[str] = None, default: Any = None) -> Any:
            if isinstance(item, dict):
                if key in item:
                    return item[key]
                if alt_key and alt_key in item:
                    return item[alt_key]
                return default
            val = getattr(item, key, None)
            if val is not None:
                return val
            if alt_key:
                val = getattr(item, alt_key, None)
                if val is not None:
                    return val
            return default

        obs_id = get_val(obs, "id")
        existing = db.scalar(select(ObservationModel).where(ObservationModel.id == obs_id))
        if existing:
            return existing

        observed_at_str = str(get_val(obs, "observed_at", "observedAt", ""))
        try:
            dt = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)

        conf = get_val(obs, "confidence")
        model = ObservationModel(
            id=obs_id,
            source=get_val(obs, "source", default="manual"),
            sensor=get_val(obs, "sensor"),
            latitude=float(get_val(obs, "latitude")),
            longitude=float(get_val(obs, "longitude")),
            observed_at=dt,
            frp=float(get_val(obs, "frp", default=0.0)),
            brightness=get_val(obs, "brightness"),
            confidence=str(conf) if conf is not None else None,
            satellite=get_val(obs, "satellite"),
            instrument=get_val(obs, "instrument"),
            daynight=get_val(obs, "daynight"),
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_by_id(db: Session, id: str) -> Optional[ObservationModel]:
        """Find observation by ID."""
        return db.scalar(select(ObservationModel).where(ObservationModel.id == id))

    @staticmethod
    def get_near_location(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[ObservationModel]:
        """
        Query observations near target location within radius_km.
        Uses bounding-box prefilter in SQL and precise Haversine in Python.
        """
        # Bounding box delta
        delta_lat = radius_km / 111.0
        cos_lat = math.cos(math.radians(latitude))
        delta_lon = radius_km / (111.0 * max(0.01, cos_lat))

        min_lat = latitude - delta_lat
        max_lat = latitude + delta_lat
        min_lon = longitude - delta_lon
        max_lon = longitude + delta_lon

        stmt = select(ObservationModel).where(
            ObservationModel.latitude.between(min_lat, max_lat),
            ObservationModel.longitude.between(min_lon, max_lon),
        )

        if from_date is not None:
            stmt = stmt.where(ObservationModel.observed_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(ObservationModel.observed_at <= to_date)

        stmt = stmt.order_by(ObservationModel.observed_at.asc()).limit(limit * 2)
        candidates = db.scalars(stmt).all()

        # Strict Haversine filter
        results = []
        for row in candidates:
            dist = haversine_km(latitude, longitude, row.latitude, row.longitude)
            if dist <= radius_km:
                results.append(row)
                if len(results) >= limit:
                    break

        return results

    @staticmethod
    def get_recent(db: Session, hours: int = 48, limit: int = 2000) -> List[ObservationModel]:
        """Query recent observations across all locations."""
        cutoff = datetime.now(timezone.utc) - (datetime.now(timezone.utc) - datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() - (hours * 3600), tz=timezone.utc
        ))
        stmt = (
            select(ObservationModel)
            .where(ObservationModel.observed_at >= cutoff)
            .order_by(ObservationModel.observed_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count(db: Session) -> int:
        """Total number of stored observations."""
        return db.scalar(select(func.count(ObservationModel.id))) or 0
