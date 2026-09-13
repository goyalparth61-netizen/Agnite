"""
Tests for geo utilities.
"""

from __future__ import annotations

import pytest

from app.utils.geo import haversine_km, is_valid_coordinate


class TestHaversine:
    """Test Haversine distance calculation."""

    def test_same_point_is_zero(self):
        assert haversine_km(21.0, 79.0, 21.0, 79.0) == 0.0

    def test_known_distance(self):
        """Mumbai (19.076, 72.877) to Delhi (28.614, 77.209) ≈ 1,148 km."""
        distance = haversine_km(19.076, 72.877, 28.614, 77.209)
        assert 1100 < distance < 1200

    def test_short_distance(self):
        """Two points ~1 km apart."""
        # ~0.009° latitude ≈ 1 km
        distance = haversine_km(21.0, 79.0, 21.009, 79.0)
        assert 0.9 < distance < 1.1

    def test_within_5km_radius(self):
        """Points within 5 km of each other."""
        d = haversine_km(21.1466, 79.0889, 21.16, 79.09)
        assert d < 5.0

    def test_antipodal_points(self):
        """Antipodal points should be ~20,000 km apart."""
        d = haversine_km(0, 0, 0, 180)
        assert 20000 < d < 20100

    def test_symmetry(self):
        """Distance is symmetric."""
        d1 = haversine_km(21.0, 79.0, 22.0, 80.0)
        d2 = haversine_km(22.0, 80.0, 21.0, 79.0)
        assert abs(d1 - d2) < 0.001


class TestCoordinateValidation:
    """Test coordinate bounds checking."""

    def test_valid_coordinates(self):
        assert is_valid_coordinate(21.1466, 79.0889) is True
        assert is_valid_coordinate(0.0, 0.0) is True
        assert is_valid_coordinate(-90.0, -180.0) is True
        assert is_valid_coordinate(90.0, 180.0) is True

    def test_invalid_latitude(self):
        assert is_valid_coordinate(91.0, 79.0) is False
        assert is_valid_coordinate(-91.0, 79.0) is False

    def test_invalid_longitude(self):
        assert is_valid_coordinate(21.0, 181.0) is False
        assert is_valid_coordinate(21.0, -181.0) is False

    def test_nan_rejected(self):
        assert is_valid_coordinate(float("nan"), 79.0) is False

    def test_inf_rejected(self):
        assert is_valid_coordinate(float("inf"), 79.0) is False
