# Software Design Document: REST API for a Todo App

**Issue:** #1  
**Status:** Draft  
**Author:** Architect Agent  

---

## 1. System Overview

This system is a single-user, local-first REST API for managing todo items. It provides full CRUD operations (Create, Read, Update, Delete) via HTTP endpoints, persists data to a file-based SQLite database, and auto-generates interactive API documentation. The system does not handle authentication, multi-user scenarios, or deployment concerns — it is optimized for local development and personal use.

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         HTTP Client                          │
│                    (curl, Postman, browser)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                   (FastAPI app instance)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        routes.py                             │
│              (Endpoint handlers for /todos)                  │
└─────────┬──────────────────────────────────────┬────────────┘
          │                                       │
          │ validates with                        │ queries/mutates
          ▼                                       ▼
┌──────────────────────┐              ┌────────────────────────┐
│     schemas.py       │              │      models.py         │
│  (Pydantic models)   │              │  (SQLAlchemy ORM)      │
└──────────────────────┘              └──────────┬─────────────┘
                                                  │
                                                  │ persists to
                                                  ▼
                                      ┌────────────────────────┐
                                      │     database.py        │
                                      │  (session factory)     │
                                      └──────────┬─────────────┘
                                                  │
                                                  ▼
                                      ┌────────────────────────┐
                                      │   todos.db (SQLite)    │
                                      └────────────────────────┘
```

## 3. Module Breakdown

### main.py
- **Responsibility:** Application entry point; creates FastAPI app instance and includes routers.
- **Inputs:** None (invoked by Uvicorn on server start).
- **Outputs:** FastAPI app instance ready to serve requests.
- **Key logic:** Imports routes, initializes database on startup, configures CORS (if needed), exposes `/docs` for Swagger UI.

### routes.py
- **Responsibility:** Define HTTP endpoint handlers for all CRUD operations on todos.
- **Inputs:** HTTP requests (path params, query params, request bodies).
- **Outputs:** HTTP responses (JSON bodies, status codes).
- **Key logic:** Validate incoming requests using Pydantic schemas, call ORM models to persist/retrieve data, return appropriate HTTP status codes (200, 201, 204, 404, 422).

### schemas.py
- **Responsibility:** Define Pydantic models for request validation and response serialization.
- **Inputs:** Raw request data (JSON payloads from HTTP clients).
- **Outputs:** Validated Python objects (Pydantic model instances).
- **Key logic:** Enforce required fields (e.g., `title` must be non-empty), define response structure matching acceptance criteria, enable FastAPI auto-documentation.

### models.py
- **Responsibility:** Define SQLAlchemy ORM models representing the `todos` database table.
- **Inputs:** None (class definitions).
- **Outputs:** ORM classes that map to database tables.
- **Key logic:** Define schema for `Todo` table with columns `id`, `title`, `completed`, `created_at`. Provide default values (e.g., `completed=False`, `created_at=datetime.utcnow()`).

### database.py
- **Responsibility:** Manage database connection, session lifecycle, and table creation.
- **Inputs:** None (configuration hardcoded for SQLite file path).
- **Outputs:** SQLAlchemy session factory for dependency injection into routes.
- **Key logic:** Create `engine` pointing to `todos.db`, create `SessionLocal` factory, provide `get_db()` dependency for FastAPI routes, call `Base.metadata.create_all()` to initialize tables on startup.

## 4. Data Models

### Database Schema (SQLAlchemy ORM)

```python
class Todo(Base):
    __tablename__ = "todos"
    
    id: int                # Primary key, auto-increment
    title: str             # Required, non-empty string
    completed: bool        # Default: False
    created_at: datetime   # Default: UTC timestamp at creation
