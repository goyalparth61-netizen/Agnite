"""
Tests for persistence engine (heat stability, recurrence scoring, persistence bands).
"""

from app.schemas.features import BaseHotspotFeatures
from app.services.persistence_service import calculate_persistence


def make_base(
    passes: int = 5,
    days: int = 4,
    span_days: float = 5.0,
    span_hours: float = 120.0,
    cv: float = 0.15,
    has_baseline: bool = True,
) -> BaseHotspotFeatures:
    return BaseHotspotFeatures(
        current_frp=25.0,
        maximum_frp=30.0,
        minimum_frp=20.0,
        mean_frp=24.0,
        median_frp=24.0,
        frp_std=24.0 * cv,
        baseline_frp=23.0 if has_baseline else None,
        frp_change=2.0 if has_baseline else None,
        frp_change_percent=8.7 if has_baseline else None,
        log_baseline_ratio=0.08,
        observation_count=passes,
        distinct_passes_count=passes,
        unique_days=days,
        history_duration_days=span_days,
        span_hours=span_hours,
        detection_frequency=days / max(1.0, span_days),
        days_since_previous=1.0,
        average_detection_interval_hours=24.0,
        thermal_variability=cv,
        spatial_spread_km=0.8,
        cluster_size=passes,
    )


class TestPersistenceService:
    def test_insufficient_history(self):
        # Single detection
        base = make_base(passes=1, days=1, span_days=0.0, span_hours=0.0)
        res = calculate_persistence(base)
        assert res.status == "INSUFFICIENT_HISTORY"
        assert res.score == 0.0

    def test_stable_recurring_source_high_persistence(self):
        # 6 passes across 5 days, low coefficient of variation (0.10)
        base = make_base(passes=6, days=5, span_days=6.0, span_hours=144.0, cv=0.10)
        res = calculate_persistence(base)

        assert res.status == "HIGH_PERSISTENCE"
        assert 65.0 <= res.score <= 100.0
        assert res.coverage_ratio > 0.7
        assert res.stability_factor > 0.85

    def test_highly_variable_source_moderate_or_low_persistence(self):
        # High CV (thermal instability)
        base = make_base(passes=3, days=2, span_days=4.0, span_hours=96.0, cv=1.8)
        res = calculate_persistence(base)

        assert res.status in ("LOW_PERSISTENCE", "MODERATE_PERSISTENCE")
        assert res.score < 65.0

    def test_score_bounds_always_0_to_100(self):
        # Edge cases: 0 passes, extreme CV, huge passes
        extreme_high = make_base(passes=50, days=30, span_days=30.0, span_hours=720.0, cv=0.01)
        res_high = calculate_persistence(extreme_high)
        assert 0.0 <= res_high.score <= 100.0

        extreme_low = make_base(passes=2, days=1, span_days=1.0, span_hours=1.5, cv=10.0, has_baseline=False)
        res_low = calculate_persistence(extreme_low)
        assert 0.0 <= res_low.score <= 100.0
