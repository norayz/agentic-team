const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
  constructor(dbPath) {
    this.dbPath = dbPath || path.join(__dirname, '../data/barista.db');
    this.db = null;
  }

  async initialize() {
    return new Promise((resolve, reject) => {
      this.db = new sqlite3.Database(this.dbPath, (err) => {
        if (err) {
          return reject(err);
        }
        console.log('Connected to SQLite database');
        this.createTables()
          .then(() => resolve())
          .catch((err) => reject(err));
      });
    });
  }

  async createTables() {
    const menuItemsTable = `
      CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
      )
    `;

    const ordersTable = `
      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        pickup_time TEXT NOT NULL,
        items TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `;

    return new Promise((resolve, reject) => {
      this.db.run(menuItemsTable, (err) => {
        if (err) return reject(err);
        this.db.run(ordersTable, (err) => {
          if (err) return reject(err);
          resolve();
        });
      });
    });
  }

  async seedMenuItems() {
    const menuItems = [
      { name: 'Espresso', description: 'Strong and bold, single shot', price: 3.00 },
      { name: 'Latte', description: 'Espresso with steamed milk', price: 4.50 },
      { name: 'Cappuccino', description: 'Espresso with foam and steamed milk', price: 4.50 },
      { name: 'Cold Brew', description: 'Smooth cold-steeped coffee', price: 4.00 },
      { name: 'Drip Coffee', description: 'Classic brewed coffee', price: 2.50 }
    ];

    const insertPromises = menuItems.map(item => {
      return new Promise((resolve, reject) => {
        const sql = 'INSERT INTO menu_items (name, description, price) VALUES (?, ?, ?)';
        this.db.run(sql, [item.name, item.description, item.price], function(err) {
          if (err) return reject(err);
          resolve();
        });
      });
    });

    return Promise.all(insertPromises);
  }

  async getMenuItems() {
    return new Promise((resolve, reject) => {
      this.db.all('SELECT * FROM menu_items', (err, rows) => {
        if (err) return reject(err);
        resolve(rows);
      });
    });
  }

  async close() {
    return new Promise((resolve, reject) => {
      if (!this.db) return resolve();
      this.db.close((err) => {
        if (err) return reject(err);
        console.log('Database connection closed');
        resolve();
      });
    });
  }
}

module.exports = Database;
