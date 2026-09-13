from __future__ import annotations

import pandas as pd


class TransformationError(ValueError):
    """Raised when order transformation cannot be completed safely."""


ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

CUSTOMER_COLUMNS = (
    "customer_id",
    "segment",
)


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate that all required columns are present."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _empty_daily_sales_report() -> pd.DataFrame:
    """Return an empty daily report with a stable schema."""
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


def _empty_customer_sales_summary() -> pd.DataFrame:
    """Return an empty customer report with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def enrich_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Attach customer attributes to orders using a validated many-to-one join."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

    if not isinstance(customers, pd.DataFrame):
        raise TransformationError(
            "customers must be a pandas DataFrame."
        )

    _validate_columns(
        orders,
        ORDER_COLUMNS,
        frame_name="orders",
    )
    _validate_columns(
        customers,
        CUSTOMER_COLUMNS,
        frame_name="customers",
    )

    customer_attributes = customers[
        list(CUSTOMER_COLUMNS)
    ].copy()

    if customer_attributes["customer_id"].isna().any():
        raise TransformationError(
            "Customer reference data contains null customer_id values."
        )

    if customer_attributes["customer_id"].duplicated().any():
        raise TransformationError(
            "Customer reference data contains duplicate customer_id values."
        )

    try:
        enriched = orders.merge(
            customer_attributes,
            on="customer_id",
            how="left",
            sort=False,
            validate="many_to_one",
        )
    except pd.errors.MergeError as exc:
        raise TransformationError(
            "Orders could not be enriched with customer reference data."
        ) from exc

    if enriched["segment"].isna().any():
        missing_customer_ids = (
            enriched.loc[
                enriched["segment"].isna(),
                "customer_id",
            ]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        raise TransformationError(
            "Orders reference customers that do not exist in the "
            f"customer dataset: {missing_customer_ids}"
        )

    return enriched


def add_order_metrics(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Add reusable order-level metrics without mutating the input."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

    _validate_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
            "created_at",
        ),
        frame_name="orders",
    )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise TransformationError(
            "orders.created_at must be a datetime-like column."
        )

    result = orders.copy()

    result["is_completed"] = result["status"].eq(
        "completed"
    )

    result["net_revenue"] = result["amount"].where(
        result["is_completed"],
        0.0,
    )

    result["order_date"] = result["created_at"].dt.date

    return result


def build_daily_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-order sales metrics by date and customer segment."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

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

    if orders.empty:
        return _empty_daily_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise TransformationError(
            "orders.created_at must be a datetime-like column."
        )

    completed = orders.loc[
        orders["status"].eq("completed")
    ].copy()

    if completed.empty:
        return _empty_daily_sales_report()

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    report = (
        completed.groupby(
            [
                "order_date",
                "segment",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    report["average_order_value"] = (
        report["revenue"]
        / report["order_count"]
    )

    return (
        report[
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


def build_customer_sales_summary(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-order revenue metrics at customer grain."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

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

    if orders.empty:
        return _empty_customer_sales_summary()

    completed = orders.loc[
        orders["status"].eq("completed")
    ].copy()

    if completed.empty:
        return _empty_customer_sales_summary()

    summary = (
        completed.groupby(
            [
                "customer_id",
                "segment",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    summary["average_order_value"] = (
        summary["revenue"]
        / summary["order_count"]
    )

    return (
        summary[
            [
                "customer_id",
                "segment",
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


def transform_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enrich orders, add reusable metrics, and build the daily report."""
    enriched = enrich_orders(
        orders,
        customers,
    )

    enriched = add_order_metrics(
        enriched,
    )

    daily_report = build_daily_sales_report(
        enriched,
    )

    return enriched, daily_report


__all__ = [
    "CUSTOMER_COLUMNS",
    "ORDER_COLUMNS",
    "TransformationError",
    "add_order_metrics",
    "build_customer_sales_summary",
    "build_daily_sales_report",
    "enrich_orders",
    "transform_orders",
]

from __future__ import annotations

import pandas as pd


class TransformationError(ValueError):
    """Raised when order transformation cannot be completed safely."""


ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
    "updated_at",
)

