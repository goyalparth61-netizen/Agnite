"""
Persistence service for evaluating thermal recurrence and stability.

Distinguishes stable recurring heat sources (e.g. industrial flares, kilns, foundries)
from sudden abnormal thermal spikes or isolated fires.
Calculates persistence_score (0-100) and persistence_status.
"""

from __future__ import annotations

from app.core.constants import (
    PERSISTENCE_STATUS_HIGH,
    PERSISTENCE_STATUS_INSUFFICIENT,
    PERSISTENCE_STATUS_LOW,
    PERSISTENCE_STATUS_MODERATE,
)
from app.schemas.features import BaseHotspotFeatures, PersistenceResult


def calculate_persistence(base_features: BaseHotspotFeatures) -> PersistenceResult:
    """
    Calculate persistence score (0-100) and status from base hotspot features.

    Evaluates:
    - Unique observation days relative to span
    - Total number of satellite passes
    - FRP coefficient of variation (thermal stability)
    - Presence of an established historical baseline older than 24h
    """
    passes = base_features.distinct_passes_count
    days = base_features.unique_days
    span_days = max(1.0, base_features.history_duration_days)

    # Insufficient history for recurrence modeling
    if passes < 2 or base_features.span_hours < 1.0:
        return PersistenceResult(
            score=0.0,
            status=PERSISTENCE_STATUS_INSUFFICIENT,
            coverage_ratio=round(days / span_days, 3),
            stability_factor=1.0,
            details="Single detection or less than 1 hour span; persistence cannot be evaluated.",
        )

    # 1. Day coverage: fraction of calendar span observed (0.0 - 1.0)
    # Day coverage = days / max(1, calendar_span_days)
    calendar_span = max(1, int(base_features.history_duration_days) + 1)
    coverage_ratio = min(1.0, days / calendar_span)

    # 2. Pass density support: reward multiple distinct passes up to 8 passes
    pass_factor = min(1.0, (passes - 1) / 7.0)

    # 3. FRP stability factor: 1 / (1 + CV)
    cv = base_features.thermal_variability
    stability_factor = 1.0 / (1.0 + cv)

    # 4. Baseline presence support
    has_baseline = 1.0 if base_features.baseline_frp is not None else 0.0

    # Composite persistence score (0 to 100)
    # 35% day coverage + 25% pass factor + 25% stability + 15% baseline
    raw_score = (
        0.35 * coverage_ratio
        + 0.25 * pass_factor
        + 0.25 * stability_factor
        + 0.15 * has_baseline
    ) * 100.0

    score = round(max(0.0, min(100.0, raw_score)), 1)

    # Map to discrete persistence status
    if passes < 2:
        status = PERSISTENCE_STATUS_INSUFFICIENT
    elif score >= 65.0 and days >= 3:
        status = PERSISTENCE_STATUS_HIGH
    elif score >= 35.0:
        status = PERSISTENCE_STATUS_MODERATE
    else:
        status = PERSISTENCE_STATUS_LOW

    details = (
        f"Detected on {days} separate day(s) across {passes} satellite overpasses. "
        f"FRP stability factor: {stability_factor:.2f}. Score: {score}/100."
    )

    return PersistenceResult(
        score=score,
        status=status,
        coverage_ratio=round(coverage_ratio, 3),
        stability_factor=round(stability_factor, 3),
        details=details,
    )
