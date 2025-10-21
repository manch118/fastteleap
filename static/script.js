// ==================== TELEGRAM WEBAPP INITIALIZATION ====================
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Apply Telegram theme
const applyTheme = () => {
    if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    
    // Update MainButton color based on theme
    tg.MainButton.setParams({
        color: getComputedStyle(document.documentElement)
            .getPropertyValue('--accent-color')
            .trim(),
        text_color: '#ffffff'
    });
};

tg.onEvent('themeChanged', applyTheme);
applyTheme();

// ==================== ADMIN DETECTION ====================
let ADMIN_ID = null; // fetched from backend config
const telegramUserId = tg?.initDataUnsafe?.user?.id || null;
let adminEnabled = false;

const applyAdminVisibility = () => {
    if (elements?.adminFab) {
        elements.adminFab.style.display = adminEnabled ? 'flex' : 'none';
    }
};

const getAdminHeaders = () => ({
    'Content-Type': 'application/json',
    'X-Telegram-Id': String(telegramUserId || '')
});

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        if (!res.ok) throw new Error('Failed to load config');
        const data = await res.json();
        ADMIN_ID = Number(data?.admin_id ?? 0);
        adminEnabled = Boolean(telegramUserId) && Number(telegramUserId) === ADMIN_ID;
        applyAdminVisibility();
    } catch (e) {
        console.error('Config fetch error:', e);
        ADMIN_ID = null;
        adminEnabled = false;
        applyAdminVisibility();
    }
}

// ==================== PRODUCTS DATA (fetched from backend) ====================
let products = [];

async function loadProducts() {
    try {
        // Add a cache-busting parameter to ensure fresh data is always fetched
        const cacheBuster = `?_=${new Date().getTime()}`;
        const res = await fetch(`/api/products${cacheBuster}`);

        if (!res.ok) throw new Error('Failed to load products');
        const data = await res.json();

        products = data.map(p => ({
            id: p.id,
            name: p.title,
            description: p.description ?? '',
            price: p.price,
            image: p.image ?? ''
        }));

        renderProducts();
        updateCartView();
    } catch (e) {
        console.error('Products fetch error:', e);
    }
}

// ==================== STATE MANAGEMENT ====================
let cart = [];
let deliveryType = 'delivery';
let paymentType = 'cash';

// ==================== DOM ELEMENTS ====================
const elements = {
    menuGrid: document.getElementById('menu-grid'),
    cartFab: document.getElementById('cart-fab'),
    cartCounter: document.getElementById('cart-counter'),
    cartFabTotal: document.getElementById('cart-fab-total'),
    cartModalOverlay: document.getElementById('cart-modal-overlay'),
    cartModal: document.getElementById('cart-modal'),
    closeCartBtn: document.getElementById('close-cart-btn'),
    cartItemsContainer: document.getElementById('cart-items-container'),
    cartTotal: document.getElementById('cart-total'),
    cartFooter: document.getElementById('cart-footer'),
    checkoutBtn: document.getElementById('checkout-btn'),
    orderFormModalOverlay: document.getElementById('order-form-modal-overlay'),
    orderFormModal: document.getElementById('order-form-modal'),
    closeOrderFormBtn: document.getElementById('close-order-form-btn'),
    orderForm: document.getElementById('order-form'),
    paymentInfo: document.getElementById('payment-info'),
    addressGroup: document.getElementById('address-group'),
    thankYouModalOverlay: document.getElementById('thank-you-modal-overlay'),
    thankYouModal: document.getElementById('thank-you-modal'),
    closeAppBtn: document.getElementById('close-app-btn'),
    hamburger: document.querySelector('.hamburger'),
    navLinks: document.querySelector('.nav-links')
};

// Admin elements (may be null if not present)
elements.adminFab = document.getElementById('admin-fab');
elements.adminModalOverlay = document.getElementById('admin-modal-overlay');
elements.adminModal = document.getElementById('admin-modal');
elements.closeAdminBtn = document.getElementById('close-admin-btn');
elements.adminForm = document.getElementById('admin-form');
elements.adminProductId = document.getElementById('admin-product-id');
elements.adminTitle = document.getElementById('admin-title');
elements.adminDescription = document.getElementById('admin-description');
elements.adminPrice = document.getElementById('admin-price');
elements.adminImage = document.getElementById('admin-image');
elements.adminNewBtn = document.getElementById('admin-new-btn');
elements.adminImageFile = document.getElementById('admin-image-file');
elements.adminImagePreview = document.getElementById('admin-image-preview');

