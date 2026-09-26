"""Pydantic schemas for MongoDB aggregation analytics responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SalesByCategory(BaseModel):
    """Aggregated sales metrics grouped by product category."""

    model_config = ConfigDict(extra="forbid")

    category: str
    order_count: int = Field(ge=0)
    item_count: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class SalesByPeriod(BaseModel):
    """Aggregated sales metrics grouped by a time period."""

    model_config = ConfigDict(extra="forbid")

    period: datetime
    order_count: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class TopProduct(BaseModel):
    """Product-level aggregation result ordered by sales performance."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_name: str
    quantity_sold: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class CustomerAnalytics(BaseModel):
    """Customer-level order and revenue aggregation."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str
    order_count: int = Field(ge=0)
    total_spend: Decimal = Field(ge=0)
    average_order_value: Decimal = Field(ge=0)


class AnalyticsResponse(BaseModel):
    """Container for analytics results returned by the API."""

    model_config = ConfigDict(extra="forbid")

    data: list[dict]
    total: int = Field(ge=0)

"""Pydantic schemas for MongoDB aggregation analytics responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SalesByCategory(BaseModel):
    """Aggregated sales metrics grouped by product category."""

    model_config = ConfigDict(extra="forbid")

    category: str
    order_count: int = Field(ge=0)
    item_count: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class SalesByPeriod(BaseModel):
    """Aggregated sales metrics grouped by a time period."""

    model_config = ConfigDict(extra="forbid")

    period: datetime
    order_count: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class TopProduct(BaseModel):
    """Product-level aggregation result ordered by sales performance."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    product_name: str
    quantity_sold: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class CustomerAnalytics(BaseModel):
    """Customer-level order and revenue aggregation."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str
    order_count: int = Field(ge=0)
    total_spend: Decimal = Field(ge=0)
    average_order_value: Decimal = Field(ge=0)


class AnalyticsResponse(BaseModel):
    """Container for analytics results returned by the API."""

    model_config = ConfigDict(extra="forbid")

    data: list[dict]
    total: int = Field(ge=0)