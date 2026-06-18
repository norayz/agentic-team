"""API endpoints for todo operations."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.database import get_db
from src.models import Todo
from src.schemas import TodoCreate, TodoUpdate, TodoResponse
from typing import List

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_or_404(db: Session, todo_id: int) -> Todo:
    """Helper to retrieve a todo or raise 404."""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    return todo


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    try:
        new_todo = Todo(title=todo.title)
        db.add(new_todo)
        db.commit()
        db.refresh(new_todo)
        return new_todo
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry."
        )


@router.get("", response_model=List[TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    """Retrieve all todo items."""
    try:
        todos = db.query(Todo).all()
        return todos
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry."
        )


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific todo item by ID."""
    try:
        todo = get_todo_or_404(db, todo_id)
        return todo
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry."
        )


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    """Update a todo item (partial update supported)."""
    try:
        todo = get_todo_or_404(db, todo_id)
        update_data = todo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(todo, field, value)
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry."
        )


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item by ID."""
    try:
        todo = get_todo_or_404(db, todo_id)
        db.delete(todo)
        db.commit()
        return None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry."
        )
