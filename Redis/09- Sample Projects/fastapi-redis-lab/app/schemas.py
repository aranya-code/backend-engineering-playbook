"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


# Product Schemas

class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Schema for product list response."""
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int


# Cart Schemas

class CartItemAdd(BaseModel):
    """Schema for adding item to cart."""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartItem(BaseModel):
    """Schema for cart item."""
    product_id: int
    product_name: str
    price: float
    quantity: int
    subtotal: float


class CartResponse(BaseModel):
    """Schema for cart response."""
    user_id: int
    items: List[CartItem]
    total_items: int
    total_price: float


# Auth Schemas

class OTPRequest(BaseModel):
    """Schema for OTP request."""
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")


class OTPVerify(BaseModel):
    """Schema for OTP verification."""
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{9,14}$")
    otp: str = Field(..., min_length=6, max_length=6)


class LoginResponse(BaseModel):
    """Schema for login response."""
    user_id: int
    phone: str
    message: str


# Analytics Schemas

class LeaderboardItem(BaseModel):
    """Schema for leaderboard item."""
    product_id: int
    product_name: str
    views: int


class LeaderboardResponse(BaseModel):
    """Schema for leaderboard response."""
    top_products: List[LeaderboardItem]
    total: int


class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    unique_visitors: int
    total_views: int
    daily_active_users: int
    top_products: List[LeaderboardItem]


# Pub/Sub Schemas

class PublishMessage(BaseModel):
    """Schema for publishing message."""
    channel: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PublishResponse(BaseModel):
    """Schema for publish response."""
    channel: str
    subscribers: int
    message: str


# Stream Schemas

class StreamEvent(BaseModel):
    """Schema for stream event."""
    event_type: str = Field(..., min_length=1)
    data: Dict[str, Any]


class StreamResponse(BaseModel):
    """Schema for stream response."""
    stream_key: str
    event_id: str
    event_type: str
    message: str


# Cache Schemas

class CacheResponse(BaseModel):
    """Schema for cache response."""
    message: str
    keys_deleted: int


# Generic Responses

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
