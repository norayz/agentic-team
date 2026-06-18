from fastapi import APIRouter, HTTPException, Depends
from typing import List
from src.schemas import TodoCreate, TodoUpdate, TodoResponse
from src import database

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate):
    """Create a new todo"""
    try:
        result = database.create_todo(todo.title)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable. Please retry.")


@router.get("", response_model=List[TodoResponse])
async def list_todos():
    """Get all todos"""
    try:
        todos = database.get_todos()
        return todos
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable. Please retry.")


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int):
    """Get a single todo by ID"""
    try:
        todo = database.get_todo_by_id(todo_id)
        if todo is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable. Please retry.")


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Update a todo"""
    try:
        # Extract only the fields that were actually provided (exclude_unset)
        update_data = todo_update.model_dump(exclude_unset=True)
        
        result = database.update_todo(
            todo_id,
            title=update_data.get('title'),
            completed=update_data.get('completed')
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="Todo not found")
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable. Please retry.")


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: int):
    """Delete a todo"""
    try:
        deleted = database.delete_todo(todo_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Todo not found")
        return None
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Database unavailable. Please retry.")
