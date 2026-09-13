"""
Tests for explainability service (evidence items, feature contributions, summary narratives).
"""

from app.schemas.analysis import AnalysisContext, RiskResult
from app.schemas.features import HotspotFeatures
from app.schemas.prediction import ClassificationPrediction, ClassScore
from app.services.explainability_service import (
    compute_contributions,
    generate_evidence,
    generate_summary,
    generate_warnings,
)


def make_sample_data():
    features = HotspotFeatures(
        current_frp=35.5,
        maximum_frp=35.5,
        minimum_frp=15.0,
        mean_frp=22.0,
        median_frp=20.0,
        frp_std=5.0,
        baseline_frp=20.0,
        frp_change=15.5,
        frp_change_percent=77.5,
        log_baseline_ratio=0.55,
        observation_count=6,
        distinct_passes_count=6,
        unique_days=5,
        history_duration_days=6.0,
        span_hours=144.0,
        detection_frequency=5 / 6.0,
        thermal_variability=0.23,
        spatial_spread_km=1.2,
        cluster_size=6,
        persistence_score=82.0,
        persistence_status="HIGH_PERSISTENCE",
        persistence_details="Detected on 5 separate days across 6 passes.",
        recurrence_signal="HIGH",
        firms_count=6,
    )
    context = AnalysisContext(
        industrialDistanceKm=0.8,
        landCover="industrial",
        windKph=15.0,
    )
    prediction = ClassificationPrediction(
        classification="Industrial Fire",
        status="classified",
        confidence=82.0,
        model_score=0.82,
        scores=[
            ClassScore(label="Industrial Fire", score=0.82),
            ClassScore(label="Persistent Industrial Heat", score=0.15),
        ],
        method="heuristic",
    )
    risk = RiskResult(
        index=78,
        level="Critical",
        method="Heuristic index",
        factors=["Elevated thermal intensity", "Significant departure from baseline"],
    )
    return features, context, prediction, risk


class TestExplainabilityService:
    def test_evidence_labels_and_values(self):
        features, context, _, _ = make_sample_data()
        evidence = generate_evidence(features, context)

        labels = {item.label: item for item in evidence}

        assert "Current thermal signal" in labels
        assert "35.5 MW" in labels["Current thermal signal"].value

        assert "Historical baseline" in labels
        assert "20.0 MW" in labels["Historical baseline"].value

        assert "Change from baseline" in labels
        assert "+77.5%" in labels["Change from baseline"].value

        assert "Persistence profile" in labels
        assert "High Persistence" in labels["Persistence profile"].value

        assert "Spatial context" in labels
        assert "industrial; industry 0.8 km" in labels["Spatial context"].value

    def test_missing_context_reported(self):
        features, _, _, _ = make_sample_data()
        context_missing = AnalysisContext(landCover="unknown", industrialDistanceKm=None)

        evidence = generate_evidence(features, context_missing)
        labels = {item.label: item for item in evidence}

        assert "Missing context" in labels
        assert "Land-cover / industry unverified" in labels["Missing context"].value

    def test_contributions_generated_when_classified(self):
        features, context, prediction, _ = make_sample_data()
        contributions = compute_contributions(features, context, prediction)

        assert len(contributions) > 0
        for c in contributions:
            assert c.feature
            assert c.direction in ("supports", "opposes")

    def test_contributions_empty_when_abstained(self):
        features, context, _, _ = make_sample_data()
        abstained_pred = ClassificationPrediction(
            classification="Insufficient evidence",
            status="abstained",
            confidence=0.0,
            scores=[],
            method="heuristic",
        )
        contributions = compute_contributions(features, context, abstained_pred)
        assert contributions == []

    def test_summary_narrative(self):
        features, context, prediction, risk = make_sample_data()
        summary = generate_summary(features, context, prediction, risk)

        assert "AGNITE detected a sharp thermal escalation" in summary
        assert "+78%" in summary or "+77%" in summary or "Critical" in summary
