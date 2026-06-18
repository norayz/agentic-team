# Barista Site - Coffee House Online Ordering

A simple web application for browsing a coffee menu and placing online orders.

## Features

- Browse full coffee/drink menu with descriptions and prices
- Add items to cart and adjust quantities
- Submit orders with name and pickup time
- Admin panel to view and manage orders
- Mobile-responsive design
- Fast-loading (<3 seconds on 3G)

## Tech Stack

- **Backend:** Node.js + Express
- **Database:** SQLite (lightweight, no separate server needed)
- **Views:** EJS templates
- **Frontend:** Vanilla JavaScript (no framework bloat)
- **Styling:** Custom CSS (mobile-first)

## Installation

```bash
npm install
```

## Usage

### Development
```bash
npm start
```

Server runs on `http://localhost:3000`

### Testing
```bash
npm test
```

### Linting
```bash
npm run lint
```

## Project Structure

```
apps/5/
├── src/
│   ├── services/
│   │   ├── database.js      # SQLite database service
│   │   └── orders.js         # Order validation & business logic
│   ├── views/
│   │   ├── menu.ejs          # Menu page
│   │   ├── cart.ejs          # Cart page
│   │   ├── confirmation.ejs  # Order confirmation
│   │   ├── admin.ejs         # Admin panel
│   │   └── error.ejs         # Error page
│   └── server.js             # Express app & routes
├── public/
│   ├── css/
│   │   └── style.css         # Minimal, mobile-first styles
│   └── js/
│       └── cart.js           # Client-side cart management
├── tests/
│   ├── services.test.js      # Data layer & business logic tests
│   └── routes.test.js        # HTTP route tests
├── data/                     # SQLite database storage
├── package.json
├── jest.config.json
└── IMPLEMENTATION.md
```

## Routes

- `GET /` - Menu page
- `GET /cart` - Cart page
- `POST /order` - Submit order
- `GET /confirmation/:orderId` - Order confirmation
- `GET /admin` - Admin panel (unlisted, no auth)
- `POST /admin/complete/:orderId` - Mark order complete

## Database Schema

### menu_items
- id (INTEGER PRIMARY KEY)
- name (TEXT)
- description (TEXT)
- price (REAL)

### orders
- id (INTEGER PRIMARY KEY)
- customer_name (TEXT)
- pickup_time (TEXT)
- items (TEXT, JSON)
- total_price (REAL)
- status (TEXT: 'pending' | 'completed')
- created_at (TEXT)

## Security Features

- Server-side price recalculation (never trust client)
- Item validation against database
- Input sanitization
- SQL injection prevention (parameterized queries)

## Performance

- Minimal JavaScript (~5KB)
- Minimal CSS (~8KB)
- No external dependencies on client
- Mobile-first responsive design
- Target: <3 seconds load on 3G

## License

ISC
