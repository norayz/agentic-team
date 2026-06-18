// Cart management using localStorage

function getCart() {
  const cart = localStorage.getItem('cart');
  return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}

function addToCart(id, name, price) {
  const cart = getCart();
  const existingItem = cart.find(item => item.id === parseInt(id));
  
  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({
      id: parseInt(id),
      name: name,
      price: parseFloat(price),
      quantity: 1
    });
  }
  
  saveCart(cart);
  showNotification(`${name} added to cart!`);
}

function removeFromCart(id) {
  const cart = getCart();
  const updatedCart = cart.filter(item => item.id !== parseInt(id));
  saveCart(updatedCart);
  displayCart();
}

function updateQuantity(id, change) {
  const cart = getCart();
  const item = cart.find(item => item.id === parseInt(id));
  
  if (item) {
    item.quantity += change;
    if (item.quantity <= 0) {
      removeFromCart(id);
    } else {
      saveCart(cart);
      displayCart();
    }
  }
}

function calculateTotal(cart) {
  return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
}

function updateCartCount() {
  const cart = getCart();
  const count = cart.reduce((total, item) => total + item.quantity, 0);
  const countElement = document.getElementById('cart-count');
  if (countElement) {
    countElement.textContent = `(${count})`;
  }
}

function displayCart() {
  const cart = getCart();
  const cartItemsDiv = document.getElementById('cart-items');
  const cartTotalDiv = document.getElementById('cart-total');
  const orderForm = document.getElementById('order-form');
  
  if (!cartItemsDiv) return;
  
  if (cart.length === 0) {
    cartItemsDiv.innerHTML = '<p>Your cart is empty. <a href="/">Browse the menu</a></p>';
    cartTotalDiv.innerHTML = '';
    if (orderForm) orderForm.style.display = 'none';
    return;
  }
  
  let html = '<div class="cart-items-list">';
  cart.forEach(item => {
    const itemTotal = item.price * item.quantity;
    html += `
      <div class="cart-item">
        <div class="item-info">
          <h4>${item.name}</h4>
          <p class="item-price">$${item.price.toFixed(2)} each</p>
        </div>
        <div class="item-controls">
          <button class="btn-quantity" onclick="updateQuantity(${item.id}, -1)">-</button>
          <span class="quantity">${item.quantity}</span>
          <button class="btn-quantity" onclick="updateQuantity(${item.id}, 1)">+</button>
          <button class="btn-remove" onclick="removeFromCart(${item.id})">Remove</button>
        </div>
        <div class="item-total">$${itemTotal.toFixed(2)}</div>
      </div>
    `;
  });
  html += '</div>';
  
  cartItemsDiv.innerHTML = html;
  
  const total = calculateTotal(cart);
  cartTotalDiv.innerHTML = `<h3>Total: $${total.toFixed(2)}</h3>`;
  
  if (orderForm) {
    orderForm.style.display = 'block';
  }
  
  updateCartCount();
}

function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 2000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  const addToCartButtons = document.querySelectorAll('.add-to-cart');
  addToCartButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      const id = e.target.dataset.id;
      const name = e.target.dataset.name;
      const price = e.target.dataset.price;
      addToCart(id, name, price);
    });
  });
  
  const orderForm = document.getElementById('order-form');
  if (orderForm) {
    orderForm.addEventListener('submit', (e) => {
      const cart = getCart();
      if (cart.length === 0) {
        e.preventDefault();
        alert('Your cart is empty!');
        return;
      }
      
      const items = cart.map(item => ({
        id: item.id,
        quantity: item.quantity
      }));
      
      document.getElementById('items').value = JSON.stringify(items);
    });
  }
  
  updateCartCount();
});
