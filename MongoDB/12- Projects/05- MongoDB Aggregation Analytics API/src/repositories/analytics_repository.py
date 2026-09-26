"""Repository for MongoDB aggregation analytics queries."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pymongo.collection import Collection

from database.connection import get_database


def get_orders_collection() -> Collection:
    """Return the orders collection used by analytics queries."""
    return get_database()["orders"]


def sales_by_category(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Aggregate order revenue and item volume by product category."""
    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.category",
                "order_count": {"$addToSet": "$_id"},
                "item_count": {"$sum": "$items.quantity"},
                "revenue": {
                    "$sum": {
                        "$multiply": [
                            "$items.quantity",
                            "$items.unit_price",
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "order_count": {"$size": "$order_count"},
                "item_count": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"revenue": -1, "category": 1}},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def sales_by_period(
    *,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "month",
) -> list[dict[str, Any]]:
    """Aggregate revenue and order count by calendar period."""
    unit_map = {
        "day": "day",
        "week": "week",
        "month": "month",
        "quarter": "quarter",
        "year": "year",
    }

    normalized_granularity = granularity.strip().lower()

    if normalized_granularity not in unit_map:
        raise ValueError(
            "granularity must be one of: day, week, month, quarter, year.",
        )

    pipeline: Sequence[dict[str, Any]] = [
        {
            "$match": {
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date,
                },
                "status": {
                    "$in": [
                        "confirmed",
                        "processing",
                        "shipped",
                        "delivered",
                    ],
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$created_at",
                        "unit": unit_map[normalized_granularity],
                        "timezone": "UTC",
                    }
                },
                "order_count": {"$sum": 1},
                "revenue": {"$sum": "$subtotal"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "period": "$_id",
                "order_count": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"period": 1}},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def top_products(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return the highest-revenue products for the selected period."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.name"},
                "quantity_sold": {"$sum": "$items.quantity"},
                "revenue": {
                    "$sum": {
                        "$multiply": [
                            "$items.quantity",
                            "$items.unit_price",
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "product_id": {"$toString": "$_id"},
                "product_name": 1,
                "quantity_sold": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"revenue": -1, "quantity_sold": -1}},
        {"$limit": limit},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def customer_analytics(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Aggregate order count and spending by customer."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {
            "$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1},
                "total_spend": {"$sum": "$subtotal"},
                "average_order_value": {"$avg": "$subtotal"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "customer_id": {"$toString": "$_id"},
                "order_count": 1,
                "total_spend": 1,
                "average_order_value": 1,
            }
        },
        {"$sort": {"total_spend": -1}},
        {"$limit": limit},
    ]

    return list(get_orders_collection().aggregate(pipeline))

"""Repository for MongoDB aggregation analytics queries."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pymongo.collection import Collection

from database.connection import get_database


def get_orders_collection() -> Collection:
    """Return the orders collection used by analytics queries."""
    return get_database()["orders"]


def sales_by_category(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Aggregate order revenue and item volume by product category."""
    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.category",
                "order_count": {"$addToSet": "$_id"},
                "item_count": {"$sum": "$items.quantity"},
                "revenue": {
                    "$sum": {
                        "$multiply": [
                            "$items.quantity",
                            "$items.unit_price",
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "order_count": {"$size": "$order_count"},
                "item_count": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"revenue": -1, "category": 1}},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def sales_by_period(
    *,
    start_date: datetime,
    end_date: datetime,
    granularity: str = "month",
) -> list[dict[str, Any]]:
    """Aggregate revenue and order count by calendar period."""
    unit_map = {
        "day": "day",
        "week": "week",
        "month": "month",
        "quarter": "quarter",
        "year": "year",
    }

    normalized_granularity = granularity.strip().lower()

    if normalized_granularity not in unit_map:
        raise ValueError(
            "granularity must be one of: day, week, month, quarter, year.",
        )

    pipeline: Sequence[dict[str, Any]] = [
        {
            "$match": {
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date,
                },
                "status": {
                    "$in": [
                        "confirmed",
                        "processing",
                        "shipped",
                        "delivered",
                    ],
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$created_at",
                        "unit": unit_map[normalized_granularity],
                        "timezone": "UTC",
                    }
                },
                "order_count": {"$sum": 1},
                "revenue": {"$sum": "$subtotal"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "period": "$_id",
                "order_count": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"period": 1}},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def top_products(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return the highest-revenue products for the selected period."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.name"},
                "quantity_sold": {"$sum": "$items.quantity"},
                "revenue": {
                    "$sum": {
                        "$multiply": [
                            "$items.quantity",
                            "$items.unit_price",
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "product_id": {"$toString": "$_id"},
                "product_name": 1,
                "quantity_sold": 1,
                "revenue": 1,
            }
        },
        {"$sort": {"revenue": -1, "quantity_sold": -1}},
        {"$limit": limit},
    ]

    return list(get_orders_collection().aggregate(pipeline))


def customer_analytics(
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Aggregate order count and spending by customer."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    match: dict[str, Any] = {
        "status": {"$in": ["confirmed", "processing", "shipped", "delivered"]},
    }

    created_at: dict[str, Any] = {}

    if start_date is not None:
        created_at["$gte"] = start_date

    if end_date is not None:
        created_at["$lt"] = end_date

    if created_at:
        match["created_at"] = created_at

    pipeline: Sequence[dict[str, Any]] = [
        {"$match": match},
        {
            "$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1},
                "total_spend": {"$sum": "$subtotal"},
                "average_order_value": {"$avg": "$subtotal"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "customer_id": {"$toString": "$_id"},
                "order_count": 1,
                "total_spend": 1,
                "average_order_value": 1,
            }
        },
        {"$sort": {"total_spend": -1}},
        {"$limit": limit},
    ]

    return list(get_orders_collection().aggregate(pipeline))