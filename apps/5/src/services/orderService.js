class OrderService {
  constructor(db) {
    this.db = db;
  }

  async createOrder(customer_name, pickup_time, items) {
    if (!customer_name || typeof customer_name !== 'string' || customer_name.trim() === '') {
      throw new Error('Customer name is required');
    }

    if (!pickup_time || typeof pickup_time !== 'string' || pickup_time.trim() === '') {
      throw new Error('Pickup time is required');
    }

    if (!Array.isArray(items) || items.length === 0) {
      throw new Error('Order must contain at least one item');
    }

    const menuItems = await this.getMenuItems();
    const menuItemsMap = new Map(menuItems.map(item => [item.id, item]));

    let totalPrice = 0;
    for (const item of items) {
      if (!item.id || typeof item.id !== 'number') {
        throw new Error('Invalid item ID');
      }

      if (!item.quantity || typeof item.quantity !== 'number' || item.quantity < 1) {
        throw new Error('Item quantity must be a positive number');
      }

      const menuItem = menuItemsMap.get(item.id);
      if (!menuItem) {
        throw new Error(`Menu item with ID ${item.id} not found`);
      }

      totalPrice += menuItem.price * item.quantity;
    }

    const itemsJson = JSON.stringify(items);

    return new Promise((resolve, reject) => {
      const sql = 'INSERT INTO orders (customer_name, pickup_time, items, total_price) VALUES (?, ?, ?, ?)';
      this.db.db.run(sql, [customer_name, pickup_time, itemsJson, totalPrice], function(err) {
        if (err) return reject(err);
        resolve({
          id: this.lastID,
          customer_name,
          pickup_time,
          items,
          total_price: totalPrice,
          status: 'pending'
        });
      });
    });
  }

  async getOrders() {
    return new Promise((resolve, reject) => {
      const sql = 'SELECT * FROM orders ORDER BY pickup_time ASC';
      this.db.db.all(sql, (err, rows) => {
        if (err) return reject(err);
        const orders = rows.map(row => ({
          ...row,
          items: JSON.parse(row.items)
        }));
        resolve(orders);
      });
    });
  }

  async completeOrder(orderId) {
    return new Promise((resolve, reject) => {
      const sql = 'UPDATE orders SET status = ? WHERE id = ?';
      this.db.db.run(sql, ['completed', orderId], function(err) {
        if (err) return reject(err);
        if (this.changes === 0) {
          return reject(new Error('Order not found'));
        }
        resolve();
      });
    });
  }

  async getMenuItems() {
    return this.db.getMenuItems();
  }
}

module.exports = OrderService;
