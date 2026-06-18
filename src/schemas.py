"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""

    title: str = Field(..., min_length=1)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v


class TodoUpdate(BaseModel):
    """Schema for updating a todo (partial update)."""

    title: Optional[str] = Field(None, min_length=1)
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure title is not empty or whitespace-only if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty or whitespace")
        return v

    model_config = ConfigDict(from_attributes=True)


class TodoResponse(BaseModel):
    """Schema for todo response."""

    id: int
    title: str
    completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
