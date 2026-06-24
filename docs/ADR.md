# Architecture Decision Record

**Issue:** #1  
**Author:** Architect Agent  

---

## Decision 1: Use Layered Architecture with 5 Focused Modules

**Status:** Accepted  

**Context:**  
For a "simple" todo API, we could put everything in a single file (`main.py`). This would minimize file count and make the entire codebase visible at a glance. However, the spec requires professional-quality code that can be extended (e.g., adding features like due dates or priorities later). We need clear separation of concerns to make testing, debugging, and future modifications manageable.

**Options Considered:**

- **Option A: Single-file monolith (`main.py` with everything)**  
  Pros: Fewest files, no imports between modules, fastest initial implementation.  
  Cons: Hard to test in isolation, violates Single Responsibility Principle, becomes unmaintainable as features are added, no clear boundaries between HTTP handling, validation, and persistence.

- **Option B: Layered architecture (main → routes → schemas + models → database)**  
  Pros: Clear separation of concerns, each module testable in isolation, idiomatic FastAPI pattern, scales well even if project grows, easier to onboard new developers.  
  Cons: More files for a "simple" project, requires understanding of layering.

- **Option C: Hexagonal/ports-and-adapters architecture**  
  Pros: Maximum flexibility, domain logic isolated from infrastructure.  
  Cons: Over-engineering for a single-entity CRUD API, adds repository pattern, service layer, and port interfaces that provide zero value at this scale.

**Decision:**  
Layered architecture (Option B). The project may be "simple" today, but clean separation of concerns is a best practice that costs almost nothing upfront and pays dividends immediately when writing tests or adding features. Onion/hexagonal architectures (Option C) are overkill — we have no complex domain logic to isolate.

**Consequences:**
- **Positive:** Each layer (HTTP → validation → ORM → database) can be tested independently. Backend engineer can write unit tests for routes without hitting the database (mock the session). Pydantic schemas enforce validation automatically. ORM models are reusable.
- **Negative:** Five files instead of one. Developer must understand the flow: `main.py` → `routes.py` → `models.py` + `schemas.py` → `database.py` → SQLite. (This is standard FastAPI practice, so "negative" is minor.)
- **Constraints:** Future features (e.g., adding tags or due dates) should follow this layering — new columns go in `models.py`, new validation rules in `schemas.py`, new endpoints in `routes.py`.

---

## Decision 2: Synchronous Routes (No async/await)

**Status:** Accepted  

**Context:**  
FastAPI fully supports async/await, and many FastAPI tutorials use `async def` for route handlers. However, async provides concurrency benefits only when I/O operations are async-compatible. SQLite is a file-based, synchronous database — it locks the entire database file during writes. Using `async` would require `aiosqlite`, add dependency management complexity, and provide zero performance benefit for this workload (single-user, local-only, low-volume).

**Options Considered:**

- **Option A: Synchronous routes (`def` instead of `async def`)**  
  Pros: Simpler code, no need for `aiosqlite`, matches SQLite's synchronous nature, easier to debug (no event loop issues), fewer dependencies.  
  Cons: Slightly less "modern" (async is trendy in Python), cannot handle concurrent requests efficiently (but spec does not require concurrency).

- **Option B: Async routes with `aiosqlite`**  
  Pros: "Modern" Python, allows concurrent request handling (FastAPI runs async routes in event loop).  
  Cons: SQLite locks the file during writes anyway, so async provides no throughput improvement. Adds `aiosqlite` dependency. Complicates testing (must use `pytest-asyncio` or similar). YAGNI — spec explicitly states single-user, local-only.

**Decision:**  
Synchronous routes (Option A). SQLite is synchronous, the workload is single-user, and there is no concurrency requirement in the spec. Using `async` would be cargo-culting "modern Python" without understanding the constraints. Simpler code wins.

**Consequences:**
- **Positive:** Fewer dependencies, simpler testing (standard `pytest` without async fixtures), code is easier for junior developers to understand, no event loop edge cases.
- **Negative:** If the project later scales to multi-user or migrates to PostgreSQL (which supports async via `asyncpg`), routes would need to be refactored to `async def`. However, this is a non-goal per the spec.
- **Constraints:** If async is needed in the future, the ORM layer (SQLAlchemy session usage in `routes.py`) would need to change to `async_session`. This is acceptable technical debt for a local-only project.

---

## Decision 3: SQLAlchemy ORM Over Raw SQL

**Status:** Accepted  

**Context:**  
The spec allows "SQLAlchemy or raw SQL — implementer's choice." Raw SQL (e.g., `cursor.execute("INSERT INTO todos ...")`) is lightweight and avoids ORM overhead. However, for a REST API where we need to serialize database rows to JSON, an ORM provides automatic mapping, type safety, and better integration with Pydantic.

**Options Considered:**

- **Option A: Raw SQL with `sqlite3` module**  
  Pros: Zero abstraction, maximum control, no ORM learning curve, slightly faster (no ORM overhead).  
  Cons: Manual SQL string construction (error-prone, no type safety), manual row-to-dict conversion for JSON serialization, no integration with Pydantic, harder to test (must mock `cursor` objects), SQL injection risk if not careful with parameterization.

- **Option B: SQLAlchemy Core (expression language, no ORM)**  
  Pros: Type-safe query construction, avoids SQL injection, integrates with Pydantic via manual mapping.  
  Cons: Still requires manual row-to-dict conversion, more verbose than ORM for simple CRUD, less idiomatic for FastAPI.

- **Option C: SQLAlchemy ORM**  
  Pros: Automatic mapping between database rows and Python objects, integrates seamlessly with Pydantic (use `orm_mode=True`), type-safe, less boilerplate for CRUD operations, easier to test (mock session, not cursor), FastAPI documentation shows ORM examples.  
  Cons: Slight performance overhead (negligible for single-user workload), learning curve for ORM concepts (sessions, declarative models).

**Decision:**  
SQLAlchemy ORM (Option C). The integration with Pydantic (via `orm_mode=True`) eliminates manual serialization code. Type safety reduces bugs. The ORM overhead is unmeasurable for a single-user API. Raw SQL (Option A) would save a few milliseconds but cost hours in manual serialization logic and testing complexity.

**Consequences:**
- **Positive:** Pydantic schemas can convert ORM objects to JSON automatically. Route handlers are concise (e.g., `db.query(Todo).all()` instead of manual SQL + row parsing). Testing is easier (mock `Session`, not database cursors). Type hints work throughout the stack.
- **Negative:** Adds SQLAlchemy dependency (but it's lightweight and well-maintained). Developer must understand ORM concepts (sessions, lazy loading). If performance becomes an issue (unlikely for single-user), optimizing ORM queries is harder than optimizing raw SQL.
- **Constraints:** All database access must go through the ORM. If raw SQL is needed for a complex query later, use `session.execute()` with SQLAlchemy Core expressions, not string concatenation.

---

**End of Architecture Decision Record**