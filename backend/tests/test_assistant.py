"""
Unit tests for AgniteAssistantService in AGNITE Phase 5A.

Verifies:
- Intent classification across all 12 intents
- Scientific explanations for classification, risk, history, persistence, OSM, alerts
- Model-aware explanation (heuristic today, trained ML tomorrow without code changes)
- Scientific honesty (never invent evidence; handle Insufficient evidence properly)
- Precautions framed as decision support rather than emergency orders
- Optional LLM fallback when disabled, failing, or timing out
"""

from __future__ import annotations

import asyncio
import pytest

from app.core.config import Settings
from app.providers.llm.base import LLMProvider
from app.schemas.assistant import ChatMessage
from app.services.agnite_service import AgniteAssistantService
from app.services.assistant_context_service import AssistantContext


@pytest.fixture
def base_settings():
    """Default settings with LLM disabled."""
    return Settings(
        enable_llm=False,
        llm_api_key="",
    )


@pytest.fixture
def rich_context():
    """Rich AssistantContext representing an industrial detection."""
    return AssistantContext(
        resolved=True,
        reference_type="analysis",
        analysis_id="analysis-101",
        latitude=21.1466,
        longitude=79.0889,
        current_frp=88.0,
        baseline_frp=20.0,
        frp_change_percent=340.0,
        distinct_times=6,
        span_hours=72.0,
        history_observation_count=6,
        classification="Industrial Fire",
        classification_confidence=91.0,
        classification_method="heuristic",
        model_name="agnite-heuristic-v1",
        risk_index=78,
        risk_level="High",
        risk_factors=["Thermal spike >300% above baseline", "Industrial infrastructure within 1 km"],
        persistence_score=45.0,
        persistence_status="moderate",
        recurrence_signal="intermittent_spike",
        industrial_distance_km=0.7,
        nearby_industrial_count=2,
        nearest_infrastructure_name="Steel Processing Unit",
        osm_status="present",
        watch_status="Location is inside monitored watch zone 'Nagpur Industrial' (threshold: 30 MW).",
        sources=["NASA FIRMS", "OpenStreetMap", "AGNITE historical database"],
        missing_evidence=["Local meteorological wind telemetry not available"],
    )


