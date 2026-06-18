// Cart management using localStorage

function getCart() {
  const cart = localStorage.getItem('cart');
  return cart ? JSON.parse(cart) : [];
}

function saveCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}

function updateCartCount() {
  const cart = getCart();
  const count = cart.reduce((sum, item) => sum + item.quantity, 0);
  const cartCountElement = document.getElementById('cart-count');
  if (cartCountElement) {
    cartCountElement.textContent = count;
  }
}

function addToCart(id, name, price) {
  const cart = getCart();
  const existingItem = cart.find(item => item.id === id);

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ id, name, price, quantity: 1 });
  }

  saveCart(cart);
  alert(`${name} added to cart!`);
}

function increaseQuantity(id) {
  const cart = getCart();
  const item = cart.find(item => item.id === id);
  if (item) {
    item.quantity += 1;
    saveCart(cart);
    renderCart();
  }
}

function decreaseQuantity(id) {
  const cart = getCart();
  const item = cart.find(item => item.id === id);
  if (item && item.quantity > 1) {
    item.quantity -= 1;
    saveCart(cart);
    renderCart();
  }
}

function removeFromCart(id) {
  let cart = getCart();
  cart = cart.filter(item => item.id !== id);
  saveCart(cart);
  renderCart();
}

function renderCart() {
  const cart = getCart();
  const cartItemsContainer = document.getElementById('cart-items');
  const cartTotalContainer = document.getElementById('cart-total');
  const emptyCartMessage = document.getElementById('empty-cart');
  const orderForm = document.getElementById('order-form');

  if (cart.length === 0) {
    emptyCartMessage.style.display = 'block';
    cartItemsContainer.innerHTML = '';
    cartTotalContainer.innerHTML = '';
    orderForm.style.display = 'none';
    return;
  }

  emptyCartMessage.style.display = 'none';
  orderForm.style.display = 'block';

  let total = 0;
  cartItemsContainer.innerHTML = '<div class="cart-items-list">';

  cart.forEach(item => {
    const itemTotal = item.price * item.quantity;
    total += itemTotal;

    cartItemsContainer.innerHTML += `
      <div class="cart-item">
        <h3>${item.name}</h3>
        <p class="price">$${item.price.toFixed(2)} each</p>
        <div class="quantity-controls">
          <button onclick="decreaseQuantity(${item.id})">-</button>
          <span>${item.quantity}</span>
          <button onclick="increaseQuantity(${item.id})">+</button>
          <button class="btn-remove" onclick="removeFromCart(${item.id})">Remove</button>
        </div>
        <p class="item-total">Subtotal: $${itemTotal.toFixed(2)}</p>
      </div>
    `;
  });

  cartItemsContainer.innerHTML += '</div>';
  cartTotalContainer.innerHTML = `<h3>Total: $${total.toFixed(2)}</h3>`;
}

function handleOrderSubmit(event) {
  event.preventDefault();

  const cart = getCart();
  if (cart.length === 0) {
    alert('Your cart is empty!');
    return;
  }

  const form = event.target;
  const customerName = form.customer_name.value;
  const pickupTime = form.pickup_time.value;

  const orderData = {
    customer_name: customerName,
    pickup_time: pickupTime,
    items: cart
  };

  const errorMessage = document.getElementById('error-message');

  fetch('/order', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(orderData)
  })
    .then(response => {
      if (response.redirected) {
        window.location.href = response.url;
      } else if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error || 'Failed to place order');
        });
      }
    })
    .catch(error => {
      errorMessage.textContent = error.message;
      errorMessage.style.display = 'block';
    });
}

// Initialize cart count on page load
updateCartCount();

// Set up event listeners on menu page
if (document.querySelector('.menu-grid')) {
  document.querySelectorAll('.add-to-cart').forEach(button => {
    button.addEventListener('click', function() {
      const id = parseInt(this.dataset.id);
      const name = this.dataset.name;
      const price = parseFloat(this.dataset.price);
      addToCart(id, name, price);
    });
  });
}

// Set up event listeners on cart page
if (document.getElementById('cart-items')) {
  renderCart();
}

if (document.getElementById('order-form')) {
  document.getElementById('order-form').addEventListener('submit', handleOrderSubmit);
}
