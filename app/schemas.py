from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator


class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    image: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Order schemas
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    delivery_type: str  # "delivery" or "pickup"
    payment_type: str  # "cash" or "online"
    comment: Optional[str] = None
    items: List[OrderItemCreate]

    @field_validator("delivery_type")
    @classmethod
    def validate_delivery_type(cls, v: str) -> str:
        if v not in ["delivery", "pickup"]:
            raise ValueError("delivery_type must be 'delivery' or 'pickup'")
        return v

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, v: str) -> str:
        if v not in ["cash", "online"]:
            raise ValueError("payment_type must be 'cash' or 'online'")
        return v


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    telegram_user_id: int
    customer_name: str
    customer_phone: str
    customer_address: Optional[str] = None
    delivery_type: str
    payment_type: str
    comment: Optional[str] = None
    subtotal: float
    delivery_cost: float
    total_amount: float
    status: str
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str = "card"  # for future expansion


class PaymentOut(BaseModel):
    payment_id: str
    payment_url: Optional[str] = None
    status: str
    amount: float


