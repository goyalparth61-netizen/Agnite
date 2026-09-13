"""
LLM Provider factory and mock/dummy implementations for AGNITE AI.

Respects ENABLE_LLM=false setting and safely defaults to None,
ensuring zero external network or API key requirements.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.providers.llm.base import LLMProvider
from app.schemas.assistant import ChatMessage

logger = logging.getLogger("app.providers.llm")


class ConfiguredLLMProvider:
    """
    Generic LLM provider wrapper for future API integration (OpenAI, Gemini, Ollama, etc.).
    Keeps strict grounding principles: never receives raw DB access.
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model or "default"

    async def generate(
        self,
        question: str,
        context_dict: Dict[str, Any],
        conversation_history: List[ChatMessage],
    ) -> str:
        """
        Placeholder generation hook. If invoked without external endpoints configured,
        raises NotImplementedError so assistant safely uses deterministic fallback.
        """
        raise NotImplementedError("External LLM provider is not configured. Falling back to deterministic assistant.")


def get_llm_provider(settings: Settings) -> Optional[LLMProvider]:
    """
    Returns an LLMProvider instance if enabled and configured, else None.
    Default: None (Deterministic AGNITE AI).
    """
    if not settings.enable_llm:
        return None

    if not settings.llm_api_key and not settings.llm_base_url:
        logger.warning("ENABLE_LLM is True but no llm_api_key or llm_base_url configured. Defaulting to deterministic.")
        return None

    return ConfiguredLLMProvider(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
