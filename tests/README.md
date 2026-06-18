# QA Test Suite for Todo API (Issue #1)

## Overview

This test suite provides comprehensive QA coverage for the REST API for a personal todo app, verifying all acceptance criteria and testing edge cases, error handling, and integration scenarios.

## Test Structure

### `test_routes.py` (Backend-provided tests)
- Basic endpoint functionality
- CRUD operations
- Response validation
- **14 tests**

### `test_qa_acceptance.py` (QA acceptance criteria tests)
- Maps each acceptance criterion from the spec to test cases
- Happy path and failure cases for each criterion
- Edge cases (long titles, Unicode, special characters)
- Error validation (invalid inputs, missing fields)
- Response structure consistency

**Acceptance Criteria Coverage:**
1. ✅ POST /todos creates todo with 201
2. ✅ GET /todos returns 200 array
3. ✅ GET /todos/{id} returns 200 or 404
4. ✅ PUT /todos/{id} updates and returns 200 or 404
5. ✅ DELETE /todos/{id} returns 204 or 404
6. ✅ POST with missing/empty title returns 422
7. ✅ Consistent JSON structure
8. ✅ Swagger UI at /docs
9. ✅ Todos persist (tested in integration)
10. ✅ Server starts with single command

### `test_qa_integration.py` (Integration tests)
- Persistence verification
- State transition validation
- Sequential and interleaved CRUD operations
- Data integrity checks
- Performance validation (<100ms per endpoint)

**Test Categories:**
- Persistence: Create, retrieve, update, delete persistence
- State transitions: Incomplete ↔ complete, title updates
- Concurrent operations: Bulk operations, interleaved CRUD
- Data integrity: ID immutability, created_at immutability, isolation
- Performance: All endpoints respond in <100ms

## Running Tests

### Run all tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_qa_acceptance.py -v
pytest tests/test_qa_integration.py -v
```

### Run specific test
```bash
pytest tests/test_qa_acceptance.py::TestAcceptanceCriteria::test_post_todos_creates_todo_with_201 -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Database

Tests use an in-memory SQLite database (temp file) that is created fresh for each test fixture, ensuring test isolation and no interference between tests.

## Expected Results

All tests should pass. If any test fails:
1. Check the error message for details
2. Verify the implementation matches the spec
3. Look for notes in `IMPLEMENTATION.md` about known limitations

## Performance Baselines

All endpoints must respond in <100ms under single-user load (per spec):
- POST /todos: <100ms ✅
- GET /todos: <100ms ✅
- GET /todos/{id}: <100ms ✅
- PUT /todos/{id}: <100ms ✅
- DELETE /todos/{id}: <100ms ✅

## Known Test Issues

- `test_root_endpoint`: Will fail until root endpoint is added (not in acceptance criteria)
  - This test is informational; the root endpoint is not specified in the requirements
  - Backend may choose to implement it or remove the test

## Test Philosophy

These tests follow adversarial testing principles:
- Test happy paths to verify basic functionality
- Test failure modes to verify error handling
- Test edge cases (empty, null, very long, Unicode, special chars)
- Test data integrity and isolation
- Test that changes persist and are atomic
- Verify response codes and structures exactly match the spec

The goal is to be confident the implementation will work correctly in production, not just that it passes basic tests.
