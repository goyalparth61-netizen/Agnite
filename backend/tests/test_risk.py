"""
Tests for risk engine (risk index bounds, severity levels, persistence decoupling, scenarios).
"""

from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.services.risk_service import calculate_risk


def make_features(
    current_frp: float = 20.0,
    baseline_frp: float | None = 20.0,
    frp_change_percent: float | None = 0.0,
    log_baseline_ratio: float = 0.0,
    persistence_score: float = 50.0,
    unique_days: int = 3,
) -> HotspotFeatures:
    return HotspotFeatures(
        current_frp=current_frp,
        maximum_frp=current_frp,
        minimum_frp=current_frp,
        mean_frp=current_frp,
        median_frp=current_frp,
        frp_std=0.0,
        baseline_frp=baseline_frp,
        frp_change=0.0 if baseline_frp else None,
        frp_change_percent=frp_change_percent,
        log_baseline_ratio=log_baseline_ratio,
        observation_count=5,
        distinct_passes_count=5,
        unique_days=unique_days,
        history_duration_days=5.0,
        span_hours=120.0,
        detection_frequency=unique_days / 5.0,
        thermal_variability=0.1,
        spatial_spread_km=0.5,
        cluster_size=5,
        persistence_score=persistence_score,
        persistence_status="HIGH_PERSISTENCE" if persistence_score >= 65 else "MODERATE_PERSISTENCE",
        recurrence_signal="HIGH",
    )


class TestRiskService:
    def test_risk_score_always_bounded_0_to_100(self):
        # Extreme low
        low_feat = make_features(current_frp=0.5, baseline_frp=10.0, log_baseline_ratio=-2.0)
        risk_low, _ = calculate_risk(low_feat, AnalysisContext())
        assert 0 <= risk_low.index <= 100

        # Extreme high
        high_feat = make_features(current_frp=2000.0, baseline_frp=10.0, log_baseline_ratio=5.0)
        risk_high, _ = calculate_risk(high_feat, AnalysisContext(landCover="forest", windKph=100.0))
        assert 0 <= risk_high.index <= 100

    def test_stable_persistent_source_is_not_high_risk(self):
        # High persistence (85), but current FRP is identical to baseline (0% change)
        feat = make_features(
            current_frp=25.0,
            baseline_frp=25.0,
            frp_change_percent=0.0,
            log_baseline_ratio=0.0,
            persistence_score=85.0,
            unique_days=6,
        )
        context = AnalysisContext(landCover="industrial", industrialDistanceKm=0.2)

        risk, _ = calculate_risk(feat, context)

        # Must NOT be High or Critical
        assert risk.index <= 50
        assert risk.level in ("Moderate", "Low")

    def test_sharp_spike_escalates_risk_to_critical_or_high(self):
        # Persistent site suddenly spikes by +150%
        feat = make_features(
            current_frp=150.0,
            baseline_frp=25.0,
            frp_change_percent=500.0,
            log_baseline_ratio=1.75,
            persistence_score=80.0,
            unique_days=5,
        )
        context = AnalysisContext(landCover="industrial", industrialDistanceKm=0.2)

        risk, _ = calculate_risk(feat, context)

        # Must escalate to High or Critical
        assert risk.index >= 75
        assert risk.level in ("High", "Critical")

    def test_scenarios_generated_properly(self):
        feat = make_features(current_frp=35.0, baseline_frp=25.0, log_baseline_ratio=0.3)
        risk, scenarios = calculate_risk(feat, AnalysisContext())

        assert len(scenarios) == 3
        horizons = [s.horizon for s in scenarios]
        assert horizons == ["24h", "48h", "7d"]

        for s in scenarios:
            assert s.low <= s.central <= s.high
            assert 0 <= s.low <= 100
            assert 0 <= s.high <= 100
            assert "WHAT-IF" in s.label
            assert "Scenario estimate — not a future-fire prediction" in s.assumption