CUSTOMER_COLUMNS = (
    "customer_id",
    "segment",
)


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate that all required columns are present."""
    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise TransformationError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _empty_daily_sales_report() -> pd.DataFrame:
    """Return an empty daily report with a stable schema."""
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


def _empty_customer_sales_summary() -> pd.DataFrame:
    """Return an empty customer report with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def enrich_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Attach customer attributes to orders using a validated many-to-one join."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

    if not isinstance(customers, pd.DataFrame):
        raise TransformationError(
            "customers must be a pandas DataFrame."
        )

    _validate_columns(
        orders,
        ORDER_COLUMNS,
        frame_name="orders",
    )
    _validate_columns(
        customers,
        CUSTOMER_COLUMNS,
        frame_name="customers",
    )

    customer_attributes = customers[
        list(CUSTOMER_COLUMNS)
    ].copy()

    if customer_attributes["customer_id"].isna().any():
        raise TransformationError(
            "Customer reference data contains null customer_id values."
        )

    if customer_attributes["customer_id"].duplicated().any():
        raise TransformationError(
            "Customer reference data contains duplicate customer_id values."
        )

    try:
        enriched = orders.merge(
            customer_attributes,
            on="customer_id",
            how="left",
            sort=False,
            validate="many_to_one",
        )
    except pd.errors.MergeError as exc:
        raise TransformationError(
            "Orders could not be enriched with customer reference data."
        ) from exc

    if enriched["segment"].isna().any():
        missing_customer_ids = (
            enriched.loc[
                enriched["segment"].isna(),
                "customer_id",
            ]
            .drop_duplicates()
            .astype("string")
            .tolist()
        )

        raise TransformationError(
            "Orders reference customers that do not exist in the "
            f"customer dataset: {missing_customer_ids}"
        )

    return enriched


def add_order_metrics(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Add reusable order-level metrics without mutating the input."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

    _validate_columns(
        orders,
        (
            "order_id",
            "status",
            "amount",
            "created_at",
        ),
        frame_name="orders",
    )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise TransformationError(
            "orders.created_at must be a datetime-like column."
        )

    result = orders.copy()

    result["is_completed"] = result["status"].eq(
        "completed"
    )

    result["net_revenue"] = result["amount"].where(
        result["is_completed"],
        0.0,
    )

    result["order_date"] = result["created_at"].dt.date

    return result


def build_daily_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-order sales metrics by date and customer segment."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

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

    if orders.empty:
        return _empty_daily_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise TransformationError(
            "orders.created_at must be a datetime-like column."
        )

    completed = orders.loc[
        orders["status"].eq("completed")
    ].copy()

    if completed.empty:
        return _empty_daily_sales_report()

    completed["order_date"] = completed[
        "created_at"
    ].dt.date

    report = (
        completed.groupby(
            [
                "order_date",
                "segment",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    report["average_order_value"] = (
        report["revenue"]
        / report["order_count"]
    )

    return (
        report[
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


def build_customer_sales_summary(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-order revenue metrics at customer grain."""
    if not isinstance(orders, pd.DataFrame):
        raise TransformationError(
            "orders must be a pandas DataFrame."
        )

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

    if orders.empty:
        return _empty_customer_sales_summary()

    completed = orders.loc[
        orders["status"].eq("completed")
    ].copy()

    if completed.empty:
        return _empty_customer_sales_summary()

    summary = (
        completed.groupby(
            [
                "customer_id",
                "segment",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    summary["average_order_value"] = (
        summary["revenue"]
        / summary["order_count"]
    )

    return (
        summary[
            [
                "customer_id",
                "segment",
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


def transform_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enrich orders, add reusable metrics, and build the daily report."""
    enriched = enrich_orders(
        orders,
        customers,
    )

    enriched = add_order_metrics(
        enriched,
    )

    daily_report = build_daily_sales_report(
        enriched,
    )

    return enriched, daily_report


__all__ = [
    "CUSTOMER_COLUMNS",
    "ORDER_COLUMNS",
    "TransformationError",
    "add_order_metrics",
    "build_customer_sales_summary",
    "build_daily_sales_report",
    "enrich_orders",
    "transform_orders",
]