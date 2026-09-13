"""
Tests for classification engine and FallbackClassifier deterministic rules.
"""

from app.ml.fallback_classifier import FallbackClassifier
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures


def make_features(
    current_frp: float = 25.0,
    baseline_frp: float | None = 22.0,
    frp_change_percent: float | None = 13.6,
    log_baseline_ratio: float = 0.12,
    persistence_score: float = 80.0,
    passes: int = 5,
    days: int = 4,
    span_hours: float = 96.0,
    thermal_var: float = 0.15,
) -> HotspotFeatures:
    return HotspotFeatures(
        current_frp=current_frp,
        maximum_frp=max(current_frp, baseline_frp or 0),
        minimum_frp=min(current_frp, baseline_frp or current_frp),
        mean_frp=(current_frp + (baseline_frp or current_frp)) / 2,
        median_frp=current_frp,
        frp_std=(current_frp - (baseline_frp or current_frp)) * 0.5,
        baseline_frp=baseline_frp,
        frp_change=(current_frp - baseline_frp) if baseline_frp else None,
        frp_change_percent=frp_change_percent,
        log_baseline_ratio=log_baseline_ratio,
        observation_count=passes,
        distinct_passes_count=passes,
        unique_days=days,
        history_duration_days=span_hours / 24.0,
        span_hours=span_hours,
        detection_frequency=days / max(1.0, span_hours / 24.0),
        thermal_variability=thermal_var,
        spatial_spread_km=0.5,
        cluster_size=passes,
        persistence_score=persistence_score,
        persistence_status="HIGH_PERSISTENCE" if persistence_score >= 65 else "MODERATE_PERSISTENCE",
        recurrence_signal="HIGH" if persistence_score >= 65 else "MODERATE",
    )


class TestClassification:
    def setup_method(self):
        self.classifier = FallbackClassifier()

    def test_persistent_industrial_heat_scenario(self):
        features = make_features(
            current_frp=28.0,
            baseline_frp=26.0,
            frp_change_percent=7.7,
            log_baseline_ratio=0.07,
            persistence_score=85.0,
            thermal_var=0.10,
        )
        context = AnalysisContext(
            industrialDistanceKm=0.3,
            landCover="industrial",
            windKph=10.0,
        )

        pred = self.classifier.predict(features, context)

        assert pred.classification == "Persistent Industrial Heat"
        assert pred.status == "classified"
        assert pred.method == "heuristic"
        assert pred.model_name == "agnite-heuristic-v1"
        assert 50.0 <= pred.confidence <= 100.0

    def test_industrial_fire_scenario(self):
        # Huge FRP spike (+300%) at industrial site
        features = make_features(
            current_frp=120.0,
            baseline_frp=25.0,
            frp_change_percent=380.0,
            log_baseline_ratio=1.54,
            persistence_score=40.0,  # Lower persistence or acute event
            thermal_var=0.9,
        )
        context = AnalysisContext(
            industrialDistanceKm=0.5,
            landCover="industrial",
            windKph=15.0,
        )

        pred = self.classifier.predict(features, context)

        assert pred.classification == "Industrial Fire"
        assert pred.status == "classified"
        assert pred.confidence >= 55.0

    def test_forest_natural_fire_scenario(self):
        features = make_features(
            current_frp=65.0,
            baseline_frp=15.0,
            frp_change_percent=333.0,
            log_baseline_ratio=1.42,
            persistence_score=25.0,
        )
        context = AnalysisContext(
            industrialDistanceKm=12.0,  # Far from industry
            landCover="forest",
            windKph=35.0,
        )

        pred = self.classifier.predict(features, context)

        assert pred.classification == "Forest / Natural Fire"
        assert pred.status == "classified"

    def test_insufficient_evidence_when_missing_context(self):
        features = make_features()
        # Missing land-cover and distance
        context = AnalysisContext(
            industrialDistanceKm=None,
            landCover="unknown",
            windKph=None,
        )

        pred = self.classifier.predict(features, context)

        assert pred.classification == "Insufficient evidence"
        assert pred.status == "abstained"
        assert pred.confidence == 0.0
        assert any("Land cover and industrial distance" in r for r in pred.reasons)

    def test_insufficient_evidence_when_insufficient_history(self):
        # Only 2 passes, 12 hours span (needs >= 4 passes, 48h)
        features = make_features(passes=2, span_hours=12.0, baseline_frp=None)
        context = AnalysisContext(
            industrialDistanceKm=1.0,
            landCover="industrial",
        )

        pred = self.classifier.predict(features, context)

        assert pred.classification == "Insufficient evidence"
        assert pred.status == "abstained"
        assert any("At least four distinct observation times" in r for r in pred.reasons)
