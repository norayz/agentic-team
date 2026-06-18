const express = require('express');
const path = require('path');
const Database = require('./database');
const OrderService = require('./services/orderService');

const app = express();
const PORT = process.env.PORT || 3000;
const DATABASE_PATH = process.env.DATABASE_PATH || path.join(__dirname, '../data/barista.db');

const db = new Database(DATABASE_PATH);
const orderService = new OrderService(db);

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '../views'));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../public')));

app.get('/', async (req, res) => {
  try {
    const menuItems = await orderService.getMenuItems();
    res.render('menu', { menuItems });
  } catch (err) {
    console.error('Error loading menu:', err);
    res.status(500).send('Error loading menu');
  }
});

app.get('/cart', (req, res) => {
  res.render('cart');
});

app.post('/order', async (req, res) => {
  try {
    const { customer_name, pickup_time, items } = req.body;
    const parsedItems = JSON.parse(items);
    
    const order = await orderService.createOrder(customer_name, pickup_time, parsedItems);
    res.redirect(`/confirmation/${order.id}`);
  } catch (err) {
    console.error('Error creating order:', err);
    res.status(400).send('Error creating order: ' + err.message);
  }
});

app.get('/confirmation/:id', async (req, res) => {
  try {
    const orders = await orderService.getOrders();
    const order = orders.find(o => o.id === parseInt(req.params.id));
    
    if (!order) {
      return res.status(404).send('Order not found');
    }
    
    const menuItems = await orderService.getMenuItems();
    const menuItemsMap = new Map(menuItems.map(item => [item.id, item]));
    
    res.render('confirmation', { order, menuItemsMap });
  } catch (err) {
    console.error('Error loading confirmation:', err);
    res.status(500).send('Error loading confirmation');
  }
});

app.get('/admin', async (req, res) => {
  try {
    const orders = await orderService.getOrders();
    const menuItems = await orderService.getMenuItems();
    const menuItemsMap = new Map(menuItems.map(item => [item.id, item]));
    
    res.render('admin', { orders, menuItemsMap });
  } catch (err) {
    console.error('Error loading admin page:', err);
    res.status(500).send('Error loading admin page');
  }
});

app.post('/admin/complete/:id', async (req, res) => {
  try {
    await orderService.completeOrder(parseInt(req.params.id));
    res.redirect('/admin');
  } catch (err) {
    console.error('Error completing order:', err);
    res.status(500).send('Error completing order: ' + err.message);
  }
});

async function start() {
  try {
    await db.initialize();
    
    const menuItems = await db.getMenuItems();
    if (menuItems.length === 0) {
      console.log('Seeding menu items...');
      await db.seedMenuItems();
    }
    
    app.listen(PORT, () => {
      console.log(`Barista Site running on http://localhost:${PORT}`);
    });
  } catch (err) {
    console.error('Failed to start application:', err);
    process.exit(1);
  }
}

process.on('SIGINT', async () => {
  console.log('\nShutting down gracefully...');
  await db.close();
  process.exit(0);
});

start();
