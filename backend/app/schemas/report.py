"""
Pydantic schemas for persistent saved analysis reports.
Matches frontend SavedReport contract.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisContext, AnalysisResult
from app.schemas.observation import Observation


class ReportCreate(BaseModel):
    """Payload for persisting an analysis report."""

    id: Optional[str] = None
    label: str = Field(..., min_length=1, max_length=128)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    classification: str
    confidence: Optional[float] = None
    risk: int = Field(..., ge=0, le=100)
    summary: str
    report: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    observations: Optional[List[Dict[str, Any]]] = None

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class ReportResponse(BaseModel):
    """Response model representing a saved analysis report."""

    id: str
    label: str
    latitude: float
    longitude: float
    classification: str
    confidence: Optional[float] = None
    risk: int
    summary: str
    report: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(..., alias="createdAt", serialization_alias="createdAt")

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }


class ReportListResponse(BaseModel):
    """List of saved reports."""

    reports: List[ReportResponse]
    total: int

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
