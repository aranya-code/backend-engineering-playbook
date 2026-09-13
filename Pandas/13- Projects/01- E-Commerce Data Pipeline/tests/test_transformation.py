from __future__ import annotations

import pandas as pd
import pytest

from src.transformation import (
    TransformationError,
    add_order_metrics,
    build_customer_sales_summary,
    build_daily_sales_report,
    enrich_orders,
    transform_orders,
)


def make_orders() -> pd.DataFrame:
    """Build representative cleaned order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-1", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T12:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                    "2026-01-02T10:05:00Z",
                    "2026-01-02T12:05:00Z",
                ],
                utc=True,
            ),
        }
    )


def make_customers() -> pd.DataFrame:
    """Build representative customer reference data."""
    return pd.DataFrame(
        {
            "customer_id": ["C-1", "C-2", "C-3"],
            "segment": [
                "premium",
                "standard",
                "enterprise",
            ],
        }
    )


def test_enrich_orders_adds_customer_segment() -> None:
    result = enrich_orders(
        make_orders(),
        make_customers(),
    )

    assert "segment" in result.columns
    assert result["segment"].tolist() == [
        "premium",
        "premium",
        "standard",
        "enterprise",
    ]


def test_enrich_orders_preserves_order_grain() -> None:
    orders = make_orders()

    result = enrich_orders(
        orders,
        make_customers(),
    )

    assert len(result) == len(orders)
    assert result["order_id"].tolist() == orders[
        "order_id"
    ].tolist()


def test_enrich_orders_preserves_order_column_values() -> None:
    orders = make_orders()

    result = enrich_orders(
        orders,
        make_customers(),
    )

    pd.testing.assert_series_equal(
        result["order_id"],
        orders["order_id"],
        check_names=False,
    )
    pd.testing.assert_series_equal(
        result["amount"],
        orders["amount"],
        check_names=False,
    )


def test_enrich_orders_rejects_duplicate_customer_ids() -> None:
    customers = pd.concat(
        [
            make_customers(),
            pd.DataFrame(
                {
                    "customer_id": ["C-1"],
                    "segment": ["standard"],
                }
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        TransformationError,
        match="duplicate customer_id",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_enrich_orders_rejects_missing_customer_reference() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    with pytest.raises(
        TransformationError,
        match="do not exist",
    ):
        enrich_orders(
            orders,
            make_customers(),
        )


def test_enrich_orders_rejects_null_customer_ids() -> None:
    customers = make_customers()
    customers.loc[0, "customer_id"] = None

    with pytest.raises(
        TransformationError,
        match="null customer_id",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_enrich_orders_rejects_missing_order_columns() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        enrich_orders(
            orders,
            make_customers(),
        )


def test_enrich_orders_rejects_missing_customer_columns() -> None:
    customers = make_customers().drop(
        columns=["segment"],
    )

    with pytest.raises(
        TransformationError,
        match="customers is missing required columns",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_add_order_metrics_adds_completion_flag() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["is_completed"].tolist() == [
        True,
        True,
        False,
        True,
    ]


def test_add_order_metrics_adds_net_revenue() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["net_revenue"].tolist() == [
        100.0,
        200.0,
        0.0,
        300.0,
    ]


def test_add_order_metrics_adds_order_date() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["order_date"].tolist() == [
        pd.Timestamp("2026-01-01").date(),
        pd.Timestamp("2026-01-01").date(),
        pd.Timestamp("2026-01-02").date(),
        pd.Timestamp("2026-01-02").date(),
    ]


def test_add_order_metrics_does_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    add_order_metrics(
        orders,
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_add_order_metrics_requires_datetime_created_at() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        TransformationError,
        match="created_at must be a datetime-like",
    ):
        add_order_metrics(
            orders,
        )


def test_build_daily_sales_report_aggregates_completed_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_build_daily_sales_report_excludes_cancelled_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    report = build_daily_sales_report(
        orders,
    )

    assert not (
        report["order_date"]
        == pd.Timestamp("2026-01-02").date()
    ).empty
    assert report["revenue"].sum() == 600.0
    assert report["order_count"].sum() == 3


def test_build_daily_sales_report_counts_distinct_customers() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "customer_id": ["C-1", "C-1"],
            "product_id": ["P-1", "P-2"],
            "status": ["completed", "completed"],
            "amount": [100.0, 200.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                ],
                utc=True,
            ),
            "segment": ["premium", "premium"],
        }
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.loc[0, "order_count"] == 2
    assert report.loc[0, "customer_count"] == 1
    assert report.loc[0, "revenue"] == 300.0
    assert report.loc[0, "average_order_value"] == 150.0


def test_build_daily_sales_report_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()
    orders["segment"] = pd.Series(
        dtype="string",
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.empty
    assert list(report.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_build_daily_sales_report_requires_datetime_created_at() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )
    orders["created_at"] = orders[
        "created_at"
    ].astype(str)

    with pytest.raises(
        TransformationError,
        match="created_at must be a datetime-like",
    ):
        build_daily_sales_report(
            orders,
        )


def test_build_customer_sales_summary_aggregates_by_customer() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert summary.to_dict("records") == [
        {
            "customer_id": "C-3",
            "segment": "enterprise",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "customer_id": "C-1",
            "segment": "premium",
            "order_count": 2,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
    ]


def test_build_customer_sales_summary_excludes_cancelled_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert "C-2" not in summary[
        "customer_id"
    ].tolist()
    assert summary["order_count"].sum() == 3
    assert summary["revenue"].sum() == 600.0


def test_build_customer_sales_summary_handles_empty_input() -> None:
    orders = enrich_orders(
        make_orders().iloc[0:0].copy(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert summary.empty
    assert list(summary.columns) == [
        "customer_id",
        "segment",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_transform_orders_returns_enriched_orders_and_daily_report() -> None:
    orders = make_orders()
    customers = make_customers()

    enriched, daily_report = transform_orders(
        orders,
        customers,
    )

    assert len(enriched) == len(orders)
    assert "segment" in enriched.columns
    assert "is_completed" in enriched.columns
    assert "net_revenue" in enriched.columns
    assert "order_date" in enriched.columns

    assert daily_report["revenue"].sum() == 600.0
    assert daily_report["order_count"].sum() == 3


def test_transform_orders_preserves_total_completed_revenue() -> None:
    orders = make_orders()
    customers = make_customers()

    enriched, daily_report = transform_orders(
        orders,
        customers,
    )

    expected_revenue = orders.loc[
        orders["status"].eq("completed"),
        "amount",
    ].sum()

    assert enriched["net_revenue"].sum() == expected_revenue
    assert daily_report["revenue"].sum() == expected_revenue


def test_transform_orders_does_not_mutate_inputs() -> None:
    orders = make_orders()
    customers = make_customers()

    original_orders = orders.copy(deep=True)
    original_customers = customers.copy(deep=True)

    transform_orders(
        orders,
        customers,
    )

    pd.testing.assert_frame_equal(
        orders,
        original_orders,
    )
    pd.testing.assert_frame_equal(
        customers,
        original_customers,
    )


def test_build_daily_sales_report_requires_segment_column() -> None:
    orders = make_orders()

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        build_daily_sales_report(
            orders,
        )


def test_build_customer_sales_summary_requires_segment_column() -> None:
    orders = make_orders()

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        build_customer_sales_summary(
            orders,
        )


def test_build_daily_sales_report_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                ],
                utc=True,
            ),
            "segment": [
                "premium",
                "premium",
                "standard",
            ],
        }
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.loc[0, "order_count"] == 2
    assert report.loc[0, "customer_count"] == 2
    assert report.loc[0, "revenue"] == 300.0
    assert report.loc[0, "average_order_value"] == 150.0

from __future__ import annotations

import pandas as pd
import pytest

from src.transformation import (
    TransformationError,
    add_order_metrics,
    build_customer_sales_summary,
    build_daily_sales_report,
    enrich_orders,
    transform_orders,
)


def make_orders() -> pd.DataFrame:
    """Build representative cleaned order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3"],
            "product_id": ["P-1", "P-2", "P-1", "P-3"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T12:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                    "2026-01-02T10:05:00Z",
                    "2026-01-02T12:05:00Z",
                ],
                utc=True,
            ),
        }
    )


