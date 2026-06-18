# Barista Site - Test Suite

## Overview

This directory contains comprehensive tests for the Barista Site coffee ordering application.

## Test Structure

### acceptance.test.js
Maps directly to the acceptance criteria from the specification. Each test verifies a specific requirement.

**Coverage:**
- [AC1] Menu page displays all items with name, description, and price
- [AC2] Each menu item has an Add to Cart button
- [AC3] Cart view shows items, quantities, and total
- [AC4] Cart has quantity controls and remove functionality
- [AC5] Order form collects customer name and pickup time
- [AC6] Orders are stored persistently in database
- [AC7] Confirmation page shows order summary
- [AC8] Admin page lists orders with details
- [AC9] Admin can mark orders complete
- [AC10] Menu items are database-driven (not hardcoded)
- [AC11] Site is mobile-responsive (375px)

**Edge Cases:**
- Empty/invalid customer names
- Missing pickup times
- Empty carts
- Invalid item IDs
- Non-existent orders
- Large quantities
- Whitespace handling

**Security:**
- Server-side price recalculation (never trust client)
- SQL injection prevention

### services.test.js
Tests database layer and business logic (data operations, validation).

### routes.test.js
Tests HTTP routes and error handling.

## Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test -- tests/acceptance.test.js

# Run with coverage
npm test -- --coverage
```

## Test Database

Tests use isolated SQLite databases in `apps/5/data/test-*.db` to avoid polluting development data. These are cleaned up automatically before and after each test.

## Test Philosophy

- **Independence:** Each test can run in isolation
- **Determinism:** Tests produce the same result every time
- **Clarity:** Test names describe what is being verified
- **Coverage:** All acceptance criteria have corresponding tests
- **Adversarial:** Tests try to break the implementation
