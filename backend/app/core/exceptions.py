"""
Custom exceptions for the AGNITE backend.

Exception handlers are registered in main.py so that FastAPI returns
JSON error bodies that match the frontend's expectations.
"""

from __future__ import annotations


class FirmsError(Exception):
    """Raised when a NASA FIRMS operation fails."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(Exception):
    """Raised when user input fails domain validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
