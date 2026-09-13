"""
Tests for ML provider abstraction and Sonu model pluggability.
"""

from unittest.mock import patch
from app.ml.fallback_classifier import FallbackClassifier
from app.ml.interfaces import ClassificationProvider
from app.ml.model_loader import load_classification_provider, reset_classification_provider
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction
from app.services.classification_service import classify_hotspot


def dummy_features() -> HotspotFeatures:
    return HotspotFeatures(
        current_frp=30.0,
        maximum_frp=30.0,
        minimum_frp=20.0,
        mean_frp=25.0,
        median_frp=25.0,
        frp_std=3.0,
        observation_count=5,
        distinct_passes_count=5,
        unique_days=4,
        history_duration_days=4.0,
        span_hours=96.0,
        detection_frequency=1.0,
        thermal_variability=0.12,
        spatial_spread_km=0.5,
        cluster_size=5,
        persistence_score=80.0,
        persistence_status="HIGH_PERSISTENCE",
        recurrence_signal="HIGH",
    )


class DummyCustomSonuModel:
    """Mock of Sonu's trained ML model implementing ClassificationProvider."""

    name: str = "sonu-randomforest-v2"
    version: str = "2.0"
    method: str = "ml"

    def predict(
        self, features: HotspotFeatures, context: AnalysisContext
    ) -> ClassificationPrediction:
        return ClassificationPrediction(
            classification="Persistent Industrial Heat",
            status="classified",
            confidence=94.5,
            model_score=0.945,
            method="ml",
            model_name=self.name,
            model_version=self.version,
        )


class TestMLProviderArchitecture:
    def teardown_method(self):
        reset_classification_provider()

    def test_fallback_selected_by_default(self):
        reset_classification_provider()
        provider = load_classification_provider()
        assert isinstance(provider, FallbackClassifier)
        assert provider.method == "heuristic"
        assert isinstance(provider, ClassificationProvider)

    def test_fallback_selected_when_model_artifact_missing(self):
        reset_classification_provider()
        from app.core.config import Settings
        with patch("app.ml.model_loader.get_settings", return_value=Settings(enable_ml_classifier=True)):
            provider = load_classification_provider()
            # File classifier.joblib does not exist, so gracefully falls back
            assert isinstance(provider, FallbackClassifier)
            assert provider.method == "heuristic"

    def test_pluggability_without_service_rewrites(self):
        """Demonstrates that Sonu's ML model plugs in seamlessly."""
        custom_model = DummyCustomSonuModel()
        assert isinstance(custom_model, ClassificationProvider)

        # Pass custom ML model into classification_service
        features = dummy_features()
        context = AnalysisContext()
        result = classify_hotspot(features, context, provider=custom_model)

        assert result.classification == "Persistent Industrial Heat"
        assert result.confidence == 94.5
        assert result.method == "ml"
        assert result.model_name == "sonu-randomforest-v2"
