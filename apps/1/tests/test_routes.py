"""Tests for todo API routes."""
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from src.main import app
from src import database


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file for the database
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Set the database path before importing
    os.environ["DATABASE_PATH"] = path
    
    # Initialize the database
    database.init_db()
    
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="function")
def client(temp_db):
    """Create a test client."""
    return TestClient(app)


class TestCreateTodo:
    def test_create_todo_success(self, client):
        """Test creating a todo with valid data."""
        response = client.post("/todos", json={"title": "Buy milk"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy milk"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_todo_missing_title(self, client):
        """Test creating a todo without title."""
        response = client.post("/todos", json={})
        assert response.status_code == 422

    def test_create_todo_empty_title(self, client):
        """Test creating a todo with empty title."""
        response = client.post("/todos", json={"title": ""})
        assert response.status_code == 422

    def test_create_todo_whitespace_title(self, client):
        """Test creating a todo with whitespace-only title."""
        response = client.post("/todos", json={"title": "   "})
        assert response.status_code == 422


class TestListTodos:
    def test_list_todos_empty(self, client):
        """Test listing todos when empty."""
        response = client.get("/todos")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_todos_with_items(self, client):
        """Test listing todos with items."""
        # Create two todos
        client.post("/todos", json={"title": "Task 1"})
        client.post("/todos", json={"title": "Task 2"})
        
        response = client.get("/todos")
        assert response.status_code == 200
        todos = response.json()
        assert len(todos) == 2
        assert todos[0]["title"] == "Task 1"
        assert todos[1]["title"] == "Task 2"


class TestGetTodo:
    def test_get_todo_success(self, client):
        """Test getting a specific todo."""
        create_response = client.post("/todos", json={"title": "Test todo"})
        todo_id = create_response.json()["id"]
        
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test todo"

    def test_get_todo_not_found(self, client):
        """Test getting a non-existent todo."""
        response = client.get("/todos/9999")
        assert response.status_code == 404


class TestUpdateTodo:
    def test_update_todo_title(self, client):
        """Test updating a todo's title."""
        create_response = client.post("/todos", json={"title": "Old title"})
        todo_id = create_response.json()["id"]
        
        response = client.put(f"/todos/{todo_id}", json={"title": "New title"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New title"
        assert data["completed"] is False

    def test_update_todo_completed(self, client):
        """Test updating a todo's completed status."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["title"] == "Task"

    def test_update_todo_partial(self, client):
        """Test partial update preserves unset fields."""
        create_response = client.post("/todos", json={"title": "Original"})
        todo_id = create_response.json()["id"]
        
        # Update only title
        response = client.put(f"/todos/{todo_id}", json={"title": "Modified"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Modified"
        assert data["completed"] is False  # Preserved
        
        # Update only completed
        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Modified"  # Preserved
        assert data["completed"] is True

    def test_update_todo_not_found(self, client):
        """Test updating a non-existent todo."""
        response = client.put("/todos/9999", json={"title": "New title"})
        assert response.status_code == 404


class TestDeleteTodo:
    def test_delete_todo_success(self, client):
        """Test deleting a todo."""
        create_response = client.post("/todos", json={"title": "To delete"})
        todo_id = create_response.json()["id"]
        
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client):
        """Test deleting a non-existent todo."""
        response = client.delete("/todos/9999")
        assert response.status_code == 404


class TestResponseStructure:
    def test_json_structure_consistency(self, client):
        """Test that response structure is consistent."""
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


class TestRootEndpoint:
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
