"""API routes for todos."""
from fastapi import APIRouter, HTTPException
from src.schemas import TodoCreate, TodoUpdate, TodoResponse
from src import database

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_or_404(todo_id: int) -> dict:
    """Helper to get a todo or raise 404."""
    todo = database.get_todo(todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.post("", status_code=201, response_model=TodoResponse)
def create_todo(todo_create: TodoCreate) -> TodoResponse:
    """Create a new todo."""
    try:
        todo = database.create_todo(todo_create.title)
        return TodoResponse(**todo)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("", response_model=list[TodoResponse])
def list_todos() -> list[TodoResponse]:
    """List all todos."""
    try:
        todos = database.get_all_todos()
        return [TodoResponse(**todo) for todo in todos]
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int) -> TodoResponse:
    """Get a single todo by ID."""
    try:
        todo = get_todo_or_404(todo_id)
        return TodoResponse(**todo)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate) -> TodoResponse:
    """Update a todo."""
    try:
        # Check if todo exists first
        _ = get_todo_or_404(todo_id)
        
        # Prepare update parameters
        update_kwargs = {}
        if todo_update.title is not None:
            update_kwargs["title"] = todo_update.title
        if todo_update.completed is not None:
            update_kwargs["completed"] = todo_update.completed
        
        # Update the todo
        updated_todo = database.update_todo(todo_id, **update_kwargs)
        if updated_todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return TodoResponse(**updated_todo)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable")


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    """Delete a todo."""
    try:
        # Check if todo exists first
        _ = get_todo_or_404(todo_id)
        
        success = database.delete_todo(todo_id)
        if not success:
            raise HTTPException(status_code=404, detail="Todo not found")
        
        return None
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
