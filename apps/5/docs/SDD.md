# Software Design Document: Barista Site — Coffee House Online Ordering

**Issue:** #5  
**Status:** Draft  
**Author:** Architect Agent  

---

## 1. System Overview

The Barista Site is a single-location coffee house ordering web application. Customers browse a menu, build a cart, and submit orders with their name and desired pickup time. The shop owner views incoming orders via an admin page and marks them complete. The system prioritizes simplicity, fast load times (sub-3s on 3G), and mobile usability. No payment processing, user accounts, or authentication are required. Orders are paid at pickup.

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Menu Page    │  │ Cart Page    │  │ Confirmation │         │
│  │ (customer)   │  │ (customer)   │  │ (customer)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                      │
│         ┌──────────────────┴──────────────────┐                 │
│         │                                      │                 │
│  ┌──────▼──────┐                    ┌─────────▼────────┐        │
│  │ Admin Page  │                    │  localStorage    │        │
│  │ (owner)     │                    │  (cart state)    │        │
│  └─────────────┘                    └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
         │                                      │
         │ HTTP (GET/POST)                      │ (client-side)
         │                                      │
┌────────▼──────────────────────────────────────▼─────────────────┐
│                    Express.js Web Server                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Route Handlers                       │   │
│  │  • GET  /          → Render menu page                    │   │
│  │  • GET  /cart      → Render cart page                    │   │
│  │  • POST /order     → Create order, return confirmation   │   │
│  │  • GET  /admin     → Render admin order list             │   │
│  │  • POST /admin/complete → Mark order complete            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────┐         │
│  │              Business Logic Layer                  │         │
│  │  ┌──────────────┐        ┌──────────────┐         │         │
│  │  │ MenuService  │        │ OrderService │         │         │
│  │  └──────────────┘        └──────────────┘         │         │
│  └─────────────────────────┬─────────────────────────┘         │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────┐         │
│  │              Data Access Layer                     │         │
│  │  ┌──────────────┐        ┌──────────────┐         │         │
│  │  │ MenuStore    │        │ OrderStore   │         │         │
│  │  │ (menu.json)  │        │ (SQLite)     │         │         │
│  │  └──────────────┘        └──────────────┘         │         │
│  └────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

## 3. Module Breakdown

### Express.js Web Server
- **Responsibility:** HTTP request handling, routing, and serving HTML pages via EJS templating.
- **Inputs:** HTTP requests (GET/POST) from browsers.
- **Outputs:** Rendered HTML pages, HTTP redirects, JSON error responses.
- **Key logic:** Parses form data, delegates to services, renders responses using EJS templates.

### Route Handlers
- **Responsibility:** Map URL paths to controller logic and handle HTTP verb-specific actions.
- **Inputs:** HTTP request objects with params, query strings, and bodies.
- **Outputs:** Calls to service layer functions; responses to client.
- **Key logic:** 
  - `GET /` loads menu items and renders menu page.
  - `POST /order` validates order payload, calls OrderService.createOrder, renders confirmation.
  - `GET /admin` loads all pending orders sorted by pickup time, renders admin view.
  - `POST /admin/complete` marks an order complete by ID.

### MenuService
- **Responsibility:** Provide access to the coffee menu items.
- **Inputs:** None (loads on startup).
- **Outputs:** Array of menu items with id, name, description, price.
- **Key logic:** Reads menu.json on initialization; caches in memory. No write operations.

### OrderService
- **Responsibility:** Create and manage customer orders.
- **Inputs:** Customer name, pickup time, array of cart items (id, quantity).
- **Outputs:** Newly created order object with unique ID and timestamp.
- **Key logic:** Validates that all item IDs exist in menu; calculates total price; assigns order ID; persists to OrderStore; returns order summary.

### MenuStore
- **Responsibility:** Load menu data from disk.
- **Inputs:** File path to `menu.json`.
- **Outputs:** Parsed JSON array of menu items.
- **Key logic:** Synchronous file read on app startup; fails fast if file missing or malformed.

### OrderStore
- **Responsibility:** Persist and retrieve orders using SQLite.
- **Inputs:** Order objects (create), order IDs (update, retrieve).
- **Outputs:** Saved orders, list of orders, update confirmations.
- **Key logic:** 
  - Orders table schema includes: id (primary key), customer_name, pickup_time, items (JSON blob), total_price, status (pending/completed), created_at.
  - `createOrder()` inserts a new row.
  - `getOrders(status)` retrieves orders filtered by status, sorted by pickup_time ASC.
  - `markComplete(orderId)` updates status to 'completed'.

