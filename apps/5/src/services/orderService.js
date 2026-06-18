class OrderService {
  constructor(database) {
    this.db = database.db;
  }

  createOrder(orderData, callback) {
    const { customer_name, pickup_time, items, total_price } = orderData;
    const itemsJson = JSON.stringify(items);
    
    this.db.run(
      `INSERT INTO orders (customer_name, pickup_time, items, total_price, status, created_at) 
       VALUES (?, ?, ?, ?, 'pending', datetime('now'))`,
      [customer_name, pickup_time, itemsJson, total_price],
      function(err) {
        if (err) {
          return callback(err, null);
        }
        callback(null, this.lastID);
      }
    );
  }

  getAllOrders(callback) {
    this.db.all(
      'SELECT * FROM orders ORDER BY pickup_time ASC',
      [],
      (err, rows) => {
        if (err) {
          return callback(err, null);
        }
        // Parse items JSON for each order
        const orders = rows.map(row => ({
          ...row,
          items: JSON.parse(row.items)
        }));
        callback(null, orders);
      }
    );
  }

  markOrderComplete(orderId, callback) {
    this.db.run(
      "UPDATE orders SET status = 'completed' WHERE id = ?",
      [orderId],
      (err) => {
        if (err) {
          return callback(err);
        }
        callback(null);
      }
    );
  }
}

module.exports = OrderService;
