"""
Risk engine for AGNITE Phase 2.

Computes a deterministic, transparent 0-100 screening risk index,
severity level ('Low' | 'Moderate' | 'High' | 'Critical'), contributing factors,
and what-if risk scenarios for 24h, 48h, and 7d horizons.

Guarantees that stable persistent thermal sources are NOT automatically
marked as high risk unless accompanied by acute thermal escalation.
"""

from __future__ import annotations

import math
from typing import List, Tuple

from app.core.constants import get_risk_level
from app.schemas.analysis import AnalysisContext, RiskResult, RiskScenario
from app.schemas.features import HotspotFeatures


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def calculate_risk(
    features: HotspotFeatures,
    context: AnalysisContext,
) -> Tuple[RiskResult, List[RiskScenario]]:
    """
    Calculate 0-100 risk score, severity tier, contributing factors, and what-if scenarios.

    Formulation:
    - Thermal Intensity (50%): log1p(current_frp) / log(201)
    - Baseline Escalation (30%): log_baseline_ratio / log(5)
    - Repeated Day Support (10%): (unique_days - 1) / 6
    - Wind / Fire Spread (10%): wind_kph / 60 if forest else 0

    Persistence Adjustment:
    - If persistence is HIGH and current FRP <= baseline: suppress escalation term to maintain Moderate risk.
    - If persistence is HIGH and current FRP > baseline (+70%+): amplify escalation to flag abnormal industrial flare/fire.
    """
    factors: List[str] = []

    # 1. Thermal Intensity Component (0.0 to 1.0)
    # 0 MW -> 0.0; ~50 MW -> ~0.74; 200+ MW -> 1.0
    intensity = _clamp(math.log1p(features.current_frp) / math.log(201.0))
    if features.current_frp >= 50.0:
        factors.append(f"Elevated thermal intensity: {features.current_frp:.1f} MW")

    # 2. Baseline Escalation Component (0.0 to 1.0)
    log_ratio = features.log_baseline_ratio
    escalation = _clamp(log_ratio / math.log(5.0))  # Ratio of 5x -> 1.0

    if features.baseline_frp is not None and features.frp_change_percent is not None:
        if features.frp_change_percent > 50.0:
            factors.append(
                f"Significant departure from historical baseline: +{features.frp_change_percent:.0f}%"
            )
        elif features.frp_change_percent < -30.0:
            factors.append(
                f"Thermal activity easing relative to baseline: {features.frp_change_percent:.0f}%"
            )

    # 3. Persistence & Repeat Support
    repeat_support = _clamp((features.unique_days - 1) / 6.0)
    if features.persistence_score >= 65.0:
        factors.append(
            f"High persistence source ({features.persistence_score:.0f}/100) on {features.unique_days} observation days"
        )

    # 4. Wind Spread Component (for forest / vegetative contexts)
    is_forest = context.land_cover == "forest"
    wind = context.wind_kph if context.wind_kph is not None else 0.0
    wind_support = _clamp(wind / 60.0) if is_forest else 0.0
    if is_forest and wind >= 25.0:
        factors.append(f"Elevated wind ({wind:.0f} km/h) in forest context")

    # 5. Combine into raw composite score (0 to 100)
    # 50% intensity + 30% escalation + 10% repeat + 10% wind
    raw_composite = (
        0.50 * intensity
        + 0.30 * escalation
        + 0.10 * repeat_support
        + 0.10 * wind_support
    )

    # Persistence decoupling:
    # If high persistence but stable or lower FRP, ensure index stays bounded in Moderate
    if features.persistence_score >= 65.0 and (
        features.frp_change_percent is None or features.frp_change_percent <= 20.0
    ):
        raw_composite = min(0.48, raw_composite)

    # Conversely, acute flare at a persistent site triggers critical attention
    if features.persistence_score >= 65.0 and (
        features.frp_change_percent is not None and features.frp_change_percent >= 80.0
    ):
        raw_composite = max(0.76, raw_composite)

    risk_index = int(round(_clamp(raw_composite) * 100.0))
    risk_level = get_risk_level(risk_index)

    method_desc = (
        "Heuristic 0–100 screening index: 50% log FRP intensity + 30% positive baseline change "
        "+ 10% repeated-day support + 10% supplied forest wind. Not a fire probability; "
        "missing baseline/weather terms contribute zero."
    )

    risk_result = RiskResult(
        index=risk_index,
        level=risk_level,
        method=method_desc,
        factors=factors,
    )

    # 6. What-If Risk Scenarios (24h, 48h, 7d)
    # These are strictly scenarios under easing, steady, or escalating assumptions.
    horizons: List[Tuple[str, float]] = [("24h", 1.0), ("48h", 1.5), ("7d", 2.5)]
    scenarios: List[RiskScenario] = []

    for h_name, multiplier in horizons:
        low_val = int(round(_clamp((risk_index - 12 * multiplier) / 100.0) * 100.0))
        central_val = risk_index
        high_val = int(
            round(
                _clamp((risk_index + (12 + wind_support * 8) * multiplier) / 100.0)
                * 100.0
            )
        )
        assumption = (
            f"Scenario estimate — not a future-fire prediction. "
            f"Illustrative easing / unchanged / escalating thermal conditions over {h_name}. "
            "Central assumes unchanged inputs; scenario bounds are what-if estimates, "
            "not statistical forecasts or fire predictions."
        )
        scenarios.append(
            RiskScenario(
                horizon=h_name,  # type: ignore[arg-type]
                low=low_val,
                central=central_val,
                high=high_val,
                label="WHAT-IF heuristic index range",
                assumption=assumption,
            )
        )

    return risk_result, scenarios