def make_customers() -> pd.DataFrame:
    """Build representative customer reference data."""
    return pd.DataFrame(
        {
            "customer_id": ["C-1", "C-2", "C-3"],
            "segment": [
                "premium",
                "standard",
                "enterprise",
            ],
        }
    )


def test_enrich_orders_adds_customer_segment() -> None:
    result = enrich_orders(
        make_orders(),
        make_customers(),
    )

    assert "segment" in result.columns
    assert result["segment"].tolist() == [
        "premium",
        "premium",
        "standard",
        "enterprise",
    ]


def test_enrich_orders_preserves_order_grain() -> None:
    orders = make_orders()

    result = enrich_orders(
        orders,
        make_customers(),
    )

    assert len(result) == len(orders)
    assert result["order_id"].tolist() == orders[
        "order_id"
    ].tolist()


def test_enrich_orders_preserves_order_column_values() -> None:
    orders = make_orders()

    result = enrich_orders(
        orders,
        make_customers(),
    )

    pd.testing.assert_series_equal(
        result["order_id"],
        orders["order_id"],
        check_names=False,
    )
    pd.testing.assert_series_equal(
        result["amount"],
        orders["amount"],
        check_names=False,
    )


def test_enrich_orders_rejects_duplicate_customer_ids() -> None:
    customers = pd.concat(
        [
            make_customers(),
            pd.DataFrame(
                {
                    "customer_id": ["C-1"],
                    "segment": ["standard"],
                }
            ),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        TransformationError,
        match="duplicate customer_id",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_enrich_orders_rejects_missing_customer_reference() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    with pytest.raises(
        TransformationError,
        match="do not exist",
    ):
        enrich_orders(
            orders,
            make_customers(),
        )


def test_enrich_orders_rejects_null_customer_ids() -> None:
    customers = make_customers()
    customers.loc[0, "customer_id"] = None

    with pytest.raises(
        TransformationError,
        match="null customer_id",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_enrich_orders_rejects_missing_order_columns() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        enrich_orders(
            orders,
            make_customers(),
        )


def test_enrich_orders_rejects_missing_customer_columns() -> None:
    customers = make_customers().drop(
        columns=["segment"],
    )

    with pytest.raises(
        TransformationError,
        match="customers is missing required columns",
    ):
        enrich_orders(
            make_orders(),
            customers,
        )


def test_add_order_metrics_adds_completion_flag() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["is_completed"].tolist() == [
        True,
        True,
        False,
        True,
    ]


def test_add_order_metrics_adds_net_revenue() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["net_revenue"].tolist() == [
        100.0,
        200.0,
        0.0,
        300.0,
    ]


def test_add_order_metrics_adds_order_date() -> None:
    result = add_order_metrics(
        make_orders(),
    )

    assert result["order_date"].tolist() == [
        pd.Timestamp("2026-01-01").date(),
        pd.Timestamp("2026-01-01").date(),
        pd.Timestamp("2026-01-02").date(),
        pd.Timestamp("2026-01-02").date(),
    ]


def test_add_order_metrics_does_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    add_order_metrics(
        orders,
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_add_order_metrics_requires_datetime_created_at() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        TransformationError,
        match="created_at must be a datetime-like",
    ):
        add_order_metrics(
            orders,
        )


def test_build_daily_sales_report_aggregates_completed_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_build_daily_sales_report_excludes_cancelled_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    report = build_daily_sales_report(
        orders,
    )

    assert not (
        report["order_date"]
        == pd.Timestamp("2026-01-02").date()
    ).empty
    assert report["revenue"].sum() == 600.0
    assert report["order_count"].sum() == 3


def test_build_daily_sales_report_counts_distinct_customers() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2"],
            "customer_id": ["C-1", "C-1"],
            "product_id": ["P-1", "P-2"],
            "status": ["completed", "completed"],
            "amount": [100.0, 200.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                ],
                utc=True,
            ),
            "segment": ["premium", "premium"],
        }
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.loc[0, "order_count"] == 2
    assert report.loc[0, "customer_count"] == 1
    assert report.loc[0, "revenue"] == 300.0
    assert report.loc[0, "average_order_value"] == 150.0


def test_build_daily_sales_report_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()
    orders["segment"] = pd.Series(
        dtype="string",
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.empty
    assert list(report.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_build_daily_sales_report_requires_datetime_created_at() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )
    orders["created_at"] = orders[
        "created_at"
    ].astype(str)

    with pytest.raises(
        TransformationError,
        match="created_at must be a datetime-like",
    ):
        build_daily_sales_report(
            orders,
        )


def test_build_customer_sales_summary_aggregates_by_customer() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert summary.to_dict("records") == [
        {
            "customer_id": "C-3",
            "segment": "enterprise",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "customer_id": "C-1",
            "segment": "premium",
            "order_count": 2,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
    ]


def test_build_customer_sales_summary_excludes_cancelled_orders() -> None:
    orders = enrich_orders(
        make_orders(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert "C-2" not in summary[
        "customer_id"
    ].tolist()
    assert summary["order_count"].sum() == 3
    assert summary["revenue"].sum() == 600.0


def test_build_customer_sales_summary_handles_empty_input() -> None:
    orders = enrich_orders(
        make_orders().iloc[0:0].copy(),
        make_customers(),
    )

    summary = build_customer_sales_summary(
        orders,
    )

    assert summary.empty
    assert list(summary.columns) == [
        "customer_id",
        "segment",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_transform_orders_returns_enriched_orders_and_daily_report() -> None:
    orders = make_orders()
    customers = make_customers()

    enriched, daily_report = transform_orders(
        orders,
        customers,
    )

    assert len(enriched) == len(orders)
    assert "segment" in enriched.columns
    assert "is_completed" in enriched.columns
    assert "net_revenue" in enriched.columns
    assert "order_date" in enriched.columns

    assert daily_report["revenue"].sum() == 600.0
    assert daily_report["order_count"].sum() == 3


def test_transform_orders_preserves_total_completed_revenue() -> None:
    orders = make_orders()
    customers = make_customers()

    enriched, daily_report = transform_orders(
        orders,
        customers,
    )

    expected_revenue = orders.loc[
        orders["status"].eq("completed"),
        "amount",
    ].sum()

    assert enriched["net_revenue"].sum() == expected_revenue
    assert daily_report["revenue"].sum() == expected_revenue


def test_transform_orders_does_not_mutate_inputs() -> None:
    orders = make_orders()
    customers = make_customers()

    original_orders = orders.copy(deep=True)
    original_customers = customers.copy(deep=True)

    transform_orders(
        orders,
        customers,
    )

    pd.testing.assert_frame_equal(
        orders,
        original_orders,
    )
    pd.testing.assert_frame_equal(
        customers,
        original_customers,
    )


def test_build_daily_sales_report_requires_segment_column() -> None:
    orders = make_orders()

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        build_daily_sales_report(
            orders,
        )


def test_build_customer_sales_summary_requires_segment_column() -> None:
    orders = make_orders()

    with pytest.raises(
        TransformationError,
        match="orders is missing required columns",
    ):
        build_customer_sales_summary(
            orders,
        )


def test_build_daily_sales_report_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                ],
                utc=True,
            ),
            "segment": [
                "premium",
                "premium",
                "standard",
            ],
        }
    )

    report = build_daily_sales_report(
        orders,
    )

    assert report.loc[0, "order_count"] == 2
    assert report.loc[0, "customer_count"] == 2
    assert report.loc[0, "revenue"] == 300.0
    assert report.loc[0, "average_order_value"] == 150.0