"""
Assistant API route for AGNITE Phase 5A.

Exposes POST /api/v1/assistant/chat for explainable, grounded thermal intelligence queries.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.providers.llm import get_llm_provider
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.agnite_service import AgniteAssistantService
from app.services.assistant_context_service import AssistantContextService

logger = logging.getLogger("app.api.routes.assistant")

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AGNITE AI about thermal anomalies, classification, risk, and history",
    description=(
        "Processes questions grounded in NASA FIRMS observations, historical baseline, "
        "OpenStreetMap industrial context, classification, and monitoring alerts. "
        "Operates 100% deterministically by default without external API keys."
    ),
)
async def assistant_chat_endpoint(
    request: AssistantChatRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AssistantChatResponse:
    """Execute grounded assistant question-answering workflow."""
    try:
        # 1. Resolve normalized context using hierarchy: analysisId -> observationId -> coords
        context = AssistantContextService.build_context(
            db=db,
            analysis_id=request.analysis_id,
            selected_observation_id=request.selected_observation_id,
            latitude=request.latitude,
            longitude=request.longitude,
        )

        # 2. Initialize assistant service with optional LLM provider (default: None)
        llm_provider = get_llm_provider(settings)
        assistant = AgniteAssistantService(settings=settings, llm_provider=llm_provider)

        # 3. Generate grounded answer
        response = await assistant.answer(
            question=request.question,
            context=context,
            conversation_history=request.conversation_history,
        )
        return response

    except ValueError as val_err:
        logger.warning("Assistant validation error: %s", val_err)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_ASSISTANT_REQUEST",
                    "message": str(val_err),
                    "retryable": False,
                }
            },
        )
    except Exception as exc:
        logger.error("Unexpected failure in assistant chat: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "ASSISTANT_FAILED",
                    "message": "Assistant query failed due to an internal server error.",
                    "retryable": False,
                }
            },
        )
