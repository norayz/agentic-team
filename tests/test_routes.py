"""Tests for API routes."""
import pytest
from fastapi.testclient import TestClient


def test_create_todo_success(client: TestClient):
    """Test creating a todo with valid data."""
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data


def test_create_todo_missing_title(client: TestClient):
    """Test creating a todo without title returns 422."""
    response = client.post("/todos", json={})
    assert response.status_code == 422


def test_create_todo_empty_title(client: TestClient):
    """Test creating a todo with empty title returns 422."""
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422


def test_list_todos_empty(client: TestClient):
    """Test listing todos when none exist."""
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_todos_with_items(client: TestClient):
    """Test listing todos with multiple items."""
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})
    
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"


def test_get_todo_success(client: TestClient):
    """Test getting a specific todo by ID."""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Buy milk"


def test_get_todo_not_found(client: TestClient):
    """Test getting a non-existent todo returns 404."""
    response = client.get("/todos/999")
    assert response.status_code == 404


def test_update_todo_title(client: TestClient):
    """Test updating a todo title."""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}", json={"title": "Buy cheese"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy cheese"
    assert data["completed"] is False


def test_update_todo_completed(client: TestClient):
    """Test updating a todo completed status."""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Buy milk"


def test_update_todo_partial(client: TestClient):
    """Test partial update preserves unset fields."""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.put(f"/todos/{todo_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is True


def test_update_todo_not_found(client: TestClient):
    """Test updating non-existent todo returns 404."""
    response = client.put("/todos/999", json={"title": "Buy cheese"})
    assert response.status_code == 404


def test_delete_todo_success(client: TestClient):
    """Test deleting a todo returns 204."""
    create_response = client.post("/todos", json={"title": "Buy milk"})
    todo_id = create_response.json()["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client: TestClient):
    """Test deleting non-existent todo returns 404."""
    response = client.delete("/todos/999")
    assert response.status_code == 404


def test_json_structure_consistency(client: TestClient):
    """Test consistent JSON structure."""
    response = client.post("/todos", json={"title": "Test"})
    data = response.json()
    
    assert "id" in data
    assert "title" in data
    assert "completed" in data
    assert "created_at" in data
    assert len(data) == 4


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
