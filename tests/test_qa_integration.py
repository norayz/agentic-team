"""QA Integration tests - verify components work together."""
import pytest
from fastapi.testclient import TestClient
import time


class TestPersistence:
    """Test that todos persist properly in the database."""

    def test_created_todo_persists_when_retrieved(self, client: TestClient):
        """Created todo can be retrieved immediately after creation."""
        create_response = client.post("/todos", json={"title": "Persist me"})
        todo_id = create_response.json()["id"]
        
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.json()["title"] == "Persist me"

    def test_updated_todo_persists_when_retrieved(self, client: TestClient):
        """Updated todo retains changes when retrieved."""
        create_response = client.post("/todos", json={"title": "Original"})
        todo_id = create_response.json()["id"]
        
        client.put(f"/todos/{todo_id}", json={"title": "Modified"})
        
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.json()["title"] == "Modified"

    def test_deleted_todo_not_retrieved(self, client: TestClient):
        """Deleted todo cannot be retrieved."""
        create_response = client.post("/todos", json={"title": "Delete me"})
        todo_id = create_response.json()["id"]
        
        client.delete(f"/todos/{todo_id}")
        
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_deleted_todo_removed_from_list(self, client: TestClient):
        """After DELETE, the todo no longer appears in GET /todos."""
        resp1 = client.post("/todos", json={"title": "Task 1"})
        resp2 = client.post("/todos", json={"title": "Task 2"})
        id1 = resp1.json()["id"]
        
        client.delete(f"/todos/{id1}")
        
        list_response = client.get("/todos")
        remaining_ids = [t["id"] for t in list_response.json()]
        assert id1 not in remaining_ids
        assert len(remaining_ids) == 1


class TestStateTransitions:
    """Test valid state transitions."""

    def test_todo_state_transition_incomplete_to_complete(self, client: TestClient):
        """Todo can transition from incomplete to complete."""
        create_response = client.post("/todos", json={"title": "Work"})
        todo_id = create_response.json()["id"]
        assert create_response.json()["completed"] is False
        
        update_response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert update_response.json()["completed"] is True

    def test_todo_state_transition_complete_back_to_incomplete(self, client: TestClient):
        """Todo can transition from complete back to incomplete."""
        create_response = client.post("/todos", json={"title": "Work"})
        todo_id = create_response.json()["id"]
        
        # Mark complete
        client.put(f"/todos/{todo_id}", json={"completed": True})
        
        # Mark incomplete again
        update_response = client.put(f"/todos/{todo_id}", json={"completed": False})
        assert update_response.json()["completed"] is False

    def test_update_title_multiple_times(self, client: TestClient):
        """Todo title can be updated multiple times."""
        create_response = client.post("/todos", json={"title": "First"})
        todo_id = create_response.json()["id"]
        
        for i in range(5):
            update_response = client.put(
                f"/todos/{todo_id}",
                json={"title": f"Update {i}"}
            )
            assert update_response.json()["title"] == f"Update {i}"

    def test_update_completed_and_title_together_and_separately(self, client: TestClient):
        """Updates can mix both fields or be separate."""
        create_response = client.post("/todos", json={"title": "Task"})
        todo_id = create_response.json()["id"]
        
        # Update both
        resp1 = client.put(
            f"/todos/{todo_id}",
            json={"title": "Updated", "completed": True}
        )
        assert resp1.json()["title"] == "Updated"
        assert resp1.json()["completed"] is True
        
        # Update only title
        resp2 = client.put(
            f"/todos/{todo_id}",
            json={"title": "Changed again"}
        )
        assert resp2.json()["title"] == "Changed again"
        assert resp2.json()["completed"] is True  # Should still be True
        
        # Update only completed
        resp3 = client.put(
            f"/todos/{todo_id}",
            json={"completed": False}
        )
        assert resp3.json()["title"] == "Changed again"  # Should still be there
        assert resp3.json()["completed"] is False


class TestConcurrentOperations:
    """Test behavior with multiple operations in sequence."""

    def test_create_many_todos_sequentially(self, client: TestClient):
        """Can create many todos without issues."""
        for i in range(100):
            response = client.post("/todos", json={"title": f"Task {i}"})
            assert response.status_code == 201
        
        list_response = client.get("/todos")
        assert len(list_response.json()) == 100

    def test_interleaved_create_read_update_delete(self, client: TestClient):
        """Mix of CRUD operations in random order."""
        # Create
        r1 = client.post("/todos", json={"title": "A"})
        id1 = r1.json()["id"]
        
        r2 = client.post("/todos", json={"title": "B"})
        id2 = r2.json()["id"]
        
        # Update
        client.put(f"/todos/{id1}", json={"completed": True})
        
        # Create
        r3 = client.post("/todos", json={"title": "C"})
        id3 = r3.json()["id"]
        
        # Read
        get1 = client.get(f"/todos/{id1}")
        assert get1.json()["completed"] is True
        
        # Delete
        client.delete(f"/todos/{id2}")
        
        # List
        list_resp = client.get("/todos")
        remaining = [t["id"] for t in list_resp.json()]
        assert id1 in remaining
        assert id2 not in remaining
        assert id3 in remaining

    def test_delete_all_todos(self, client: TestClient):
        """Can delete all todos one by one."""
        # Create 10 todos
        ids = []
        for i in range(10):
            r = client.post("/todos", json={"title": f"Task {i}"})
            ids.append(r.json()["id"])
        
        # Delete all
        for todo_id in ids:
            response = client.delete(f"/todos/{todo_id}")
            assert response.status_code == 204
        
        # Verify list is empty
        list_response = client.get("/todos")
        assert list_response.json() == []

    def test_bulk_update_completed_status(self, client: TestClient):
        """Can mark multiple todos as complete."""
        # Create 5 todos
        ids = []
        for i in range(5):
            r = client.post("/todos", json={"title": f"Task {i}"})
            ids.append(r.json()["id"])
        
        # Mark all as complete
        for todo_id in ids:
            client.put(f"/todos/{todo_id}", json={"completed": True})
        
        # Verify all are complete
        list_response = client.get("/todos")
        todos = list_response.json()
        assert all(t["completed"] is True for t in todos)


