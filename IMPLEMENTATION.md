# Implementation Notes

**Issue:** #1  
**Branch:** backend/issue-1  

## What Was Built

A complete REST API for a personal todo app using FastAPI and SQLAlchemy, with full CRUD operations:

### Module Breakdown

1. **src/database.py** (Database Setup)
   - SQLAlchemy engine and session factory with SQLite support
   - `init_db()` function to create all tables at app startup
   - `get_db()` dependency injection for routes
   - Error handling for database initialization failures

2. **src/models.py** (Data Model)
   - `Todo` SQLAlchemy model with fields: id, title, completed (default: false), created_at (auto-set to UTC now)

3. **src/schemas.py** (Request/Response Validation)
   - `TodoCreate` for POST requests (required title field)
   - `TodoUpdate` for PUT requests (optional title and completed fields)
   - `TodoResponse` for all responses (id, title, completed, created_at)
   - Unified validation: title must not be empty or whitespace-only

4. **src/routes.py** (API Endpoints)
   - `POST /todos` — Create new todo (returns 201)
   - `GET /todos` — List all todos (returns 200)
   - `GET /todos/{id}` — Get single todo (returns 200 or 404)
   - `PUT /todos/{id}` — Update todo fields (returns 200 or 404)
   - `DELETE /todos/{id}` — Delete todo (returns 204 or 404)
   - Helper function `get_todo_or_404()` to reduce repetition
   - Comprehensive exception handling for all SQLAlchemy errors

5. **src/main.py** (App Factory)
   - FastAPI app with metadata (title, description, version)
   - Startup event to initialize database tables
   - Router registration

6. **main.py** (Uvicorn Entry Point)
   - Configurable host and port from environment variables
   - Development mode enabled via APP_ENV environment variable

### Key Features

- ✅ Full CRUD functionality for todos
- ✅ Persistent storage using SQLite (default: todos.db in current directory)
- ✅ Auto-generated Swagger UI at `/docs` and ReDoc at `/redoc`
- ✅ Pydantic validation with clear error messages (422 for invalid input)
- ✅ Proper HTTP status codes (201, 200, 204, 404, 503)
- ✅ Database exception handling with 503 Service Unavailable responses
- ✅ Partial updates (PUT can update title, completed, or both)
- ✅ Consistent JSON response format with all required fields
- ✅ Environment variable configuration (DATABASE_URL, API_HOST, API_PORT, APP_ENV)

## Deviations from SDD

None. Implementation follows SDD exactly.

## Known Limitations

1. **Single-user only** — No authentication, designed for personal use as per spec
2. **SQLite concurrency** — Limited concurrent write support (by design, single-user)
3. **No migrations** — Schema changes require manual table recreation
4. **No logging** — Not included per non-goals in spec
5. **No advanced validation** — Title length, special characters, etc. not restricted

## How to Run

### Prerequisites
- Python 3.10 or higher
- pip or conda for package management

### Local Development (with auto-reload)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload

# The API will be available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

### Production Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export APP_ENV=production
export DATABASE_URL=sqlite:///./todos.db
export API_PORT=8000

# Start the server (without reload)
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker (with docker-compose)

```bash
# Copy environment file
cp .env.example .env

# Start with docker-compose
docker-compose up --build

# The API will be available at http://localhost:8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_routes.py
```

## Testing

All acceptance criteria have passing tests in `tests/test_routes.py`:
- POST /todos creates todo with 201 status
- POST /todos rejects empty title with 422 status
- GET /todos returns all todos
- GET /todos/{id} returns single todo or 404
- PUT /todos/{id} updates todo fields or 404
- DELETE /todos/{id} deletes todo or 404
- All responses have correct JSON structure
- Swagger UI auto-generates at /docs

## Code Review Changes (v2)

Addressed all blocking code review issues:

1. **DELETE endpoint return statement** — Added explicit `return None` for clarity
2. **Database exception handling** — All endpoints now catch `SQLAlchemyError` and return 503
3. **Missing pytest dependency** — Added `pytest==7.4.4` to requirements.txt
4. **Unified validation** — Removed redundant validators, now single validation rule per field
5. **Database initialization error handling** — Wrapped engine creation and table creation in try/except
6. **Startup-time table creation** — Moved to app startup event via `@app.on_event("startup")`
7. **Extracted helper function** — `get_todo_or_404()` reduces repetition in GET, PUT, DELETE
8. **Environment variable configuration** — main.py now reads API_HOST and API_PORT from env
9. **Updated dependencies** — All packages pinned to latest stable versions