// ==================== RENDER PRODUCTS ====================
const renderProducts = () => {
    elements.menuGrid.innerHTML = '';
    
    products.forEach((product, index) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.animationDelay = `${index * 0.05}s`;
        
        const adminControls = adminEnabled ? `
            <div style="display:flex; gap:8px;">
                <button class="add-to-cart-btn edit-product-btn" data-id="${product.id}">
                    <i class="fas fa-pen"></i>
                    <span>Редактировать</span>
                </button>
                <button class="add-to-cart-btn delete-product-btn" data-id="${product.id}">
                    <i class="fas fa-trash"></i>
                    <span>Удалить</span>
                </button>
            </div>
        ` : '';

        card.innerHTML = `
            <img src="${product.image}" alt="${product.name}" class="product-image" loading="lazy">
            <div class="product-info">
                <h3>${product.name}</h3>
                <p>${product.description}</p>
                <div class="product-footer">
                    <span class="product-price">${product.price} ₽</span>
                    <button class="add-to-cart-btn" data-id="${product.id}">
                        <i class="fas fa-cart-plus"></i>
                        <span>Добавить</span>
                    </button>
                </div>
                ${adminControls}
            </div>
        `;
        
        elements.menuGrid.appendChild(card);
    });
};

// ==================== CART FUNCTIONS ====================
const addToCart = (productId) => {
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({ id: productId, quantity: 1 });
    }
    
    updateCartView();
    tg.HapticFeedback.impactOccurred('light');
};

const changeQuantity = (productId, action) => {
    const item = cart.find(item => item.id === productId);
    if (!item) return;
    
    if (action === 'increase') {
        item.quantity++;
        tg.HapticFeedback.impactOccurred('light');
    } else if (action === 'decrease') {
        item.quantity--;
        tg.HapticFeedback.impactOccurred('light');
        
        if (item.quantity === 0) {
            removeFromCart(productId);
        }
    }
    
    updateCartView();
};

const removeFromCart = (productId) => {
    cart = cart.filter(item => item.id !== productId);
    updateCartView();
    tg.HapticFeedback.notificationOccurred('success');
};

const calculateTotal = () => {
    return cart.reduce((sum, item) => {
        const product = products.find(p => p.id === item.id);
        return sum + product.price * item.quantity;
    }, 0);
};

