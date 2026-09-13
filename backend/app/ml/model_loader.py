"""
Model loader singleton for AGNITE.

Loads the classification provider once during FastAPI startup.
Controlled by ENABLE_ML_CLASSIFIER:
- When false: returns FallbackClassifier (heuristic rules)
- When true and artifact exists: returns MLClassifier
- When true but artifact missing/broken: logs warning, gracefully returns FallbackClassifier
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.ml.fallback_classifier import FallbackClassifier
from app.ml.interfaces import ClassificationProvider

logger = logging.getLogger("app.ml.model_loader")

_LOADED_PROVIDER: Optional[ClassificationProvider] = None


def get_artifacts_dir() -> Path:
    """Return path to app/ml/artifacts."""
    return Path(__file__).parent / "artifacts"


def load_classification_provider() -> ClassificationProvider:
    """Load and cache classification provider according to environment configuration."""
    global _LOADED_PROVIDER
    if _LOADED_PROVIDER is not None:
        return _LOADED_PROVIDER

    settings = get_settings()
    artifacts_dir = get_artifacts_dir()

    if not settings.enable_ml_classifier:
        logger.info("ML classifier disabled (ENABLE_ML_CLASSIFIER=false); using FallbackClassifier.")
        _LOADED_PROVIDER = FallbackClassifier()
        return _LOADED_PROVIDER

    model_path = artifacts_dir / "classifier.joblib"
    schema_path = artifacts_dir / "feature_schema.json"
    metadata_path = artifacts_dir / "model_metadata.json"

    if not model_path.exists():
        logger.warning(
            "ENABLE_ML_CLASSIFIER=true but %s not found. Falling back to FallbackClassifier.",
            model_path,
        )
        _LOADED_PROVIDER = FallbackClassifier()
        return _LOADED_PROVIDER

    try:
        import joblib

        model = joblib.load(model_path)
        schema = {}
        metadata = {}

        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        from app.ml.classifier import MLClassifier

        logger.info("Successfully loaded ML model from %s", model_path)
        _LOADED_PROVIDER = MLClassifier(model=model, schema=schema, metadata=metadata)
        return _LOADED_PROVIDER
    except Exception as e:
        logger.error(
            "Failed to load ML model artifact (%s). Falling back to FallbackClassifier.", e
        )
        _LOADED_PROVIDER = FallbackClassifier()
        return _LOADED_PROVIDER


def reset_classification_provider() -> None:
    """Reset cached provider (useful for testing provider switching)."""
    global _LOADED_PROVIDER
    _LOADED_PROVIDER = None
