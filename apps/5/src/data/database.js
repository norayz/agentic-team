const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
  constructor(dbPath = './barista.db') {
    this.dbPath = dbPath;
    this.db = new sqlite3.Database(dbPath);
    this.initialize();
  }

  initialize() {
    // Create menu_items table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
      )
    `);

    // Create orders table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        pickup_time TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Seed menu items if table is empty
    this.db.get('SELECT COUNT(*) as count FROM menu_items', (err, row) => {
      if (!err && row.count === 0) {
        this.seedMenuItems();
      }
    });
  }

  seedMenuItems() {
    const menuItems = [
      { name: 'Espresso', description: 'Rich and bold single shot', price: 2.50 },
      { name: 'Latte', description: 'Smooth espresso with steamed milk', price: 4.50 },
      { name: 'Cappuccino', description: 'Espresso with foamed milk', price: 4.00 },
      { name: 'Cold Brew', description: 'Smooth cold-steeped coffee', price: 4.00 },
      { name: 'Drip Coffee', description: 'Classic house blend', price: 2.00 },
      { name: 'Americano', description: 'Espresso with hot water', price: 3.00 },
      { name: 'Mocha', description: 'Espresso with chocolate and steamed milk', price: 5.00 },
      { name: 'Macchiato', description: 'Espresso with a dollop of foam', price: 3.50 }
    ];

    const stmt = this.db.prepare('INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)');
    menuItems.forEach(item => {
      stmt.run(item.name, item.description, item.price);
    });
    stmt.finalize();
  }

  close() {
    this.db.close();
  }
}

module.exports = Database;
