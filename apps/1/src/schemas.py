"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()


class TodoUpdate(BaseModel):
    """Schema for updating a todo (all fields optional)."""
    title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate title is not empty/whitespace if provided."""
        if v is not None and (not v.strip()):
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip() if v else None


class TodoResponse(BaseModel):
    """Schema for todo responses."""
    id: int
    title: str
    completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
