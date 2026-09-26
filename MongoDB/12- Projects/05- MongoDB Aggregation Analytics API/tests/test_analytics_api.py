"""API tests for the MongoDB aggregation analytics endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def analytics_headers() -> dict[str, str]:
    """Return common request headers used by analytics endpoints."""
    return {"Accept": "application/json"}


def test_health_endpoint(client: TestClient) -> None:
    """Verify that the application health endpoint is available."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sales_by_category_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the sales-by-category endpoint returns aggregation results."""
    expected = [
        {
            "category": "Electronics",
            "order_count": 4,
            "item_count": 7,
            "revenue": "499.93",
        },
        {
            "category": "Books",
            "order_count": 2,
            "item_count": 5,
            "revenue": "149.95",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/sales-by-category",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_sales_by_category_passes_date_filters(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify date query parameters reach the analytics service."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_sales_by_category(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        fake_get_sales_by_category,
    )

    response = client.get(
        "/analytics/sales-by-category"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z",
    )

    assert response.status_code == 200
    assert captured["start_date"] == datetime(
        2025,
        1,
        1,
        tzinfo=timezone.utc,
    )
    assert captured["end_date"] == datetime(
        2025,
        2,
        1,
        tzinfo=timezone.utc,
    )


def test_sales_by_period_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the sales-by-period endpoint returns period aggregates."""
    expected = [
        {
            "period": "2025-01-01T00:00:00Z",
            "order_count": 12,
            "revenue": "1299.90",
        },
        {
            "period": "2025-02-01T00:00:00Z",
            "order_count": 15,
            "revenue": "1599.50",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_period",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-03-01T00:00:00Z"
        "&granularity=month",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


@pytest.mark.parametrize(
    "granularity",
    ["day", "week", "month", "quarter", "year"],
)
def test_sales_by_period_accepts_supported_granularities(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    granularity: str,
) -> None:
    """Verify supported period granularities are accepted by the API."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_sales_by_period(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_period",
        fake_get_sales_by_period,
    )

    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z"
        f"&granularity={granularity}",
    )

    assert response.status_code == 200
    assert captured["granularity"] == granularity


def test_sales_by_period_rejects_invalid_granularity(
    client: TestClient,
) -> None:
    """Verify unsupported aggregation granularities return a validation error."""
    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z"
        "&granularity=hour",
    )

    assert response.status_code in {400, 422}


