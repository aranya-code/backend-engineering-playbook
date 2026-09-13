from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class ReportingError(ValueError):
    """Raised when a reporting operation cannot be completed safely."""


ORDER_REQUIRED_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
)

ENRICHED_ORDER_REQUIRED_COLUMNS = (
    *ORDER_REQUIRED_COLUMNS,
    "segment",
)


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Container for the primary pipeline reports."""

    daily_sales: pd.DataFrame
    customer_sales: pd.DataFrame
    product_sales: pd.DataFrame


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate that a DataFrame contains all required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise ReportingError(
            f"{frame_name} must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise ReportingError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _completed_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Return completed orders without mutating the source DataFrame."""
    if orders.empty:
        return orders.copy()

    return orders.loc[
        orders["status"].eq("completed")
    ].copy()


def _empty_daily_sales_report() -> pd.DataFrame:
    """Return an empty daily sales report with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_customer_sales_report() -> pd.DataFrame:
    """Return an empty customer sales report with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_product_sales_report() -> pd.DataFrame:
    """Return an empty product sales report with a stable schema."""
    return pd.DataFrame(
        {
            "product_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_segment_sales_report() -> pd.DataFrame:
    """Return an empty segment sales report with a stable schema."""
    return pd.DataFrame(
        {
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_segment_sales_report() -> pd.DataFrame:
    """Return an empty daily-segment report with a stable schema."""
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


def _build_sales_metrics(
    orders: pd.DataFrame,
    grouping_columns: list[str],
) -> pd.DataFrame:
    """Build common completed-sales metrics for a grouping grain."""
    grouped = (
        orders.groupby(
            grouping_columns,
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    grouped["average_order_value"] = (
        grouped["revenue"]
        / grouped["order_count"]
    )

    return grouped


def build_daily_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build daily completed-sales metrics."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_daily_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_customer_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at customer grain."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_customer_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_customer_sales_report()

    result = _build_sales_metrics(
        completed,
        ["customer_id"],
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


def build_product_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at product grain."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_product_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_product_sales_report()

    result = _build_sales_metrics(
        completed,
        ["product_id"],
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


def build_segment_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at customer-segment grain."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_segment_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_segment_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_daily_segment_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics by date and customer segment."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_daily_segment_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_segment_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_report_bundle(
    orders: pd.DataFrame,
) -> ReportResult:
    """Build the primary report set from enriched order data."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    return ReportResult(
        daily_sales=build_daily_sales_report(
            orders
        ),
        customer_sales=build_customer_sales_report(
            orders
        ),
        product_sales=build_product_sales_report(
            orders
        ),
    )


def add_period_metrics(
    report: pd.DataFrame,
    *,
    date_column: str = "order_date",
) -> pd.DataFrame:
    """Add calendar period fields to a date-grain report."""
    if not isinstance(report, pd.DataFrame):
        raise ReportingError(
            "report must be a pandas DataFrame."
        )

    if date_column not in report.columns:
        raise ReportingError(
            f"Report is missing date column: {date_column}"
        )

    result = report.copy()

    dates = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    if dates.isna().any():
        raise ReportingError(
            f"{date_column} contains invalid or missing dates."
        )

    result["year"] = dates.dt.year.astype("int64")
    result["month"] = dates.dt.month.astype("int64")
    result["quarter"] = dates.dt.quarter.astype("int64")
    result["week"] = (
        dates.dt.isocalendar().week.astype("int64")
    )

    return result


def build_financial_reconciliation(
    orders: pd.DataFrame,
    report: pd.DataFrame,
) -> pd.DataFrame:
    """Compare source revenue with report revenue by date."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    _validate_columns(
        report,
        (
            "order_date",
            "revenue",
        ),
        frame_name="report",
    )

    if orders.empty and report.empty:
        return pd.DataFrame(
            {
                "order_date": pd.Series(dtype="object"),
                "source_revenue": pd.Series(dtype="float64"),
                "reported_revenue": pd.Series(dtype="float64"),
                "revenue_variance": pd.Series(dtype="float64"),
            }
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        source = pd.DataFrame(
            columns=[
                "order_date",
                "source_revenue",
            ]
        )
    else:
        completed["order_date"] = completed[
            "created_at"
        ].dt.date

        source = (
            completed.groupby(
                "order_date",
                as_index=False,
            )["amount"]
            .sum()
            .rename(
                columns={
                    "amount": "source_revenue",
                }
            )
        )

    reported = (
        report[
            [
                "order_date",
                "revenue",
            ]
        ]
        .groupby(
            "order_date",
            as_index=False,
        )["revenue"]
        .sum()
        .rename(
            columns={
                "revenue": "reported_revenue",
            }
        )
    )

    reconciliation = source.merge(
        reported,
        on="order_date",
        how="outer",
        sort=True,
    )

    reconciliation[
        [
            "source_revenue",
            "reported_revenue",
        ]
    ] = reconciliation[
        [
            "source_revenue",
            "reported_revenue",
        ]
    ].fillna(0.0)

    reconciliation["revenue_variance"] = (
        reconciliation["reported_revenue"]
        - reconciliation["source_revenue"]
    )

    return reconciliation[
        [
            "order_date",
            "source_revenue",
            "reported_revenue",
            "revenue_variance",
        ]
    ].reset_index(drop=True)


__all__ = [
    "ENRICHED_ORDER_REQUIRED_COLUMNS",
    "ORDER_REQUIRED_COLUMNS",
    "ReportResult",
    "ReportingError",
    "add_period_metrics",
    "build_customer_sales_report",
    "build_daily_sales_report",
    "build_daily_segment_sales_report",
    "build_financial_reconciliation",
    "build_product_sales_report",
    "build_report_bundle",
    "build_segment_sales_report",
]

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class ReportingError(ValueError):
    """Raised when a reporting operation cannot be completed safely."""


ORDER_REQUIRED_COLUMNS = (
    "order_id",
    "customer_id",
    "product_id",
    "status",
    "amount",
    "created_at",
)

ENRICHED_ORDER_REQUIRED_COLUMNS = (
    *ORDER_REQUIRED_COLUMNS,
    "segment",
)


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Container for the primary pipeline reports."""

    daily_sales: pd.DataFrame
    customer_sales: pd.DataFrame
    product_sales: pd.DataFrame


def _validate_columns(
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    *,
    frame_name: str,
) -> None:
    """Validate that a DataFrame contains all required columns."""
    if not isinstance(frame, pd.DataFrame):
        raise ReportingError(
            f"{frame_name} must be a pandas DataFrame."
        )

    missing = [
        column
        for column in required_columns
        if column not in frame.columns
    ]

    if missing:
        raise ReportingError(
            f"{frame_name} is missing required columns: "
            + ", ".join(missing)
        )


def _completed_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Return completed orders without mutating the source DataFrame."""
    if orders.empty:
        return orders.copy()

    return orders.loc[
        orders["status"].eq("completed")
    ].copy()


def _empty_daily_sales_report() -> pd.DataFrame:
    """Return an empty daily sales report with a stable schema."""
    return pd.DataFrame(
        {
            "order_date": pd.Series(dtype="object"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_customer_sales_report() -> pd.DataFrame:
    """Return an empty customer sales report with a stable schema."""
    return pd.DataFrame(
        {
            "customer_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_product_sales_report() -> pd.DataFrame:
    """Return an empty product sales report with a stable schema."""
    return pd.DataFrame(
        {
            "product_id": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_segment_sales_report() -> pd.DataFrame:
    """Return an empty segment sales report with a stable schema."""
    return pd.DataFrame(
        {
            "segment": pd.Series(dtype="string"),
            "order_count": pd.Series(dtype="int64"),
            "customer_count": pd.Series(dtype="int64"),
            "revenue": pd.Series(dtype="float64"),
            "average_order_value": pd.Series(dtype="float64"),
        }
    )


def _empty_daily_segment_sales_report() -> pd.DataFrame:
    """Return an empty daily-segment report with a stable schema."""
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


def _build_sales_metrics(
    orders: pd.DataFrame,
    grouping_columns: list[str],
) -> pd.DataFrame:
    """Build common completed-sales metrics for a grouping grain."""
    grouped = (
        orders.groupby(
            grouping_columns,
            as_index=False,
            dropna=False,
        )
        .agg(
            order_count=("order_id", "nunique"),
            revenue=("amount", "sum"),
        )
    )

    grouped["average_order_value"] = (
        grouped["revenue"]
        / grouped["order_count"]
    )

    return grouped


def build_daily_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build daily completed-sales metrics."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_daily_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_customer_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at customer grain."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_customer_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_customer_sales_report()

    result = _build_sales_metrics(
        completed,
        ["customer_id"],
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


def build_product_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at product grain."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_product_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_product_sales_report()

    result = _build_sales_metrics(
        completed,
        ["product_id"],
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


def build_segment_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics at customer-segment grain."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_segment_sales_report()

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_segment_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_daily_segment_sales_report(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build completed-sales metrics by date and customer segment."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    if orders.empty:
        return _empty_daily_segment_sales_report()

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        return _empty_daily_segment_sales_report()

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
        result["revenue"]
        / result["order_count"]
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


def build_report_bundle(
    orders: pd.DataFrame,
) -> ReportResult:
    """Build the primary report set from enriched order data."""
    _validate_columns(
        orders,
        ENRICHED_ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    return ReportResult(
        daily_sales=build_daily_sales_report(
            orders
        ),
        customer_sales=build_customer_sales_report(
            orders
        ),
        product_sales=build_product_sales_report(
            orders
        ),
    )


def add_period_metrics(
    report: pd.DataFrame,
    *,
    date_column: str = "order_date",
) -> pd.DataFrame:
    """Add calendar period fields to a date-grain report."""
    if not isinstance(report, pd.DataFrame):
        raise ReportingError(
            "report must be a pandas DataFrame."
        )

    if date_column not in report.columns:
        raise ReportingError(
            f"Report is missing date column: {date_column}"
        )

    result = report.copy()

    dates = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    if dates.isna().any():
        raise ReportingError(
            f"{date_column} contains invalid or missing dates."
        )

    result["year"] = dates.dt.year.astype("int64")
    result["month"] = dates.dt.month.astype("int64")
    result["quarter"] = dates.dt.quarter.astype("int64")
    result["week"] = (
        dates.dt.isocalendar().week.astype("int64")
    )

    return result


def build_financial_reconciliation(
    orders: pd.DataFrame,
    report: pd.DataFrame,
) -> pd.DataFrame:
    """Compare source revenue with report revenue by date."""
    _validate_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        frame_name="orders",
    )

    _validate_columns(
        report,
        (
            "order_date",
            "revenue",
        ),
        frame_name="report",
    )

    if orders.empty and report.empty:
        return pd.DataFrame(
            {
                "order_date": pd.Series(dtype="object"),
                "source_revenue": pd.Series(dtype="float64"),
                "reported_revenue": pd.Series(dtype="float64"),
                "revenue_variance": pd.Series(dtype="float64"),
            }
        )

    if not pd.api.types.is_datetime64_any_dtype(
        orders["created_at"]
    ):
        raise ReportingError(
            "orders.created_at must be a datetime-like column."
        )

    completed = _completed_orders(orders)

    if completed.empty:
        source = pd.DataFrame(
            columns=[
                "order_date",
                "source_revenue",
            ]
        )
    else:
        completed["order_date"] = completed[
            "created_at"
        ].dt.date

        source = (
            completed.groupby(
                "order_date",
                as_index=False,
            )["amount"]
            .sum()
            .rename(
                columns={
                    "amount": "source_revenue",
                }
            )
        )

    reported = (
        report[
            [
                "order_date",
                "revenue",
            ]
        ]
        .groupby(
            "order_date",
            as_index=False,
        )["revenue"]
        .sum()
        .rename(
            columns={
                "revenue": "reported_revenue",
            }
        )
    )

    reconciliation = source.merge(
        reported,
        on="order_date",
        how="outer",
        sort=True,
    )

    reconciliation[
        [
            "source_revenue",
            "reported_revenue",
        ]
    ] = reconciliation[
        [
            "source_revenue",
            "reported_revenue",
        ]
    ].fillna(0.0)

    reconciliation["revenue_variance"] = (
        reconciliation["reported_revenue"]
        - reconciliation["source_revenue"]
    )

    return reconciliation[
        [
            "order_date",
            "source_revenue",
            "reported_revenue",
            "revenue_variance",
        ]
    ].reset_index(drop=True)


__all__ = [
    "ENRICHED_ORDER_REQUIRED_COLUMNS",
    "ORDER_REQUIRED_COLUMNS",
    "ReportResult",
    "ReportingError",
    "add_period_metrics",
    "build_customer_sales_report",
    "build_daily_sales_report",
    "build_daily_segment_sales_report",
    "build_financial_reconciliation",
    "build_product_sales_report",
    "build_report_bundle",
    "build_segment_sales_report",
]