"""
Hotspot service for spatial grouping and nearby thermal observation search.

Uses Haversine distance from app.utils.geo to filter observations within
a specified search radius (default 5 km) around a selected hotspot.
"""

from __future__ import annotations

from typing import List, Tuple
from app.core.constants import DEFAULT_SEARCH_RADIUS_KM
from app.schemas.observation import Observation
from app.utils.dates import iso_to_epoch_ms
from app.utils.geo import haversine_km, is_valid_coordinate

DAY_MS = 86_400_000
MAX_HISTORY_DAYS = 30


def deduplicate_observations(
    observations: List[Observation],
) -> Tuple[List[Observation], int]:
    """
    Filter duplicate records matching the frontend deduplication rules.

    Deduplicates by observation ID or identical (timestamp, lat 5-dec, lon 5-dec).
    Returns (unique_observations, excluded_count).
    """
    seen_ids: set[str] = set()
    seen_measurements: set[str] = set()
    unique: List[Observation] = []

    for obs in observations:
        if not is_valid_coordinate(obs.latitude, obs.longitude):
            continue
        try:
            ts = iso_to_epoch_ms(obs.observed_at)
        except Exception:
            continue

        key = f"{ts}:{obs.latitude:.5f}:{obs.longitude:.5f}"
        if obs.id in seen_ids or key in seen_measurements:
            continue

        seen_ids.add(obs.id)
        seen_measurements.add(key)
        unique.append(obs)

    # Sort chronologically (oldest first)
    unique.sort(key=lambda x: (iso_to_epoch_ms(x.observed_at), x.id))
    excluded = len(observations) - len(unique)
    return unique, excluded


def get_nearby_observations(
    selected_observation: Observation,
    observations: List[Observation],
    radius_km: float = DEFAULT_SEARCH_RADIUS_KM,
    max_history_days: int = MAX_HISTORY_DAYS,
) -> Tuple[List[Observation], List[Observation], int]:
    """
    Retrieve observations within radius_km of selected_observation.

    Returns:
      (nearby_observations, all_unique_observations, excluded_count)
      where nearby_observations are chronologically sorted (oldest first).
    """
    if not is_valid_coordinate(
        selected_observation.latitude, selected_observation.longitude
    ):
        raise ValueError(
            f"Invalid selected observation coordinates: {selected_observation.latitude}, {selected_observation.longitude}"
        )

    unique_obs, excluded_dupes = deduplicate_observations(observations)
    if not unique_obs:
        return [], [], len(observations)

    center_lat = selected_observation.latitude
    center_lon = selected_observation.longitude

    # Find points within radius_km
    at_site = [
        obs
        for obs in unique_obs
        if haversine_km(center_lat, center_lon, obs.latitude, obs.longitude)
        <= radius_km
    ]

    if not at_site:
        return [], unique_obs, len(observations)

    # Anchor time to latest detection at site
    latest_ts = iso_to_epoch_ms(at_site[-1].observed_at)
    min_ts = latest_ts - (max_history_days * DAY_MS)

    # Filter within max_history_days
    nearby = [obs for obs in at_site if iso_to_epoch_ms(obs.observed_at) >= min_ts]
    nearby.sort(key=lambda x: (iso_to_epoch_ms(x.observed_at), x.id))

    total_excluded = len(observations) - len(nearby)
    return nearby, unique_obs, total_excluded
