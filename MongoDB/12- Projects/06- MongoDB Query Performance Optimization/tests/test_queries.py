"""Tests for MongoDB query performance optimization examples."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.queries.optimized import (
    aggregate_customer_sales,
    count_recent_orders,
    find_recent_orders,
    find_recent_orders_by_date,
)


def test_find_recent_orders_builds_optimized_query() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter(
        [
            {
                "_id": "order-1",
                "customer_id": "customer-1",
                "status": "completed",
            }
        ]
    )

    result = find_recent_orders(
        collection,
        "customer-1",
        limit=25,
    )

    collection.find.assert_called_once_with(
        {
            "customer_id": "customer-1",
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
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(25)
    assert len(result) == 1


def test_find_recent_orders_by_date_applies_range_projection_sort_and_limit() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 2, 1, tzinfo=timezone.utc)

    result = find_recent_orders_by_date(
        collection,
        start_date=start_date,
        end_date=end_date,
        limit=100,
    )

    collection.find.assert_called_once_with(
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
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(100)
    assert result == []


def test_count_recent_orders_uses_server_side_count() -> None:
    collection = MagicMock()
    collection.count_documents.return_value = 12

    result = count_recent_orders(
        collection,
        customer_id="customer-1",
        days=30,
    )

    collection.count_documents.assert_called_once()
    query = collection.count_documents.call_args.args[0]

    assert query["customer_id"] == "customer-1"
    assert query["status"] == "completed"
    assert "$gte" in query["created_at"]
    assert result == 12


def test_aggregate_customer_sales_filters_before_grouping() -> None:
    collection = MagicMock()
    collection.aggregate.return_value = iter(
        [
            {
                "customer_id": "customer-1",
                "order_count": 10,
                "total_sales": 1500.0,
                "average_order_value": 150.0,
            }
        ]
    )

    result = aggregate_customer_sales(
        collection,
        customer_id="customer-1",
    )

    pipeline = collection.aggregate.call_args.args[0]

    assert pipeline[0] == {
        "$match": {
            "customer_id": "customer-1",
            "status": "completed",
        }
    }
    assert pipeline[1]["$group"]["_id"] == "$customer_id"
    assert pipeline[2]["$project"]["_id"] == 0
    collection.aggregate.assert_called_once_with(
        pipeline,
        allowDiskUse=True,
    )
    assert result[0]["order_count"] == 10

"""Tests for MongoDB query performance optimization examples."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.queries.optimized import (
    aggregate_customer_sales,
    count_recent_orders,
    find_recent_orders,
    find_recent_orders_by_date,
)


def test_find_recent_orders_builds_optimized_query() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter(
        [
            {
                "_id": "order-1",
                "customer_id": "customer-1",
                "status": "completed",
            }
        ]
    )

    result = find_recent_orders(
        collection,
        "customer-1",
        limit=25,
    )

    collection.find.assert_called_once_with(
        {
            "customer_id": "customer-1",
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
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(25)
    assert len(result) == 1


def test_find_recent_orders_by_date_applies_range_projection_sort_and_limit() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 2, 1, tzinfo=timezone.utc)

    result = find_recent_orders_by_date(
        collection,
        start_date=start_date,
        end_date=end_date,
        limit=100,
    )

    collection.find.assert_called_once_with(
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
    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(100)
    assert result == []


def test_count_recent_orders_uses_server_side_count() -> None:
    collection = MagicMock()
    collection.count_documents.return_value = 12

    result = count_recent_orders(
        collection,
        customer_id="customer-1",
        days=30,
    )

    collection.count_documents.assert_called_once()
    query = collection.count_documents.call_args.args[0]

    assert query["customer_id"] == "customer-1"
    assert query["status"] == "completed"
    assert "$gte" in query["created_at"]
    assert result == 12


def test_aggregate_customer_sales_filters_before_grouping() -> None:
    collection = MagicMock()
    collection.aggregate.return_value = iter(
        [
            {
                "customer_id": "customer-1",
                "order_count": 10,
                "total_sales": 1500.0,
                "average_order_value": 150.0,
            }
        ]
    )

    result = aggregate_customer_sales(
        collection,
        customer_id="customer-1",
    )

    pipeline = collection.aggregate.call_args.args[0]

    assert pipeline[0] == {
        "$match": {
            "customer_id": "customer-1",
            "status": "completed",
        }
    }
    assert pipeline[1]["$group"]["_id"] == "$customer_id"
    assert pipeline[2]["$project"]["_id"] == 0
    collection.aggregate.assert_called_once_with(
        pipeline,
        allowDiskUse=True,
    )
    assert result[0]["order_count"] == 10