"""
AGNITE AI Assistant Service (Phase 5A).

Provides transparent, auditable, and scientifically honest explanations grounded
in NASA FIRMS satellite observations, OpenStreetMap context, historical intelligence,
risk scoring, and classification engines.

Core Principles:
1. 100% Deterministic by default (zero external LLM / API key dependencies).
2. Never fabricates evidence or coordinates; explicitly reports missing evidence.
3. Automatically adapts between explainable heuristic rules and trained ML models.
4. Frames recommendations as decision-support guidance, not operational alarms.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings
from app.providers.llm.base import LLMProvider
from app.schemas.assistant import AssistantChatResponse, ChatMessage
from app.services.assistant_context_service import AssistantContext

logger = logging.getLogger("app.services.agnite_service")


class AgniteAssistantService:
    """Core explanation and question-answering service for AGNITE."""

    def __init__(self, settings: Settings, llm_provider: Optional[LLMProvider] = None):
        self._settings = settings
        self._llm_provider = llm_provider

    async def answer(
        self,
        question: str,
        context: AssistantContext,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> AssistantChatResponse:
        """
        Process user query and return grounded, structured response.
        Attempts optional LLM generation if enabled; always safely falls back
        to the deterministic engine.
        """
        conversation_history = conversation_history or []

        # ── Optional LLM Execution (Behind ENABLE_LLM) ───────────────
        if self._settings.enable_llm and self._llm_provider:
            try:
                llm_answer = await self._llm_provider.generate(
                    question=question,
                    context_dict=context.model_dump(),
                    conversation_history=conversation_history,
                )
                if llm_answer and llm_answer.strip():
                    return self._build_response(
                        answer=llm_answer.strip(),
                        mode="llm",
                        context=context,
                    )
            except Exception as exc:
                logger.warning(
                    "Optional LLM generation failed or timed out: %s. Falling back to deterministic assistant.",
                    exc,
                )

        # ── Deterministic Grounded Reasoning ─────────────────────────
        intent = self._classify_intent(question, conversation_history)
        answer = self._generate_deterministic_answer(intent, context, question)
        return self._build_response(
            answer=answer,
            mode="deterministic",
            context=context,
        )

    def _classify_intent(
        self, question: str, conversation_history: List[ChatMessage]
    ) -> str:
        """Determine question intent using conversational keyword matching."""
        q = question.lower()

        # How did it think / pipeline
        if re.search(r"how did (you|agnite)|reach this conclusion|thought process|pipeline|how does it work|how it works", q):
            return "how_it_works"

        # Precautions / Recommendations / Actions
        if re.search(r"precaution|recommend|action|inspect|what should (we|authorities|i)|guidance|response|safeguard", q):
            return "precautions"

        # Missing evidence
        if re.search(r"missing|lack|need more|incomplete|what.*(missing|absent|needed)|kami", q):
            return "missing_evidence"

        # Evidence / Proof / Data points
        if re.search(r"evidence|proof|basis|data point|support.*result|observations", q) and not re.search(r"miss", q):
            return "evidence"

        # Classification explanation
        if re.search(r"why.*class|explain.*class|how.*classified|classification|kyu|reason for class", q):
            return "classification_explanation"

        # Risk explanation
        if re.search(r"risk|danger|threat|severity|why.*high.*risk|why.*risk", q):
            return "risk_explanation"

        # Persistence
        if re.search(r"persist|stable source|continuous heat|flare|permanent", q):
            return "persistence"

        # Recurrence
        if re.search(r"recur|pattern|frequency|cycle|repeat|how often", q):
            return "recurrence"

        # Industrial context / OSM
        if re.search(r"industrial|factory|plant|infrastructure|osm|nearby.*(building|facility)|chimney|refinery", q):
            return "industrial_context"

        # History / Past
        if re.search(r"history|happened.*(before|previously)|past|baseline|earlier", q):
            return "history"

        # Watches / Alerts
        if re.search(r"alert|watch|monitor|notif|alarm", q):
            return "alerts"

        # Summary / Overview
        if re.search(r"summary|overview|status|what is this|tell me about", q):
            return "summary"

        return "general"

    def _generate_deterministic_answer(
        self, intent: str, context: AssistantContext, original_question: str
    ) -> str:
        """Assemble fully grounded explanation using verified backend context."""
        # Check if reference is completely unresolved
        if not context.resolved or context.reference_type == "none":
            return (
                "AGNITE does not currently have a selected hotspot or analysis record to evaluate. "
                "Please select an observation on the satellite feed or run site analysis first. "
                f"Missing information: {', '.join(context.missing_evidence) if context.missing_evidence else 'No reference coordinates.'}"
            )

        if intent == "classification_explanation":
            return self._explain_classification(context)
        elif intent == "risk_explanation":
            return self._explain_risk(context)
        elif intent == "history":
            return self._explain_history(context)
        elif intent == "persistence":
            return self._explain_persistence(context)
        elif intent == "recurrence":
            return self._explain_recurrence(context)
        elif intent == "industrial_context":
            return self._explain_industrial_context(context)
        elif intent == "evidence":
            return self._explain_evidence(context)
        elif intent == "missing_evidence":
            return self._explain_missing_evidence(context)
        elif intent == "precautions":
            return self._explain_precautions(context)
        elif intent == "alerts":
            return self._explain_alerts(context)
        elif intent == "how_it_works":
            return self._explain_how_it_works(context)
        elif intent == "summary":
            return self._explain_summary(context)
        else:
            return self._explain_general(context, original_question)

    def _explain_classification(self, context: AssistantContext) -> str:
        """Transparent explanation of classification results and model metadata."""
        if not context.classification:
            return (
                "Classification has not yet been performed for this site. "
                "Run site analysis to calculate feature vectors and generate an explainable classification."
            )

        # Requirement 5: Insufficient evidence must not be explained as a definitive fire
        if context.classification.lower() == "insufficient evidence":
            missing_str = "; ".join(context.missing_evidence) if context.missing_evidence else "limited satellite passes"
            return (
                f"AGNITE classified this site as '{context.classification}'. "
                "The available satellite detections and spatial context do not provide enough verified evidence "
                "to confirm or rule out an active thermal event. "
                f"Key missing factors include: {missing_str}. "
                "Multi-pass observation over 48+ hours and local field verification are required."
            )

        # Model methodology disclosure (Requirement 24: heuristic vs ML)
        method = context.classification_method or "heuristic"
        model_name = context.model_name or "agnite-heuristic-v1"
        if method == "ml":
            engine_desc = f"the trained {model_name} machine learning classifier"
        else:
            engine_desc = f"its explainable heuristic classification engine ({model_name})"

        conf_str = f" with {context.classification_confidence:.1f}% estimated confidence" if context.classification_confidence is not None else ""
        frp_str = f"{context.current_frp:.1f} MW" if context.current_frp is not None else "an unquantified"

        reasons = []
        if context.baseline_frp is not None and context.current_frp is not None:
            if context.frp_change_percent is not None:
                reasons.append(
                    f"the current {frp_str} thermal signal is {context.frp_change_percent:+.1f}% relative to its historical baseline of {context.baseline_frp:.1f} MW"
                )
        if context.industrial_distance_km is not None:
            reasons.append(f"mapped industrial infrastructure is approximately {context.industrial_distance_km:.1f} km away")
        if context.persistence_score is not None:
            reasons.append(f"the site shows a persistence score of {context.persistence_score:.0f}/100 ({context.persistence_status or 'evaluated'})")

        # Feature contributions if present
        contrib_text = ""
        if context.contributions:
            top_contribs = context.contributions[:2]
            c_desc = [f"{c['feature']} ({c['direction']} leading classification)" for c in top_contribs]
            contrib_text = f" Key contributing features include: {', '.join(c_desc)}."

        reason_text = f" This result was derived because {'; '.join(reasons)}." if reasons else ""

        return (
            f"AGNITE classified this detection as '{context.classification}'{conf_str} using {engine_desc}."
            f"{reason_text}{contrib_text} "
            "Note: Satellite thermal detections indicate surface heat emissions and require ground context for absolute confirmation."
        )

    def _explain_risk(self, context: AssistantContext) -> str:
        """Detailed breakdown of risk index, factors, and baseline deviations."""
        if context.risk_index is None:
            return (
                "Quantitative risk scoring is not yet available for this location. "
                "Run site analysis to calculate the transparent 0-100 risk index."
            )

        level = context.risk_level or "Unrated"
        index = context.risk_index

        parts = [f"AGNITE currently evaluates this site at a risk index of {index}/100 ({level})."]

        # Actual risk factors (no fabricated factors)
        if context.risk_factors:
            factors_str = "; ".join(context.risk_factors)
            parts.append(f"Primary risk factors identified: {factors_str}.")
        elif context.current_frp is not None and context.baseline_frp is not None:
            if context.frp_change_percent is not None and context.frp_change_percent > 50:
                parts.append(
                    f"Risk is driven by a significant thermal elevation: current FRP of {context.current_frp:.1f} MW "
                    f"is {context.frp_change_percent:+.1f}% above the historical baseline of {context.baseline_frp:.1f} MW."
                )
            else:
                parts.append(
                    f"Current FRP is {context.current_frp:.1f} MW against a baseline of {context.baseline_frp:.1f} MW."
                )

        if context.persistence_score is not None:
            if context.persistence_score >= 70:
                parts.append(
                    f"High persistence ({context.persistence_score:.0f}/100) indicates a recurring thermal source, "
                    "which moderates acute wildland risk while confirming sustained industrial heat."
                )
            elif context.persistence_score < 40:
                parts.append(
                    f"Low persistence ({context.persistence_score:.0f}/100) highlights this as an acute, non-steady thermal anomaly."
                )

        if context.warnings:
            parts.append(f"Operational notes: {' '.join(context.warnings[:2])}")

        parts.append(
            "This index is an objective screening metric for decision support, not an emergency evacuation order."
        )
        return " ".join(parts)

    def _explain_history(self, context: AssistantContext) -> str:
        """Summary of historical multi-pass database intelligence."""
        count = context.history_observation_count
        if count < 2:
            return (
                f"Historical observations for this location are limited ({count} observation(s) on record). "
                "Reliable baseline calculations require multiple satellite passes over a 48+ hour window. "
                "Currently, historical trends cannot be validated with high statistical confidence."
            )

        details = [f"Database history includes {count} observations near this location."]
        if context.distinct_times:
            details.append(f"These span {context.distinct_times} distinct satellite acquisition passes")
            if context.span_hours:
                details.append(f"over {context.span_hours:.1f} hours.")
            else:
                details.append(".")

        if context.baseline_frp is not None and context.current_frp is not None:
            diff = context.current_frp - context.baseline_frp
            diff_str = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
            pct_str = f" ({context.frp_change_percent:+.1f}%)" if context.frp_change_percent is not None else ""
            details.append(
                f"The historical baseline FRP is {context.baseline_frp:.1f} MW, whereas the latest observed signal "
                f"is {context.current_frp:.1f} MW ({diff_str} MW deviation{pct_str})."
            )

        if context.recurrence_signal:
            details.append(f"Observed recurrence behavior: {context.recurrence_signal}.")

        return " ".join(details)

    def _explain_persistence(self, context: AssistantContext) -> str:
        """Explanation of persistence scoring and temporal stability."""
        if context.persistence_score is None:
            return (
                "Persistence scoring requires multi-pass historical observations to evaluate temporal stability. "
                "With single-pass or missing history, persistence cannot yet be computed."
            )

        score = context.persistence_score
        status = context.persistence_status or "evaluated"

        if score >= 70:
            return (
                f"Persistence is high at {score:.0f}/100 ({status}). "
                "This indicates a temporally stable, recurring thermal emitter, consistent with continuous industrial "
                "operations such as flare stacks, blast furnaces, or cement kilns rather than an uncontained wildland blaze."
            )
        elif score >= 40:
            return (
                f"Persistence is moderate at {score:.0f}/100 ({status}). "
                "The thermal signature shows intermittent or fluctuating activity across satellite passes, "
                "differentiating it from both constant stationary industrial emitters and brief single-pass flares."
            )
        else:
            return (
                f"Persistence is low at {score:.0f}/100 ({status}). "
                "The thermal anomaly appears acute or recently emergent, showing high variance from past passes "
                "and lacking the stable profile of established industrial thermal infrastructure."
            )

    def _explain_recurrence(self, context: AssistantContext) -> str:
        """Explanation of recurrence signals."""
        if not context.recurrence_signal:
            return (
                "Recurrence signal has not been established. Multi-day satellite observations "
                "are required to determine whether heat events recur on regular diurnal or weekly cycles."
            )

        sig = context.recurrence_signal.replace("_", " ").title()
        return (
            f"AGNITE's recurrence signal for this site is '{sig}'. "
            "This metric assesses how consistently thermal anomalies reappear across distinct satellite overpasses, "
            "distinguishing between routine facility operations and unexpected thermal spikes."
        )

    def _explain_industrial_context(self, context: AssistantContext) -> str:
        """Detail mapped OpenStreetMap infrastructure proximity."""
        if context.osm_status == "unavailable":
            return (
                "OpenStreetMap spatial data was unavailable or timed out during analysis. "
                "Nearby industrial proximity could not be verified automatically, and default spatial assumptions were applied."
            )

        if context.industrial_distance_km is not None:
            dist = context.industrial_distance_km
            name = context.nearest_infrastructure_name or "industrial facility"
            count = context.nearby_industrial_count

            if dist <= 1.0:
                proximity_desc = f"in immediate proximity ({dist:.2f} km)"
            elif dist <= 5.0:
                proximity_desc = f"within regional proximity ({dist:.2f} km)"
            else:
                proximity_desc = f"at a distance of {dist:.2f} km"

            count_str = f" (among {count} mapped industrial features within 5 km)" if count > 1 else ""
            return (
                f"Mapped industrial infrastructure ({name}) was identified {proximity_desc}{count_str} via OpenStreetMap. "
                "Industrial proximity supports classification of routine or industrial thermal processes."
            )

        return (
            "No mapped industrial facilities were identified within the 5 km radius in the OpenStreetMap database. "
            "However, unmapped facilities or agricultural operations may still be present in the area."
        )

    def _explain_evidence(self, context: AssistantContext) -> str:
        """Enumerate supporting evidence items and observations."""
        if not context.evidence_items:
            # Fallback to synthesizing what telemetry we have
            items = []
            if context.current_frp is not None:
                items.append(f"Observed Fire Radiative Power (FRP): {context.current_frp:.1f} MW")
            if context.brightness is not None:
                items.append(f"Sensor Brightness Temperature: {context.brightness:.1f} K")
            if context.satellite or context.sensor:
                items.append(f"Observing Platform: {context.satellite or 'Satellite'} / {context.sensor or 'Sensor'}")
            if context.history_observation_count:
                items.append(f"Recorded Nearby Passes: {context.history_observation_count} observations")

            if not items:
                return "No supporting observational evidence is currently loaded for this site."
            return "Supporting observational evidence on record: " + "; ".join(items) + "."

        evidence_bullets = [f"{e['label']}: {e['value']} ({e['detail']})" for e in context.evidence_items[:5]]
        return "Evidence supporting this assessment includes: " + "; ".join(evidence_bullets) + "."

    def _explain_missing_evidence(self, context: AssistantContext) -> str:
        """Explicitly detail missing variables, sensor boundaries, and unqueried inputs."""
        if not context.missing_evidence and not context.model_limitations:
            return (
                "The analysis incorporates core satellite telemetry, historical baseline, and spatial context. "
                "However, real-time ground verification and meteorological telemetry (such as local wind gusts) "
                "are not collected automatically and should be reviewed locally."
            )

        missing_list = list(context.missing_evidence)
        if context.model_limitations:
            missing_list.extend(context.model_limitations[:2])

        return (
            "The following evidence is currently missing or constrained: "
            + "; ".join(missing_list)
            + ". Ground inspections and complementary sensors should be consulted before operational decisions."
        )

    def _explain_precautions(self, context: AssistantContext) -> str:
        """Grounded decision-support recommendations (Requirement 11)."""
        recs = []

        # Ground verification
        recs.append("Dispatch local field or industrial personnel to visually verify the hotspot source.")

        # Industrial checks
        if context.industrial_distance_km is not None and context.industrial_distance_km <= 2.0:
            recs.append("Review industrial thermal management systems, flare stack operations, and kiln telemetry at nearby facilities.")

        # FRP Trend monitoring
        if context.current_frp is not None and context.baseline_frp is not None and context.current_frp > context.baseline_frp:
            recs.append("Monitor the upcoming satellite overpasses to determine whether FRP intensity is stabilizing or escalating.")
        else:
            recs.append("Compare upcoming satellite passes (VIIRS/MODIS) to monitor signal continuation.")

        # Vegetative / natural checks
        if context.classification and "natural" in context.classification.lower():
            recs.append("Inspect surrounding vegetation, wind direction, and buffer zones for potential wildfire spread.")

        # Historical review
        if context.history_observation_count > 2:
            recs.append("Cross-reference plant operational logs with past historical detections to verify planned flaring.")

        formatted_recs = "; ".join(recs[:4])
        return (
            f"Recommended decision-support precautions: {formatted_recs}. "
            "Note: These recommendations represent screening precautions based on satellite thermal telemetry, not emergency orders."
        )

    def _explain_alerts(self, context: AssistantContext) -> str:
        """Explain watch locations and triggered alerts."""
        parts = []
        if context.watch_status:
            parts.append(context.watch_status)

        if context.recent_alerts:
            alert_descs = [
                f"[{a['severity'].upper()}] {a['title']}: {a['message']}"
                for a in context.recent_alerts[:3]
            ]
            parts.append(f"Active alerts on record: {'; '.join(alert_descs)}.")
        else:
            parts.append("No active alerts are currently triggered for this location.")

        return " ".join(parts)

    def _explain_how_it_works(self, context: AssistantContext) -> str:
        """Step-by-step transparent explanation of the 8-step AGNITE pipeline (Requirement 12)."""
        method = context.classification_method or "heuristic"
        model_name = context.model_name or "agnite-heuristic-v1"

        if method == "ml":
            engine_text = f"Trained Machine Learning Model ({model_name})"
        else:
            engine_text = f"Explainable Heuristic Classification Engine ({model_name})"

        return (
            "AGNITE reached this conclusion through its transparent 8-step thermal intelligence pipeline: "
            "1. NASA Satellite Detection: Captured raw thermal radiative emission (FRP, brightness temperature). "
            "2. Database History Query: Retrieved historical satellite passes within a 5 km radius. "
            "3. Baseline Comparison: Evaluated current FRP against the established historical baseline. "
            "4. Persistence & Recurrence: Calculated multi-pass temporal stability and recurrence patterns. "
            "5. OpenStreetMap Spatial Context: Mapped proximity to industrial infrastructure and land cover. "
            f"6. Classification Layer: Combined available evidence via {engine_text}. "
            "7. Risk Engine: Computed an objective 0-100 risk index from deviation, intensity, and persistence. "
            "8. Explainability & Provenance: Generated feature contributions, evidence lists, and auditable sources."
        )

    def _explain_summary(self, context: AssistantContext) -> str:
        """Concise executive overview of the current hotspot."""
        lat_str = f"{context.latitude:.4f}" if context.latitude else "N/A"
        lon_str = f"{context.longitude:.4f}" if context.longitude else "N/A"
        frp_str = f"{context.current_frp:.1f} MW" if context.current_frp is not None else "Unknown FRP"
        class_str = context.classification or "Unclassified"
        risk_str = f"{context.risk_index}/100 ({context.risk_level})" if context.risk_index is not None else "Unrated"

        return (
            f"Site Overview ({lat_str}, {lon_str}): Current thermal signal is {frp_str}. "
            f"Classification: {class_str}. Risk Index: {risk_str}. "
            f"History: {context.history_observation_count} observation(s) on record. "
            f"Monitoring: {context.watch_status or 'Not monitored'}."
        )

    def _explain_general(self, context: AssistantContext, question: str) -> str:
        """Fallback grounded response with suggested next queries."""
        summary = self._explain_summary(context)
        return (
            f"{summary} "
            "I can answer specific questions regarding why it was classified this way, "
            "why the risk is at this level, its historical baseline, industrial infrastructure nearby, "
            "missing evidence, or recommended precautions."
        )

    def _build_response(
        self,
        answer: str,
        mode: str,
        context: AssistantContext,
    ) -> AssistantChatResponse:
        """Assemble typed AssistantChatResponse with sources and dynamic suggested questions."""
        suggested = self._generate_suggested_questions(context)

        # Collect evidence strings
        evidence_used = [
            f"{item['label']}: {item['value']}"
            for item in context.evidence_items[:5]
        ]
        if not evidence_used and context.current_frp is not None:
            evidence_used.append(f"Current FRP: {context.current_frp:.1f} MW")
        if context.baseline_frp is not None:
            evidence_used.append(f"Baseline FRP: {context.baseline_frp:.1f} MW")
        if context.industrial_distance_km is not None:
            evidence_used.append(f"Industrial Distance: {context.industrial_distance_km:.2f} km")

        return AssistantChatResponse(
            answer=answer,
            mode=mode,  # type: ignore[arg-type]
            grounded=True,
            analysis_id=context.analysis_id,
            classification=context.classification,
            risk=context.risk_index,
            sources=context.sources or ["AGNITE Thermal Intelligence"],
            evidence_used=evidence_used,
            limitations=context.missing_evidence or context.model_limitations,
            suggested_questions=suggested,
        )

    def _generate_suggested_questions(self, context: AssistantContext) -> List[str]:
        """Generate relevant follow-up questions tailored to available context."""
        suggestions = []

        if context.classification:
            suggestions.append("Why was this classified this way?")
        if context.risk_index is not None:
            suggestions.append(f"Why is the risk rated {context.risk_level or 'at this level'}?")
        if context.history_observation_count > 1:
            suggestions.append("What happened here previously?")
        else:
            suggestions.append("What evidence is missing?")

        if context.industrial_distance_km is not None:
            suggestions.append("Is industrial infrastructure nearby?")

        suggestions.append("What precautions should be taken?")
        suggestions.append("How did AGNITE reach this conclusion?")

        return suggestions[:4]
