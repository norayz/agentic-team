# Implementation Notes

**Issue:** #1  
**Branch:** backend/1  

## What Was Built

A complete REST API for managing todo items using FastAPI and SQLite3 (raw SQL with parameterized queries). The implementation provides full CRUD operations with proper error handling, validation, and HTTP status codes.

### Key Components

#### 1. Database Layer (`src/database.py`)
- Raw sqlite3 with parameterized queries (prevents SQL injection)
- Functions: `init_db()`, `create_todo()`, `get_todos()`, `get_todo_by_id()`, `update_todo()`, `delete_todo()`
- Environment variable configuration: `DATABASE_URL` (defaults to `sqlite:///./todos.db`)
- Proper error handling with rollback on failures
- Context manager for safe database connections

#### 2. Validation Schemas (`src/schemas.py`)
- `TodoCreate`: Validates non-empty, non-whitespace titles
- `TodoUpdate`: Optional fields for partial updates with validation
- `TodoResponse`: Consistent response structure with all required fields
- Pydantic field validators ensure data integrity

#### 3. API Routes (`src/routes.py`)
- `POST /todos` — Create new todo (201 on success, 422 on validation error, 503 on DB error)
- `GET /todos` — List all todos (200)
- `GET /todos/{id}` — Get single todo (200 if found, 404 if not)
- `PUT /todos/{id}` — Update todo title and/or completed status (200 on success, 404 if not found, 503 on DB error)
- `DELETE /todos/{id}` — Delete todo (204 on success, 404 if not found, 503 on DB error)
- Proper exception handling with meaningful error messages
- Partial updates preserve unset fields via `model_dump(exclude_unset=True)`

#### 4. Application Factory (`src/main.py`)
- FastAPI app with startup event to initialize database
- Auto-generated Swagger UI at `/docs`
- Root endpoint at `/` for health check
- Includes API metadata (title, description, version)

#### 5. Entry Point (`main.py`)
- Uvicorn server configuration
- Configurable host and port via environment variables
- Support for `--reload` in development

#### 6. Tests (`tests/test_routes.py`)
- 14 comprehensive tests covering all acceptance criteria
- Tests for happy paths, error cases, and edge cases
- Temporary database per test for isolation
- Coverage of:
  - Create with validation (empty/whitespace rejection)
  - List (empty and with items)
  - Get (found and not found)
  - Update (title, completed, partial)
  - Delete (success and not found)
  - JSON structure consistency
  - Root endpoint
  - Swagger UI accessibility

## Deviations from SDD

**Single major deviation (by design spec):**

- **ORM Choice**: The SDD specified "SQLAlchemy or raw SQL — implementer's choice". Due to Python 3.13 incompatibility with SQLAlchemy 2.0.x and 2.1.x, this implementation uses **raw sqlite3 with parameterized queries** instead of SQLAlchemy ORM.
  
  **Why this was necessary:**
  - SQLAlchemy imports fail on Python 3.13 due to typing module incompatibilities
  - Raw sqlite3 is in Python's standard library, adds no external dependencies
  - Parameterized queries provide full SQL injection protection
  - More explicit control over database operations
  - Actually simpler for single-user local app (no ORM overhead)
  
  **Impact on functionality**: None. All acceptance criteria are met identically.

## Known Limitations

1. **Single-user, local-only design** — As per spec requirements, no authentication, no multi-user support, no concurrent access handling beyond SQLite's built-in locking

2. **No advanced queries** — No search, filtering, sorting, or pagination (not in spec)

3. **No transaction rollback for partial updates** — If validation passes but an update query fails, the state is consistent but some fields may not have changed. This is acceptable for a single-user local API

4. **Database file permissions** — No special handling for database file permissions (relies on OS umask)

## How to Run

### Prerequisites
- Python 3.10+ (tested with 3.13)
- pip

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

### Running Tests

```bash
# Run all tests
pytest tests/test_routes.py -v

# Run a specific test
pytest tests/test_routes.py::test_create_todo_success -v
```

### Using with Docker

The Dockerfile (from DevOps PR #3) will build and run this application:

```bash
# Build Docker image
docker build -t todos-api .

# Run in Docker
docker run -p 8000:8000 todos-api

# With docker-compose
docker-compose up --build
```

### Environment Variables

```bash
# Database location (defaults to sqlite:///./todos.db in current directory)
DATABASE_URL="sqlite:///./todos.db"

# Server host and port (defaults to 0.0.0.0:8000)
API_HOST="0.0.0.0"
API_PORT="8000"
```

## Testing in Sandbox

All code was implemented following TDD methodology:

1. **Database layer tests** — Verified `init_db()`, `create_todo()` with title validation
2. **Schema validation tests** — Verified Pydantic validators reject empty/whitespace titles
3. **CRUD operations tests** — All 5 endpoints tested with success and error paths
4. **Partial update tests** — Verified `exclude_unset=True` preserves unset fields
5. **Error handling tests** — Database errors return 503, validation errors return 422
6. **Persistence tests** — Todo data survives across database reconnections

## Code Quality

- ✅ No magic numbers — All constants named
- ✅ Meaningful names — Functions and variables clearly named
- ✅ Fail loudly — Errors raise exceptions, not silent failures
- ✅ No dead code — All code is used
- ✅ DRY principle — No unnecessary duplication
- ✅ Single responsibility — Each module has one job
- ✅ Security — Parameterized queries prevent injection, no secrets in code
- ✅ Type hints — All functions annotated
- ✅ Exception handling — All error paths handled

## Architecture

```
apps/1/
├── src/
│   ├── __init__.py
│   ├── database.py      # Raw SQL data access layer
│   ├── schemas.py       # Pydantic validation schemas
│   ├── routes.py        # FastAPI endpoints
│   └── main.py          # Application factory
├── main.py              # Uvicorn entry point
├── tests/
│   ├── __init__.py
│   └── test_routes.py   # Comprehensive test suite (14 tests)
├── requirements.txt     # Dependencies (FastAPI, Pydantic, Pytest, HTTPx)
└── IMPLEMENTATION.md    # This file
```

## Acceptance Criteria — All Met

- [x] POST /todos creates todo with 201, returns id, title, completed (default false), created_at
- [x] GET /todos returns array of all todos with 200
- [x] GET /todos/{id} returns single todo with 200, returns 404 if not found
- [x] PUT /todos/{id} updates title and/or completed with 200, returns 404 if not found
- [x] DELETE /todos/{id} returns 204 on success, 404 if not found
- [x] POST /todos with missing/empty title returns 422
- [x] All responses use consistent JSON structure
- [x] Swagger UI accessible at /docs
- [x] Todos persist across server restarts (SQLite file-based)
- [x] Server starts with single command (uvicorn src.main:app --reload)