const updateCartView = () => {
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = calculateTotal();
    
    // Update FAB
    if (totalItems > 0) {
        elements.cartCounter.textContent = totalItems;
        elements.cartCounter.style.display = 'flex';
        elements.cartFabTotal.textContent = `${totalPrice} ₽`;
        elements.cartFabTotal.style.display = 'block';
    } else {
        elements.cartCounter.style.display = 'none';
        elements.cartFabTotal.style.display = 'none';
    }
    
    // Update cart modal
    if (cart.length === 0) {
        elements.cartItemsContainer.innerHTML = `
            <div class="empty-cart-message">
                <i class="fas fa-shopping-basket"></i>
                <p>Ваша корзина пуста</p>
            </div>
        `;
        elements.cartFooter.style.display = 'none';
    } else {
        elements.cartFooter.style.display = 'block';
        elements.cartItemsContainer.innerHTML = '';
        
        cart.forEach(item => {
            const product = products.find(p => p.id === item.id);
            const cartItem = document.createElement('li');
            cartItem.className = 'cart-item';
            
            cartItem.innerHTML = `
                <img src="${product.image}" alt="${product.name}" class="cart-item-image">
                <div class="cart-item-info">
                    <h4>${product.name}</h4>
                    <span class="cart-item-price">${item.quantity} × ${product.price} ₽</span>
                </div>
                <div class="cart-item-controls">
                    <button class="quantity-btn" data-id="${item.id}" data-action="decrease">−</button>
                    <span>${item.quantity}</span>
                    <button class="quantity-btn" data-id="${item.id}" data-action="increase">+</button>
                    <button class="remove-item-btn" data-id="${item.id}">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
            
            elements.cartItemsContainer.appendChild(cartItem);
        });
    }
    
    elements.cartTotal.textContent = `${totalPrice} ₽`;
    tg.MainButton.setText(`Оформить заказ · ${totalPrice} ₽`);
};

// ==================== MODAL FUNCTIONS ====================
const openModal = (overlayElement, modalElement) => {
    overlayElement.classList.add('active');
    tg.HapticFeedback.impactOccurred('medium');
};

const closeModal = (overlayElement, modalElement) => {
    overlayElement.classList.remove('active');
};

const showCartModal = () => {
    openModal(elements.cartModalOverlay, elements.cartModal);
};

const hideCartModal = () => {
    closeModal(elements.cartModalOverlay, elements.cartModal);
};

const showAdminModal = () => {
    if (!elements.adminModalOverlay) return;
    openModal(elements.adminModalOverlay, elements.adminModal);
};

const hideAdminModal = () => {
    if (!elements.adminModalOverlay) return;
    closeModal(elements.adminModalOverlay, elements.adminModal);
};

const showOrderForm = () => {
    console.log('[DEBUG] showOrderForm called, cart length:', cart.length);
    if (cart.length === 0) {
        console.log('[DEBUG] Cart is empty, showing alert');
        tg.showAlert('Ваша корзина пуста!');
        return;
    }

    console.log('[DEBUG] Hiding cart modal and showing order form');
    hideCartModal();
    setTimeout(() => {
        openModal(elements.orderFormModalOverlay, elements.orderFormModal);
        tg.MainButton.show();
        tg.MainButton.setText(`Подтвердить заказ · ${calculateTotal()} ₽`);
        console.log('[DEBUG] Order form modal opened, MainButton shown');
    }, 300);
};

const hideOrderForm = () => {
    closeModal(elements.orderFormModalOverlay, elements.orderFormModal);
    // MainButton is now hidden only when the process is fully complete or cancelled.
    tg.MainButton.hide();
};

const showThankYouModal = () => {
    hideOrderForm();
    openModal(elements.thankYouModalOverlay, elements.thankYouModal);
    tg.HapticFeedback.notificationOccurred('success');
    
    // Clear cart
    cart = [];
    updateCartView();
};

// ==================== ORDER FORM LOGIC ====================
const updatePaymentInfo = () => {
    const infoText = paymentType === 'cash'
        ? 'Оплата наличными при получении'
        : 'Вы будете перенаправлены на страницу оплаты';
    
    elements.paymentInfo.innerHTML = `
        <i class="fas fa-info-circle"></i>
        ${infoText}
    `;
};

const updateAddressField = () => {
    const addressInput = document.getElementById('address');
    elements.addressGroup.style.display = deliveryType === 'delivery' ? 'block' : 'none';
    addressInput.required = deliveryType === 'delivery';
};

const handleMainButtonClick = async () => {
    console.log(`[DEBUG] MainButton clicked. Payment: ${paymentType}, Delivery: ${deliveryType}`);

    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();

    if (!name) {
        tg.showAlert('Пожалуйста, укажите ваше имя.');
        return;
    }

    // A more robust phone validation (at least 10 digits)
    if (!phone || phone.replace(/\D/g, '').length < 10) {
        tg.showAlert('Пожалуйста, укажите корректный номер телефона.');
        return;
    }

    if (deliveryType === 'delivery' && !address) {
        tg.showAlert('Пожалуйста, укажите адрес доставки.');
        return;
    }

    // Show loading indicator on the main button
    tg.MainButton.showProgress();

    const orderData = {
        customer_name: document.getElementById('name').value,
        customer_phone: document.getElementById('phone').value,
        customer_address: document.getElementById('address').value,
        delivery_type: deliveryType, // FIX: Use correct variable name
        payment_type: paymentType,   // FIX: Use correct variable name
        comment: document.getElementById('comment').value,
        items: cart.map(item => {
            const product = products.find(p => p.id === item.id);
            return {
                product_id: item.id,
                quantity: item.quantity,
            };
        })
    };

    console.log('[DEBUG] Sending order data to backend:', JSON.stringify(orderData, null, 2));

    try {
        // Create order
        const orderRes = await fetch('/api/orders/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Id': String(telegramUserId || ''),
            },
            body: JSON.stringify(orderData)
        });

        if (!orderRes.ok) {
            const errorText = await orderRes.text();
            console.error('Order creation failed:', errorText);
            tg.showAlert(`Ошибка создания заказа: ${errorText || 'Неизвестная ошибка'}`);
            throw new Error(errorText || 'Failed to create order');
        }

        const order = await orderRes.json();
        console.log('[DEBUG] Order created successfully:', order);

        if (paymentType === 'online') {
            // Create payment
            const paymentRes = await fetch(`/api/orders/${order.id}/payment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Id': String(telegramUserId || ''),
                },
                body: JSON.stringify({ order_id: order.id }),
            });

            if (!paymentRes.ok) {
                const paymentError = await paymentRes.text();
                tg.showAlert(`Ошибка платежа: ${paymentError}`);
                throw new Error('Failed to create payment');
            }

            const payment = await paymentRes.json();
            console.log('[DEBUG] Payment created:', payment);

            tg.showPopup({
                title: 'Переход к оплате',
                message: `Сумма к оплате: ${order.total_amount} ₽`,
                buttons: [
                    { id: 'cancel', type: 'cancel', text: 'Отмена' },
                    { id: 'ok', type: 'ok', text: 'Оплатить' }
                ]
            }, (buttonId) => {
                if (buttonId === 'ok') {
                    // Open payment URL in external browser
                    tg.openLink(payment.payment_url);

                    // Send order data to bot for tracking
                    tg.sendData(JSON.stringify({
                        order_id: order.id,
                        payment_id: payment.payment_id,
                        total_amount: order.total_amount,
                        status: 'payment_initiated',
                    }));

                    tg.MainButton.hide(); // Hide button after action
                    showThankYouModal();
                }
            });
        } else {
            // Cash payment - just send order data
            tg.sendData(JSON.stringify({
                order_id: order.id,
                total_amount: order.total_amount,
                payment_type: 'cash',
            }));
            tg.MainButton.hide(); // Hide button after action
            showThankYouModal();
        }

    } catch (error) {
        console.error('Error in handleMainButtonClick:', error);
        tg.showAlert(`Ошибка: ${error.message}`);
    } finally {
        // Hide loading indicator
        if (tg.MainButton.isProgressVisible) {
            tg.MainButton.hideProgress();
        }
    }
};

