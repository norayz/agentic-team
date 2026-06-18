from pydantic import BaseModel, field_validator
from datetime import datetime


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Validate that title is not empty or just whitespace."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class TodoUpdate(BaseModel):
    """Schema for updating a todo. Both fields are optional."""
    title: str | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_not_empty_if_provided(cls, v: str | None) -> str | None:
        """Validate that title is not empty or just whitespace if provided."""
        if v is not None and (not isinstance(v, str) or not v.strip()):
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip() if v else None


class TodoResponse(BaseModel):
    """Schema for todo responses. Matches database model."""
    id: int
    title: str
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
