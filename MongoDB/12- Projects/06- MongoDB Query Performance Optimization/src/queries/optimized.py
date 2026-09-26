"""Optimized MongoDB query examples for performance comparison and benchmarking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection


def find_recent_orders(
    collection: Collection[dict[str, Any]],
    customer_id: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fetch recent customer orders using a compound-index-friendly query."""
    cursor = (
        collection.find(
            {
                "customer_id": customer_id,
                "status": "completed",
            },
            {
                "_id": 1,
                "customer_id": 1,
                "status": 1,
                "total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    return list(cursor)


def find_recent_orders_by_date(
    collection: Collection[dict[str, Any]],
    *,
    start_date: datetime,
    end_date: datetime,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch orders in a bounded date range with projection and limit."""
    cursor = (
        collection.find(
            {
                "status": "completed",
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date,
                },
            },
            {
                "_id": 1,
                "customer_id": 1,
                "status": 1,
                "total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    return list(cursor)


def count_recent_orders(
    collection: Collection[dict[str, Any]],
    *,
    customer_id: str,
    days: int = 30,
) -> int:
    """Count recent completed orders using a server-side count operation."""
    cutoff = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    # The query is intentionally selective so the matching index can
    # reduce the amount of data examined.
    return collection.count_documents(
        {
            "customer_id": customer_id,
            "status": "completed",
            "created_at": {"$gte": cutoff},
        }
    )


def aggregate_customer_sales(
    collection: Collection[dict[str, Any]],
    *,
    customer_id: str,
) -> list[dict[str, Any]]:
    """Aggregate customer sales after filtering the working set early."""
    pipeline = [
        {
            "$match": {
                "customer_id": customer_id,
                "status": "completed",
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1},
                "total_sales": {"$sum": "$total"},
                "average_order_value": {"$avg": "$total"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "customer_id": "$_id",
                "order_count": 1,
                "total_sales": 1,
                "average_order_value": 1,
            }
        },
    ]

    return list(collection.aggregate(pipeline, allowDiskUse=True))

"""Optimized MongoDB query examples for performance comparison and benchmarking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.collection import Collection


def find_recent_orders(
    collection: Collection[dict[str, Any]],
    customer_id: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Fetch recent customer orders using a compound-index-friendly query."""
    cursor = (
        collection.find(
            {
                "customer_id": customer_id,
                "status": "completed",
            },
            {
                "_id": 1,
                "customer_id": 1,
                "status": 1,
                "total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    return list(cursor)


def find_recent_orders_by_date(
    collection: Collection[dict[str, Any]],
    *,
    start_date: datetime,
    end_date: datetime,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch orders in a bounded date range with projection and limit."""
    cursor = (
        collection.find(
            {
                "status": "completed",
                "created_at": {
                    "$gte": start_date,
                    "$lt": end_date,
                },
            },
            {
                "_id": 1,
                "customer_id": 1,
                "status": 1,
                "total": 1,
                "created_at": 1,
            },
        )
        .sort("created_at", -1)
        .limit(limit)
    )

    return list(cursor)


def count_recent_orders(
    collection: Collection[dict[str, Any]],
    *,
    customer_id: str,
    days: int = 30,
) -> int:
    """Count recent completed orders using a server-side count operation."""
    cutoff = datetime.now(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    # The query is intentionally selective so the matching index can
    # reduce the amount of data examined.
    return collection.count_documents(
        {
            "customer_id": customer_id,
            "status": "completed",
            "created_at": {"$gte": cutoff},
        }
    )


def aggregate_customer_sales(
    collection: Collection[dict[str, Any]],
    *,
    customer_id: str,
) -> list[dict[str, Any]]:
    """Aggregate customer sales after filtering the working set early."""
    pipeline = [
        {
            "$match": {
                "customer_id": customer_id,
                "status": "completed",
            }
        },
        {
            "$group": {
                "_id": "$customer_id",
                "order_count": {"$sum": 1},
                "total_sales": {"$sum": "$total"},
                "average_order_value": {"$avg": "$total"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "customer_id": "$_id",
                "order_count": 1,
                "total_sales": 1,
                "average_order_value": 1,
            }
        },
    ]

    return list(collection.aggregate(pipeline, allowDiskUse=True))