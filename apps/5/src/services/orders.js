const { getAllMenuItems, createOrder: createOrderInDb } = require('./database');

/**
 * Validate and create an order
 * - Never trust client prices, always recalculate from database
 * - Validate all items exist in menu
 * - Validate required fields
 */
function validateAndCreateOrder(customerName, pickupTime, items) {
  // Validation: required fields
  if (!customerName || !customerName.trim()) {
    throw new Error('Customer name is required');
  }

  if (!pickupTime) {
    throw new Error('Pickup time is required');
  }

  // Validation: items must be an array and not empty
  if (!Array.isArray(items) || items.length === 0) {
    throw new Error('Order must contain at least one item');
  }

  // Get current menu prices from database
  const menuItems = getAllMenuItems();
  const menuMap = new Map(menuItems.map(item => [item.id, item]));

  // Validation: all items must exist in menu
  for (const item of items) {
    if (!menuMap.has(item.id)) {
      throw new Error(`Invalid item ID: ${item.id}`);
    }
  }

  // Security: Recalculate total price from database (never trust client)
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

  // Round to 2 decimal places
  totalPrice = Math.round(totalPrice * 100) / 100;

  // Create order in database
  const orderId = createOrderInDb(
    customerName.trim(),
    pickupTime,
    validatedItems,
    totalPrice
  );

  return orderId;
}

module.exports = {
  validateAndCreateOrder
};
