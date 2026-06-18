import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todos.db")

# Extract file path from DATABASE_URL (handle both sqlite:/// and file paths)
if DATABASE_URL.startswith("sqlite:///"):
    DB_PATH = DATABASE_URL.replace("sqlite:///", "")
else:
    DB_PATH = DATABASE_URL


def init_db():
    """Initialize database schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to initialize database at {DB_PATH}: {e}")


@contextmanager
def get_db():
    """Context manager for database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        conn.close()


def create_todo(title: str, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Create a new todo"""
    from datetime import datetime
    
    close_conn = conn is None
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
        
        created_at = datetime.utcnow().isoformat()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO todos (title, completed, created_at) VALUES (?, ?, ?)',
            (title, False, created_at)
        )
        conn.commit()
        
        todo_id = cursor.lastrowid
        return get_todo_by_id(todo_id, conn)
    except sqlite3.Error as e:
        if close_conn:
            conn.close()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if close_conn and conn:
            conn.close()


def get_todos(conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Get all todos"""
    close_conn = conn is None
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, completed, created_at FROM todos ORDER BY id')
        rows = cursor.fetchall()
        
        todos = []
        for row in rows:
            todos.append({
                'id': row['id'],
                'title': row['title'],
                'completed': bool(row['completed']),
                'created_at': row['created_at']
            })
        return todos
    except sqlite3.Error as e:
        if close_conn:
            conn.close()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if close_conn and conn:
            conn.close()


def get_todo_by_id(todo_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """Get a todo by ID"""
    close_conn = conn is None
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, completed, created_at FROM todos WHERE id = ?', (todo_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'completed': bool(row['completed']),
                'created_at': row['created_at']
            }
        return None
    except sqlite3.Error as e:
        if close_conn:
            conn.close()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if close_conn and conn:
            conn.close()


def update_todo(todo_id: int, title: Optional[str] = None, completed: Optional[bool] = None, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
    """Update a todo"""
    close_conn = conn is None
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        # Check if todo exists
        cursor.execute('SELECT id FROM todos WHERE id = ?', (todo_id,))
        if not cursor.fetchone():
            if close_conn:
                conn.close()
            return None
        
        # Build update query
        updates = []
        params = []
        
        if title is not None:
            updates.append('title = ?')
            params.append(title)
        
        if completed is not None:
            updates.append('completed = ?')
            params.append(completed)
        
        if updates:
            params.append(todo_id)
            query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        return get_todo_by_id(todo_id, conn)
    except sqlite3.Error as e:
        if close_conn:
            conn.close()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if close_conn and conn:
            conn.close()


def delete_todo(todo_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Delete a todo"""
    close_conn = conn is None
    try:
        if conn is None:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        # Check if todo exists
        cursor.execute('SELECT id FROM todos WHERE id = ?', (todo_id,))
        if not cursor.fetchone():
            if close_conn:
                conn.close()
            return False
        
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        if close_conn:
            conn.close()
        raise RuntimeError(f"Database error: {e}") from e
    finally:
        if close_conn and conn:
            conn.close()
