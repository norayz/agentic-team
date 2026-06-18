"""Database initialization and connection management using raw sqlite3."""
import sqlite3
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

DATABASE_PATH = os.getenv("DATABASE_PATH", "todos.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=5.0)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to connect to database at {DATABASE_PATH}: {e}")


def init_db() -> None:
    """Initialize the database schema."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create todos table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to initialize database: {e}")


def create_todo(title: str) -> Dict[str, Any]:
    """Create a new todo."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        created_at = datetime.now(timezone.utc).isoformat()
        
        cursor.execute(
            "INSERT INTO todos (title, completed, created_at) VALUES (?, ?, ?)",
            (title, False, created_at)
        )
        conn.commit()
        
        todo_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": todo_id,
            "title": title,
            "completed": False,
            "created_at": created_at
        }
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error creating todo: {e}")


def get_all_todos() -> List[Dict[str, Any]]:
    """Get all todos."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, completed, created_at FROM todos ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error getting todos: {e}")


def get_todo(todo_id: int) -> Optional[Dict[str, Any]]:
    """Get a single todo by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
            (todo_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"]
        }
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error getting todo: {e}")


def update_todo(
    todo_id: int,
    title: Optional[str] = None,
    completed: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """Update a todo."""
    try:
        # First check if todo exists
        existing = get_todo(todo_id)
        if existing is None:
            return None
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build the update query dynamically
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if completed is not None:
            updates.append("completed = ?")
            params.append(completed)
        
        if not updates:
            # No updates requested, return existing todo
            conn.close()
            return existing
        
        params.append(todo_id)
        update_sql = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(update_sql, params)
        conn.commit()
        conn.close()
        
        # Fetch and return the updated todo
        return get_todo(todo_id)
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error updating todo: {e}")


def delete_todo(todo_id: int) -> bool:
    """Delete a todo. Returns True if deleted, False if not found."""
    try:
        # First check if todo exists
        existing = get_todo(todo_id)
        if existing is None:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
        conn.close()
        
        return True
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error deleting todo: {e}")
