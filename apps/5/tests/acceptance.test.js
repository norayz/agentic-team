const request = require('supertest');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

/**
 * Acceptance Tests for Barista Site (Issue #5)
 * 
 * These tests map directly to acceptance criteria from the spec.
 * Each test verifies that the implementation meets a specific requirement.
 */

const testDbPath = path.join(__dirname, '../data/test-acceptance.db');

describe('Barista Site - Acceptance Criteria', () => {
  let app;
  let db;

  beforeEach(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    // Create fresh test database
    db = new Database(testDbPath);

    // Initialize schema
    db.exec(`
      CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
      )
    `);

    db.exec(`
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        pickup_time TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `);

    // Seed menu items to match what the spec describes
    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold Italian-style espresso shot', 3.50);
    insert.run('Latte', 'Smooth espresso with steamed milk and light foam', 4.50);
    insert.run('Cappuccino', 'Espresso with equal parts steamed milk and foam', 4.75);
    insert.run('Cold Brew', 'Smooth, cold-steeped coffee served over ice', 4.25);
    insert.run('Drip Coffee', 'Classic drip coffee, freshly brewed', 2.75);

    db.close();

    // Require app after database is set up
    app = require('../src/server');
  });

  afterEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  /**
   * Acceptance Criterion:
   * A menu page displays all available items with name, description, and price.
   */
  test('[AC1] Menu page displays all items with name, description, and price', async () => {
    const response = await request(app).get('/');
    
    expect(response.status).toBe(200);
    expect(response.text).toContain('Espresso');
    expect(response.text).toContain('Rich and bold');
    expect(response.text).toContain('3.50');
    expect(response.text).toContain('Latte');
    expect(response.text).toContain('4.50');
  });

  /**
   * Acceptance Criterion:
   * Each menu item has an "Add to Cart" button that adds it to a cart.
   */
  test('[AC2] Each menu item has an Add to Cart button', async () => {
    const response = await request(app).get('/');
    
    expect(response.status).toBe(200);
    // Check for Add to Cart button with data attributes
    expect(response.text).toContain('Add to Cart');
    expect(response.text).toContain('data-id');
    expect(response.text).toContain('data-name');
    expect(response.text).toContain('data-price');
  });

  /**
   * Acceptance Criterion:
   * A cart view shows selected items, quantities, and total price.
   */
  test('[AC3] Cart view exists and can display items', async () => {
    const response = await request(app).get('/cart');
    
    expect(response.status).toBe(200);
    expect(response.text).toContain('Cart');
    expect(response.text).toContain('cart-items');
    expect(response.text).toContain('cart-total');
  });

  /**
   * Acceptance Criterion:
   * Customer can increase/decrease quantity or remove items from the cart.
   */
  test('[AC4] Cart has quantity controls and remove functionality', async () => {
    const response = await request(app).get('/cart');
    
    expect(response.status).toBe(200);
    // Check for quantity control functions
    expect(response.text).toContain('increaseQuantity');
    expect(response.text).toContain('decreaseQuantity');
    expect(response.text).toContain('removeFromCart');
  });

  /**
   * Acceptance Criterion:
   * An order submission form collects customer name and desired pickup time.
   */
  test('[AC5] Order form collects customer name and pickup time', async () => {
    const response = await request(app).get('/cart');
    
    expect(response.status).toBe(200);
    expect(response.text).toContain('customer_name');
    expect(response.text).toContain('pickup_time');
    expect(response.text).toContain('order-form');
  });

  /**
   * Acceptance Criterion:
   * Submitting an order stores it persistently (survives server restart).
   */
  test('[AC6] Order is stored persistently in database', async () => {
    // Submit an order
    const orderData = {
      customer_name: 'Test Customer',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 2 }]
    };

    const response = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302);

    // Verify order exists in database
    const testDb = new Database(testDbPath);
    const orders = testDb.prepare('SELECT * FROM orders').all();
    testDb.close();

    expect(orders).toHaveLength(1);
    expect(orders[0].customer_name).toBe('Test Customer');
  });

  /**
   * Acceptance Criterion:
   * After submission, the customer sees an order confirmation with a summary of their order.
   */
  test('[AC7] Confirmation page shows order summary after submission', async () => {
    // Create an order
    const orderData = {
      customer_name: 'Jane Doe',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 2 }]
    };

    const orderResponse = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    const orderId = orderResponse.headers.location.split('/').pop();

    // Check confirmation page
    const response = await request(app).get(`/confirmation/${orderId}`);
    
    expect(response.status).toBe(200);
    expect(response.text).toContain('Confirmed');
    expect(response.text).toContain('Jane Doe');
    expect(response.text).toContain('Espresso');
    expect(response.text).toContain('Total');
  });

  /**
   * Acceptance Criterion:
   * An admin page (at `/admin`) lists all orders sorted by pickup time,
   * showing customer name, items, and pickup time.
   */
  test('[AC8] Admin page lists orders with customer name, items, and pickup time', async () => {
    // Create multiple orders
    await request(app)
      .post('/order')
      .send({
        customer_name: 'Customer A',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    await request(app)
      .post('/order')
      .send({
        customer_name: 'Customer B',
        pickup_time: '2024-01-15T09:00:00',
        items: [{ id: 2, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    // Check admin page
    const response = await request(app).get('/admin');
    
    expect(response.status).toBe(200);
    expect(response.text).toContain('Admin');
    expect(response.text).toContain('Customer A');
    expect(response.text).toContain('Customer B');
    expect(response.text).toContain('Pickup');
  });

  /**
   * Acceptance Criterion:
   * Each order on the admin page has a "Mark Complete" button
   * that moves it to a completed state.
   */
  test('[AC9] Admin page has Mark Complete button that updates order status', async () => {
    // Create an order
    const orderResponse = await request(app)
      .post('/order')
      .send({
        customer_name: 'Test',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    const orderId = orderResponse.headers.location.split('/').pop();

    // Check admin page has the button
    let adminResponse = await request(app).get('/admin');
    expect(adminResponse.text).toContain('Mark Complete');

    // Mark order complete
    const completeResponse = await request(app).post(`/admin/complete/${orderId}`);
    expect(completeResponse.status).toBe(302);

    // Verify order status changed in database
    const testDb = new Database(testDbPath);
    const order = testDb.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
    testDb.close();

    expect(order.status).toBe('completed');
  });

  /**
   * Acceptance Criterion:
   * The menu items are configurable via a data file or database (not hardcoded in HTML).
   */
  test('[AC10] Menu items are stored in database, not hardcoded in HTML', async () => {
    // Verify menu items come from database by checking database structure
    const testDb = new Database(testDbPath);
    const menuItems = testDb.prepare('SELECT * FROM menu_items').all();
    testDb.close();

    expect(menuItems.length).toBeGreaterThan(0);
    
    // Verify menu page renders database items
    const response = await request(app).get('/');
    menuItems.forEach(item => {
      expect(response.text).toContain(item.name);
    });
  });

  /**
   * Acceptance Criterion (Mobile Responsiveness):
   * The site is responsive and usable on viewports as small as 375px wide (mobile).
   */
  test('[AC11] Site has mobile-responsive CSS for 375px viewport', async () => {
    // Check that CSS file exists and contains mobile media queries
    const cssPath = path.join(__dirname, '../public/css/style.css');
    expect(fs.existsSync(cssPath)).toBe(true);

    const cssContent = fs.readFileSync(cssPath, 'utf8');
    // Check for mobile-first responsive design patterns
    expect(cssContent).toContain('max-width');
    expect(cssContent).toContain('@media');
    expect(cssContent).toContain('375px');
  });
});

/**
 * Edge Case Tests
 * These test boundary conditions and error scenarios
 */
describe('Barista Site - Edge Cases', () => {
  let app;
  let db;

  beforeEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    db = new Database(testDbPath);

    db.exec(`
      CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
      )
    `);

    db.exec(`
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        pickup_time TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `);

    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold', 3.50);
    insert.run('Latte', 'Smooth', 4.50);

    db.close();
    app = require('../src/server');
  });

  afterEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  test('[EDGE] Empty customer name returns error', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: '',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('Customer name');
  });

  test('[EDGE] Missing pickup time returns error', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: 'John',
        pickup_time: '',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('Pickup time');
  });

  test('[EDGE] Empty cart returns error', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: 'John',
        pickup_time: '2024-01-15T10:00:00',
        items: []
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('at least one item');
  });

  test('[EDGE] Invalid item ID returns error', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: 'John',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 999, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('Invalid item ID');
  });

  test('[EDGE] Non-existent order ID returns 404', async () => {
    const response = await request(app).get('/confirmation/999');
    expect(response.status).toBe(404);
    expect(response.text).toContain('Order not found');
  });

  test('[EDGE] Marking non-existent order complete returns 404', async () => {
    const response = await request(app).post('/admin/complete/999');
    expect(response.status).toBe(404);
    expect(response.text).toContain('Order not found');
  });

  test('[EDGE] Customer name with whitespace is trimmed', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: '  John Doe  ',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302);

    const testDb = new Database(testDbPath);
    const order = testDb.prepare('SELECT * FROM orders').get();
    testDb.close();

    expect(order.customer_name).toBe('John Doe');
  });

  test('[EDGE] Large order quantity is handled correctly', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: 'Bulk Order',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 100 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302);

    const testDb = new Database(testDbPath);
    const order = testDb.prepare('SELECT * FROM orders').get();
    testDb.close();

    // 100 * 3.50 = 350.00
    expect(order.total_price).toBe(350.00);
  });
});

