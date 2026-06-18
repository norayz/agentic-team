const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

// Use a temporary database for testing
const testDbPath = path.join(__dirname, '../data/test.db');

// Mock the database path before requiring the modules
process.env.NODE_ENV = 'test';

describe('Database Service', () => {
  let db;
  let dbService;

  beforeEach(() => {
    // Remove test database if it exists
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }

    // Create a fresh database for each test
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

    // Create mock dbService functions
    dbService = {
      getAllMenuItems: () => db.prepare('SELECT * FROM menu_items ORDER BY price ASC').all(),
      getMenuItemById: (id) => db.prepare('SELECT * FROM menu_items WHERE id = ?').get(id),
      createOrder: (customerName, pickupTime, items, totalPrice) => {
        const insert = db.prepare(`
          INSERT INTO orders (customer_name, pickup_time, items, total_price, status)
          VALUES (?, ?, ?, ?, 'pending')
        `);
        const result = insert.run(customerName, pickupTime, JSON.stringify(items), totalPrice);
        return result.lastInsertRowid;
      },
      getOrderById: (id) => {
        const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(id);
        if (order) {
          order.items = JSON.parse(order.items);
        }
        return order;
      },
      getAllOrders: () => {
        const orders = db.prepare('SELECT * FROM orders ORDER BY pickup_time ASC').all();
        return orders.map(order => ({ ...order, items: JSON.parse(order.items) }));
      },
      getPendingOrders: () => {
        const orders = db.prepare(`
          SELECT * FROM orders WHERE status = 'pending' ORDER BY pickup_time ASC
        `).all();
        return orders.map(order => ({ ...order, items: JSON.parse(order.items) }));
      },
      markOrderComplete: (orderId) => {
        const update = db.prepare(`UPDATE orders SET status = 'completed' WHERE id = ?`);
        const result = update.run(orderId);
        return result.changes > 0;
      }
    };
  });

  afterEach(() => {
    db.close();
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  test('database initializes with correct schema', () => {
    const tables = db.prepare(
      "SELECT name FROM sqlite_master WHERE type='table'"
    ).all();

    const tableNames = tables.map(t => t.name);
    expect(tableNames).toContain('menu_items');
    expect(tableNames).toContain('orders');
  });

  test('menu items can be seeded', () => {
    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price)
      VALUES (?, ?, ?)
    `);

    insert.run('Espresso', 'Rich and bold', 3.50);
    insert.run('Latte', 'Smooth espresso with milk', 4.50);

    const items = dbService.getAllMenuItems();
    expect(items).toHaveLength(2);
    expect(items[0].name).toBe('Espresso');
  });

  test('getAllMenuItems returns all menu items', () => {
    // Seed data
    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold', 3.50);
    insert.run('Latte', 'Smooth', 4.50);

    const items = dbService.getAllMenuItems();
    expect(items).toHaveLength(2);
    expect(items[0].price).toBe(3.50);
  });

  test('createOrder inserts order into database', () => {
    const items = [{ id: 1, name: 'Espresso', price: 3.50, quantity: 2 }];
    const orderId = dbService.createOrder('John Doe', '2024-01-15T10:00:00', items, 7.00);

    expect(orderId).toBe(1);

    const order = dbService.getOrderById(orderId);
    expect(order.customer_name).toBe('John Doe');
    expect(order.total_price).toBe(7.00);
    expect(order.status).toBe('pending');
  });

  test('getOrderById returns order with parsed items', () => {
    const items = [{ id: 1, name: 'Espresso', price: 3.50, quantity: 2 }];
    const orderId = dbService.createOrder('John Doe', '2024-01-15T10:00:00', items, 7.00);

    const order = dbService.getOrderById(orderId);
    expect(order.items).toBeInstanceOf(Array);
    expect(order.items[0].name).toBe('Espresso');
  });

  test('getPendingOrders returns only pending orders', () => {
    const items = [{ id: 1, name: 'Espresso', price: 3.50, quantity: 1 }];
    dbService.createOrder('John', '2024-01-15T10:00:00', items, 3.50);
    const orderId2 = dbService.createOrder('Jane', '2024-01-15T11:00:00', items, 3.50);

    dbService.markOrderComplete(orderId2);

    const pendingOrders = dbService.getPendingOrders();
    expect(pendingOrders).toHaveLength(1);
    expect(pendingOrders[0].customer_name).toBe('John');
  });

  test('markOrderComplete updates order status', () => {
    const items = [{ id: 1, name: 'Espresso', price: 3.50, quantity: 1 }];
    const orderId = dbService.createOrder('John', '2024-01-15T10:00:00', items, 3.50);

    const success = dbService.markOrderComplete(orderId);
    expect(success).toBe(true);

    const order = dbService.getOrderById(orderId);
    expect(order.status).toBe('completed');
  });
});

describe('Order Validation Service', () => {
  let db;
  let validateAndCreateOrder;

  beforeEach(() => {
    // Remove test database if it exists
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

    // Seed menu items
    const insert = db.prepare(`
      INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)
    `);
    insert.run('Espresso', 'Rich and bold', 3.50);
    insert.run('Latte', 'Smooth', 4.50);

    // Mock the services
    const getAllMenuItems = () => db.prepare('SELECT * FROM menu_items ORDER BY price ASC').all();
    const createOrderInDb = (customerName, pickupTime, items, totalPrice) => {
      const insert = db.prepare(`
        INSERT INTO orders (customer_name, pickup_time, items, total_price, status)
        VALUES (?, ?, ?, ?, 'pending')
      `);
      const result = insert.run(customerName, pickupTime, JSON.stringify(items), totalPrice);
      return result.lastInsertRowid;
    };

    validateAndCreateOrder = (customerName, pickupTime, items) => {
      if (!customerName || !customerName.trim()) {
        throw new Error('Customer name is required');
      }
      if (!pickupTime) {
        throw new Error('Pickup time is required');
      }
      if (!Array.isArray(items) || items.length === 0) {
        throw new Error('Order must contain at least one item');
      }

      const menuItems = getAllMenuItems();
      const menuMap = new Map(menuItems.map(item => [item.id, item]));

      for (const item of items) {
        if (!menuMap.has(item.id)) {
          throw new Error(`Invalid item ID: ${item.id}`);
        }
      }

      let totalPrice = 0;
      const validatedItems = [];

      for (const item of items) {
        const menuItem = menuMap.get(item.id);
        const quantity = parseInt(item.quantity) || 1;

        if (quantity < 1) {
          throw new Error('Item quantity must be at least 1');
        }

        validatedItems.push({
          id: menuItem.id,
          name: menuItem.name,
          price: menuItem.price,
          quantity: quantity
        });

        totalPrice += menuItem.price * quantity;
      }

      totalPrice = Math.round(totalPrice * 100) / 100;

      const orderId = createOrderInDb(
        customerName.trim(),
        pickupTime,
        validatedItems,
        totalPrice
      );

      return orderId;
    };
  });

  afterEach(() => {
    db.close();
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  test('validates required customer name', () => {
    expect(() => {
      validateAndCreateOrder('', '2024-01-15T10:00:00', [{ id: 1, quantity: 1 }]);
    }).toThrow('Customer name is required');
  });

  test('validates required pickup time', () => {
    expect(() => {
      validateAndCreateOrder('John', '', [{ id: 1, quantity: 1 }]);
    }).toThrow('Pickup time is required');
  });

  test('validates empty cart', () => {
    expect(() => {
      validateAndCreateOrder('John', '2024-01-15T10:00:00', []);
    }).toThrow('Order must contain at least one item');
  });

  test('validates item existence in menu', () => {
    expect(() => {
      validateAndCreateOrder('John', '2024-01-15T10:00:00', [{ id: 999, quantity: 1 }]);
    }).toThrow('Invalid item ID: 999');
  });

  test('recalculates price from database (never trust client)', () => {
    const orderId = validateAndCreateOrder(
      'John',
      '2024-01-15T10:00:00',
      [{ id: 1, quantity: 2, price: 999.99 }] // Client sends wrong price
    );

    const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
    expect(order.total_price).toBe(7.00); // 3.50 * 2 = 7.00 (from database)
  });

  test('creates order with valid data', () => {
    const orderId = validateAndCreateOrder(
      'John Doe',
      '2024-01-15T10:00:00',
      [{ id: 1, quantity: 2 }]
    );

    expect(orderId).toBe(1);

    const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
    expect(order.customer_name).toBe('John Doe');
    expect(order.total_price).toBe(7.00);
  });
});
