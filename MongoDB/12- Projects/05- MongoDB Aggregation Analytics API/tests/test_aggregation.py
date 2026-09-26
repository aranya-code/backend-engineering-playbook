"""Tests for MongoDB aggregation repository and service behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from bson import Decimal128, ObjectId

from repositories import analytics_repository
from services import analytics_service


class FakeCollection:
    """Capture aggregation pipelines without requiring a MongoDB server."""

    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []
        self.pipelines: list[list[dict[str, Any]]] = []

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Record a pipeline and return deterministic test results."""
        self.pipelines.append(pipeline)
        return self.documents


@pytest.fixture
def fake_collection(monkeypatch: pytest.MonkeyPatch) -> FakeCollection:
    """Replace the repository collection with an in-memory fake."""
    collection = FakeCollection(
        documents=[
            {
                "category": "Electronics",
                "order_count": 4,
                "item_count": 7,
                "revenue": Decimal128("499.93"),
            },
        ],
    )

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    return collection


@pytest.fixture
def sample_dates() -> tuple[datetime, datetime]:
    """Return a deterministic UTC analytics window."""
    return (
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 2, 1, tzinfo=timezone.utc),
    )


def test_sales_by_category_builds_expected_pipeline(
    fake_collection: FakeCollection,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify category aggregation filtering, grouping, and sorting."""
    start_date, end_date = sample_dates

    result = analytics_repository.sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )

    assert result == [
        {
            "category": "Electronics",
            "order_count": 4,
            "item_count": 7,
            "revenue": Decimal128("499.93"),
        },
    ]

    pipeline = fake_collection.pipelines[0]

    assert pipeline[0] == {
        "$match": {
            "status": {
                "$in": [
                    "confirmed",
                    "processing",
                    "shipped",
                    "delivered",
                ],
            },
            "created_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        },
    }

    assert pipeline[1] == {"$unwind": "$items"}
    assert "$group" in pipeline[2]
    assert pipeline[-1] == {"$sort": {"revenue": -1, "category": 1}}


def test_sales_by_category_without_dates_omits_date_filter(
    fake_collection: FakeCollection,
) -> None:
    """Verify that date filtering is optional for category analytics."""
    analytics_repository.sales_by_category()

    match_stage = fake_collection.pipelines[0][0]["$match"]

    assert "created_at" not in match_stage
    assert match_stage["status"]["$in"] == [
        "confirmed",
        "processing",
        "shipped",
        "delivered",
    ]


@pytest.mark.parametrize(
    ("granularity", "expected_unit"),
    [
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("quarter", "quarter"),
        ("year", "year"),
    ],
)
def test_sales_by_period_uses_requested_granularity(
    monkeypatch: pytest.MonkeyPatch,
    granularity: str,
    expected_unit: str,
) -> None:
    """Verify that period aggregation maps supported granularities correctly."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    analytics_repository.sales_by_period(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )

    date_trunc = collection.pipelines[0][1]["$group"]["_id"]["$dateTrunc"]

    assert date_trunc == {
        "date": "$created_at",
        "unit": expected_unit,
        "timezone": "UTC",
    }


def test_sales_by_period_rejects_invalid_granularity() -> None:
    """Verify unsupported aggregation granularities fail fast."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 2, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="granularity must be one of"):
        analytics_repository.sales_by_period(
            start_date=start_date,
            end_date=end_date,
            granularity="hour",
        )


def test_sales_by_period_rejects_reversed_date_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the service rejects an invalid analytics time range."""
    with pytest.raises(
        ValueError,
        match="start_date must be earlier than end_date",
    ):
        analytics_service.get_sales_by_period(
            start_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )


def test_top_products_applies_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify top-product aggregation applies the requested result limit."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.top_products(limit=5)

    pipeline = collection.pipelines[0]

    assert pipeline[-1] == {"$limit": 5}
    assert pipeline[-2] == {
        "$sort": {
            "revenue": -1,
            "quantity_sold": -1,
        },
    }


def test_top_products_rejects_non_positive_limit() -> None:
    """Verify invalid product limits fail before database access."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_repository.top_products(limit=0)


def test_customer_analytics_groups_by_customer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify customer analytics uses customer_id as its grouping key."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.customer_analytics(limit=20)

    group_stage = collection.pipelines[0][1]["$group"]

    assert group_stage["_id"] == "$customer_id"
    assert group_stage["order_count"] == {"$sum": 1}
    assert group_stage["total_spend"] == {"$sum": "$subtotal"}
    assert group_stage["average_order_value"] == {"$avg": "$subtotal"}


def test_customer_analytics_rejects_non_positive_limit() -> None:
    """Verify invalid customer limits fail before database access."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_repository.customer_analytics(limit=0)


def test_service_delegates_category_analytics(
    monkeypatch: pytest.MonkeyPatch,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify the service delegates category analytics to the repository."""
    start_date, end_date = sample_dates
    expected = [
        {
            "category": "Electronics",
            "order_count": 3,
            "item_count": 5,
            "revenue": Decimal("299.95"),
        },
    ]

    def fake_sales_by_category(
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        assert start_date is not None
        assert end_date is not None
        return expected

    monkeypatch.setattr(
        analytics_service,
        "sales_by_category",
        fake_sales_by_category,
    )

    result = analytics_service.get_sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )

    assert result == expected


def test_service_rejects_invalid_top_product_limit() -> None:
    """Verify service-level validation prevents invalid limits."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_service.get_top_products(limit=0)


def test_service_rejects_invalid_customer_limit() -> None:
    """Verify service-level validation prevents invalid limits."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_service.get_customer_analytics(limit=0)


def test_customer_analytics_applies_date_filter(
    monkeypatch: pytest.MonkeyPatch,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify customer aggregation applies an optional date range."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    start_date, end_date = sample_dates

    analytics_repository.customer_analytics(
        start_date=start_date,
        end_date=end_date,
        limit=10,
    )

    match_stage = collection.pipelines[0][0]["$match"]

    assert match_stage["created_at"] == {
        "$gte": start_date,
        "$lt": end_date,
    }


def test_top_products_converts_product_id_to_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify product identifiers are normalized for API responses."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.top_products(limit=3)

    project_stage = collection.pipelines[0][3]["$project"]

    assert project_stage["product_id"] == {"$toString": "$_id"}

"""Tests for MongoDB aggregation repository and service behavior."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from bson import Decimal128, ObjectId

from repositories import analytics_repository
from services import analytics_service


class FakeCollection:
    """Capture aggregation pipelines without requiring a MongoDB server."""

    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or []
        self.pipelines: list[list[dict[str, Any]]] = []

    def aggregate(self, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Record a pipeline and return deterministic test results."""
        self.pipelines.append(pipeline)
        return self.documents


@pytest.fixture
def fake_collection(monkeypatch: pytest.MonkeyPatch) -> FakeCollection:
    """Replace the repository collection with an in-memory fake."""
    collection = FakeCollection(
        documents=[
            {
                "category": "Electronics",
                "order_count": 4,
                "item_count": 7,
                "revenue": Decimal128("499.93"),
            },
        ],
    )

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    return collection


@pytest.fixture
def sample_dates() -> tuple[datetime, datetime]:
    """Return a deterministic UTC analytics window."""
    return (
        datetime(2025, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 2, 1, tzinfo=timezone.utc),
    )


def test_sales_by_category_builds_expected_pipeline(
    fake_collection: FakeCollection,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify category aggregation filtering, grouping, and sorting."""
    start_date, end_date = sample_dates

    result = analytics_repository.sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )

    assert result == [
        {
            "category": "Electronics",
            "order_count": 4,
            "item_count": 7,
            "revenue": Decimal128("499.93"),
        },
    ]

    pipeline = fake_collection.pipelines[0]

    assert pipeline[0] == {
        "$match": {
            "status": {
                "$in": [
                    "confirmed",
                    "processing",
                    "shipped",
                    "delivered",
                ],
            },
            "created_at": {
                "$gte": start_date,
                "$lt": end_date,
            },
        },
    }

    assert pipeline[1] == {"$unwind": "$items"}
    assert "$group" in pipeline[2]
    assert pipeline[-1] == {"$sort": {"revenue": -1, "category": 1}}


def test_sales_by_category_without_dates_omits_date_filter(
    fake_collection: FakeCollection,
) -> None:
    """Verify that date filtering is optional for category analytics."""
    analytics_repository.sales_by_category()

    match_stage = fake_collection.pipelines[0][0]["$match"]

    assert "created_at" not in match_stage
    assert match_stage["status"]["$in"] == [
        "confirmed",
        "processing",
        "shipped",
        "delivered",
    ]


@pytest.mark.parametrize(
    ("granularity", "expected_unit"),
    [
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
        ("quarter", "quarter"),
        ("year", "year"),
    ],
)
def test_sales_by_period_uses_requested_granularity(
    monkeypatch: pytest.MonkeyPatch,
    granularity: str,
    expected_unit: str,
) -> None:
    """Verify that period aggregation maps supported granularities correctly."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 1, tzinfo=timezone.utc)

    analytics_repository.sales_by_period(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )

    date_trunc = collection.pipelines[0][1]["$group"]["_id"]["$dateTrunc"]

    assert date_trunc == {
        "date": "$created_at",
        "unit": expected_unit,
        "timezone": "UTC",
    }


def test_sales_by_period_rejects_invalid_granularity() -> None:
    """Verify unsupported aggregation granularities fail fast."""
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 2, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="granularity must be one of"):
        analytics_repository.sales_by_period(
            start_date=start_date,
            end_date=end_date,
            granularity="hour",
        )


def test_sales_by_period_rejects_reversed_date_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the service rejects an invalid analytics time range."""
    with pytest.raises(
        ValueError,
        match="start_date must be earlier than end_date",
    ):
        analytics_service.get_sales_by_period(
            start_date=datetime(2025, 2, 1, tzinfo=timezone.utc),
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )


def test_top_products_applies_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify top-product aggregation applies the requested result limit."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.top_products(limit=5)

    pipeline = collection.pipelines[0]

    assert pipeline[-1] == {"$limit": 5}
    assert pipeline[-2] == {
        "$sort": {
            "revenue": -1,
            "quantity_sold": -1,
        },
    }


def test_top_products_rejects_non_positive_limit() -> None:
    """Verify invalid product limits fail before database access."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_repository.top_products(limit=0)


def test_customer_analytics_groups_by_customer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify customer analytics uses customer_id as its grouping key."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.customer_analytics(limit=20)

    group_stage = collection.pipelines[0][1]["$group"]

    assert group_stage["_id"] == "$customer_id"
    assert group_stage["order_count"] == {"$sum": 1}
    assert group_stage["total_spend"] == {"$sum": "$subtotal"}
    assert group_stage["average_order_value"] == {"$avg": "$subtotal"}


def test_customer_analytics_rejects_non_positive_limit() -> None:
    """Verify invalid customer limits fail before database access."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_repository.customer_analytics(limit=0)


def test_service_delegates_category_analytics(
    monkeypatch: pytest.MonkeyPatch,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify the service delegates category analytics to the repository."""
    start_date, end_date = sample_dates
    expected = [
        {
            "category": "Electronics",
            "order_count": 3,
            "item_count": 5,
            "revenue": Decimal("299.95"),
        },
    ]

    def fake_sales_by_category(
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        assert start_date is not None
        assert end_date is not None
        return expected

    monkeypatch.setattr(
        analytics_service,
        "sales_by_category",
        fake_sales_by_category,
    )

    result = analytics_service.get_sales_by_category(
        start_date=start_date,
        end_date=end_date,
    )

    assert result == expected


def test_service_rejects_invalid_top_product_limit() -> None:
    """Verify service-level validation prevents invalid limits."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_service.get_top_products(limit=0)


def test_service_rejects_invalid_customer_limit() -> None:
    """Verify service-level validation prevents invalid limits."""
    with pytest.raises(ValueError, match="limit must be greater than zero"):
        analytics_service.get_customer_analytics(limit=0)


def test_customer_analytics_applies_date_filter(
    monkeypatch: pytest.MonkeyPatch,
    sample_dates: tuple[datetime, datetime],
) -> None:
    """Verify customer aggregation applies an optional date range."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    start_date, end_date = sample_dates

    analytics_repository.customer_analytics(
        start_date=start_date,
        end_date=end_date,
        limit=10,
    )

    match_stage = collection.pipelines[0][0]["$match"]

    assert match_stage["created_at"] == {
        "$gte": start_date,
        "$lt": end_date,
    }


def test_top_products_converts_product_id_to_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify product identifiers are normalized for API responses."""
    collection = FakeCollection()

    monkeypatch.setattr(
        analytics_repository,
        "get_orders_collection",
        lambda: collection,
    )

    analytics_repository.top_products(limit=3)

    project_stage = collection.pipelines[0][3]["$project"]

    assert project_stage["product_id"] == {"$toString": "$_id"}