/**
 * Security Tests
 * These verify that server-side validation works correctly
 */
describe('Barista Site - Security', () => {
  let app;
  let db;

  beforeEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    db = new Database(testDbPath);

    db.exec(`
      CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
      )
    `);

    db.exec(`
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        pickup_time TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `);

    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold', 3.50);

    db.close();
    app = require('../src/server');
  });

  afterEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  test('[SECURITY] Server recalculates price from database (never trusts client)', async () => {
    // Client tries to send incorrect price
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: 'Hacker',
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 2, price: 0.01 }] // Client sends wrong price
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302);

    const testDb = new Database(testDbPath);
    const order = testDb.prepare('SELECT * FROM orders').get();
    testDb.close();

    // Server should use database price (3.50 * 2 = 7.00)
    expect(order.total_price).toBe(7.00);
  });

  test('[SECURITY] SQL injection in customer name is prevented', async () => {
    const response = await request(app)
      .post('/order')
      .send({
        customer_name: "'; DROP TABLE orders; --",
        pickup_time: '2024-01-15T10:00:00',
        items: [{ id: 1, quantity: 1 }]
      })
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302);

    // Verify table still exists and contains order
    const testDb = new Database(testDbPath);
    const orders = testDb.prepare('SELECT * FROM orders').all();
    testDb.close();

    expect(orders).toHaveLength(1);
  });
});
