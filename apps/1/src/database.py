"""Database layer with raw SQL queries."""

import sqlite3
import os
from datetime import datetime
from typing import Optional


class Database:
    """SQLite database wrapper with parameterized queries."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Defaults to environment
                    variable DATABASE_URL or 'todos.db'.
        """
        if db_path is None:
            db_path = os.getenv("DATABASE_URL", "todos.db")
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    completed BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize database at {self.db_path}: {e}"
            )

    def create_todo(self, title: str) -> dict:
        """Create a new todo.
        
        Args:
            title: Todo title (required, non-empty)
            
        Returns:
            Dictionary with id, title, completed, created_at
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO todos (title, completed, created_at) VALUES (?, ?, ?)",
                (title, False, now),
            )
            conn.commit()

            todo_id = cursor.lastrowid
            conn.close()

            return {
                "id": todo_id,
                "title": title,
                "completed": False,
                "created_at": now,
            }
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

    def get_todos(self) -> list:
        """Get all todos.
        
        Returns:
            List of todos sorted by id
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, title, completed, created_at FROM todos ORDER BY id"
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "completed": bool(row[2]),
                    "created_at": row[3],
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

    def get_todo(self, todo_id: int) -> Optional[dict]:
        """Get a single todo by ID.
        
        Args:
            todo_id: ID of todo to retrieve
            
        Returns:
            Todo dictionary or None if not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, title, completed, created_at FROM todos WHERE id = ?",
                (todo_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if row is None:
                return None

            return {
                "id": row[0],
                "title": row[1],
                "completed": bool(row[2]),
                "created_at": row[3],
            }
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

    def update_todo(
        self, todo_id: int, title: Optional[str] = None, completed: Optional[bool] = None
    ) -> Optional[dict]:
        """Update a todo (partial update).
        
        Only provided fields are updated. Unset fields are preserved.
        
        Args:
            todo_id: ID of todo to update
            title: New title (optional)
            completed: New completed status (optional)
            
        Returns:
            Updated todo dictionary or None if not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            # Fetch current todo
            todo = self.get_todo(todo_id)
            if todo is None:
                return None

            # Only update fields that were provided
            new_title = title if title is not None else todo["title"]
            new_completed = (
                completed if completed is not None else todo["completed"]
            )

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
                (new_title, new_completed, todo_id),
            )
            conn.commit()
            conn.close()

            return {
                "id": todo_id,
                "title": new_title,
                "completed": new_completed,
                "created_at": todo["created_at"],
            }
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a todo.
        
        Args:
            todo_id: ID of todo to delete
            
        Returns:
            True if todo was deleted, False if not found
            
        Raises:
            RuntimeError: If database operation fails
        """
        try:
            todo = self.get_todo(todo_id)
            if todo is None:
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            conn.commit()
            conn.close()

            return True
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error: {e}")