// ==================== NAVIGATION ====================
const navigateTo = (pageId) => {
    // Update sections
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`.nav-link[data-page="${pageId}"]`)?.classList.add('active');
    
    // Close mobile menu
    elements.navLinks.classList.remove('active');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    tg.HapticFeedback.impactOccurred('light');
};

// ==================== EVENT LISTENERS ====================

// Load config first, then products
loadConfig().then(() => loadProducts());

// Navigation
elements.navLinks.addEventListener('click', (e) => {
    if (e.target.classList.contains('nav-link')) {
        e.preventDefault();
        const pageId = e.target.dataset.page;
        navigateTo(pageId);
    }
});

// Mobile menu toggle
elements.hamburger.addEventListener('click', () => {
    elements.navLinks.classList.toggle('active');
    tg.HapticFeedback.impactOccurred('light');
});

// Home button navigation
document.addEventListener('click', (e) => {
    if (e.target.closest('[data-navigate]')) {
        const page = e.target.closest('[data-navigate]').dataset.navigate;
        navigateTo(page);
    }
});

// Add to cart
elements.menuGrid.addEventListener('click', (e) => {
    const btn = e.target.closest('.add-to-cart-btn');
    if (btn && !btn.classList.contains('edit-product-btn') && !btn.classList.contains('delete-product-btn')) {
        const productId = parseInt(btn.dataset.id, 10);
        addToCart(productId);
    }
});

