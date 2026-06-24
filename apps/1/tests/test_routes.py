"""Comprehensive tests for todo API endpoints."""

import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from src.main import create_app


@pytest.fixture
def test_db_path():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def client(test_db_path):
    """Create a test client with temporary database."""
    app = create_app(db_path=test_db_path)
    return TestClient(app)


class TestCreateTodo:
    """Tests for POST /todos endpoint."""

    def test_create_todo_success(self, client):
        """POST /todos with valid title returns 201."""
        response = client.post("/todos", json={"title": "Buy milk"})
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Buy milk"
        assert data["completed"] is False
        assert data["created_at"] is not None

    def test_create_todo_empty_title(self, client):
        """POST /todos with empty title returns 422."""
        response = client.post("/todos", json={"title": ""})
        assert response.status_code == 422

    def test_create_todo_whitespace_title(self, client):
        """POST /todos with whitespace-only title returns 422."""
        response = client.post("/todos", json={"title": "   "})
        assert response.status_code == 422

    def test_create_todo_missing_title(self, client):
        """POST /todos without title returns 422."""
        response = client.post("/todos", json={})
        assert response.status_code == 422


class TestListTodos:
    """Tests for GET /todos endpoint."""

    def test_list_todos_empty(self, client):
        """GET /todos returns 200 with empty array initially."""
        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_todos_with_items(self, client):
        """GET /todos returns 200 with all todos after creation."""
        # Create a few todos
        client.post("/todos", json={"title": "Task 1"})
        client.post("/todos", json={"title": "Task 2"})
        client.post("/todos", json={"title": "Task 3"})

        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"
        assert data[2]["title"] == "Task 3"


class TestGetTodo:
    """Tests for GET /todos/{id} endpoint."""

    def test_get_todo_success(self, client):
        """GET /todos/{id} returns 200 if found."""
        # Create a todo
        client.post("/todos", json={"title": "Buy milk"})

        response = client.get("/todos/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Buy milk"
        assert data["completed"] is False

    def test_get_todo_not_found(self, client):
        """GET /todos/{id} returns 404 if not found."""
        response = client.get("/todos/999")
        assert response.status_code == 404


class TestUpdateTodo:
    """Tests for PUT /todos/{id} endpoint."""

    def test_update_todo_title(self, client):
        """PUT /todos/{id} updates title and returns 200."""
        # Create a todo
        client.post("/todos", json={"title": "Buy milk"})

        response = client.put("/todos/1", json={"title": "Buy milk and eggs"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Buy milk and eggs"
        assert data["completed"] is False  # Should be preserved

    def test_update_todo_completed(self, client):
        """PUT /todos/{id} updates completed and returns 200."""
        # Create a todo
        client.post("/todos", json={"title": "Buy milk"})

        response = client.put("/todos/1", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert data["title"] == "Buy milk"  # Should be preserved

    def test_update_todo_partial(self, client):
        """PUT /todos/{id} partial update preserves unset fields."""
        # Create a todo
        client.post("/todos", json={"title": "Buy milk"})
        # Mark as complete
        client.put("/todos/1", json={"completed": True})
        # Update only title
        response = client.put("/todos/1", json={"title": "Buy eggs"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Buy eggs"
        assert data["completed"] is True  # Should be preserved

    def test_update_todo_not_found(self, client):
        """PUT /todos/{id} returns 404 if not found."""
        response = client.put("/todos/999", json={"title": "Nope"})
        assert response.status_code == 404


class TestDeleteTodo:
    """Tests for DELETE /todos/{id} endpoint."""

    def test_delete_todo_success(self, client):
        """DELETE /todos/{id} returns 204 on success."""
        # Create a todo
        client.post("/todos", json={"title": "Buy milk"})

        response = client.delete("/todos/1")
        assert response.status_code == 204

        # Verify it's deleted
        response = client.get("/todos/1")
        assert response.status_code == 404

    def test_delete_todo_not_found(self, client):
        """DELETE /todos/{id} returns 404 if not found."""
        response = client.delete("/todos/999")
        assert response.status_code == 404


class TestIntegration:
    """Integration tests for full workflow."""

    def test_json_structure_consistency(self, client):
        """All responses have consistent JSON structure."""
        # Create todo
        response = client.post("/todos", json={"title": "Test"})
        todo = response.json()
        assert set(todo.keys()) == {"id", "title", "completed", "created_at"}

        # Get todos
        response = client.get("/todos")
        todos = response.json()
        assert all(set(t.keys()) == {"id", "title", "completed", "created_at"} for t in todos)

        # Get single todo
        response = client.get("/todos/1")
        todo = response.json()
        assert set(todo.keys()) == {"id", "title", "completed", "created_at"}

    def test_swagger_ui_available(self, client):
        """Swagger UI is accessible at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200
        # Check for swagger or openapi content
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_full_workflow(self, client):
        """Test full workflow: create, read, update, delete."""
        # Create
        response = client.post("/todos", json={"title": "Buy milk"})
        assert response.status_code == 201
        todo_id = response.json()["id"]

        # Read
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Buy milk"

        # Update
        response = client.put(
            f"/todos/{todo_id}",
            json={"title": "Buy milk and eggs", "completed": True},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Buy milk and eggs"
        assert response.json()["completed"] is True

        # Delete
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204

        # Verify deleted
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 404
