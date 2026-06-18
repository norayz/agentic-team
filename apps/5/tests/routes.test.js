const request = require('supertest');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

// Use a test database
const testDbPath = path.join(__dirname, '../data/test-routes.db');

describe('HTTP Routes', () => {
  let app;
  let db;

  beforeEach(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    // Create fresh test database
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

    // Seed menu items
    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold', 3.50);
    insert.run('Latte', 'Smooth', 4.50);

    db.close();

    // Require app after database is set up
    app = require('../src/server');
  });

  afterEach(() => {
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  test('GET / returns menu page', async () => {
    const response = await request(app).get('/');
    expect(response.status).toBe(200);
    expect(response.text).toContain('Menu');
    expect(response.text).toContain('Espresso');
  });

  test('GET /cart returns cart page', async () => {
    const response = await request(app).get('/cart');
    expect(response.status).toBe(200);
    expect(response.text).toContain('Cart');
  });

  test('POST /order with valid data creates order', async () => {
    const orderData = {
      customer_name: 'John Doe',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 2 }]
    };

    const response = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(302); // Redirect to confirmation
    expect(response.headers.location).toMatch(/\/confirmation\/\d+/);
  });

  test('POST /order with missing customer_name returns 400', async () => {
    const orderData = {
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 1 }]
    };

    const response = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('Customer name is required');
  });

  test('POST /order with empty items returns 400', async () => {
    const orderData = {
      customer_name: 'John',
      pickup_time: '2024-01-15T10:00:00',
      items: []
    };

    const response = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('at least one item');
  });

  test('POST /order with invalid item ID returns 400', async () => {
    const orderData = {
      customer_name: 'John',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 999, quantity: 1 }]
    };

    const response = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    expect(response.status).toBe(400);
    expect(response.body.error).toContain('Invalid item ID');
  });

  test('GET /confirmation/:orderId returns confirmation page', async () => {
    // Create an order first
    const orderData = {
      customer_name: 'John Doe',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 2 }]
    };

    const orderResponse = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    const orderId = orderResponse.headers.location.split('/').pop();

    const response = await request(app).get(`/confirmation/${orderId}`);
    expect(response.status).toBe(200);
    expect(response.text).toContain('Order Confirmed');
    expect(response.text).toContain('John Doe');
  });

  test('GET /confirmation/:orderId with invalid ID returns 404', async () => {
    const response = await request(app).get('/confirmation/999');
    expect(response.status).toBe(404);
    expect(response.text).toContain('Order not found');
  });

  test('GET /admin returns admin page', async () => {
    const response = await request(app).get('/admin');
    expect(response.status).toBe(200);
    expect(response.text).toContain('Admin');
    expect(response.text).toContain('Pending Orders');
  });

  test('POST /admin/complete/:orderId marks order complete', async () => {
    // Create an order first
    const orderData = {
      customer_name: 'John',
      pickup_time: '2024-01-15T10:00:00',
      items: [{ id: 1, quantity: 1 }]
    };

    const orderResponse = await request(app)
      .post('/order')
      .send(orderData)
      .set('Content-Type', 'application/json');

    const orderId = orderResponse.headers.location.split('/').pop();

    const response = await request(app).post(`/admin/complete/${orderId}`);
    expect(response.status).toBe(302); // Redirect back to admin
    expect(response.headers.location).toBe('/admin');
  });

  test('POST /admin/complete/:orderId with invalid ID returns 404', async () => {
    const response = await request(app).post('/admin/complete/999');
    expect(response.status).toBe(404);
    expect(response.text).toContain('Order not found');
  });

  test('GET /nonexistent returns 404', async () => {
    const response = await request(app).get('/nonexistent');
    expect(response.status).toBe(404);
    expect(response.text).toContain('Page not found');
  });
});
