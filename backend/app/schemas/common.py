"""
Common response models shared across API routes.
"""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Frontend expects ``{ "error": "..." }`` for all error responses."""

    error: str