### Client-Side Cart (localStorage)
- **Responsibility:** Maintain cart state across page navigation without requiring sessions.
- **Inputs:** User interactions (add to cart, change quantity, remove item).
- **Outputs:** Updated cart array stored in browser's localStorage.
- **Key logic:** 
  - Cart structure: `[{id, name, price, quantity}, ...]`.
  - Plain JavaScript functions: `addToCart(item)`, `updateQuantity(itemId, newQty)`, `removeFromCart(itemId)`, `getCart()`, `clearCart()`.
  - On cart page load, read from localStorage and render.
  - On order submission success, clear cart.

## 4. Data Models

### MenuItem (menu.json)
```json
{
  "id": "string (UUID or slug, e.g., 'espresso')",
  "name": "string (e.g., 'Espresso')",
  "description": "string (e.g., 'Rich, bold shot of coffee')",
  "price": "number (e.g., 3.50)"
}
```

**Example:**
```json
[
  {
    "id": "espresso",
    "name": "Espresso",
    "description": "Rich, bold shot of coffee",
    "price": 3.50
  },
  {
    "id": "latte",
    "name": "Latte",
    "description": "Smooth espresso with steamed milk",
    "price": 4.50
  }
]
```

### CartItem (localStorage, client-side)
```json
{
  "id": "string (matches MenuItem.id)",
  "name": "string",
  "price": "number",
  "quantity": "integer (>= 1)"
}
```

### Order (SQLite table: orders)
```sql
CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_name TEXT NOT NULL,
  pickup_time TEXT NOT NULL,  -- ISO 8601 datetime string
  items TEXT NOT NULL,         -- JSON array of CartItem objects
  total_price REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' or 'completed'
  created_at TEXT NOT NULL     -- ISO 8601 datetime string
);
```

**Order object (application layer):**
```typescript
{
  id: number,
  customerName: string,
  pickupTime: string,  // ISO 8601
  items: CartItem[],
  totalPrice: number,
  status: 'pending' | 'completed',
  createdAt: string    // ISO 8601
}
```

### Order Submission Payload (POST /order)
```json
{
  "customerName": "string (required, 1-100 chars)",
  "pickupTime": "string (required, ISO 8601 or HTML datetime-local format)",
  "items": [
    {
      "id": "string",
      "quantity": "integer (>= 1)"
    }
  ]
}
```

## 5. API Contracts

### GET /
**Description:** Render the menu page.
**Request:** None.
**Response:** HTML page with menu items, each showing name, description, price, and "Add to Cart" button.
**Template data:**
```javascript
{
  menuItems: MenuItem[]
}
```

### GET /cart
**Description:** Render the cart page.
**Request:** None (cart data comes from client-side localStorage).
**Response:** HTML page with:
- Cart items rendered from localStorage.
- Quantity controls (increment/decrement/remove).
- Total price calculation.
- Order form (customer name, pickup time inputs).
- Submit button.

**Template data:**
```javascript
{
  // Empty or minimal server data; cart is client-rendered
}
```

### POST /order
**Description:** Submit a new order.
**Request headers:** `Content-Type: application/x-www-form-urlencoded` (from HTML form).
**Request body:**
```
customerName=John+Doe&pickupTime=2026-06-18T10:30&items=[{"id":"espresso","quantity":2}]
```
(Note: `items` will be JSON string from hidden input populated by JavaScript)

**Success response (HTTP 200):**
Render confirmation page with:
```javascript
{
  order: {
    id: number,
    customerName: string,
    pickupTime: string,
    items: CartItem[],
    totalPrice: number
  }
}
```

**Error response (HTTP 400):**
Render error page or redirect to cart with error message:
- Missing required fields (customerName, pickupTime, items).
- Invalid item IDs in cart.
- Pickup time in the past.
- Invalid quantity (<= 0).

### GET /admin
**Description:** Render admin order management page.
**Request:** None.
**Response:** HTML page listing all orders.
**Template data:**
```javascript
{
  pendingOrders: Order[],   // sorted by pickupTime ASC
  completedOrders: Order[]  // sorted by pickupTime DESC
}
```

### POST /admin/complete
**Description:** Mark an order as completed.
**Request headers:** `Content-Type: application/x-www-form-urlencoded`.
**Request body:**
```
orderId=123
```

**Success response (HTTP 302):**
Redirect to `/admin`.

**Error response (HTTP 400):**
Render error page:
- Order ID not found.
- Order already completed.

## 6. Technology Choices

### Node.js + Express.js
**Why:** Ubiquitous, single-language stack (JavaScript server + client), excellent hosting support, minimal boilerplate. Express is lightweight and has a mature ecosystem.

