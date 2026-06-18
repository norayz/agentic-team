"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""

    title: str = Field(..., min_length=1, description="Todo title")


class TodoUpdate(BaseModel):
    """Schema for updating a todo (partial update)."""

    title: Optional[str] = Field(None, min_length=1, description="Todo title")
    completed: Optional[bool] = Field(None, description="Completion status")

    class Config:
        validate_assignment = True


class TodoResponse(BaseModel):
    """Schema for todo response."""

    id: int
    title: str
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
