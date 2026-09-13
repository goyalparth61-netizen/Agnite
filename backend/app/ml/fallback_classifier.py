"""
Deterministic Fallback Classifier for AGNITE Phase 2.

Implements ClassificationProvider using transparent, deterministic rules.
Does NOT claim to be an ML model (method = "heuristic").
Provides reliable offline classification and acts as the fallback when
the trained Sonu ML model is unavailable.
"""

from __future__ import annotations

import math
from typing import List

from app.core.constants import (
    CLASS_FOREST_FIRE,
    CLASS_INDUSTRIAL_FIRE,
    CLASS_INSUFFICIENT_EVIDENCE,
    CLASS_OTHER_ANOMALY,
    CLASS_PERSISTENT_HEAT,
    PERSISTENCE_STATUS_HIGH,
    PERSISTENCE_STATUS_MODERATE,
)
from app.schemas.analysis import AnalysisContext
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import (
    ClassificationPrediction,
    ClassScore,
)

CANDIDATE_CLASSES = [
    CLASS_INDUSTRIAL_FIRE,
    CLASS_PERSISTENT_HEAT,
    CLASS_FOREST_FIRE,
    CLASS_OTHER_ANOMALY,
]

LIMITATIONS = [
    "Transparent heuristic rule engine; no machine learning weights used.",
    "Does not replace on-site fire verification or satellite imagery ground truth.",
    "Heuristic scores reflect rule-based evidence matching, not calibrated statistical probabilities.",
]


class FallbackClassifier:
    """Deterministic, transparent rule-based classifier."""

    name: str = "agnite-heuristic-v1"
    version: str = "1.0"
    method: str = "heuristic"

    def predict(
        self, features: HotspotFeatures, context: AnalysisContext
    ) -> ClassificationPrediction:
        """
        Evaluate hotspot features against deterministic rules.

        Abstains with 'Insufficient evidence' if essential history, baseline passes,
        or site context (land cover, industrial distance) are missing.
        """
        reasons: List[str] = []

        # 1. History & baseline sufficiency checks
        has_baseline = features.baseline_frp is not None
        has_min_passes = features.distinct_passes_count >= 4
        has_min_span = features.span_hours >= 48.0

        if not has_min_passes or not has_min_span or not has_baseline:
            reasons.append(
                "At least four distinct observation times spanning 48 hours, "
                "including two baseline passes older than 24 hours, are required."
            )

        # 2. Context sufficiency checks
        if context.land_cover == "unknown" or context.industrial_distance_km is None:
            reasons.append(
                "Land cover and industrial distance are required to distinguish thermal causes."
            )

        # 3. If missing required evidence -> abstain
        if reasons:
            return ClassificationPrediction(
                classification=CLASS_INSUFFICIENT_EVIDENCE,
                status="abstained",
                confidence=0.0,
                model_score=None,
                scores=[],
                probabilities=None,
                method=self.method,
                model_name=self.name,
                model_version=self.version,
                training_source=None,
                metrics=None,
                sample_count=None,
                limitations=LIMITATIONS,
                reasons=reasons,
            )

        # 4. Calculate rule weights for candidate classes
        # Base indicators
        ind_dist = context.industrial_distance_km or 0.0
        ind_proximity = 1.0 / (1.0 + ind_dist / 2.0)  # ~1.0 if at industry, ~0 if far
        is_industrial_land = context.land_cover == "industrial"
        is_forest_land = context.land_cover == "forest"
        is_urban_land = context.land_cover == "urban"

        # FRP dynamics
        frp_escalation = max(0.0, features.log_baseline_ratio)
        current_intensity = math.log1p(features.current_frp) / math.log(201.0)
        persistence_norm = features.persistence_score / 100.0
        stability_norm = 1.0 / (1.0 + features.thermal_variability)

        # Class rule scores (unnormalized logits)
        # Persistent Industrial Heat:
        # High persistence + close industrial distance + stable FRP + industrial land
        persistent_score = (
            2.5 * persistence_norm
            + 2.0 * ind_proximity
            + 1.5 * stability_norm
            + (1.5 if is_industrial_land else 0.0)
            - 1.5 * frp_escalation
        )

        # Industrial Fire:
        # Industrial context + sharp FRP escalation + elevated intensity - high stability
        ind_fire_score = (
            2.5 * frp_escalation
            + 2.0 * ind_proximity
            + 1.5 * current_intensity
            + (1.5 if is_industrial_land else 0.0)
            - 0.5 * persistence_norm
        )

        # Forest / Natural Fire:
        # Forest land cover + far from industry + wind support + thermal escalation
        wind_sup = min(1.0, (context.wind_kph or 12.0) / 60.0) if is_forest_land else 0.0
        forest_score = (
            3.0 * (1.0 if is_forest_land else 0.0)
            + 1.5 * current_intensity
            + 1.0 * frp_escalation
            + 1.0 * wind_sup
            - 2.0 * ind_proximity
        )

        # Other Thermal Anomaly:
        # Urban or other land cover, or intermediate unclear signals
        anomaly_score = (
            1.5 * (1.0 if is_urban_land or context.land_cover == "other" else 0.0)
            + 1.0 * (1.0 - persistence_norm)
            + 0.5 * (1.0 - ind_proximity)
        )

        raw_scores = {
            CLASS_PERSISTENT_HEAT: persistent_score,
            CLASS_INDUSTRIAL_FIRE: ind_fire_score,
            CLASS_FOREST_FIRE: forest_score,
            CLASS_OTHER_ANOMALY: anomaly_score,
        }

        # Softmax normalization for relative scores
        max_s = max(raw_scores.values())
        exp_scores = {k: math.exp(v - max_s) for k, v in raw_scores.items()}
        total_exp = sum(exp_scores.values())
        probs = {k: v / total_exp for k, v in exp_scores.items()}

        ranked = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_class, top_score = ranked[0]
        runner_up_class, runner_up_score = ranked[1]

        # Check separation threshold
        if top_score < 0.38 or (top_score - runner_up_score) < 0.08:
            reasons.append(
                f"Candidate classes '{top_class}' and '{runner_up_class}' are not "
                f"sufficiently separated by heuristic rules."
            )
            return ClassificationPrediction(
                classification=CLASS_OTHER_ANOMALY,
                status="classified",
                confidence=round(top_score * 70.0, 1),
                model_score=round(top_score, 2),
                scores=[
                    ClassScore(label=k, score=round(v, 4)) for k, v in ranked
                ],
                probabilities={k: round(v, 4) for k, v in probs.items()},
                method=self.method,
                model_name=self.name,
                model_version=self.version,
                training_source=None,
                metrics=None,
                sample_count=None,
                limitations=LIMITATIONS,
                reasons=reasons,
            )

        # Derive conservative confidence (0-100)
        confidence = round(min(92.0, max(45.0, top_score * 100.0)), 1)

        return ClassificationPrediction(
            classification=top_class,
            status="classified",
            confidence=confidence,
            model_score=round(top_score, 2),
            scores=[ClassScore(label=k, score=round(v, 4)) for k, v in ranked],
            probabilities={k: round(v, 4) for k, v in probs.items()},
            method=self.method,
            model_name=self.name,
            model_version=self.version,
            training_source=None,
            metrics=None,
            sample_count=None,
            limitations=LIMITATIONS,
            reasons=[],
        )
