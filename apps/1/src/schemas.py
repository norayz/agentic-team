"""Pydantic request/response schemas with validation."""

from pydantic import BaseModel, field_validator
from typing import Optional


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""

    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class TodoUpdate(BaseModel):
    """Schema for updating a todo (partial update)."""

    title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty_or_none(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title (if provided) is not empty or whitespace-only."""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip() if v else None


class TodoResponse(BaseModel):
    """Schema for todo response."""

    id: int
    title: str
    completed: bool
    created_at: str
