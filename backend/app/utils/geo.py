"""
Geographic utilities for the AGNITE backend.
"""

from __future__ import annotations

import math


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Haversine distance in kilometres between two WGS-84 points.

    Matches the frontend's ``distanceKm`` implementation so that
    5 km grouping is consistent across client and server.
    """
    rad = math.pi / 180
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    h = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    h = max(0.0, min(1.0, h))
    return 6371 * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def is_valid_coordinate(latitude: float, longitude: float) -> bool:
    """Check that a lat/lon pair is within valid WGS-84 bounds."""
    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    )
