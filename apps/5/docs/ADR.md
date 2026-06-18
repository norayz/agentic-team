# Architecture Decision Record

**Issue:** #5  
**Author:** Architect Agent  

---

## Decision 1: Use Server-Side Rendering (SSR) with EJS Over Single-Page Application (SPA)

**Status:** Accepted  

**Context:** The spec requires sub-3-second page load on slow 3G connections. We need to choose between:
- Server-side rendering (SSR) where HTML is generated on the server and sent to the browser ready-to-display.
- Single-page application (SPA) where the client downloads a JavaScript framework bundle, then fetches and renders data.

The target users are coffee shop customers on mobile devices, potentially with poor connectivity. The application has minimal interactivity requirements (no real-time updates, no complex client state beyond a shopping cart).

**Options Considered:**

- **Option A: Server-Side Rendering with EJS**  
  - **Pros:** 
    - First Contentful Paint (FCP) is fast — browser receives ready-to-render HTML immediately.
    - Minimal JavaScript bundle (only cart logic, <5KB).
    - Progressive enhancement: site works with JavaScript disabled for menu browsing.
    - Simple deployment: one server process.
  - **Cons:** 
    - Full page reloads on navigation (though acceptable for this use case).
    - Less "app-like" feel compared to SPA.

- **Option B: React or Vue SPA with API Backend**  
  - **Pros:** 
    - Rich client-side interactions.
    - No page reloads; smoother UX for cart updates.
    - Modern developer experience.
  - **Cons:** 
    - Large initial bundle (React + ReactDOM ≈ 40KB gzipped minimum; Vue ≈ 25KB).
    - Blank screen until JavaScript loads and executes.
    - Additional round-trips for API data after JS loads.
    - Fails 3G load time requirement without aggressive optimization.

**Decision:** Use Server-Side Rendering with EJS.

**Rationale:** The spec's most critical non-functional requirement is <3s load on 3G. SSR guarantees fast Time-to-Interactive because the browser receives complete HTML. The application has low interactivity: customers view a menu (static read), add to cart (simple state), and submit a form. These do not require a framework. A React SPA would add 30-50KB of JavaScript before the user sees any content, making the 3G constraint nearly impossible without heroic optimization.

**Consequences:**  
- **Easier:** Fast initial page loads. Simple testing (render HTML, inspect output). Low hosting resource usage.
- **Harder:** No instant client-side transitions between pages. Cart state must be managed in localStorage (acceptable trade-off).
- **Future constraint:** If the shop owner later wants real-time order status updates, we'd need to add WebSocket or polling, but SSR doesn't prevent that.

---

## Decision 2: Use SQLite Over PostgreSQL or MongoDB

**Status:** Accepted  

**Context:** Orders must be persisted across server restarts. The spec states low traffic (<100 orders/day), single location, and requires "easy to deploy." We need to choose a data persistence layer.

**Options Considered:**

- **Option A: SQLite (embedded file-based database)**  
  - **Pros:** 
    - Zero configuration: no separate database server to install or manage.
    - Single file storage; trivial to back up (copy one file).
    - More than sufficient for <100 orders/day (SQLite handles thousands of writes/sec).
    - ACID compliance for order integrity.
  - **Cons:** 
    - No concurrent write scaling (not a problem at this traffic level).
    - Not ideal for multi-server deployments (but spec is single location).

- **Option B: PostgreSQL**  
  - **Pros:** 
    - Industry-standard relational database.
    - Better for high concurrency and large datasets.
  - **Cons:** 
    - Requires separate database server process (added operational complexity).
    - Deployment becomes two-service problem (app + DB).
    - Overkill for stated traffic volume.

- **Option C: JSON file**  
  - **Pros:** 
    - Simplest possible: read/write JSON with fs module.
  - **Cons:** 
    - No transactional safety (file corruption risk on crash during write).
    - Poor query performance (full file read for every lookup).
    - No built-in indexing or sorting.

**Decision:** Use SQLite.

**Rationale:** SQLite hits the sweet spot for this use case. It provides real database features (transactions, indexes, SQL queries) without operational overhead. The spec emphasizes simplicity and easy deployment; a separate database server violates that. JSON files are too brittle for order data that the business depends on. SQLite is battle-tested (used by browsers, mobile apps, and embedded systems) and has excellent Node.js bindings.

**Consequences:**  
- **Easier:** Single-command deployment (`npm start`). No database server to configure, secure, or monitor. Backups are file copies. Local development identical to production.
- **Harder:** If traffic grows beyond single-server capacity, migrating to a client-server database requires code changes (though the ORM abstraction in OrderStore minimizes this).
- **Future constraint:** If the coffee house expands to multiple locations with centralized order management, we'd need to migrate to PostgreSQL or similar. However, the spec explicitly excludes multi-location support as a non-goal.

---

## Decision 3: Store Cart State in localStorage Instead of Server-Side Sessions

**Status:** Accepted  

**Context:** Customers need to add items to a cart, navigate between menu and cart pages, and not lose their cart contents. We need to decide where cart state lives.

**Options Considered:**

- **Option A: Browser localStorage (client-side)**  
  - **Pros:** 
    - No server-side session management (no session store, no cookies, no session ID tracking).
    - Cart persists even if the user closes the tab and returns later (good UX).
    - Stateless server: easier to scale horizontally if needed.
    - Works offline (user can build cart without connectivity, submit when online).
  - **Cons:** 
    - Cart data is client-side, so can be manipulated (mitigated by server-side validation on order submit).
    - Doesn't sync across devices (acceptable for stated use case).

- **Option B: Server-side sessions (cookies + session store)**  
  - **Pros:** 
    - Cart data is authoritative on server.
    - Cart sync across tabs on same device.
  - **Cons:** 
    - Requires session middleware (express-session).
    - Requires session store (memory, Redis, or DB) for persistence across restarts.
    - Cart lost if user closes browser (worse UX than localStorage).
    - Adds complexity: cookie management, session expiry, CSRF concerns.

- **Option C: No cart persistence (session-only)**  
  - **Pros:** 
    - Simplest implementation.
  - **Cons:** 
    - Poor UX: cart lost on page close.
    - Doesn't meet implicit usability expectations for an ordering site.

**Decision:** Use localStorage for cart state.

**Rationale:** The spec does not require user accounts or login, so there's no user identity to associate a cart with on the server. Server-side sessions add complexity without clear benefit. localStorage provides better UX (cart persists across sessions) and keeps the server stateless. The risk of client-side cart manipulation is mitigated by server-side validation in OrderService: when the order is submitted, we re-validate all item IDs against the menu and recalculate the total price server-side, so a malicious client cannot inject fake items or prices.

**Consequences:**  
- **Easier:** No session middleware. Stateless server (simpler deployment, easier horizontal scaling if needed). Better UX (cart survives browser close).
- **Harder:** Cart doesn't sync across devices (but spec has no multi-device requirement). Must implement client-side cart JavaScript (but this is small and straightforward).
- **Security consideration:** Server MUST re-validate all cart data on order submission. Never trust client-provided prices or item definitions — treat cart items as item ID + quantity only, look up price from server-side menu data.