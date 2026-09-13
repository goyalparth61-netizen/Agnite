"""
Protocol definition for optional LLM providers in AGNITE.

Allows transparent pluggability for language models in future phases
while keeping the core system 100% deterministic and offline-first by default.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol
from app.schemas.assistant import ChatMessage


class LLMProvider(Protocol):
    """Protocol that any future LLM provider must implement."""

    async def generate(
        self,
        question: str,
        context_dict: Dict[str, Any],
        conversation_history: List[ChatMessage],
    ) -> str:
        """
        Generate grounded response from structured context and question.

        Must raise an exception or return an empty string if unable to generate,
        triggering automatic deterministic fallback.
        """
        ...