### EJS (Embedded JavaScript templating)
**Why:** Server-side rendering ensures fast initial page load (<3s on 3G). EJS is simple, has no build step, and allows progressive enhancement with minimal client-side JS.

### SQLite
**Why:** Zero-configuration embedded database; no separate DB server required. Perfect for low-traffic, single-location use case (<100 orders/day). File-based persistence survives restarts.

### JSON file for menu (menu.json)
**Why:** Spec requires configurability without hardcoding. JSON is human-editable and requires no CMS. Shop owner can edit with any text editor.

### Vanilla JavaScript (no framework) for client-side cart
**Why:** Minimal bundle size to meet 3G load constraint. Cart logic is simple (add/remove/update quantity) and doesn't justify React/Vue overhead.

### CSS: Custom minimal stylesheet (no framework)
**Why:** Frameworks like Bootstrap add 50-150KB. Custom CSS targeting only required components keeps bundle tiny. Flexbox and CSS Grid provide responsive layout without extra dependencies.

## 7. Implementation Order

1. **Project scaffolding and data layer**
   - Initialize Node.js project with Express, EJS, sqlite3.
   - Define SQLite schema and create OrderStore module with CRUD operations.
   - Create menu.json with sample coffee items.
   - Create MenuStore module to load menu.json.
   - Write unit tests for OrderStore and MenuStore.
   - **Why first:** Foundation for all features; can be tested in isolation.

2. **Menu page (customer view)**
   - Create MenuService.
   - Implement `GET /` route handler.
   - Create EJS template for menu page (responsive grid layout).
   - Add "Add to Cart" buttons (client-side JS to write to localStorage).
   - Test menu rendering and cart addition.
   - **Why second:** Simplest customer-facing feature; establishes templating patterns.

3. **Cart page and order submission**
   - Implement client-side cart.js (localStorage CRUD, quantity controls).
   - Create `GET /cart` route and EJS template.
   - Implement order form (customer name, pickup time datetime-local input).
   - Create OrderService with validation logic.
   - Implement `POST /order` route handler.
   - Create confirmation page template.
   - Test full order flow end-to-end.
   - **Why third:** Core customer journey; depends on menu and data layer.

4. **Admin order management**
   - Implement `GET /admin` route handler.
   - Create admin.ejs template listing pending and completed orders.
   - Implement `POST /admin/complete` route handler.
   - Style admin page for usability (tables, buttons).
   - Test order lifecycle (submit → view in admin → mark complete).
   - **Why fourth:** Depends on orders existing; separate workflow from customer.

5. **Responsive design and performance optimization**
   - Refine CSS for mobile (375px) and desktop viewports.
   - Optimize images (if any logos/icons added).
   - Minify CSS/JS.
   - Test with Lighthouse on simulated 3G.
   - **Why last:** All features must exist before tuning performance.

6. **Deployment preparation**
   - Document environment variables (if any).
   - Create start script (`npm start`).
   - Write README with setup and deployment instructions.
   - Verify app runs with single command.
   - **Why last:** Deploy-ready application requires all features complete.

## 8. Error Handling Strategy

### Expected Errors (User Input)
- **Invalid order submission** (missing fields, invalid item IDs, past pickup time): Return HTTP 400 with user-friendly error message rendered in the cart page or a dedicated error page. Do not crash the server.
- **Empty cart submission**: Detect on client-side and show alert; block form submission.
- **Non-existent order ID in admin complete action**: Return HTTP 400 or redirect to admin with error message.

**Logging:** Log validation failures at INFO level with sanitized input (no PII in logs).

### Unexpected Errors (System Failures)
- **Database connection failure**: Log at ERROR level; return HTTP 500 with generic message ("Service temporarily unavailable"). Do not expose stack traces to users.
- **menu.json read failure on startup**: Fail fast with clear error message; exit process. Menu is required for app to function.
- **SQLite write failure** (disk full, permissions): Log at ERROR level; return HTTP 500 to user; alert operator.

**Logging:** Use a structured logger (e.g., `pino` or `winston`) with log levels (DEBUG, INFO, WARN, ERROR). Log all errors with stack traces.

**No Retry Logic:** Given low traffic and simplicity constraint, no automatic retries. Operator can manually retry failed operations via admin UI or restart if needed.

### Client-Side Errors
- **localStorage quota exceeded** (unlikely with cart data): Show alert to user; fallback to session-only cart (lost on page close).
- **JavaScript disabled**: Cart will not function; show message: "JavaScript is required for ordering."

**Validation:** All user input validated server-side even if client-side validation present. Never trust client data.