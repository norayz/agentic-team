const express = require('express');
const path = require('path');
const {
  getAllMenuItems,
  getOrderById,
  getPendingOrders,
  markOrderComplete
} = require('./services/database');
const { validateAndCreateOrder } = require('./services/orders');

const app = express();

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../public')));

// Routes

// GET / - Menu page
app.get('/', (req, res) => {
  const menuItems = getAllMenuItems();
  res.render('menu', { menuItems });
});

// GET /cart - Cart page
app.get('/cart', (req, res) => {
  res.render('cart');
});

// POST /order - Submit order
app.post('/order', (req, res) => {
  const { customer_name, pickup_time, items } = req.body;

  try {
    const orderId = validateAndCreateOrder(customer_name, pickup_time, items);
    res.redirect(`/confirmation/${orderId}`);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// GET /confirmation/:orderId - Order confirmation page
app.get('/confirmation/:orderId', (req, res) => {
  const orderId = parseInt(req.params.orderId);
  const order = getOrderById(orderId);

  if (!order) {
    return res.status(404).render('error', { message: 'Order not found' });
  }

  res.render('confirmation', { order });
});

// GET /admin - Admin panel
app.get('/admin', (req, res) => {
  const orders = getPendingOrders();
  res.render('admin', { orders });
});

// POST /admin/complete/:orderId - Mark order as complete
app.post('/admin/complete/:orderId', (req, res) => {
  const orderId = parseInt(req.params.orderId);
  const success = markOrderComplete(orderId);

  if (!success) {
    return res.status(404).render('error', { message: 'Order not found' });
  }

  res.redirect('/admin');
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('error', { message: 'Page not found' });
});

module.exports = app;
