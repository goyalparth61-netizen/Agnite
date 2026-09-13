"""
Classification service for AGNITE.

Orchestrates prediction by dispatching to the configured ClassificationProvider
(either FallbackClassifier or MLClassifier).
"""

from __future__ import annotations

from typing import Optional

from app.ml.interfaces import ClassificationProvider
from app.ml.model_loader import load_classification_provider
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction


def classify_hotspot(
    features: HotspotFeatures,
    context: AnalysisContext,
    provider: Optional[ClassificationProvider] = None,
) -> ClassificationPrediction:
    """
    Classify thermal hotspot using the active classification provider.

    Accepts an optional provider instance (useful for dependency injection in tests).
    """
    active_provider = provider or load_classification_provider()
    return active_provider.predict(features, context)
