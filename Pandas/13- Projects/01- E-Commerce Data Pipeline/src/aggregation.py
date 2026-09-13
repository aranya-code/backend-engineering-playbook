from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


class AggregationError(ValueError):
    """Raised when aggregation cannot be performed safely."""


COMPLETED_STATUS = "completed"


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate the presence of required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise AggregationError(
            f"{frame_name} must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise AggregationError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _completed_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Return completed orders without mutating the input."""
    if orders.empty:
        return orders.copy()

    return orders.loc[
        orders["status"].eq(COMPLETED_STATUS)
    ].copy()


def _empty_customer_sales() -> pd.DataFrame:
    """Return an empty customer-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_product_sales() -> pd.DataFrame:
    """Return an empty product-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "product_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_sales() -> pd.DataFrame:
    """Return an empty daily aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_segment_sales() -> pd.DataFrame:
    """Return an empty segment-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_segment_sales() -> pd.DataFrame:
    """Return an empty daily-segment aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def aggregate_customer_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales at customer grain."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_customer_sales()

    result = (
        completed.groupby(
            "customer_id",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "customer_id",
                "order_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "customer_id",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_product_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales at product grain."""
    _validate_columns(
        orders,
        (
            "order_id",
            "product_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_product_sales()

    result = (
        completed.groupby(
            "product_id",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "product_id",
                "order_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "product_id",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_daily_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by calendar day."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "created_at",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_sales()

    if not pd.api.types.is_datetime64_any_dtype(
        completed["created_at"]
    ):
        raise AggregationError(
            "orders.created_at must be a datetime-like column."
        )

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    result = (
        completed.groupby(
            "order_date",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "order_date",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by="order_date",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


def aggregate_segment_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by customer segment."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "segment",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_segment_sales()

    result = (
        completed.groupby(
            "segment",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "segment",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "segment",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_daily_segment_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by day and customer segment."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "created_at",
            "segment",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_segment_sales()

    if not pd.api.types.is_datetime64_any_dtype(
        completed["created_at"]
    ):
        raise AggregationError(
            "orders.created_at must be a datetime-like column."
        )

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    result = (
        completed.groupby(
            [
                "order_date",
                "segment",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "order_date",
                "segment",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "order_date",
                "segment",
            ],
            ascending=[
                True,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def calculate_total_revenue(
    orders: pd.DataFrame,
) -> float:
    """Calculate total completed-order revenue."""
    _validate_columns(
        orders,
        (
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return 0.0

    return float(completed["amount"].sum())


def calculate_average_order_value(
    orders: pd.DataFrame,
) -> float:
    """Calculate AOV at unique-order grain.

    The function first collapses records by ``order_id`` so repeated
    rows for the same order do not inflate either revenue or order count.
    """
    _validate_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return 0.0

    order_totals = (
        completed.groupby(
            "order_id",
            as_index=False,
        )["amount"]
        .sum()
    )

    if order_totals.empty:
        return 0.0

    return float(order_totals["amount"].mean())


def aggregate_pipeline_metrics(
    orders: pd.DataFrame,
) -> dict[str, float | int]:
    """Calculate key pipeline metrics from the cleaned order dataset."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    return {
        "input_rows": int(len(orders)),
        "completed_rows": int(len(completed)),
        "unique_orders": int(orders["order_id"].nunique()),
        "unique_customers": int(
            orders["customer_id"].nunique()
        ),
        "total_revenue": calculate_total_revenue(
            orders
        ),
        "average_order_value": calculate_average_order_value(
            orders
        ),
    }


def aggregate_orders(
    orders: pd.DataFrame,
    *,
    grouping_columns: Iterable[str],
) -> pd.DataFrame:
    """Perform a reusable completed-order aggregation for arbitrary dimensions."""
    grouping = tuple(grouping_columns)

    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            *grouping,
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        columns = list(grouping) + [
            "order_count",
            "customer_count",
            "revenue",
            "average_order_value",
        ]

        return pd.DataFrame(
            columns=columns
        )

    result = (
        completed.groupby(
            list(grouping),
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return result.reset_index(drop=True)


__all__ = [
    "AggregationError",
    "COMPLETED_STATUS",
    "aggregate_customer_sales",
    "aggregate_daily_sales",
    "aggregate_daily_segment_sales",
    "aggregate_orders",
    "aggregate_pipeline_metrics",
    "aggregate_product_sales",
    "aggregate_segment_sales",
    "calculate_average_order_value",
    "calculate_total_revenue",
]

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


class AggregationError(ValueError):
    """Raised when aggregation cannot be performed safely."""


COMPLETED_STATUS = "completed"


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate the presence of required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise AggregationError(
            f"{frame_name} must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise AggregationError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _completed_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Return completed orders without mutating the input."""
    if orders.empty:
        return orders.copy()

    return orders.loc[
        orders["status"].eq(COMPLETED_STATUS)
    ].copy()


def _empty_customer_sales() -> pd.DataFrame:
    """Return an empty customer-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_product_sales() -> pd.DataFrame:
    """Return an empty product-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "product_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_sales() -> pd.DataFrame:
    """Return an empty daily aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_segment_sales() -> pd.DataFrame:
    """Return an empty segment-level aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_segment_sales() -> pd.DataFrame:
    """Return an empty daily-segment aggregate with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def aggregate_customer_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales at customer grain."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_customer_sales()

    result = (
        completed.groupby(
            "customer_id",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "customer_id",
                "order_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "customer_id",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_product_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales at product grain."""
    _validate_columns(
        orders,
        (
            "order_id",
            "product_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_product_sales()

    result = (
        completed.groupby(
            "product_id",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "product_id",
                "order_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "product_id",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_daily_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by calendar day."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "created_at",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_sales()

    if not pd.api.types.is_datetime64_any_dtype(
        completed["created_at"]
    ):
        raise AggregationError(
            "orders.created_at must be a datetime-like column."
        )

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    result = (
        completed.groupby(
            "order_date",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "order_date",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by="order_date",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


def aggregate_segment_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by customer segment."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "segment",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_segment_sales()

    result = (
        completed.groupby(
            "segment",
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "segment",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "revenue",
                "segment",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def aggregate_daily_segment_sales(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate completed sales by day and customer segment."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            "created_at",
            "segment",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_segment_sales()

    if not pd.api.types.is_datetime64_any_dtype(
        completed["created_at"]
    ):
        raise AggregationError(
            "orders.created_at must be a datetime-like column."
        )

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    result = (
        completed.groupby(
            [
                "order_date",
                "segment",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return (
        result[
            [
                "order_date",
                "segment",
                "order_count",
                "customer_count",
                "revenue",
                "average_order_value",
            ]
        ]
        .sort_values(
            by=[
                "order_date",
                "segment",
            ],
            ascending=[
                True,
                True,
            ],
            kind="mergesort",
            na_position="last",
        )
        .reset_index(drop=True)
    )


def calculate_total_revenue(
    orders: pd.DataFrame,
) -> float:
    """Calculate total completed-order revenue."""
    _validate_columns(
        orders,
        (
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return 0.0

    return float(completed["amount"].sum())


def calculate_average_order_value(
    orders: pd.DataFrame,
) -> float:
    """Calculate AOV at unique-order grain.

    The function first collapses records by ``order_id`` so repeated
    rows for the same order do not inflate either revenue or order count.
    """
    _validate_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        return 0.0

    order_totals = (
        completed.groupby(
            "order_id",
            as_index=False,
        )["amount"]
        .sum()
    )

    if order_totals.empty:
        return 0.0

    return float(order_totals["amount"].mean())


def aggregate_pipeline_metrics(
    orders: pd.DataFrame,
) -> dict[str, float | int]:
    """Calculate key pipeline metrics from the cleaned order dataset."""
    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    return {
        "input_rows": int(len(orders)),
        "completed_rows": int(len(completed)),
        "unique_orders": int(orders["order_id"].nunique()),
        "unique_customers": int(
            orders["customer_id"].nunique()
        ),
        "total_revenue": calculate_total_revenue(
            orders
        ),
        "average_order_value": calculate_average_order_value(
            orders
        ),
    }


def aggregate_orders(
    orders: pd.DataFrame,
    *,
    grouping_columns: Iterable[str],
) -> pd.DataFrame:
    """Perform a reusable completed-order aggregation for arbitrary dimensions."""
    grouping = tuple(grouping_columns)

    _validate_columns(
        orders,
        (
            "order_id",
            "customer_id",
            "status",
            "amount",
            *grouping,
        ),
        frame_name="orders",
    )

    completed = _completed_orders(orders)

    if completed.empty:
        columns = list(grouping) + [
            "order_count",
            "customer_count",
            "revenue",
            "average_order_value",
        ]

        return pd.DataFrame(
            columns=columns
        )

    result = (
        completed.groupby(
            list(grouping),
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    result["average_order_value"] = (
        result["revenue"] / result["order_count"]
    )

    return result.reset_index(drop=True)


__all__ = [
    "AggregationError",
    "COMPLETED_STATUS",
    "aggregate_customer_sales",
    "aggregate_daily_sales",
    "aggregate_daily_segment_sales",
    "aggregate_orders",
    "aggregate_pipeline_metrics",
    "aggregate_product_sales",
    "aggregate_segment_sales",
    "calculate_average_order_value",
    "calculate_total_revenue",
]