// Admin edit/delete buttons on product cards
elements.menuGrid.addEventListener('click', async (e) => {
    const editBtn = e.target.closest('.edit-product-btn');
    const deleteBtn = e.target.closest('.delete-product-btn');
    if (!adminEnabled) return;

    if (editBtn) {
        const productId = parseInt(editBtn.dataset.id, 10);
        const product = products.find(p => p.id === productId);
        if (!product) return;
        elements.adminProductId.value = String(product.id);
        elements.adminTitle.value = product.name || '';
        elements.adminDescription.value = product.description || '';
        elements.adminPrice.value = String(product.price || '');
        elements.adminImage.value = product.image || '';
        showAdminModal();
    }

    if (deleteBtn) {
        const productId = parseInt(deleteBtn.dataset.id, 10);
        try {
            const res = await fetch(`/api/admin/products/${productId}`, {
                method: 'DELETE',
                headers: getAdminHeaders()
            });
            if (!res.ok) throw new Error('Delete failed');
            await loadProducts();
            tg.HapticFeedback.notificationOccurred('success');
        } catch (err) {
            console.error(err);
            tg.showAlert('Не удалось удалить товар');
        }
    }
});

// Cart FAB
elements.cartFab.addEventListener('click', showCartModal);

// Close cart modal
elements.closeCartBtn.addEventListener('click', hideCartModal);

// Cart modal overlay click
elements.cartModalOverlay.addEventListener('click', (e) => {
    if (e.target === elements.cartModalOverlay) {
        hideCartModal();
    }
});

// Admin modal events
if (elements.adminFab) {
    elements.adminFab.addEventListener('click', () => {
        if (!adminEnabled) return;
        // reset form for new product
        elements.adminProductId.value = '';
        elements.adminTitle.value = '';
        elements.adminDescription.value = '';
        elements.adminPrice.value = '';
        elements.adminImage.value = '';
        showAdminModal();
    });
}

if (elements.closeAdminBtn) {
    elements.closeAdminBtn.addEventListener('click', hideAdminModal);
}

if (elements.adminModalOverlay) {
    elements.adminModalOverlay.addEventListener('click', (e) => {
        if (e.target === elements.adminModalOverlay) {
            hideAdminModal();
        }
    });
}

if (elements.adminNewBtn) {
    elements.adminNewBtn.addEventListener('click', () => {
        elements.adminProductId.value = '';
        elements.adminTitle.value = '';
        elements.adminDescription.value = '';
        elements.adminPrice.value = '';
        elements.adminImage.value = '';
        if (elements.adminImagePreview) {
            elements.adminImagePreview.src = '';
            elements.adminImagePreview.style.display = 'none';
        }
    });
}

// Admin form submit (create or update)
if (elements.adminForm) {
    elements.adminForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!adminEnabled) return;

        const id = elements.adminProductId.value.trim();
        let imageUrl = elements.adminImage.value.trim() || '';

        // If file selected, upload first
        const file = elements.adminImageFile?.files?.[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);
            try {
                const uploadRes = await fetch('/api/admin/upload-image', {
                    method: 'POST',
                    headers: { 'X-Telegram-Id': String(telegramUserId || '') },
                    body: formData
                });
                if (!uploadRes.ok) throw new Error('Upload failed');
                const uploadJson = await uploadRes.json();
                imageUrl = uploadJson.url || imageUrl;
            } catch (err) {
                console.error(err);
                tg.showAlert('Не удалось загрузить изображение');
                return;
            }
        }

        const payload = {
            title: elements.adminTitle.value.trim(),
            description: elements.adminDescription.value.trim() || null,
            price: Number(elements.adminPrice.value),
            image: imageUrl || null
        };

        try {
            const url = id ? `/api/admin/products/${id}` : '/api/admin/products';
            const method = id ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method,
                headers: getAdminHeaders(),
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || 'Admin save failed');
            }
            await loadProducts();
            hideAdminModal();
            if (elements.adminImagePreview) {
                elements.adminImagePreview.src = '';
                elements.adminImagePreview.style.display = 'none';
            }
            tg.HapticFeedback.notificationOccurred('success');
        } catch (err) {
            console.error(err);
            tg.showAlert('Не удалось сохранить товар');
        }
    });
}

// Live preview: URL field
if (elements.adminImage) {
    elements.adminImage.addEventListener('input', () => {
        const url = elements.adminImage.value.trim();
        if (elements.adminImagePreview) {
            if (url) {
                elements.adminImagePreview.src = url;
                elements.adminImagePreview.style.display = 'block';
            } else {
                elements.adminImagePreview.src = '';
                elements.adminImagePreview.style.display = 'none';
            }
        }
    });
}

