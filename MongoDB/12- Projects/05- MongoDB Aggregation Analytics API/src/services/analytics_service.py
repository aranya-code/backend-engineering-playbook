"""Service layer for MongoDB aggregation analytics."""

from __future__ import annotations

from datetime import datetime

from repositories.analytics_repository import (
    customer_analytics,
    sales_by_category,
    sales_by_period,
    top_products,
)


def get_sales_by_category(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """Return aggregated sales metrics grouped by product category."""
    return sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )


def get_sales_by_period(
    *,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "month",
) -> list[dict]:
    """Return aggregated sales metrics grouped by calendar period."""
    if start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date.")

    return sales_by_period(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


def get_top_products(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
) -> list[dict]:
    """Return the highest-revenue products for the selected period."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return top_products(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


def get_customer_analytics(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return customer-level order and spending analytics."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return customer_analytics(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

"""Service layer for MongoDB aggregation analytics."""

from __future__ import annotations

from datetime import datetime

from repositories.analytics_repository import (
    customer_analytics,
    sales_by_category,
    sales_by_period,
    top_products,
)


def get_sales_by_category(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """Return aggregated sales metrics grouped by product category."""
    return sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )


def get_sales_by_period(
    *,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "month",
) -> list[dict]:
    """Return aggregated sales metrics grouped by calendar period."""
    if start_date >= end_date:
        raise ValueError("start_date must be earlier than end_date.")

    return sales_by_period(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )


def get_top_products(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
) -> list[dict]:
    """Return the highest-revenue products for the selected period."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return top_products(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


def get_customer_analytics(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return customer-level order and spending analytics."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return customer_analytics(
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )