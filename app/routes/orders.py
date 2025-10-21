from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session # Removed joinedload as it's not strictly needed for this change
from aiogram import Bot # Import Bot for Telegram notifications

from ..database import get_db
from .. import models, schemas
from ..settings import settings
from ..yookassa import get_yookassa_client


telegram_bot = None
if settings.bot_token:
    telegram_bot = Bot(token=settings.bot_token)
    print("[DEBUG] Telegram Bot client initialized in orders.py")
else:
    print("[WARNING] BOT_TOKEN is not configured in settings. Telegram notifications will not work from orders.py.")


router = APIRouter(prefix="/api/orders", tags=["orders"])


def get_telegram_user_id(x_telegram_id: Optional[str] = Header(None, alias="X-Telegram-Id")) -> int:
    """Extract Telegram user ID from header."""
    if x_telegram_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Telegram-Id header missing")
    try:
        return int(x_telegram_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Telegram-Id header")


def calculate_delivery_cost(delivery_type: str, subtotal: float) -> float:
    """Calculate delivery cost based on type and order amount."""
    if delivery_type == "pickup":
        return 0.0
    
    # Free delivery for orders over 1500 rubles
    FREE_DELIVERY_THRESHOLD = 1500.0
    DELIVERY_COST = 500.0
    
    if subtotal >= FREE_DELIVERY_THRESHOLD:
        return 0.0
    
    return DELIVERY_COST


@router.post("/", response_model=schemas.OrderOut)
async def create_order( # Changed to async
    order_data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    telegram_user_id: int = Depends(get_telegram_user_id)
):
    print(f"[ORDER] Creating order for user {telegram_user_id}")
    print(f"[ORDER] Order data: {order_data.dict()}")
    """Create a new order with delivery calculation."""
    
    # Validate delivery address requirement
    if order_data.delivery_type == "delivery" and not order_data.customer_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Address is required for delivery"
        )
    
    # Calculate subtotal
    subtotal = 0.0
    order_items = []
    
    for item_data in order_data.items:
        # Get product details
        product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item_data.product_id} not found"
            )
        
        item_total = product.price * item_data.quantity
        subtotal += item_total
        
        # Prepare order item data
        order_items.append({
            "product_id": product.id,
            "product_name": product.title,
            "product_price": product.price,
            "quantity": item_data.quantity
        })
    
    # Calculate delivery cost
    delivery_cost = calculate_delivery_cost(order_data.delivery_type, subtotal)
    total_amount = subtotal + delivery_cost
    
    # Create order
    order = models.Order(
        telegram_user_id=telegram_user_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        customer_address=order_data.customer_address,
        delivery_type=order_data.delivery_type,
        payment_type=order_data.payment_type,
        comment=order_data.comment,
        subtotal=subtotal,
        delivery_cost=delivery_cost,
        total_amount=total_amount,
        status=models.OrderStatus.PENDING
    )
    
    db.add(order)
    db.flush()  # Get the order ID
    
    # Create order items
    for item_data in order_items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            product_price=item_data["product_price"],
            quantity=item_data["quantity"]
        )
        db.add(order_item)
    
    db.commit()
    db.refresh(order)

    print(f"[ORDER] Order created successfully with ID: {order.id}")

    # Send Telegram notification for cash orders to admin
    if order.payment_type == models.PaymentType.CASH and telegram_bot and settings.admin_id:
        try:
            order_details = f"<b>🔔 Новый заказ №{order.id} (Наличные)</b>\n\n" \
                            f"<b>Клиент:</b> {order.customer_name}\n" \
                            f"<b>Телефон:</b> {order.customer_phone}\n" \
                            f"<b>Тип доставки:</b> {'Доставка' if order.delivery_type == 'delivery' else 'Самовывоз'}\n"
            if order.delivery_type == 'delivery':
                order_details += f"<b>Адрес:</b> {order.customer_address}\n"
            if order.comment:
                order_details += f"<b>Комментарий:</b> {order.comment}\n"
            
            order_details += "\n<b>Состав заказа:</b>\n"
            for item_data in order_items: # Use the list constructed earlier
                order_details += f"- {item_data['product_name']} x {item_data['quantity']} ({item_data['product_price']:.2f} ₽/шт)\n"
            
            order_details += f"\n<b>Подытог:</b> {order.subtotal:.2f} ₽\n" \
                             f"<b>Доставка:</b> {order.delivery_cost:.2f} ₽\n" \
                             f"<b>Итого к оплате:</b> {order.total_amount:.2f} ₽\n" \
                             f"<b>Статус:</b> {order.status.value}"

            await telegram_bot.send_message(
                chat_id=settings.admin_id,
                text=order_details,
                parse_mode="HTML"
            )
            print(f"[ORDER] Telegram notification sent for order {order.id} to admin {settings.admin_id}")
        except Exception as e:
            print(f"[ERROR] Failed to send Telegram notification for order {order.id}: {e}")

    return order


