import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.main import app
from src import database


@pytest.fixture
def db_file():
    """Create a temporary database for testing"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    # Set environment variable to use temp database
    os.environ['DATABASE_URL'] = f"sqlite:///{temp_db.name}"
    # Reload database module to use new path
    import importlib
    importlib.reload(database)
    
    # Initialize database
    database.init_db()
    
    yield temp_db.name
    
    # Cleanup
    if os.path.exists(temp_db.name):
        os.remove(temp_db.name)


@pytest.fixture
def client(db_file):
    """Create test client"""
    return TestClient(app)


def test_create_todo_success(client):
    """Test creating a todo successfully"""
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_todo_missing_title(client):
    """Test creating a todo without title"""
    response = client.post("/todos", json={})
    assert response.status_code == 422


def test_create_todo_empty_title(client):
    """Test creating a todo with empty title"""
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422


def test_create_todo_whitespace_title(client):
    """Test creating a todo with whitespace-only title"""
    response = client.post("/todos", json={"title": "   "})
    assert response.status_code == 422


def test_list_todos_empty(client):
    """Test listing todos when empty"""
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_list_todos_with_items(client):
    """Test listing todos with multiple items"""
    # Create two todos
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})
    
    response = client.get("/todos")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 2
    assert todos[0]["title"] == "Task 1"
    assert todos[1]["title"] == "Task 2"


def test_get_todo_success(client):
    """Test getting a single todo"""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Buy milk"


def test_get_todo_not_found(client):
    """Test getting a non-existent todo"""
    response = client.get("/todos/999")
    assert response.status_code == 404


def test_update_todo_title(client):
    """Test updating todo title"""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}", json={"title": "Buy eggs"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy eggs"
    assert data["completed"] is False  # Should be preserved


def test_update_todo_completed(client):
    """Test updating todo completed status"""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Buy milk"  # Should be preserved


def test_update_todo_partial(client):
    """Test partial update preserves unset fields"""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    # Update only completed
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Buy milk"  # Original title preserved
    
    # Update only title
    response = client.put(f"/todos/{todo_id}", json={"title": "Buy eggs"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy eggs"
    assert data["completed"] is True  # Previous completed status preserved


def test_update_todo_not_found(client):
    """Test updating non-existent todo"""
    response = client.put("/todos/999", json={"title": "Updated"})
    assert response.status_code == 404


def test_delete_todo_success(client):
    """Test deleting a todo"""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client):
    """Test deleting non-existent todo"""
    response = client.delete("/todos/999")
    assert response.status_code == 404


def test_json_structure_consistency(client):
    """Test that JSON responses have consistent structure"""
    response = client.post("/todos", json={"title": "Test"})
    data = response.json()
    
    # Verify all required fields are present
    assert "id" in data
    assert "title" in data
    assert "completed" in data
    assert "created_at" in data
    
    # Verify types
    assert isinstance(data["id"], int)
    assert isinstance(data["title"], str)
    assert isinstance(data["completed"], bool)
    assert isinstance(data["created_at"], str)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_swagger_ui(client):
    """Test Swagger UI is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
