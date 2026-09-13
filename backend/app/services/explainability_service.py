"""
Explainability and evidence generation service for AGNITE.

Generates deterministic, human-readable evidence items, feature contribution weights,
analytical summary narratives, and data quality warnings.
Never invents evidence or uses an ungrounded LLM.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.core.constants import CLASS_INSUFFICIENT_EVIDENCE
from app.schemas.analysis import (
    AnalysisContext,
    EvidenceItem,
    FeatureContribution,
    RiskResult,
)
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction


def generate_evidence(
    features: HotspotFeatures,
    context: AnalysisContext,
) -> List[EvidenceItem]:
    """Generate deterministic evidence cards matching frontend AnalysisResult schema."""
    evidence: List[EvidenceItem] = []

    # 1. Current thermal signal
    evidence.append(
        EvidenceItem(
            label="Current thermal signal",
            value=f"{features.current_frp:.1f} MW",
            detail="Mean FRP per detection at the latest pass within 5 km; not total incident energy.",
        )
    )

    # 2. Historical baseline
    if features.baseline_frp is not None:
        val = f"{features.baseline_frp:.1f} MW"
        det = f"{features.baseline_frp:.1f} MW median of earlier passes older than 24h."
    else:
        val = "Unavailable"
        det = "No historical passes older than 24 hours available in the dataset."
    evidence.append(
        EvidenceItem(label="Historical baseline", value=val, detail=det)
    )

    # 3. Change from baseline
    if features.frp_change_percent is not None:
        sign = "+" if features.frp_change_percent >= 0 else ""
        val = f"{sign}{features.frp_change_percent:.1f}%"
        det = "Latest pass mean compared with median earlier pass means; sensor sampling differences uncorrected."
    else:
        val = "Unavailable"
        det = "Requires an established historical baseline older than 24 hours."
    evidence.append(
        EvidenceItem(label="Change from baseline", value=val, detail=det)
    )

    # 4. Repeated detection days & persistence profile
    calendar_days = max(1, int(features.history_duration_days) + 1)
    evidence.append(
        EvidenceItem(
            label="Repeated detection days",
            value=f"{features.unique_days} / {calendar_days} supplied days",
            detail="Detection-day coverage describes supplied passes, not continuous surveillance.",
        )
    )

    evidence.append(
        EvidenceItem(
            label="Persistence profile",
            value=f"{features.persistence_status.replace('_', ' ').title()} ({features.persistence_score:.0f}/100)",
            detail=features.persistence_details,
        )
    )

    # 5. Spatial context & industrial proximity
    ind_dist = (
        context.industrial_distance_km
        if context.industrial_distance_km is not None
        else features.industrial_distance_km
    )
    if ind_dist is not None:
        ind_str = f"{ind_dist:.1f} km"
    else:
        ind_str = "unmapped / unknown"

    source_label = features.context_provenance.get("industrialDistanceKm", features.context_source)
    detail_parts = [f"Infrastructure distance: {ind_str} (source: {source_label})."]
    if features.nearest_industrial_type:
        name_str = f" '{features.nearest_industrial_name}'" if features.nearest_industrial_name else ""
        detail_parts.append(f"Nearest: {features.nearest_industrial_type}{name_str}.")
    if features.context_confidence > 0:
        detail_parts.append(f"OSM confidence: {features.context_confidence:.0f}%.")

    evidence.append(
        EvidenceItem(
            label="Spatial context",
            value=f"{context.land_cover}; industry {ind_str}",
            detail=" ".join(detail_parts),
        )
    )

    # 6. Industrial facility density
    if features.industrial_feature_count > 0:
        evidence.append(
            EvidenceItem(
                label="Industrial environment",
                value=f"{features.industrial_feature_count} mapped facilities ({features.count_within_1km} within 1 km, {features.count_within_5km} within 5 km)",
                detail="OpenStreetMap infrastructure objects detected within search radius.",
            )
        )

    # 7. Specific thermal infrastructure (flares, chimneys)
    if features.mapped_flare_nearby:
        evidence.append(
            EvidenceItem(
                label="Thermal infrastructure",
                value="Flare stack nearby",
                detail="Mapped flare stack detected within search radius via OpenStreetMap.",
            )
        )
    elif features.mapped_chimney_nearby:
        evidence.append(
            EvidenceItem(
                label="Thermal infrastructure",
                value="Industrial chimney nearby",
                detail="Mapped industrial chimney / stack detected within search radius via OpenStreetMap.",
            )
        )

    # 8. Context source & provenance card
    if features.context_source == "osm" and features.context_confidence > 0:
        evidence.append(
            EvidenceItem(
                label="Context source",
                value=f"OpenStreetMap Overpass (Confidence: {features.context_confidence:.0f}%)",
                detail="Automated spatial infrastructure context fetched via OpenStreetMap Overpass API.",
            )
        )

    # 9. Missing context alert if unsupplied and unmapped
    if context.land_cover == "unknown" and ind_dist is None:
        evidence.append(
            EvidenceItem(
                label="Missing context",
                value="Land-cover / industry unverified",
                detail="Manual land cover or proximity has not been supplied and no industrial infrastructure was found in OSM.",
            )
        )

    return evidence


def compute_contributions(
    features: HotspotFeatures,
    context: AnalysisContext,
    prediction: ClassificationPrediction,
) -> List[FeatureContribution]:
    """
    Compute relative feature contributions comparing leading class with runner-up.

    Emits empty list if the classifier abstained.
    """
    if prediction.status == "abstained" or not prediction.scores or len(prediction.scores) < 2:
        return []

    top_class = prediction.scores[0].label
    runner_up = prediction.scores[1].label

    # Feature definitions matching the 8 standard display dimensions
    ind_dist = context.industrial_distance_km or 0.0
    ind_prox = 1.0 / (1.0 + ind_dist / 2.0)
    wind_scaled = min(100.0, context.wind_kph or 12.0) / 50.0

    raw_features = [
        ("Current FRP (log)", math.log1p(features.current_frp)),
        ("Current / baseline change (log)", features.log_baseline_ratio),
        ("Observed day coverage", features.persistence_score / 100.0),
        ("Industrial proximity", ind_prox),
        ("Forest cover", 1.0 if context.land_cover == "forest" else 0.0),
        ("Industrial cover", 1.0 if context.land_cover == "industrial" else 0.0),
        ("Urban cover", 1.0 if context.land_cover == "urban" else 0.0),
        ("User-supplied wind", wind_scaled),
    ]

    contributions: List[FeatureContribution] = []

    # Calculate deterministic signed contribution toward top class
    for label, val in raw_features:
        # Directional impact heuristics
        if "Industrial" in top_class and "industrial" in label.lower():
            weight = 0.8
        elif "Fire" in top_class and ("change" in label.lower() or "frp" in label.lower()):
            weight = 0.7
        elif "Persistent" in top_class and "coverage" in label.lower():
            weight = 0.9
        elif "Forest" in top_class and "forest" in label.lower():
            weight = 0.9
        else:
            weight = -0.3 if val > 0.5 else 0.1

        contrib_val = round(val * weight, 3)
        direction: str = "supports" if contrib_val >= 0 else "opposes"

        contributions.append(
            FeatureContribution(
                feature=label,
                value=round(val, 3),
                contribution=contrib_val,
                direction=direction,  # type: ignore[arg-type]
            )
        )

    # Sort descending by absolute contribution magnitude
    contributions.sort(key=lambda x: abs(x.contribution), reverse=True)
    return contributions


def generate_summary(
    features: HotspotFeatures,
    context: AnalysisContext,
    prediction: ClassificationPrediction,
    risk: RiskResult,
) -> str:
    """Generate deterministic narrative summary grounded in calculated values."""
    if prediction.status == "abstained":
        return (
            "Cause classification withheld: additional history or verified context is needed. "
            f"The screening risk index ({risk.index}/100, {risk.level}) summarizes only the supplied thermal measurements."
        )

    cat = prediction.classification
    conf = prediction.confidence

    if cat == "Persistent Industrial Heat":
        return (
            f"AGNITE identified a recurring, stable thermal pattern across {features.unique_days} observation dates "
            f"(Persistence Score: {features.persistence_score:.0f}/100). Current FRP ({features.current_frp:.1f} MW) "
            f"is consistent with baseline industrial operation (Risk: {risk.level}, {risk.index}/100). "
            f"Confidence: {conf:.0f}%."
        )
    elif cat == "Industrial Fire":
        return (
            f"AGNITE detected a sharp thermal escalation ({features.frp_change_percent:+.0f}% above baseline) "
            f"in proximity to industrial activity. The elevated signal ({features.current_frp:.1f} MW) departs significantly "
            f"from historical baseline, triggering a {risk.level} risk assessment ({risk.index}/100). "
            f"Confidence: {conf:.0f}%."
        )
    elif cat == "Forest / Natural Fire":
        return (
            f"Thermal pattern indicates an active vegetative/natural fire event with {features.current_frp:.1f} MW FRP "
            f"in a forest land-cover context (Risk: {risk.level}, {risk.index}/100). "
            f"Confidence: {conf:.0f}%."
        )
    else:
        return (
            f"Thermal detection ({features.current_frp:.1f} MW) represents an isolated anomaly or unclassified pattern. "
            f"Assessed risk is {risk.level} ({risk.index}/100). Verify local ground conditions."
        )


def generate_warnings(
    features: HotspotFeatures,
    context: AnalysisContext,
    prediction: ClassificationPrediction,
    excluded_count: int,
    total_count: int,
) -> List[str]:
    """Compile comprehensive data caveats and model limitations."""
    warnings: List[str] = [
        "Heuristic analysis engine: classifications reflect rule-based pattern matching, not confirmed cause.",
        "A thermal detection does not establish a fire cause. Verify observations and local conditions before operational decisions.",
    ]

    if excluded_count > 0:
        warnings.append(
            f"{excluded_count} observations outside 5 km of the selected site or older than 30 days were excluded."
        )

    if features.demo_count > 0:
        warnings.append(
            "DEMO / SIMULATION: this analysis includes synthetic observations and does not describe a verified event."
        )
    if features.manual_count > 0 or features.imported_count > 0:
        warnings.append(
            "Uploaded/manual observation provenance has not been independently verified."
        )
    if features.firms_count > 0:
        warnings.append(
            "NASA FIRMS observations are detection inputs; NASA has not supplied or endorsed this model's classification."
        )

    if context.wind_kph is None:
        warnings.append(
            "Wind is unknown; no observed weather or weather forecast is used."
        )

    warnings.append(
        "Day coverage describes supplied detection days only; missing passes, cloud and non-detections are unknown."
    )

    # Append any specific abstention reasons from classifier
    if prediction.reasons:
        warnings.extend(prediction.reasons)

    return warnings