def test_top_products_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the top-products endpoint returns ranked products."""
    expected = [
        {
            "product_id": "65f1a2b3c4d5e6f789012345",
            "product_name": "Mechanical Keyboard",
            "quantity_sold": 42,
            "revenue": "4199.58",
        },
        {
            "product_id": "65f1a2b3c4d5e6f789012346",
            "product_name": "USB-C Hub",
            "quantity_sold": 31,
            "revenue": "1549.69",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/top-products?limit=10",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_top_products_passes_limit_to_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the API forwards the requested product limit."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_top_products(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        fake_get_top_products,
    )

    response = client.get("/analytics/top-products?limit=25")

    assert response.status_code == 200
    assert captured["limit"] == 25


def test_top_products_rejects_non_positive_limit(
    client: TestClient,
) -> None:
    """Verify invalid product limits are rejected."""
    response = client.get("/analytics/top-products?limit=0")

    assert response.status_code in {400, 422}


def test_customer_analytics_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the customer analytics endpoint returns customer metrics."""
    expected = [
        {
            "customer_id": "customer-001",
            "order_count": 12,
            "total_spend": "2499.90",
            "average_order_value": "208.325",
        },
        {
            "customer_id": "customer-002",
            "order_count": 7,
            "total_spend": "1199.93",
            "average_order_value": "171.41857142857143",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_customer_analytics",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/customers?limit=100",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_customer_analytics_passes_limit_to_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the API forwards the requested customer limit."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_customer_analytics(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_customer_analytics",
        fake_get_customer_analytics,
    )

    response = client.get("/analytics/customers?limit=50")

    assert response.status_code == 200
    assert captured["limit"] == 50


def test_customer_analytics_rejects_non_positive_limit(
    client: TestClient,
) -> None:
    """Verify invalid customer limits are rejected."""
    response = client.get("/analytics/customers?limit=0")

    assert response.status_code in {400, 422}


def test_analytics_endpoint_returns_empty_result(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify an empty aggregation result is represented consistently."""
    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        lambda **_: [],
    )

    response = client.get("/analytics/sales-by-category")

    assert response.status_code == 200
    assert response.json() == {
        "data": [],
        "total": 0,
    }


def test_analytics_endpoint_maps_service_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify service-level validation errors become client errors."""
    from services import analytics_service

    def raise_validation_error(**_: Any) -> list[dict[str, Any]]:
        raise ValueError("limit must be greater than zero.")

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        raise_validation_error,
    )

    response = client.get("/analytics/top-products?limit=10")

    assert response.status_code in {400, 422}


@pytest.mark.parametrize(
    ("endpoint", "service_function"),
    [
        (
            "/analytics/sales-by-category",
            "get_sales_by_category",
        ),
        (
            "/analytics/sales-by-period",
            "get_sales_by_period",
        ),
        (
            "/analytics/top-products",
            "get_top_products",
        ),
        (
            "/analytics/customers",
            "get_customer_analytics",
        ),
    ],
)
def test_analytics_routes_are_registered(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    service_function: str,
) -> None:
    """Verify each expected analytics route is registered."""
    from services import analytics_service

    if service_function == "get_sales_by_period":
        monkeypatch.setattr(
            analytics_service,
            service_function,
            lambda **_: [],
        )
        response = client.get(
            f"{endpoint}"
            "?start_date=2025-01-01T00:00:00Z"
            "&end_date=2025-02-01T00:00:00Z",
        )
    else:
        monkeypatch.setattr(
            analytics_service,
            service_function,
            lambda **_: [],
        )
        response = client.get(endpoint)

    assert response.status_code != 404

"""API tests for the MongoDB aggregation analytics endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def analytics_headers() -> dict[str, str]:
    """Return common request headers used by analytics endpoints."""
    return {"Accept": "application/json"}


def test_health_endpoint(client: TestClient) -> None:
    """Verify that the application health endpoint is available."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sales_by_category_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the sales-by-category endpoint returns aggregation results."""
    expected = [
        {
            "category": "Electronics",
            "order_count": 4,
            "item_count": 7,
            "revenue": "499.93",
        },
        {
            "category": "Books",
            "order_count": 2,
            "item_count": 5,
            "revenue": "149.95",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/sales-by-category",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_sales_by_category_passes_date_filters(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify date query parameters reach the analytics service."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_sales_by_category(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        fake_get_sales_by_category,
    )

    response = client.get(
        "/analytics/sales-by-category"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z",
    )

    assert response.status_code == 200
    assert captured["start_date"] == datetime(
        2025,
        1,
        1,
        tzinfo=timezone.utc,
    )
    assert captured["end_date"] == datetime(
        2025,
        2,
        1,
        tzinfo=timezone.utc,
    )


def test_sales_by_period_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the sales-by-period endpoint returns period aggregates."""
    expected = [
        {
            "period": "2025-01-01T00:00:00Z",
            "order_count": 12,
            "revenue": "1299.90",
        },
        {
            "period": "2025-02-01T00:00:00Z",
            "order_count": 15,
            "revenue": "1599.50",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_period",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-03-01T00:00:00Z"
        "&granularity=month",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


@pytest.mark.parametrize(
    "granularity",
    ["day", "week", "month", "quarter", "year"],
)
def test_sales_by_period_accepts_supported_granularities(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    granularity: str,
) -> None:
    """Verify supported period granularities are accepted by the API."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_sales_by_period(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_period",
        fake_get_sales_by_period,
    )

    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z"
        f"&granularity={granularity}",
    )

    assert response.status_code == 200
    assert captured["granularity"] == granularity


def test_sales_by_period_rejects_invalid_granularity(
    client: TestClient,
) -> None:
    """Verify unsupported aggregation granularities return a validation error."""
    response = client.get(
        "/analytics/sales-by-period"
        "?start_date=2025-01-01T00:00:00Z"
        "&end_date=2025-02-01T00:00:00Z"
        "&granularity=hour",
    )

    assert response.status_code in {400, 422}


def test_top_products_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the top-products endpoint returns ranked products."""
    expected = [
        {
            "product_id": "65f1a2b3c4d5e6f789012345",
            "product_name": "Mechanical Keyboard",
            "quantity_sold": 42,
            "revenue": "4199.58",
        },
        {
            "product_id": "65f1a2b3c4d5e6f789012346",
            "product_name": "USB-C Hub",
            "quantity_sold": 31,
            "revenue": "1549.69",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/top-products?limit=10",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_top_products_passes_limit_to_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the API forwards the requested product limit."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_top_products(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        fake_get_top_products,
    )

    response = client.get("/analytics/top-products?limit=25")

    assert response.status_code == 200
    assert captured["limit"] == 25


def test_top_products_rejects_non_positive_limit(
    client: TestClient,
) -> None:
    """Verify invalid product limits are rejected."""
    response = client.get("/analytics/top-products?limit=0")

    assert response.status_code in {400, 422}


def test_customer_analytics_returns_analytics(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the customer analytics endpoint returns customer metrics."""
    expected = [
        {
            "customer_id": "customer-001",
            "order_count": 12,
            "total_spend": "2499.90",
            "average_order_value": "208.325",
        },
        {
            "customer_id": "customer-002",
            "order_count": 7,
            "total_spend": "1199.93",
            "average_order_value": "171.41857142857143",
        },
    ]

    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_customer_analytics",
        lambda **_: expected,
    )

    response = client.get(
        "/analytics/customers?limit=100",
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["data"] == expected
    assert payload["total"] == len(expected)


def test_customer_analytics_passes_limit_to_service(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the API forwards the requested customer limit."""
    from services import analytics_service

    captured: dict[str, Any] = {}

    def fake_get_customer_analytics(**kwargs: Any) -> list[dict[str, Any]]:
        captured.update(kwargs)
        return []

    monkeypatch.setattr(
        analytics_service,
        "get_customer_analytics",
        fake_get_customer_analytics,
    )

    response = client.get("/analytics/customers?limit=50")

    assert response.status_code == 200
    assert captured["limit"] == 50


def test_customer_analytics_rejects_non_positive_limit(
    client: TestClient,
) -> None:
    """Verify invalid customer limits are rejected."""
    response = client.get("/analytics/customers?limit=0")

    assert response.status_code in {400, 422}


def test_analytics_endpoint_returns_empty_result(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify an empty aggregation result is represented consistently."""
    from services import analytics_service

    monkeypatch.setattr(
        analytics_service,
        "get_sales_by_category",
        lambda **_: [],
    )

    response = client.get("/analytics/sales-by-category")

    assert response.status_code == 200
    assert response.json() == {
        "data": [],
        "total": 0,
    }


def test_analytics_endpoint_maps_service_errors(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify service-level validation errors become client errors."""
    from services import analytics_service

    def raise_validation_error(**_: Any) -> list[dict[str, Any]]:
        raise ValueError("limit must be greater than zero.")

    monkeypatch.setattr(
        analytics_service,
        "get_top_products",
        raise_validation_error,
    )

    response = client.get("/analytics/top-products?limit=10")

    assert response.status_code in {400, 422}


@pytest.mark.parametrize(
    ("endpoint", "service_function"),
    [
        (
            "/analytics/sales-by-category",
            "get_sales_by_category",
        ),
        (
            "/analytics/sales-by-period",
            "get_sales_by_period",
        ),
        (
            "/analytics/top-products",
            "get_top_products",
        ),
        (
            "/analytics/customers",
            "get_customer_analytics",
        ),
    ],
)
def test_analytics_routes_are_registered(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    endpoint: str,
    service_function: str,
) -> None:
    """Verify each expected analytics route is registered."""
    from services import analytics_service

    if service_function == "get_sales_by_period":
        monkeypatch.setattr(
            analytics_service,
            service_function,
            lambda **_: [],
        )
        response = client.get(
            f"{endpoint}"
            "?start_date=2025-01-01T00:00:00Z"
            "&end_date=2025-02-01T00:00:00Z",
        )
    else:
        monkeypatch.setattr(
            analytics_service,
            service_function,
            lambda **_: [],
        )
        response = client.get(endpoint)

    assert response.status_code != 404