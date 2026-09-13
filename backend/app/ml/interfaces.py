"""
Classification provider interface protocol.

Allows interchangeable swapping between FallbackClassifier (heuristic rules)
and MLClassifier (trained Sonu model) without altering routes, services,
or the frontend contract.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction


@runtime_checkable
class ClassificationProvider(Protocol):
    """Protocol for thermal anomaly classification providers."""

    name: str
    version: str
    method: str

    def predict(
        self, features: HotspotFeatures, context: AnalysisContext
    ) -> ClassificationPrediction:
        """
        Predict thermal category, confidence, and class probabilities
        given a consolidated HotspotFeatures vector and site context.
        """
        ...
