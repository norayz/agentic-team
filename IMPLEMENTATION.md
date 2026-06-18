# Implementation Notes

**Issue:** #1  
**Branch:** backend/issue-1  

## What Was Built

A complete REST API for managing todo items using FastAPI and SQLite, meeting all acceptance criteria:

### Module Breakdown (from SDD)

1. **src/models.py** — SQLAlchemy ORM model
   - `Todo` model with fields: id (PK), title, completed, created_at
   - All fields map directly to API response schema

2. **src/schemas.py** — Pydantic validation schemas
   - `TodoCreate` — validates POST requests (title required, min_length=1)
   - `TodoUpdate` — validates PUT requests (partial updates with Optional fields)
   - `TodoResponse` — validates responses (id, title, completed, created_at)
   - Uses `exclude_unset=True` pattern (per Team Lead review note)

3. **src/database.py** — Database initialization and session management
   - SQLite database at `todos.db` (configurable via DATABASE_URL env var)
   - `init_db()` creates all tables on startup
   - `get_db()` dependency injection for routes

4. **src/routes.py** — All five API endpoints
   - POST /todos — Create todo, returns 201 with created todo
   - GET /todos — List all todos, returns 200 with array
   - GET /todos/{id} — Get single todo, returns 200 or 404
   - PUT /todos/{id} — Update todo (partial), returns 200 or 404
   - DELETE /todos/{id} — Delete todo, returns 204 or 404
   - Proper HTTP status codes for all cases
   - 404 errors with descriptive messages for missing todos
   - 422 validation errors for invalid input (handled by Pydantic)

5. **src/main.py** — FastAPI application entry point
   - Initializes database on startup
   - Includes routes
   - Provides Swagger UI at /docs and ReDoc at /redoc
   - Root endpoint with welcome message
   - Entry point for `uvicorn main:app --reload`

### Test Coverage

**tests/conftest.py** — Pytest fixtures
- `test_db` fixture creates isolated test database
- `client` fixture provides TestClient for API testing
- Dependency overrides for clean test isolation

**tests/test_routes.py** — 18 comprehensive tests covering:
- Create todo (success, missing title, empty title)
- List todos (empty, with items)
- Get todo (success, not found)
- Update todo (title only, completed only, partial updates)
- Delete todo (success, not found)
- JSON structure consistency
- Root endpoint

## Deviations from SDD

None. Implementation follows SDD exactly:
- Synchronous routes (no async/await) as specified
- SQLAlchemy ORM with Pydantic integration
- Partial update support using `exclude_unset=True` (per Team Lead guidance)
- Proper database initialization and session management
- All endpoints return correct status codes and schemas

## Known Limitations

None for the current scope. The implementation covers all acceptance criteria:
- ✓ POST /todos creates with 201
- ✓ GET /todos returns all
- ✓ GET /todos/{id} returns single or 404
- ✓ PUT /todos/{id} updates (partial) with 200 or 404
- ✓ DELETE /todos/{id} with 204 or 404
- ✓ 422 for missing/empty title
- ✓ Consistent JSON structure
- ✓ Swagger UI at /docs
- ✓ Persistence across restarts
- ✓ Single command startup

## How to Run

### Prerequisites
```bash
python3.10+
pip
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Start the API server with auto-reload
uvicorn src.main:app --reload

# Or without auto-reload (production-like)
uvicorn src.main:app
```

The server will start on `http://localhost:8000`

### Accessing the API
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Root endpoint: http://localhost:8000/

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes.py -v

# Run with coverage
pytest --cov=src tests/
```

### Example API Usage

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk"}'

# Response: {"id": 1, "title": "Buy milk", "completed": false, "created_at": "2024-01-01T..."}

# List all todos
curl http://localhost:8000/todos

# Get specific todo
curl http://localhost:8000/todos/1

# Update todo (mark complete)
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete todo
curl -X DELETE http://localhost:8000/todos/1
```

### Database
The SQLite database file `todos.db` will be created in the current directory on first run. Todos persist across server restarts.

To reset the database, simply delete `todos.db` and restart the server.
