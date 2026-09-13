"""
Pydantic schemas for the AGNITE AI Assistant (Phase 5A).

Defines the contract for POST /api/v1/assistant/chat, chat messages,
grounded responses, and context-aware question recommendations.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """A single turn in conversation history."""

    role: Literal["user", "assistant", "system"]
    text: str = Field(..., min_length=1, max_length=2000, description="Message text")

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class AssistantChatRequest(BaseModel):
    """Request payload for POST /api/v1/assistant/chat."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User question regarding the thermal hotspot or analysis.",
    )
    selected_observation_id: Optional[str] = Field(
        None,
        alias="selectedObservationId",
        serialization_alias="selectedObservationId",
        description="ID of the selected thermal observation.",
    )
    analysis_id: Optional[str] = Field(
        None,
        alias="analysisId",
        serialization_alias="analysisId",
        description="ID of a persisted thermal analysis record.",
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Latitude of the location of interest (-90 to 90).",
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Longitude of the location of interest (-180 to 180).",
    )
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        alias="conversationHistory",
        serialization_alias="conversationHistory",
        max_length=20,
        description="Recent conversation turns for conversational continuity (max 20 turns).",
    )

    @field_validator("question")
    @classmethod
    def validate_question_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Question cannot be empty or solely whitespace.")
        return trimmed

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class AssistantChatResponse(BaseModel):
    """Grounded, auditable response from the AGNITE AI Assistant."""

    answer: str = Field(..., description="Grounded explanation or decision-support answer.")
    mode: Literal["deterministic", "llm"] = Field(
        "deterministic", description="Engine used to generate the answer."
    )
    grounded: bool = Field(
        True, description="Indicates whether the answer is strictly derived from backend data."
    )
    analysis_id: Optional[str] = Field(
        None,
        alias="analysisId",
        serialization_alias="analysisId",
        description="Associated analysis record ID, if resolved.",
    )
    classification: Optional[str] = Field(
        None, description="Current classification of the referenced site."
    )
    risk: Optional[int] = Field(
        None, ge=0, le=100, description="Risk index (0-100) of the referenced site."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Data and computation sources backing this response.",
    )
    evidence_used: List[str] = Field(
        default_factory=list,
        alias="evidenceUsed",
        serialization_alias="evidenceUsed",
        description="Concrete data points and observations used to build the answer.",
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Missing data, sensor limits, or scientific boundaries applicable to this answer.",
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        alias="suggestedQuestions",
        serialization_alias="suggestedQuestions",
        description="Relevant follow-up questions based on available context.",
    )

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
