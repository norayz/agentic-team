"""Request and response schemas for the Todo API."""
from pydantic import BaseModel, field_validator
from typing import Optional


class TodoCreate(BaseModel):
    """Schema for creating a new todo."""
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate that title is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("title must not be empty or contain only whitespace")
        return v.strip()


class TodoUpdate(BaseModel):
    """Schema for updating a todo."""
    title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate that title is not empty or whitespace-only if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("title must not be empty or contain only whitespace")
        return v.strip() if v else None

    class Config:
        use_enum_values = True


class TodoResponse(BaseModel):
    """Schema for todo responses."""
    id: int
    title: str
    completed: bool
    created_at: str

    class Config:
        from_attributes = True
