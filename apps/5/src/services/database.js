const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// Ensure data directory exists
const dataDir = path.join(__dirname, '../../data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const dbPath = path.join(dataDir, 'barista.db');
const db = new Database(dbPath);

// Initialize database schema
function initializeDatabase() {
  // Create menu_items table
  db.exec(`
    CREATE TABLE IF NOT EXISTS menu_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      description TEXT NOT NULL,
      price REAL NOT NULL
    )
  `);

  // Create orders table
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

  // Seed menu items if table is empty
  const count = db.prepare('SELECT COUNT(*) as count FROM menu_items').get();
  if (count.count === 0) {
    seedMenuItems();
  }
}

// Seed sample menu items
function seedMenuItems() {
  const menuItems = [
    {
      name: 'Espresso',
      description: 'Rich and bold Italian-style espresso shot',
      price: 3.50
    },
    {
      name: 'Latte',
      description: 'Smooth espresso with steamed milk and light foam',
      price: 4.50
    },
    {
      name: 'Cappuccino',
      description: 'Espresso with equal parts steamed milk and foam',
      price: 4.75
    },
    {
      name: 'Cold Brew',
      description: 'Smooth, cold-steeped coffee served over ice',
      price: 4.25
    },
    {
      name: 'Drip Coffee',
      description: 'Classic drip coffee, freshly brewed',
      price: 2.75
    }
  ];

  const insert = db.prepare(`
    INSERT INTO menu_items (name, description, price)
    VALUES (@name, @description, @price)
  `);

  const insertMany = db.transaction((items) => {
    for (const item of items) {
      insert.run(item);
    }
  });

  insertMany(menuItems);
}

// Get all menu items
function getAllMenuItems() {
  return db.prepare('SELECT * FROM menu_items ORDER BY price ASC').all();
}

// Get menu item by ID
function getMenuItemById(id) {
  return db.prepare('SELECT * FROM menu_items WHERE id = ?').get(id);
}

// Create a new order
function createOrder(customerName, pickupTime, items, totalPrice) {
  const insert = db.prepare(`
    INSERT INTO orders (customer_name, pickup_time, items, total_price, status)
    VALUES (?, ?, ?, ?, 'pending')
  `);

  const result = insert.run(
    customerName,
    pickupTime,
    JSON.stringify(items),
    totalPrice
  );

  return result.lastInsertRowid;
}

// Get order by ID
function getOrderById(id) {
  const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(id);
  if (order) {
    order.items = JSON.parse(order.items);
  }
  return order;
}

// Get all orders
function getAllOrders() {
  const orders = db.prepare(
    'SELECT * FROM orders ORDER BY pickup_time ASC'
  ).all();

  return orders.map(order => ({
    ...order,
    items: JSON.parse(order.items)
  }));
}

// Get pending orders
function getPendingOrders() {
  const orders = db.prepare(`
    SELECT * FROM orders
    WHERE status = 'pending'
    ORDER BY pickup_time ASC
  `).all();

  return orders.map(order => ({
    ...order,
    items: JSON.parse(order.items)
  }));
}

// Mark order as complete
function markOrderComplete(orderId) {
  const update = db.prepare(`
    UPDATE orders
    SET status = 'completed'
    WHERE id = ?
  `);

  const result = update.run(orderId);
  return result.changes > 0;
}

// Initialize database on module load
initializeDatabase();

module.exports = {
  db,
  getAllMenuItems,
  getMenuItemById,
  createOrder,
  getOrderById,
  getAllOrders,
  getPendingOrders,
  markOrderComplete
};