// Live preview: file field
if (elements.adminImageFile) {
    elements.adminImageFile.addEventListener('change', () => {
        const file = elements.adminImageFile.files?.[0];
        if (file && elements.adminImagePreview) {
            const reader = new FileReader();
            reader.onload = () => {
                elements.adminImagePreview.src = reader.result;
                elements.adminImagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });
}

// Cart item controls
elements.cartItemsContainer.addEventListener('click', (e) => {
    const quantityBtn = e.target.closest('.quantity-btn');
    const removeBtn = e.target.closest('.remove-item-btn');
    
    if (quantityBtn) {
        const productId = parseInt(quantityBtn.dataset.id, 10);
        const action = quantityBtn.dataset.action;
        changeQuantity(productId, action);
    }
    
    if (removeBtn) {
        const productId = parseInt(removeBtn.dataset.id, 10);
        removeFromCart(productId);
    }
});

// Checkout button
elements.checkoutBtn.addEventListener('click', () => {
    console.log('[DEBUG] Checkout button clicked');
    showOrderForm();
});

// Close order form
elements.closeOrderFormBtn.addEventListener('click', hideOrderForm);

// Order form overlay click
elements.orderFormModalOverlay.addEventListener('click', (e) => {
    if (e.target === elements.orderFormModalOverlay) {
        hideOrderForm();
    }
});

// Order form toggles
elements.orderForm.addEventListener('click', (e) => {
    const option = e.target.closest('.toggle-switch-option');
    if (!option) return;
    
    const parent = option.parentElement;
    parent.querySelector('.active')?.classList.remove('active');
    option.classList.add('active');
    
    if (option.dataset.delivery) {
        deliveryType = option.dataset.delivery;
        updateAddressField();
    }
    
    if (option.dataset.payment) {
        paymentType = option.dataset.payment;
        updatePaymentInfo();
    }
    
    tg.HapticFeedback.impactOccurred('light');
});

// Telegram MainButton
tg.MainButton.onClick(handleMainButtonClick);

// Close app button
elements.closeAppBtn.addEventListener('click', () => {
    tg.close();
});

// ==================== TELEGRAM BACK BUTTON ====================
tg.BackButton.onClick(() => {
    if (elements.orderFormModalOverlay.classList.contains('active')) {
        hideOrderForm();
        showCartModal();
    } else if (elements.cartModalOverlay.classList.contains('active')) {
        hideCartModal();
    } else {
        const currentPage = document.querySelector('.page-section.active').id;
        if (currentPage !== 'home') {
            navigateTo('home');
        }
    }
});

// Show/hide back button based on context
const updateBackButton = () => {
    const currentPage = document.querySelector('.page-section.active').id;
    const isModalOpen = elements.cartModalOverlay.classList.contains('active') ||
                        elements.orderFormModalOverlay.classList.contains('active');
    
    if (currentPage !== 'home' || isModalOpen) {
        tg.BackButton.show();
    } else {
        tg.BackButton.hide();
    }
};

// Monitor page changes and modal states
const observer = new MutationObserver(updateBackButton);
observer.observe(document.body, {
    attributes: true,
    subtree: true,
    attributeFilter: ['class']
});

// ==================== FORM VALIDATION ====================
const phoneInput = document.getElementById('phone');

// Format phone number as user types
phoneInput.addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length > 0) {
        if (value[0] === '7') {
            value = value.substring(1);
        }
        
        let formatted = '+7';
        if (value.length > 0) {
            formatted += ' (' + value.substring(0, 3);
        }
        if (value.length >= 4) {
            formatted += ') ' + value.substring(3, 6);
        }
        if (value.length >= 7) {
            formatted += '-' + value.substring(6, 8);
        }
        if (value.length >= 9) {
            formatted += '-' + value.substring(8, 10);
        }
        
        e.target.value = formatted;
    }
});

// Validate form before submission
const validateForm = () => {
    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();
    
    if (!name) {
        tg.showAlert('Пожалуйста, укажите ваше имя');
        return false;
    }
    
    if (!phone || phone.length < 18) {
        tg.showAlert('Пожалуйста, укажите корректный номер телефона');
        return false;
    }
    
    if (deliveryType === 'delivery' && !address) {
        tg.showAlert('Пожалуйста, укажите адрес доставки');
        return false;
    }
    
    return true;
};