```

**Table: `todos`**

| Column      | Type        | Constraints                     |
|-------------|-------------|---------------------------------|
| id          | INTEGER     | PRIMARY KEY, AUTOINCREMENT      |
| title       | TEXT        | NOT NULL                        |
| completed   | BOOLEAN     | NOT NULL, DEFAULT FALSE         |
| created_at  | DATETIME    | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### API Schemas (Pydantic)

**TodoCreate** (request body for `POST /todos`)
```python
{
    "title": str  # required, min_length=1
}
```

**TodoUpdate** (request body for `PUT /todos/{id}`)
```python
{
    "title": Optional[str],      # optional, if provided must be non-empty
    "completed": Optional[bool]  # optional
}
```

**TodoResponse** (response body for all successful reads/writes)
```python
{
    "id": int,
    "title": str,
    "completed": bool,
    "created_at": str  # ISO 8601 format: "2024-01-01T12:00:00"
}
```

## 5. API Contracts

### POST /todos
**Purpose:** Create a new todo item.  
**Request Body:**  
```json
{
    "title": "Buy milk"
}
```
**Success Response (201 Created):**  
```json
{
    "id": 1,
    "title": "Buy milk",
    "completed": false,
    "created_at": "2024-01-15T10:30:00"
}
```
**Error Responses:**  
- `422 Unprocessable Entity` — if `title` is missing or empty string  
```json
{
    "detail": [
        {
            "loc": ["body", "title"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

---

### GET /todos
**Purpose:** Retrieve all todo items.  
**Request:** No body or parameters.  
**Success Response (200 OK):**  
```json
[
    {
        "id": 1,
        "title": "Buy milk",
        "completed": false,
        "created_at": "2024-01-15T10:30:00"
    },
    {
        "id": 2,
        "title": "Walk the dog",
        "completed": true,
        "created_at": "2024-01-15T11:00:00"
    }
]
```
**Notes:** Returns empty array `[]` if no todos exist.

---

### GET /todos/{id}
**Purpose:** Retrieve a single todo item by ID.  
**Path Parameter:** `id` (integer)  
**Success Response (200 OK):**  
```json
{
    "id": 1,
    "title": "Buy milk",
    "completed": false,
    "created_at": "2024-01-15T10:30:00"
}
```
**Error Responses:**  
- `404 Not Found` — if todo with given ID does not exist  
```json
{
    "detail": "Todo not found"
}
```

---

### PUT /todos/{id}
**Purpose:** Update a todo's title and/or completed status.  
**Path Parameter:** `id` (integer)  
**Request Body (all fields optional, but at least one should be provided):**  
```json
{
    "title": "Buy oat milk",
    "completed": true
}
```
**Success Response (200 OK):**  
```json
{
    "id": 1,
    "title": "Buy oat milk",
    "completed": true,
    "created_at": "2024-01-15T10:30:00"
}
```
**Error Responses:**  
- `404 Not Found` — if todo with given ID does not exist  
```json
{
    "detail": "Todo not found"
}
```
- `422 Unprocessable Entity` — if `title` is provided but is an empty string  

---

### DELETE /todos/{id}
**Purpose:** Delete a todo item by ID.  
**Path Parameter:** `id` (integer)  
**Success Response (204 No Content):**  
- No response body.

**Error Responses:**  
- `404 Not Found` — if todo with given ID does not exist  
```json
{
    "detail": "Todo not found"
}
```

---

### Swagger UI
**Endpoint:** `GET /docs`  
**Purpose:** Interactive API documentation auto-generated by FastAPI.  
**Notes:** All endpoints above must be documented with request/response schemas visible in Swagger UI.

## 6. Technology Choices

| Technology       | Justification                                                                                                                                                  |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Python 3.10+** | Specified in constraints; modern language features (type hints, match statements).                                                                              |
| **FastAPI**      | Specified in constraints; provides auto-generated OpenAPI docs, Pydantic validation, and async support (though we won't use async for SQLite).                |
| **SQLite**       | Specified in constraints; file-based, zero-config, perfect for local single-user persistence.                                                                  |
| **SQLAlchemy**   | Chosen over raw SQL for type-safety, easier testing, better integration with Pydantic, and cleaner code. ORM overhead is negligible for single-user workload. |
| **Uvicorn**      | Specified in constraints; lightweight ASGI server, standard for FastAPI.                                                                                       |
| **Pydantic**     | Comes with FastAPI; enforces request validation and powers auto-generated docs.                                                                                |

**Why synchronous routes (no `async`/`await`)?**  
SQLite is a synchronous, file-based database. Using `async` would require `aiosqlite` and add complexity without performance benefit for single-user local usage. Simpler code wins.

## 7. Implementation Order

1. **Database setup (`database.py`, `models.py`)**  
   - Define `Todo` ORM model with all fields.  
   - Create database engine and session factory.  
   - Test: Run script to create `todos.db` and verify table schema with `sqlite3` CLI.

2. **Pydantic schemas (`schemas.py`)**  
   - Define `TodoCreate`, `TodoUpdate`, `TodoResponse`.  
   - Test: Instantiate schemas with valid/invalid data and assert validation behavior.

3. **Create endpoint (`POST /todos` in `routes.py`)**  
   - Implement route handler that accepts `TodoCreate`, saves to DB, returns `TodoResponse`.  
   - Test: Use `curl` or Postman to POST a new todo, verify 201 response and DB persistence.

4. **Read endpoints (`GET /todos`, `GET /todos/{id}` in `routes.py`)**  
   - Implement list-all and get-by-id handlers.  
   - Test: Verify 200 responses, empty array for no todos, 404 for missing ID.

5. **Update endpoint (`PUT /todos/{id}` in `routes.py`)**  
   - Implement handler that updates `title` and/or `completed`, returns updated todo.  
   - Test: Verify 200 response with updated data, 404 for missing ID, 422 for empty title.

6. **Delete endpoint (`DELETE /todos/{id}` in `routes.py`)**  
   - Implement handler that deletes by ID, returns 204.  
   - Test: Verify 204 response, 404 for missing ID, confirm DB deletion.

7. **Application entry point (`main.py`)**  
   - Create FastAPI app, include router, add startup event to initialize DB.  
   - Test: Run `uvicorn main:app --reload`, verify server starts, access `/docs`, test all endpoints.

8. **Dependencies (`requirements.txt`)**  
   - List `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic` (if not bundled with FastAPI).  
   - Test: Create fresh virtualenv, `pip install -r requirements.txt`, verify server runs.

**Why this order?**  
Foundations first (database, schemas), then endpoints in dependency order (create → read → update → delete), finally integration (main app). Each step is testable before moving to the next.

## 8. Error Handling Strategy

### Expected Errors (Client mistakes)
- **Missing required fields:** Return `422 Unprocessable Entity` with FastAPI's default Pydantic validation error format.
- **Empty string for `title`:** Return `422 Unprocessable Entity` — enforce with Pydantic `min_length=1` constraint.
- **Invalid ID (not found):** Return `404 Not Found` with JSON body `{"detail": "Todo not found"}`.

### Unexpected Errors (Server issues)
- **Database connection failure:** Let FastAPI's default exception handler return `500 Internal Server Error`. (SQLite file-based DB should never fail unless disk is full or permissions are wrong.)
- **Constraint violations (e.g., NULL in NOT NULL column):** Should never happen if Pydantic validation works correctly. If it does, return `500 Internal Server Error`.

### Logging
- No explicit logging infrastructure required (per Non-Goals).
- Print statements or Uvicorn's default logging are sufficient for local debugging.

### Retry Behavior
- No retries needed — all operations are synchronous and deterministic.
- If a request fails, the client should retry manually.

---

**End of Software Design Document**