@router.get("/", response_model=list[schemas.OrderOut])
def get_user_orders(
    db: Session = Depends(get_db),
    telegram_user_id: int = Depends(get_telegram_user_id)
):
    """Get orders for the current user."""
    orders = db.query(models.Order).filter(
        models.Order.telegram_user_id == telegram_user_id
    ).order_by(models.Order.created_at.desc()).all()
    
    return orders


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    telegram_user_id: int = Depends(get_telegram_user_id)
):
    """Get a specific order by ID."""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.telegram_user_id == telegram_user_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.post("/{order_id}/payment", response_model=schemas.PaymentOut)
async def create_payment(
    order_id: int,
    payment_data: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    telegram_user_id: int = Depends(get_telegram_user_id)
):
    """Create payment for an order using YooKassa."""
    
    # Get order
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.telegram_user_id == telegram_user_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.payment_type != models.PaymentType.ONLINE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not configured for online payment"
        )
    
    if order.status != models.OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not in pending status"
        )
    
    try:
        print(f"[DEBUG] Creating payment for order {order.id}, amount: {order.total_amount}")
        print(f"[DEBUG] Payment success URL: {settings.payment_success_url}")

        # Create payment with YooKassa
        yookassa = get_yookassa_client()
        print(f"[DEBUG] YooKassa client obtained: {yookassa}")

        payment_response = await yookassa.create_payment(
            amount=order.total_amount,
            description=f"Order #{order.id} - Bakery",
            return_url=settings.payment_success_url,
            metadata={
                "order_id": str(order.id),
                "telegram_user_id": str(telegram_user_id)
            }
        )

        print(f"[DEBUG] Payment response: {payment_response}")
        print(f"[DEBUG] Payment URL: {payment_response.get('confirmation', {}).get('confirmation_url')}")

        if not payment_response.get('confirmation', {}).get('confirmation_url'):
            print("[ERROR] No confirmation URL in payment response!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment URL not received from YooKassa"
            )
        
        # Update order with payment ID
        order.payment_id = payment_response["id"]
        db.commit()
        
        return schemas.PaymentOut(
            payment_id=payment_response["id"],
            payment_url=payment_response["confirmation"]["confirmation_url"],
            status=payment_response["status"],
            amount=order.total_amount
        )
    
    except ValueError as e:
        # Handle misconfiguration of YooKassa credentials
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Payment service is not configured"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post("/webhook/payment")
async def payment_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Webhook for YooKassa payment status updates."""
    
    try:
        # Extract payment information from webhook
        payment_id = webhook_data.get("object", {}).get("id")
        payment_status = webhook_data.get("object", {}).get("status")
        
        if not payment_id or not payment_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing payment_id or status in webhook data"
            )
        
        # Find order by payment ID
        order = db.query(models.Order).filter(
            models.Order.payment_id == payment_id
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found for payment"
            )
        
        # Update order status based on payment status
        if payment_status == "succeeded":
            order.status = models.OrderStatus.PAID
        elif payment_status == "canceled":
            order.status = models.OrderStatus.CANCELLED
        elif payment_status in ["waiting_for_capture", "processing"]:
            order.status = models.OrderStatus.PROCESSING
        
        db.commit()
        
        return {
            "status": "ok", 
            "order_id": order.id, 
            "new_status": order.status.value,
            "payment_status": payment_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}"
        )