// ==================== LOCAL STORAGE MANAGEMENT ====================
const STORAGE_KEY = 'bakery_cart';

// Save cart to localStorage
const saveCart = () => {
    try {
        const data = {
            cart,
            timestamp: Date.now()
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
        console.error('Error saving cart:', error);
    }
};

// Load cart from localStorage
const loadCart = () => {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (data) {
            const parsed = JSON.parse(data);
            
            // Check if cart is less than 24 hours old
            const hoursSinceUpdate = (Date.now() - parsed.timestamp) / (1000 * 60 * 60);
            if (hoursSinceUpdate < 24) {
                cart = parsed.cart || [];
                updateCartView();
            } else {
                // Clear old cart
                localStorage.removeItem(STORAGE_KEY);
            }
        }
    } catch (error) {
        console.error('Error loading cart:', error);
    }
};

// Update saveCart calls
const originalUpdateCartView = updateCartView;
updateCartView = () => {
    originalUpdateCartView();
    saveCart();
};

// ==================== SCROLL ANIMATIONS ====================
const observeElements = () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    }, {
        threshold: 0.1
    });
    
    document.querySelectorAll('.product-card, .info-card').forEach(el => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });
};

// ==================== SWIPE GESTURES ====================
let touchStartX = 0;
let touchEndX = 0;

const handleSwipe = () => {
    const swipeThreshold = 100;
    const diff = touchEndX - touchStartX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (elements.cartModalOverlay.classList.contains('active')) {
            if (diff > 0) { // Swipe right
                hideCartModal();
            }
        }
    }
};

document.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
});

document.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

// ==================== PERFORMANCE OPTIMIZATIONS ====================

// Lazy load images
if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.src = img.src;
    });
} else {
    // Fallback for browsers that don't support lazy loading
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// Debounce function for performance
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// ==================== ERROR HANDLING ====================
window.addEventListener('error', (event) => {
    console.error('Application error:', event.error);
    tg.showAlert('Произошла ошибка. Пожалуйста, попробуйте обновить страницу.');
});

// Handle offline/online events
window.addEventListener('offline', () => {
    tg.showAlert('Отсутствует подключение к интернету');
});

window.addEventListener('online', () => {
    tg.showPopup({
        title: 'Подключение восстановлено',
        message: 'Вы снова онлайн',
        buttons: [{ type: 'ok' }]
    });
});

// ==================== INITIALIZATION ====================
const init = () => {
    // Load saved cart
    loadCart();
    
    // Initialize back button state
    updateBackButton();
    
    // Set up scroll animations
    observeElements();
    
    // Update payment info initially
    updatePaymentInfo();
    
    // Update address field initially
    updateAddressField();
    
    // Log app ready
    console.log('Bakery App initialized successfully');
    
    // Notify Telegram that app is ready
    tg.ready();
};

// Start the app
init();

// ==================== UTILITY FUNCTIONS ====================

// Format price
const formatPrice = (price) => {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0
    }).format(price);
};

// Get product by ID
const getProduct = (id) => {
    return products.find(p => p.id === id);
};

// Calculate delivery cost
const getDeliveryCost = () => {
    const total = calculateTotal();
    const FREE_DELIVERY_THRESHOLD = 1500;
    const DELIVERY_COST = 250;
    
    if (deliveryType === 'pickup') return 0;
    return total >= FREE_DELIVERY_THRESHOLD ? 0 : DELIVERY_COST;
};

// Update cart total with delivery
const updateCartTotalWithDelivery = () => {
    const subtotal = calculateTotal();
    const delivery = getDeliveryCost();
    const total = subtotal + delivery;
    
    return {
        subtotal,
        delivery,
        total
    };
};

// Export for debugging (remove in production)
if (typeof window !== 'undefined') {
    window.bakeryApp = {
        cart,
        products,
        navigateTo,
        addToCart,
        clearCart: () => {
            cart = [];
            updateCartView();
        }
    };
}

console.log('🥐 Bakery Telegram Mini App loaded successfully!');