class TestDataIntegrity:
    """Test that data remains consistent and correct."""

    def test_id_immutable_after_creation(self, client: TestClient):
        """Todo ID doesn't change after creation."""
        r1 = client.post("/todos", json={"title": "Task"})
        id1 = r1.json()["id"]
        
        client.put(f"/todos/{id1}", json={"title": "Updated"})
        
        r2 = client.get(f"/todos/{id1}")
        assert r2.json()["id"] == id1

    def test_created_at_immutable_after_creation(self, client: TestClient):
        """created_at doesn't change after creation."""
        r1 = client.post("/todos", json={"title": "Task"})
        original_created_at = r1.json()["created_at"]
        todo_id = r1.json()["id"]
        
        # Wait a bit
        time.sleep(0.1)
        
        # Update
        client.put(f"/todos/{todo_id}", json={"title": "Updated"})
        
        r2 = client.get(f"/todos/{todo_id}")
        assert r2.json()["created_at"] == original_created_at

    def test_todos_do_not_interfere_with_each_other(self, client: TestClient):
        """Changes to one todo don't affect others."""
        # Create 3 todos
        ids = []
        for i in range(3):
            r = client.post("/todos", json={"title": f"Task {i}"})
            ids.append(r.json()["id"])
        
        # Update first todo
        client.put(f"/todos/{ids[0]}", json={"title": "Modified", "completed": True})
        
        # Verify others are unchanged
        r2 = client.get(f"/todos/{ids[1]}")
        assert r2.json()["title"] == "Task 1"
        assert r2.json()["completed"] is False
        
        r3 = client.get(f"/todos/{ids[2]}")
        assert r3.json()["title"] == "Task 2"
        assert r3.json()["completed"] is False

    def test_list_todos_shows_all_updates(self, client: TestClient):
        """GET /todos reflects all create, update, delete operations."""
        # Create
        r1 = client.post("/todos", json={"title": "A"})
        id1 = r1.json()["id"]
        
        list1 = client.get("/todos").json()
        assert len(list1) == 1
        
        # Create another
        r2 = client.post("/todos", json={"title": "B"})
        list2 = client.get("/todos").json()
        assert len(list2) == 2
        
        # Update first
        client.put(f"/todos/{id1}", json={"title": "A Modified"})
        list3 = client.get("/todos").json()
        modified = [t for t in list3 if t["id"] == id1][0]
        assert modified["title"] == "A Modified"
        
        # Delete first
        client.delete(f"/todos/{id1}")
        list4 = client.get("/todos").json()
        assert len(list4) == 1
        assert list4[0]["title"] == "B"


class TestPerformance:
    """Test performance requirements (spec says <100ms per endpoint)."""

    def test_create_todo_response_time(self, client: TestClient):
        """POST /todos completes in <100ms."""
        import time
        start = time.time()
        client.post("/todos", json={"title": "Task"})
        elapsed = (time.time() - start) * 1000  # Convert to ms
        assert elapsed < 100, f"POST took {elapsed:.2f}ms, expected <100ms"

    def test_get_todos_response_time(self, client: TestClient):
        """GET /todos completes in <100ms."""
        import time
        # Create some todos first
        for i in range(10):
            client.post("/todos", json={"title": f"Task {i}"})
        
        start = time.time()
        client.get("/todos")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"GET /todos took {elapsed:.2f}ms, expected <100ms"

    def test_get_todo_by_id_response_time(self, client: TestClient):
        """GET /todos/{id} completes in <100ms."""
        import time
        r = client.post("/todos", json={"title": "Task"})
        todo_id = r.json()["id"]
        
        start = time.time()
        client.get(f"/todos/{todo_id}")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"GET /todos/{{id}} took {elapsed:.2f}ms, expected <100ms"

    def test_update_todo_response_time(self, client: TestClient):
        """PUT /todos/{id} completes in <100ms."""
        import time
        r = client.post("/todos", json={"title": "Task"})
        todo_id = r.json()["id"]
        
        start = time.time()
        client.put(f"/todos/{todo_id}", json={"title": "Updated"})
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"PUT took {elapsed:.2f}ms, expected <100ms"

    def test_delete_todo_response_time(self, client: TestClient):
        """DELETE /todos/{id} completes in <100ms."""
        import time
        r = client.post("/todos", json={"title": "Task"})
        todo_id = r.json()["id"]
        
        start = time.time()
        client.delete(f"/todos/{todo_id}")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 100, f"DELETE took {elapsed:.2f}ms, expected <100ms"
