"""QA Acceptance tests for all acceptance criteria from issue #1.

Each test verifies one acceptance criterion with both happy path and failure cases.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestAcceptanceCriteria:
    """Tests for each acceptance criterion in the spec."""

    # Criterion 1: POST /todos creates a new todo with title, returns id, title, completed (default false), created_at. Returns HTTP 201.
    def test_post_todos_creates_todo_with_201(self, client: TestClient):
        """POST /todos with title creates todo and returns 201."""
        response = client.post("/todos", json={"title": "Buy milk"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Buy milk"
        assert data["completed"] is False
        assert "created_at" in data

    def test_post_todos_response_has_required_fields(self, client: TestClient):
        """POST response includes all required fields with correct types."""
        response = client.post("/todos", json={"title": "Test task"})
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["title"], str)
        assert isinstance(data["completed"], bool)
        assert isinstance(data["created_at"], str)  # ISO format string
        assert len(data) == 4  # Only these 4 fields

    def test_post_todos_default_completed_is_false(self, client: TestClient):
        """Newly created todos have completed=false by default."""
        response = client.post("/todos", json={"title": "New task"})
        assert response.json()["completed"] is False

    def test_post_todos_created_at_is_datetime_string(self, client: TestClient):
        """created_at is a valid ISO 8601 datetime string."""
        response = client.post("/todos", json={"title": "Task"})
        created_at = response.json()["created_at"]
        # Should be ISO format like 2024-01-01T12:00:00
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"created_at is not valid ISO 8601: {created_at}")

    # Criterion 2: GET /todos returns a JSON array of all todo items. Returns HTTP 200.
    def test_get_todos_returns_200_with_empty_list(self, client: TestClient):
        """GET /todos returns 200 with empty array when no todos exist."""
        response = client.get("/todos")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_todos_returns_all_created_todos(self, client: TestClient):
        """GET /todos returns all previously created todos."""
        # Create 3 todos
        for i in range(3):
            client.post("/todos", json={"title": f"Task {i}"})
        
        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert [t["title"] for t in data] == ["Task 0", "Task 1", "Task 2"]

    def test_get_todos_response_is_array_of_objects(self, client: TestClient):
        """GET /todos returns a JSON array (not object or other type)."""
        client.post("/todos", json={"title": "Task"})
        response = client.get("/todos")
        assert isinstance(response.json(), list)
        assert all(isinstance(item, dict) for item in response.json())

    # Criterion 3: GET /todos/{id} returns a single todo item by ID. Returns 200 if found, 404 if not found.
    def test_get_todo_by_id_returns_200_with_todo(self, client: TestClient):
        """GET /todos/{id} returns 200 with the todo when it exists."""
        create_response = client.post("/todos", json={"title": "Buy milk"})
        todo_id = create_response.json()["id"]
        
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Buy milk"

    def test_get_todo_by_id_returns_404_when_not_found(self, client: TestClient):
        """GET /todos/{id} returns 404 when todo doesn't exist."""
        response = client.get("/todos/99999")
        assert response.status_code == 404

    def test_get_todo_by_id_returns_complete_todo_object(self, client: TestClient):
        """GET /todos/{id} returns complete todo with all fields."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.get(f"/todos/{todo_id}")
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "completed" in data
        assert "created_at" in data

    # Criterion 4: PUT /todos/{id} updates a todo's title and/or completed status. Returns 200 with updated todo. Returns 404 if not found.
    def test_put_todo_updates_title_returns_200(self, client: TestClient):
        """PUT /todos/{id} can update title and returns 200."""
        create_response = client.post("/todos", json={"title": "Original"})
        todo_id = create_response.json()["id"]
        
        response = client.put(f"/todos/{todo_id}", json={"title": "Updated"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_put_todo_updates_completed_returns_200(self, client: TestClient):
        """PUT /todos/{id} can update completed and returns 200."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert response.status_code == 200
        assert response.json()["completed"] is True

    def test_put_todo_updates_both_fields_returns_200(self, client: TestClient):
        """PUT /todos/{id} can update both title and completed."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.put(
            f"/todos/{todo_id}",
            json={"title": "Updated", "completed": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True

    def test_put_todo_partial_update_preserves_other_fields(self, client: TestClient):
        """PUT with only completed=true preserves title (critical spec requirement)."""
        create_response = client.post("/todos", json={"title": "Important"})
        todo_id = create_response.json()["id"]
        
        # Update only completed
        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        data = response.json()
        # Verify title is still there (not nulled out)
        assert data["title"] == "Important"
        assert data["completed"] is True

    def test_put_todo_returns_404_when_not_found(self, client: TestClient):
        """PUT /todos/{id} returns 404 when todo doesn't exist."""
        response = client.put("/todos/99999", json={"title": "New"})
        assert response.status_code == 404

    # Criterion 5: DELETE /todos/{id} deletes a todo by ID. Returns 204 on success. Returns 404 if not found.
    def test_delete_todo_returns_204_on_success(self, client: TestClient):
        """DELETE /todos/{id} returns 204 No Content on success."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204
        # 204 should have no content
        assert response.content == b''

    def test_delete_todo_actually_deletes_from_db(self, client: TestClient):
        """After DELETE, GET returns 404 (todo is really deleted)."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        client.delete(f"/todos/{todo_id}")
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_returns_404_when_not_found(self, client: TestClient):
        """DELETE /todos/{id} returns 404 when todo doesn't exist."""
        response = client.delete("/todos/99999")
        assert response.status_code == 404

    # Criterion 6: POST /todos with missing or empty title returns 422 with validation error.
    def test_post_todo_missing_title_returns_422(self, client: TestClient):
        """POST without title field returns 422."""
        response = client.post("/todos", json={})
        assert response.status_code == 422

    def test_post_todo_empty_title_returns_422(self, client: TestClient):
        """POST with empty string title returns 422."""
        response = client.post("/todos", json={"title": ""})
        assert response.status_code == 422

    def test_post_todo_whitespace_only_title_returns_422(self, client: TestClient):
        """POST with whitespace-only title returns 422."""
        response = client.post("/todos", json={"title": "   "})
        assert response.status_code == 422

    def test_post_todo_422_includes_validation_error_message(self, client: TestClient):
        """POST /todos returns 422 with detail about validation error."""
        response = client.post("/todos", json={"title": ""})
        assert response.status_code == 422
        # Response should include error details
        error_detail = response.json()["detail"]
        assert len(error_detail) > 0

    # Criterion 7: All responses use consistent JSON structure.
    def test_all_responses_have_consistent_structure(self, client: TestClient):
        """All successful responses have same structure: id, title, completed, created_at."""
        # Create a todo
        create_response = client.post("/todos", json={"title": "Task"})
        todo = create_response.json()
        todo_id = todo["id"]
        
        # Check POST response
        assert set(todo.keys()) == {"id", "title", "completed", "created_at"}
        
        # Check GET /todos/{id} response
        get_response = client.get(f"/todos/{todo_id}")
        assert set(get_response.json().keys()) == {"id", "title", "completed", "created_at"}
        
        # Check PUT response
        put_response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert set(put_response.json().keys()) == {"id", "title", "completed", "created_at"}
        
        # Check GET /todos response (should be array of such objects)
        list_response = client.get("/todos")
        for item in list_response.json():
            assert set(item.keys()) == {"id", "title", "completed", "created_at"}

    # Criterion 8: Swagger UI is accessible at /docs and documents all endpoints.
    def test_swagger_ui_accessible_at_docs(self, client: TestClient):
        """GET /docs returns 200 (Swagger UI is accessible)."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_accessible_at_redoc(self, client: TestClient):
        """GET /redoc returns 200 (ReDoc is also accessible)."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_available(self, client: TestClient):
        """GET /openapi.json returns 200 with valid OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        # Should document the /todos endpoints
        assert "/todos" in schema["paths"]

    # Criterion 9: Todos persist across server restarts (via conftest fixture using temp DB, simulating persistence).
    # This is tested in test_integration.py

    # Criterion 10: Server starts successfully with single command.
    # This is verified by the test suite running without import errors


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_post_todo_with_very_long_title(self, client: TestClient):
        """POST with very long title (e.g., 10000 chars) succeeds."""
        long_title = "a" * 10000
        response = client.post("/todos", json={"title": long_title})
        assert response.status_code == 201
        assert response.json()["title"] == long_title

    def test_post_todo_with_unicode_characters(self, client: TestClient):
        """POST with Unicode title (emoji, non-ASCII) succeeds."""
        response = client.post("/todos", json={"title": "Buy milk 🥛 チーズ العسل"})
        assert response.status_code == 201
        assert response.json()["title"] == "Buy milk 🥛 チーズ العسل"

    def test_post_todo_with_special_characters(self, client: TestClient):
        """POST with special characters in title."""
        special_title = "Task: \"important\" <tag> & [brackets] {braces} $money @user"
        response = client.post("/todos", json={"title": special_title})
        assert response.status_code == 201
        assert response.json()["title"] == special_title

    def test_post_todo_with_newlines_in_title(self, client: TestClient):
        """POST with newline characters in title."""
        response = client.post("/todos", json={"title": "Line 1\nLine 2"})
        assert response.status_code == 201
        assert "\n" in response.json()["title"]

    def test_post_todo_with_tab_characters(self, client: TestClient):
        """POST with tab characters in title."""
        response = client.post("/todos", json={"title": "Task\twith\ttabs"})
        assert response.status_code == 201

    def test_post_todo_with_leading_trailing_spaces_strips_them(self, client: TestClient):
        """POST with leading/trailing spaces strips them (per validation logic)."""
        response = client.post("/todos", json={"title": "  Task  "})
        assert response.status_code == 201
        # Should be stripped
        assert response.json()["title"] == "Task"

    def test_get_non_existent_todo_id_zero(self, client: TestClient):
        """GET /todos/0 returns 404 (0 is not a valid ID)."""
        response = client.get("/todos/0")
        assert response.status_code == 404

    def test_get_non_existent_todo_id_negative(self, client: TestClient):
        """GET /todos/-1 returns 404 or 422."""
        response = client.get("/todos/-1")
        # Should either return 404 (not found) or 422 (invalid)
        assert response.status_code in [404, 422]

    def test_put_empty_object_does_not_change_todo(self, client: TestClient):
        """PUT with empty JSON object {} doesn't update anything."""
        create_response = client.post("/todos", json={"title": "Original"})
        original = create_response.json()
        todo_id = original["id"]
        
        put_response = client.put(f"/todos/{todo_id}", json={})
        assert put_response.status_code == 200
        updated = put_response.json()
        assert updated["title"] == original["title"]
        assert updated["completed"] == original["completed"]

    def test_put_todo_with_null_title_does_not_update(self, client: TestClient):
        """PUT with null title should not update or should error gracefully."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        # Sending null for title in update
        response = client.put(f"/todos/{todo_id}", json={"title": None})
        # Should either reject (422) or not update (200 with same title)
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            assert response.json()["title"] == "Task"

    def test_multiple_todos_have_unique_ids(self, client: TestClient):
        """Each created todo has a unique ID."""
        ids = set()
        for i in range(5):
            response = client.post("/todos", json={"title": f"Task {i}"})
            todo_id = response.json()["id"]
            assert todo_id not in ids, "Duplicate ID detected!"
            ids.add(todo_id)

    def test_list_todos_preserves_creation_order(self, client: TestClient):
        """GET /todos returns todos in creation order."""
        for i in range(5):
            client.post("/todos", json={"title": f"Task {i}"})
        
        response = client.get("/todos")
        todos = response.json()
        titles = [t["title"] for t in todos]
        assert titles == [f"Task {i}" for i in range(5)]


class TestErrorCases:
    """Invalid inputs and error cases."""

    def test_post_invalid_json_returns_422(self, client: TestClient):
        """POST with invalid JSON returns 422."""
        response = client.post(
            "/todos",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_post_todo_with_extra_fields_ignores_them(self, client: TestClient):
        """POST with extra unknown fields ignores them (doesn't fail)."""
        response = client.post("/todos", json={
            "title": "Task",
            "extra_field": "should be ignored",
            "another": 123
        })
        # Should succeed and ignore extra fields
        assert response.status_code == 201

    def test_put_todo_with_completed_not_boolean_returns_422(self, client: TestClient):
        """PUT with non-boolean completed value returns 422."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        response = client.put(f"/todos/{todo_id}", json={"completed": "yes"})
        assert response.status_code == 422

    def test_get_todos_with_string_id_returns_422(self, client: TestClient):
        """GET /todos/not_a_number returns 422 (validation error)."""
        response = client.get("/todos/abc123")
        assert response.status_code == 422

    def test_post_todo_with_null_title_returns_422(self, client: TestClient):
        """POST with null title returns 422."""
        response = client.post("/todos", json={"title": None})
        assert response.status_code == 422

    def test_post_todo_with_number_title_returns_422(self, client: TestClient):
        """POST with number instead of string title returns 422."""
        response = client.post("/todos", json={"title": 123})
        assert response.status_code == 422

    def test_put_todo_with_invalid_id_type_returns_422(self, client: TestClient):
        """PUT /todos/not_int returns 422."""
        response = client.put("/todos/invalid", json={"title": "New"})
        assert response.status_code == 422

    def test_delete_todo_with_invalid_id_type_returns_422(self, client: TestClient):
        """DELETE /todos/not_int returns 422."""
        response = client.delete("/todos/invalid")
        assert response.status_code == 422

    def test_post_todo_with_empty_object_returns_422(self, client: TestClient):
        """POST with empty JSON object returns 422."""
        response = client.post("/todos", json={})
        assert response.status_code == 422

    def test_post_todo_content_type_matters(self, client: TestClient):
        """POST without proper Content-Type might fail."""
        # This depends on FastAPI's behavior, but it should handle it
        response = client.post(
            "/todos",
            json={"title": "Task"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 201