@pytest.mark.asyncio
class TestIntentClassificationAndExplanations:
    async def test_classification_explanation_heuristic(self, base_settings, rich_context):
        """Explains heuristic classification honestly without claiming ML."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Why was this hotspot classified this way?", rich_context)

        assert resp.mode == "deterministic"
        assert resp.grounded is True
        assert "Industrial Fire" in resp.answer
        assert "heuristic" in resp.answer
        assert "340.0%" in resp.answer
        assert "0.7 km" in resp.answer
        assert "NASA FIRMS" in resp.sources

    async def test_classification_explanation_future_ml_model(self, base_settings, rich_context):
        """When classification_method is 'ml', assistant automatically adapts without code change."""
        rich_context.classification_method = "ml"
        rich_context.model_name = "sonu-xgboost-thermal-v1"

        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Why was this hotspot classified this way?", rich_context)

        assert "sonu-xgboost-thermal-v1" in resp.answer
        assert "machine learning classifier" in resp.answer
        assert "heuristic" not in resp.answer

    async def test_classification_insufficient_evidence_never_confirms_fire(self, base_settings, rich_context):
        """When classification is Insufficient evidence, does not claim confirmed fire."""
        rich_context.classification = "Insufficient evidence"
        rich_context.missing_evidence = ["Only 1 observation pass recorded", "No baseline established"]

        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Explain the classification", rich_context)

        assert "Insufficient evidence" in resp.answer
        assert "do not provide enough verified evidence" in resp.answer
        assert "Multi-pass observation" in resp.answer

    async def test_risk_explanation_uses_actual_factors(self, base_settings, rich_context):
        """Risk explanation uses actual risk factors, FRP elevation and persistence."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Why is the risk high?", rich_context)

        assert "78/100" in resp.answer
        assert "High" in resp.answer
        assert "Thermal spike >300% above baseline" in resp.answer
        assert "decision support" in resp.answer

    async def test_risk_explanation_handles_missing_risk(self, base_settings):
        """Handles missing risk index gracefully."""
        ctx = AssistantContext(resolved=True, reference_type="coordinates", latitude=21.0, longitude=79.0)
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Why is the risk high?", ctx)

        assert "Quantitative risk scoring is not yet available" in resp.answer

    async def test_history_explanation(self, base_settings, rich_context):
        """Summarizes database observation count, span hours, and baseline comparison."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("What happened here previously?", rich_context)

        assert "6 observations" in resp.answer
        assert "72.0 hours" in resp.answer
        assert "20.0 MW" in resp.answer
        assert "88.0 MW" in resp.answer

    async def test_insufficient_history_handled(self, base_settings):
        """Explains when historical data is insufficient."""
        ctx = AssistantContext(
            resolved=True,
            reference_type="coordinates",
            latitude=21.0,
            longitude=79.0,
            history_observation_count=1,
        )
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("What is the history of this site?", ctx)

        assert "limited (1 observation(s) on record)" in resp.answer

    async def test_persistence_high_vs_low(self, base_settings, rich_context):
        """Distinguishes high continuous persistence from low acute persistence."""
        svc = AgniteAssistantService(settings=base_settings)

        # High persistence test
        rich_context.persistence_score = 88.0
        resp_high = await svc.answer("Is this a persistent thermal source?", rich_context)
        assert "temporarily stable" in resp_high.answer.lower() or "stable" in resp_high.answer.lower()

        # Low persistence test
        rich_context.persistence_score = 25.0
        resp_low = await svc.answer("Is this a persistent thermal source?", rich_context)
        assert "acute" in resp_low.answer.lower() or "low" in resp_low.answer.lower()

    async def test_osm_industrial_proximity_and_unavailable(self, base_settings, rich_context):
        """Explains industrial proximity and handles OSM unavailable warning."""
        svc = AgniteAssistantService(settings=base_settings)

        # Normal proximity
        resp = await svc.answer("Is there industrial infrastructure nearby?", rich_context)
        assert "Steel Processing Unit" in resp.answer
        assert "0.70 km" in resp.answer

        # OSM unavailable
        rich_context.osm_status = "unavailable"
        resp_unavail = await svc.answer("What industrial infrastructure is nearby?", rich_context)
        assert "unavailable or timed out" in resp_unavail.answer

    async def test_precautions_never_evacuate_command(self, base_settings, rich_context):
        """Precautions provide sensible decision support and avoid alarmist evacuation orders."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("What precautions should be taken?", rich_context)

        assert "field or industrial personnel" in resp.answer
        assert "Evacuate immediately" not in resp.answer
        assert "satellite overpasses" in resp.answer

    async def test_how_it_thinks_8_step_pipeline(self, base_settings, rich_context):
        """Answers pipeline queries with the transparent 8-step explanation."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("How did AGNITE reach this conclusion?", rich_context)

        assert "8-step thermal intelligence pipeline" in resp.answer
        assert "NASA Satellite Detection" in resp.answer
        assert "Baseline Comparison" in resp.answer
        assert "OpenStreetMap Spatial Context" in resp.answer

    async def test_missing_evidence_enumeration(self, base_settings, rich_context):
        """Accurately enumerates what evidence is missing."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("What evidence is missing?", rich_context)

        assert "Local meteorological wind telemetry" in resp.answer

    async def test_suggested_questions_included(self, base_settings, rich_context):
        """Response includes context-aware suggested follow-up questions."""
        svc = AgniteAssistantService(settings=base_settings)
        resp = await svc.answer("Summary of this hotspot", rich_context)

        assert len(resp.suggested_questions) > 0
        assert any("classified" in q for q in resp.suggested_questions)


@pytest.mark.asyncio
class TestOptionalLLMAndFallback:
    class FailingLLMProvider(LLMProvider):
        async def generate(self, question, context_dict, conversation_history) -> str:
            raise RuntimeError("Upstream LLM API error 500")

    class TimeoutLLMProvider(LLMProvider):
        async def generate(self, question, context_dict, conversation_history) -> str:
            await asyncio.sleep(0.01)
            raise TimeoutError("LLM generation timed out after 10s")

    class SuccessfulLLMProvider(LLMProvider):
        async def generate(self, question, context_dict, conversation_history) -> str:
            return "This is a grounded LLM generated response explaining the 88 MW signal."

    async def test_llm_failure_falls_back_to_deterministic(self, rich_context):
        """When LLM provider fails, assistant seamlessly returns deterministic answer."""
        settings = Settings(enable_llm=True, llm_api_key="mock-key")
        svc = AgniteAssistantService(settings=settings, llm_provider=self.FailingLLMProvider())

        resp = await svc.answer("Why is the risk high?", rich_context)
        assert resp.mode == "deterministic"
        assert resp.grounded is True
        assert "78/100" in resp.answer

    async def test_llm_timeout_falls_back_to_deterministic(self, rich_context):
        """When LLM provider times out, assistant falls back to deterministic."""
        settings = Settings(enable_llm=True, llm_api_key="mock-key")
        svc = AgniteAssistantService(settings=settings, llm_provider=self.TimeoutLLMProvider())

        resp = await svc.answer("What happened here before?", rich_context)
        assert resp.mode == "deterministic"
        assert "6 observations" in resp.answer

    async def test_llm_success_returns_llm_mode(self, rich_context):
        """When LLM succeeds, returns response with mode='llm' and grounded=True."""
        settings = Settings(enable_llm=True, llm_api_key="mock-key")
        svc = AgniteAssistantService(settings=settings, llm_provider=self.SuccessfulLLMProvider())

        resp = await svc.answer("Explain this hotspot", rich_context)
        assert resp.mode == "llm"
        assert resp.grounded is True
        assert "88 MW signal" in resp.answer
