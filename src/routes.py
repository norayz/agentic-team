from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.database import get_db
from src.models import Todo
from src.schemas import TodoCreate, TodoUpdate, TodoResponse

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_or_404(db: Session, todo_id: int) -> Todo:
    """Helper to get a todo by ID or raise 404."""
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo_create: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo."""
    try:
        db_todo = Todo(title=todo_create.title)
        db.add(db_todo)
        db.commit()
        db.refresh(db_todo)
        return db_todo
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry.",
        ) from e


@router.get("", response_model=list[TodoResponse])
def list_todos(db: Session = Depends(get_db)):
    """List all todos."""
    try:
        todos = db.query(Todo).all()
        return todos
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry.",
        ) from e


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a single todo by ID."""
    try:
        db_todo = get_todo_or_404(db, todo_id)
        return db_todo
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry.",
        ) from e


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)
):
    """Update a todo."""
    try:
        db_todo = get_todo_or_404(db, todo_id)
        
        # Only update fields that were provided
        update_data = todo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_todo, field, value)
        
        db.commit()
        db.refresh(db_todo)
        return db_todo
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry.",
        ) from e


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo."""
    try:
        db_todo = get_todo_or_404(db, todo_id)
        db.delete(db_todo)
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please retry.",
        ) from e
