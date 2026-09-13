"""
Analysis API route for AGNITE Phase 2.

Exposes POST /api/v1/analysis/run for full thermal intelligence evaluation.
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.analysis import AnalysisRequest, AnalysisResult
from app.services.analysis_service import run_hotspot_analysis

logger = logging.getLogger("app.api.routes.analysis")

router = APIRouter(tags=["Analysis"])


@router.post(
    "/analysis/run",
    response_model=AnalysisResult,
    summary="Run AI-powered thermal intelligence analysis on a selected hotspot",
    description=(
        "Executes spatial clustering (5 km), historical baseline calculation, "
        "persistence evaluation, classification, risk scoring, and explainability."
    ),
)
async def run_analysis_endpoint(request: AnalysisRequest) -> AnalysisResult:
    """Run hotspot analysis workflow."""
    try:
        return await run_hotspot_analysis(request)
    except ValueError as val_err:
        logger.warning("Analysis validation error: %s", val_err)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_ANALYSIS_REQUEST",
                    "message": str(val_err),
                    "retryable": False,
                }
            },
        )
    except Exception as exc:
        logger.error("Unexpected analysis failure: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "ANALYSIS_FAILED",
                    "message": "Thermal intelligence analysis failed due to an internal error.",
                    "retryable": False,
                }
            },
        )
