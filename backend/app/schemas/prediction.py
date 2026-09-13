"""
Prediction schemas for classification engine.

Standardized output schema for all classification providers (FallbackClassifier,
MLClassifier) implementing ClassificationProvider.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ClassScore(BaseModel):
    """Candidate class with relative score / probability."""

    label: str
    score: float = Field(..., ge=0, le=1)


class ClassificationPrediction(BaseModel):
    """Standardized prediction emitted by any ClassificationProvider."""

    classification: str = Field(
        ...,
        description="Predicted class or 'Insufficient evidence'",
    )
    status: Literal["classified", "abstained"] = "classified"
    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Conservative confidence (0-100) separate from risk",
    )
    model_score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Model softmax score / leading probability",
    )
    scores: List[ClassScore] = Field(default_factory=list)
    probabilities: Optional[Dict[str, float]] = None

    method: Literal["heuristic", "ml"] = "heuristic"
    model_name: str = "agnite-heuristic-v1"
    model_version: str = "1.0"
    training_source: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    sample_count: Optional[int] = None
    limitations: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "protected_namespaces": (),
    }
