"""
Tests for history service (temporal grouping, stats, baseline calculation).
"""

import pytest
from app.schemas.observation import Observation
from app.services.history_service import compute_history


def make_obs(id_str: str, dt_str: str, frp: float) -> Observation:
    return Observation(
        id=id_str,
        latitude=21.1466,
        longitude=79.0889,
        observedAt=dt_str,
        frp=frp,
        source="firms",
    )


class TestHistoryService:
    def test_single_observation(self):
        obs = [make_obs("o1", "2026-09-13T12:00:00.000Z", 25.0)]
        h = compute_history(obs)

        assert h.observation_count == 1
        assert h.distinct_passes_count == 1
        assert h.current_frp == 25.0
        assert h.baseline_frp is None
        assert h.frp_change is None
        assert h.span_hours == 0.0
        assert h.unique_days_count == 1
        assert len(h.timeline) == 1

    def test_overpass_pixel_aggregation(self):
        # 2 pixels at the exact same timestamp
        p1 = make_obs("p1", "2026-09-13T12:00:00.000Z", 20.0)
        p2 = make_obs("p2", "2026-09-13T12:00:00.000Z", 40.0)

        h = compute_history([p1, p2])
        assert h.observation_count == 2
        assert h.distinct_passes_count == 1
        # Mean of pass pixels: (20 + 40) / 2 = 30.0
        assert h.current_frp == 30.0
        assert h.passes[0].pixel_count == 2

    def test_baseline_median_older_than_24h(self):
        # Latest pass: Sep 13 at 12:00
        # Cutoff: Sep 12 at 12:00
        # Baseline candidates must be < cutoff
        p_base1 = make_obs("b1", "2026-09-10T10:00:00.000Z", 10.0)
        p_base2 = make_obs("b2", "2026-09-11T10:00:00.000Z", 20.0)
        p_base3 = make_obs("b3", "2026-09-12T08:00:00.000Z", 30.0)
        # Pass within last 24h (not in baseline)
        p_recent = make_obs("r1", "2026-09-13T02:00:00.000Z", 50.0)
        # Current pass
        p_current = make_obs("c1", "2026-09-13T12:00:00.000Z", 60.0)

        h = compute_history([p_base1, p_base2, p_base3, p_recent, p_current])

        # Median of [10.0, 20.0, 30.0] = 20.0
        assert h.baseline_frp == 20.0
        assert h.baseline_passes_count == 3
        assert h.current_frp == 60.0
        # Change: 60 - 20 = 40.0
        assert h.frp_change == 40.0
        # Percentage: (60 / 20 - 1) * 100 = 200.0%
        assert h.frp_change_percentage == 200.0
        assert h.previous_frp == 50.0

    def test_statistics_and_intervals(self):
        p1 = make_obs("p1", "2026-09-10T00:00:00.000Z", 10.0)
        p2 = make_obs("p2", "2026-09-11T12:00:00.000Z", 20.0)
        p3 = make_obs("p3", "2026-09-13T00:00:00.000Z", 30.0)

        h = compute_history([p1, p2, p3])

        assert h.maximum_frp == 30.0
        assert h.minimum_frp == 10.0
        assert h.mean_frp == 20.0
        assert h.median_frp == 20.0
        assert h.span_hours == 72.0
        assert h.unique_days_count == 3
        # Days since previous: Sep 11 12:00 to Sep 13 00:00 = 36h = 1.5 days
        assert h.days_since_previous == 1.5

    def test_empty_observations_raise(self):
        with pytest.raises(ValueError, match="Cannot compute history"):
            compute_history([])
