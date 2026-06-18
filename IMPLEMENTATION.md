# Implementation Notes

**Issue:** #1  
**Branch:** backend/issue-1  

## What Was Built

A complete REST API for managing todo items using FastAPI, SQLAlchemy, and SQLite.

### Module Breakdown (Following SDD)

1. **src/main.py** — FastAPI application factory
   - Creates app with title, description, and version
   - Includes router with all endpoints
   - Root endpoint at `/` provides API metadata

2. **src/routes.py** — All five API endpoints
   - `POST /todos` — Create new todo (201 on success, 422 on validation error)
   - `GET /todos` — List all todos (200, always returns array)
   - `GET /todos/{id}` — Get single todo (200 if found, 404 otherwise)
   - `PUT /todos/{id}` — Update todo with partial update support (200 if found, 404 otherwise)
   - `DELETE /todos/{id}` — Delete todo (204 on success, 404 otherwise)

3. **src/schemas.py** — Pydantic request/response schemas
   - `TodoCreate` — Validates title is required and non-empty
   - `TodoUpdate` — Optional title and completed fields; uses `exclude_unset=True` for partial updates
   - `TodoResponse` — Includes id, title, completed, created_at

4. **src/models.py** — SQLAlchemy ORM model
   - `Todo` — Represents a todo item with all required fields
   - Default values: completed=False, created_at=current UTC time

5. **src/database.py** — Database configuration
   - SQLite database (file-based at ./todos.db or via DATABASE_URL env var)
   - SessionLocal factory for dependency injection
   - Tables created on startup

6. **main.py** — Entry point for uvicorn
   - Imports app from src/main and starts server

7. **requirements.txt** — All dependencies pinned

### Swagger UI

- Automatically generated at `/docs` with full request/response schemas
- ReDoc also available at `/redoc`
- All endpoints documented with descriptions

## Deviations from SDD

None. Implementation follows the SDD exactly:

- Five endpoints with correct status codes and behavior ✓
- JSON request/response schemas match spec ✓
- Validation errors return 422 ✓
- Swagger UI at /docs ✓
- SQLite persistence ✓
- SQLAlchemy ORM ✓
- Single-user, local-only design ✓
- No authentication, external services, or advanced features ✓

## Known Limitations

- No concurrent request handling (uvicorn runs single-threaded by default in reload mode)
- No request logging infrastructure
- No rate limiting
- No deployment to cloud (runs on localhost:8000)
- SQLite suitable only for single-process use (not recommended for multi-process servers)

## How to Run

### Prerequisites

- Python 3.10 or later
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Start the Server

```bash
# Option 1: Using uvicorn directly
uvicorn main:app --reload

# Option 2: Using Python entry point
python main.py
```

Server will start at `http://localhost:8000`

### API Documentation

After server starts:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

### Test the API

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk"}'

# List all todos
curl http://localhost:8000/todos

# Get a single todo
curl http://localhost:8000/todos/1

# Update a todo
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete a todo
curl -X DELETE http://localhost:8000/todos/1
```

### Persistent Database

Todos are stored in `./todos.db` (SQLite file). This file persists across server restarts.

To reset:
```bash
rm todos.db
```

Next server start will create a fresh database.

### Environment Variables

Optional:
- `DATABASE_URL` — Override database connection string (default: `sqlite:///./todos.db`)

Example:
```bash
DATABASE_URL="sqlite:///./data/todos.db" uvicorn main:app --reload
```
