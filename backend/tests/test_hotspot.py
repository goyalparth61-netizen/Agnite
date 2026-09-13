"""
Tests for hotspot service spatial grouping and nearby observation filtering.
"""

import pytest
from app.schemas.observation import Observation
from app.services.hotspot_service import deduplicate_observations, get_nearby_observations


def make_obs(id_str: str, lat: float, lon: float, dt_str: str, frp: float = 20.0) -> Observation:
    return Observation(
        id=id_str,
        latitude=lat,
        longitude=lon,
        observedAt=dt_str,
        frp=frp,
        source="firms",
    )


class TestHotspotService:
    def test_inside_and_outside_radius(self):
        # Reference point: Nagpur center (21.1466, 79.0889)
        selected = make_obs("center", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 35.0)

        # ~2.2 km away
        inside = make_obs("nearby", 21.1600, 79.0889, "2026-09-13T10:00:00.000Z", 25.0)

        # ~11 km away
        outside = make_obs("far", 21.2500, 79.0889, "2026-09-13T09:00:00.000Z", 40.0)

        nearby, all_unique, excluded = get_nearby_observations(
            selected_observation=selected,
            observations=[selected, inside, outside],
            radius_km=5.0,
        )

        nearby_ids = [o.id for o in nearby]
        assert "center" in nearby_ids
        assert "nearby" in nearby_ids
        assert "far" not in nearby_ids
        assert excluded == 1

    def test_same_coordinate_included(self):
        selected = make_obs("p1", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 30.0)
        another_time = make_obs("p2", 21.1466, 79.0889, "2026-09-12T12:00:00.000Z", 28.0)

        nearby, _, excluded = get_nearby_observations(
            selected_observation=selected,
            observations=[selected, another_time],
            radius_km=5.0,
        )
        assert len(nearby) == 2
        assert excluded == 0

    def test_chronological_ordering(self):
        selected = make_obs("p3", 21.1466, 79.0889, "2026-09-13T14:00:00.000Z", 30.0)
        p1 = make_obs("p1", 21.1466, 79.0889, "2026-09-10T10:00:00.000Z", 15.0)
        p2 = make_obs("p2", 21.1466, 79.0889, "2026-09-12T11:00:00.000Z", 20.0)

        nearby, _, _ = get_nearby_observations(
            selected_observation=selected,
            observations=[selected, p1, p2],
            radius_km=5.0,
        )
        # Oldest first
        assert [o.id for o in nearby] == ["p1", "p2", "p3"]

    def test_deduplication(self):
        obs1 = make_obs("dup1", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 30.0)
        obs2 = make_obs("dup1", 21.1466, 79.0889, "2026-09-13T12:00:00.000Z", 30.0)  # Same ID
        obs3 = make_obs("diff_id", 21.146601, 79.088902, "2026-09-13T12:00:00.000Z", 30.0)  # Same rounded coord+time

        unique, excluded = deduplicate_observations([obs1, obs2, obs3])
        assert len(unique) == 1
        assert excluded == 2

    def test_invalid_coordinates_raise(self):
        selected = make_obs("bad", 21.0, 79.0, "2026-09-13T12:00:00.000Z", 30.0)
        object.__setattr__(selected, "latitude", 999.0)
        with pytest.raises(ValueError, match="Invalid selected observation coordinates"):
            get_nearby_observations(selected, [selected])
