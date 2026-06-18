"""API routes for todo CRUD operations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Todo
from src.schemas import TodoCreate, TodoUpdate, TodoResponse
from typing import List

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=201)
def create_todo(todo_create: TodoCreate, db: Session = Depends(get_db)):
    """
    Create a new todo item.

    - **title** (required): The title of the todo
    - Returns 201 with the created todo
    - Returns 422 if title is missing or empty
    """
    db_todo = Todo(title=todo_create.title)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.get("", response_model=List[TodoResponse], status_code=200)
def list_todos(db: Session = Depends(get_db)):
    """
    List all todo items.

    - Returns 200 with a JSON array of all todos
    - Returns empty array if no todos exist
    """
    todos = db.query(Todo).all()
    return todos


@router.get("/{todo_id}", response_model=TodoResponse, status_code=200)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """
    Get a single todo item by ID.

    - Returns 200 if found
    - Returns 404 if not found
    """
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


@router.put("/{todo_id}", response_model=TodoResponse, status_code=200)
def update_todo(
    todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)
):
    """
    Update a todo item.

    - **title** (optional): Update the title
    - **completed** (optional): Update the completion status
    - Returns 200 with the updated todo
    - Returns 404 if not found
    - Partial updates: only provided fields are updated
    """
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Apply only the fields that were explicitly set
    update_dict = todo_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_todo, key, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """
    Delete a todo item.

    - Returns 204 on success
    - Returns 404 if not found
    """
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
