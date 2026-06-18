"""API routes for todo operations."""

from fastapi import APIRouter, HTTPException, status
from src.database import Database
from src.schemas import TodoCreate, TodoUpdate, TodoResponse
from typing import Optional

router = APIRouter(prefix="/todos", tags=["todos"])

# Global database instance (initialized in main)
_db: Optional[Database] = None


def set_database(db: Database) -> None:
    """Set the database instance for routes."""
    global _db
    _db = db


def get_db() -> Database:
    """Get the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
def create_todo(todo_create: TodoCreate) -> TodoResponse:
    """Create a new todo.
    
    Returns HTTP 201 with created todo.
    Returns HTTP 422 if title is invalid.
    """
    try:
        db = get_db()
        result = db.create_todo(todo_create.title)
        return TodoResponse(**result)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )


@router.get("", response_model=list[TodoResponse])
def list_todos() -> list[TodoResponse]:
    """Get all todos.
    
    Returns HTTP 200 with array of todos.
    """
    try:
        db = get_db()
        todos = db.get_todos()
        return [TodoResponse(**todo) for todo in todos]
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int) -> TodoResponse:
    """Get a single todo by ID.
    
    Returns HTTP 200 if found.
    Returns HTTP 404 if not found.
    """
    try:
        db = get_db()
        todo = db.get_todo(todo_id)
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
            )
        return TodoResponse(**todo)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate) -> TodoResponse:
    """Update a todo (partial update).
    
    Only provided fields are updated. Unset fields are preserved.
    
    Returns HTTP 200 if updated.
    Returns HTTP 404 if not found.
    """
    try:
        db = get_db()
        todo = db.update_todo(
            todo_id, title=todo_update.title, completed=todo_update.completed
        )
        if todo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
            )
        return TodoResponse(**todo)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> None:
    """Delete a todo.
    
    Returns HTTP 204 if deleted.
    Returns HTTP 404 if not found.
    """
    try:
        db = get_db()
        success = db.delete_todo(todo_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}",
        )
