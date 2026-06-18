"""API routes for todo operations."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Todo
from src.schemas import TodoCreate, TodoResponse, TodoUpdate
from typing import List

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)) -> TodoResponse:
    """Create a new todo item."""
    db_todo = Todo(title=todo.title)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return TodoResponse.model_validate(db_todo)


@router.get("", response_model=List[TodoResponse])
def list_todos(db: Session = Depends(get_db)) -> List[TodoResponse]:
    """List all todo items."""
    todos = db.query(Todo).all()
    return [TodoResponse.model_validate(todo) for todo in todos]


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)) -> TodoResponse:
    """Get a specific todo item by ID."""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )
    return TodoResponse.model_validate(todo)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)
) -> TodoResponse:
    """Update a todo item (partial update supported)."""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )
    
    update_data = todo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    db.commit()
    db.refresh(todo)
    return TodoResponse.model_validate(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a todo item by ID."""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found",
        )
    
    db.delete(todo)
    db.commit()
