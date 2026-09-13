"""
ML Classifier adapter for AGNITE.

Implements ClassificationProvider protocol by adapting an arbitrary scikit-learn
or joblib model artifact. Validates features against feature_schema.json, executes
predict_proba(), and converts predictions to standardized ClassificationPrediction.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.constants import CLASS_OTHER_ANOMALY
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction, ClassScore

logger = logging.getLogger("app.ml.classifier")


class MLClassifier:
    """Adapter for trained ML models (e.g. Sonu's Random Forest / XGBoost model)."""

    def __init__(
        self,
        model: Any,
        schema: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> None:
        self.model = model
        self.schema = schema
        self.metadata = metadata
        self.name = metadata.get("model_name", "agnite-ml-classifier")
        self.version = metadata.get("version", "1.0")
        self.method = "ml"
        self.classes = metadata.get(
            "classes",
            [
                "Industrial Fire",
                "Persistent Industrial Heat",
                "Forest / Natural Fire",
                "Other Thermal Anomaly",
            ],
        )

    def _extract_feature_vector(
        self, features: HotspotFeatures, context: AnalysisContext
    ) -> List[float]:
        """Convert typed features into ordered numerical vector according to schema."""
        feature_order = self.schema.get("feature_order", [])
        vector: List[float] = []

        is_forest = 1.0 if context.land_cover == "forest" else 0.0
        is_industrial = 1.0 if context.land_cover == "industrial" else 0.0
        is_urban = 1.0 if context.land_cover == "urban" else 0.0
        ind_dist = (
            context.industrial_distance_km
            if context.industrial_distance_km is not None
            else 10.0
        )
        wind = context.wind_kph if context.wind_kph is not None else 12.0
        base_frp = features.baseline_frp if features.baseline_frp is not None else 0.0
        change_pct = (
            features.frp_change_percent
            if features.frp_change_percent is not None
            else 0.0
        )

        lookup: Dict[str, float] = {
            "current_frp": float(features.current_frp),
            "baseline_frp": float(base_frp),
            "log_baseline_ratio": float(features.log_baseline_ratio),
            "frp_change_percent": float(change_pct),
            "persistence_score": float(features.persistence_score),
            "unique_days": float(features.unique_days),
            "distinct_passes_count": float(features.distinct_passes_count),
            "thermal_variability": float(features.thermal_variability),
            "industrial_distance_km": float(ind_dist),
            "forest_cover": is_forest,
            "industrial_cover": is_industrial,
            "urban_cover": is_urban,
            "wind_kph": float(wind),
        }

        for fname in feature_order:
            vector.append(lookup.get(fname, 0.0))

        return vector

    def predict(
        self, features: HotspotFeatures, context: AnalysisContext
    ) -> ClassificationPrediction:
        """Run ML model inference and return standardized prediction."""
        try:
            vec = self._extract_feature_vector(features, context)
            input_matrix = [vec]

            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(input_matrix)[0]
                model_classes = getattr(self.model, "classes_", self.classes)
                class_probs = {
                    str(c): float(p) for c, p in zip(model_classes, probs)
                }
            else:
                pred = self.model.predict(input_matrix)[0]
                class_probs = {str(c): (1.0 if c == pred else 0.0) for c in self.classes}

            ranked = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
            top_class, top_prob = ranked[0]
            confidence = round(top_prob * 100.0, 1)

            scores = [
                ClassScore(label=c, score=round(p, 4)) for c, p in ranked
            ]

            return ClassificationPrediction(
                classification=top_class,
                status="classified",
                confidence=confidence,
                model_score=round(top_prob, 2),
                scores=scores,
                probabilities=class_probs,
                method=self.method,
                model_name=self.name,
                model_version=self.version,
                training_source=self.metadata.get("algorithm", "Trained ML"),
                metrics=self.metadata.get("metrics"),
                sample_count=self.metadata.get("sample_count"),
                limitations=self.metadata.get("limitations", []),
                reasons=[],
            )
        except Exception as e:
            logger.error("ML model prediction error: %s", e)
            raise
