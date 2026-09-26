"""FastAPI routes for MongoDB aggregation analytics."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from schemas.analytics import AnalyticsResponse
from services.analytics_service import (
    get_customer_analytics,
    get_sales_by_category,
    get_sales_by_period,
    get_top_products,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def _parse_optional_date(
    value: str | None,
    parameter_name: str,
) -> datetime | None:
    """Parse an optional ISO-8601 date and normalize it to UTC."""
    if value is None:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{parameter_name} must be a valid ISO-8601 datetime.",
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


@router.get(
    "/sales-by-category",
    response_model=AnalyticsResponse,
)
def sales_by_category(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> AnalyticsResponse:
    """Return revenue and item volume grouped by product category."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_sales_by_category(
        start_date=start,
        end_date=end,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/sales-by-period",
    response_model=AnalyticsResponse,
)
def sales_by_period(
    start_date: str = Query(...),
    end_date: str = Query(...),
    granularity: str = Query(default="month"),
) -> AnalyticsResponse:
    """Return revenue and order count grouped by calendar period."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is None or end is None:
        raise HTTPException(
            status_code=400,
            detail="start_date and end_date are required.",
        )

    try:
        data = get_sales_by_period(
            start_date=start,
            end_date=end,
            granularity=granularity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/top-products",
    response_model=AnalyticsResponse,
)
def top_products(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> AnalyticsResponse:
    """Return the highest-revenue products for the selected period."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_top_products(
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/customers",
    response_model=AnalyticsResponse,
)
def customers(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> AnalyticsResponse:
    """Return customer-level order and spending analytics."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_customer_analytics(
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )

"""FastAPI routes for MongoDB aggregation analytics."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from schemas.analytics import AnalyticsResponse
from services.analytics_service import (
    get_customer_analytics,
    get_sales_by_category,
    get_sales_by_period,
    get_top_products,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def _parse_optional_date(
    value: str | None,
    parameter_name: str,
) -> datetime | None:
    """Parse an optional ISO-8601 date and normalize it to UTC."""
    if value is None:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{parameter_name} must be a valid ISO-8601 datetime.",
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


@router.get(
    "/sales-by-category",
    response_model=AnalyticsResponse,
)
def sales_by_category(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> AnalyticsResponse:
    """Return revenue and item volume grouped by product category."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_sales_by_category(
        start_date=start,
        end_date=end,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/sales-by-period",
    response_model=AnalyticsResponse,
)
def sales_by_period(
    start_date: str = Query(...),
    end_date: str = Query(...),
    granularity: str = Query(default="month"),
) -> AnalyticsResponse:
    """Return revenue and order count grouped by calendar period."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is None or end is None:
        raise HTTPException(
            status_code=400,
            detail="start_date and end_date are required.",
        )

    try:
        data = get_sales_by_period(
            start_date=start,
            end_date=end,
            granularity=granularity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/top-products",
    response_model=AnalyticsResponse,
)
def top_products(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> AnalyticsResponse:
    """Return the highest-revenue products for the selected period."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_top_products(
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )


@router.get(
    "/customers",
    response_model=AnalyticsResponse,
)
def customers(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> AnalyticsResponse:
    """Return customer-level order and spending analytics."""
    start = _parse_optional_date(start_date, "start_date")
    end = _parse_optional_date(end_date, "end_date")

    if start is not None and end is not None and start >= end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date.",
        )

    data = get_customer_analytics(
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return AnalyticsResponse(
        data=data,
        total=len(data),
    )