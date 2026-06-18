# Barista Site - Coffee House Online Ordering

A simple web application for browsing menu items and placing coffee orders online.

## Features

- Browse coffee menu with prices
- Add items to cart (localStorage)
- Place orders with name and pickup time
- View order confirmation
- Admin page to view and manage orders

## Tech Stack

- Node.js + Express
- EJS templates (server-side rendering)
- SQLite database
- Vanilla JavaScript (client-side cart)

## Installation

```bash
npm install
```

## Running the Application

```bash
npm start
```

The application will be available at `http://localhost:3000`

## Environment Variables

- `PORT` - Server port (default: 3000)
- `DATABASE_PATH` - Path to SQLite database file (default: `./data/barista.db`)
- `NODE_ENV` - Environment (development/production)

## Project Structure

```
src/
  app.js              - Main Express application
  database.js         - SQLite database wrapper
  services/
    orderService.js   - Order business logic
views/
  menu.ejs           - Menu page
  cart.ejs           - Cart page
  confirmation.ejs   - Order confirmation
  admin.ejs          - Admin orders page
public/
  css/styles.css     - Styles
  js/cart.js         - Client-side cart management
```

## Admin Access

Access the admin page at: `/admin`

## Menu Configuration

Menu items are seeded automatically on first run. The default items are:
- Espresso ($3.00)
- Latte ($4.50)
- Cappuccino ($4.50)
- Cold Brew ($4.00)
- Drip Coffee ($2.50)

## Security Notes

- The server recalculates all prices from the menu database (never trusts client-provided prices)
- Item IDs are validated against the menu before order creation
- Quantities must be positive integers
- Order data persists in SQLite (survives server restart)

## Deployment

See `IMPLEMENTATION.md` for deployment details.
