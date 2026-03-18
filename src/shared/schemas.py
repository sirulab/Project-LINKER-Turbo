"""Shared Pydantic/SQLModel schemas (e.g. ErrorResponse)."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
