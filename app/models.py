from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeliveryType(str, enum.Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"


class PaymentType(str, enum.Enum):
    CASH = "cash"
    ONLINE = "online"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(Integer, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_address = Column(Text, nullable=True)  # null for pickup
    delivery_type = Column(Enum(DeliveryType), nullable=False)
    payment_type = Column(Enum(PaymentType), nullable=False)
    comment = Column(Text, nullable=True)
    
    subtotal = Column(Float, nullable=False)  # products total
    delivery_cost = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_id = Column(String(255), nullable=True)  # external payment system ID
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to order items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)  # snapshot at order time
    product_price = Column(Float, nullable=False)  # snapshot at order time
    quantity = Column(Integer, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")


