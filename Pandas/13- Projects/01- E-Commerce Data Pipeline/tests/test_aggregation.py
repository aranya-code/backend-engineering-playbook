from __future__ import annotations

import pandas as pd
import pytest

from src.aggregation import (
    AggregationError,
    aggregate_customer_sales,
    aggregate_daily_sales,
    aggregate_daily_segment_sales,
    aggregate_orders,
    aggregate_pipeline_metrics,
    aggregate_product_sales,
    aggregate_segment_sales,
    calculate_average_order_value,
    calculate_total_revenue,
)


def make_orders() -> pd.DataFrame:
    """Build representative enriched order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4", "O-5"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3", "C-4"],
            "product_id": ["P-1", "P-2", "P-1", "P-3", "P-2"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0, 150.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-01T12:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T11:00:00Z",
                ],
                utc=True,
            ),
            "segment": [
                "premium",
                "premium",
                "standard",
                "enterprise",
                "standard",
            ],
        }
    )


def test_aggregate_customer_sales() -> None:
    result = aggregate_customer_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "customer_id": "C-3",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "customer_id": "C-4",
            "order_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
        {
            "customer_id": "C-1",
            "order_count": 2,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
    ]


def test_aggregate_customer_sales_excludes_cancelled_orders() -> None:
    result = aggregate_customer_sales(
        make_orders(),
    )

    assert "C-2" not in result["customer_id"].tolist()
    assert result["order_count"].sum() == 4
    assert result["revenue"].sum() == 750.0


def test_aggregate_product_sales() -> None:
    result = aggregate_product_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "product_id": "P-2",
            "order_count": 2,
            "revenue": 350.0,
            "average_order_value": 175.0,
        },
        {
            "product_id": "P-1",
            "order_count": 1,
            "revenue": 100.0,
            "average_order_value": 100.0,
        },
        {
            "product_id": "P-3",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_aggregate_daily_sales() -> None:
    result = aggregate_daily_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "order_count": 2,
            "customer_count": 2,
            "revenue": 450.0,
            "average_order_value": 225.0,
        },
    ]


def test_aggregate_segment_sales() -> None:
    result = aggregate_segment_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "segment": "premium",
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
    ]


def test_aggregate_daily_segment_sales() -> None:
    result = aggregate_daily_segment_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "segment": "premium",
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
    ]


def test_calculate_total_revenue() -> None:
    assert calculate_total_revenue(
        make_orders(),
    ) == 750.0


def test_calculate_total_revenue_returns_zero_when_no_completed_orders() -> None:
    orders = make_orders()
    orders["status"] = "cancelled"

    assert calculate_total_revenue(
        orders,
    ) == 0.0


def test_calculate_average_order_value() -> None:
    assert calculate_average_order_value(
        make_orders(),
    ) == 187.5


def test_calculate_average_order_value_uses_unique_order_grain() -> None:
    orders = make_orders()
    duplicate = orders.loc[[0]].copy()
    duplicate["product_id"] = "P-9"
    duplicate["amount"] = 25.0

    combined = pd.concat(
        [
            orders,
            duplicate,
        ],
        ignore_index=True,
    )

    assert calculate_average_order_value(
        combined,
    ) == 218.75


def test_aggregate_pipeline_metrics() -> None:
    result = aggregate_pipeline_metrics(
        make_orders(),
    )

    assert result == {
        "input_rows": 5,
        "completed_rows": 4,
        "unique_orders": 5,
        "unique_customers": 4,
        "total_revenue": 750.0,
        "average_order_value": 187.5,
    }


def test_aggregate_orders_supports_custom_grouping() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["product_id", "segment"],
    )

    assert result.to_dict("records") == [
        {
            "product_id": "P-1",
            "segment": "premium",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 100.0,
            "average_order_value": 100.0,
        },
        {
            "product_id": "P-2",
            "segment": "premium",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 200.0,
            "average_order_value": 200.0,
        },
        {
            "product_id": "P-2",
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
        {
            "product_id": "P-3",
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_aggregate_orders_excludes_cancelled_orders() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["product_id"],
    )

    assert result["revenue"].sum() == 750.0
    assert result["order_count"].sum() == 4


def test_aggregate_customer_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_customer_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "customer_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_product_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_product_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "product_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_daily_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_daily_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_segment_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_segment_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "segment",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_daily_segment_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_daily_segment_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "order_date",
        "segment",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_orders_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_orders(
        orders,
        grouping_columns=["product_id"],
    )

    assert result.empty
    assert list(result.columns) == [
        "product_id",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


@pytest.mark.parametrize(
    "function,required_grouping",
    [
        (aggregate_customer_sales, None),
        (aggregate_product_sales, None),
        (aggregate_daily_sales, None),
        (aggregate_segment_sales, None),
        (aggregate_daily_segment_sales, None),
    ],
)
def test_aggregation_functions_raise_for_missing_columns(
    function,
    required_grouping,
) -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    with pytest.raises(
        AggregationError,
        match="missing required columns",
    ):
        if required_grouping is None:
            function(orders)
        else:
            function(
                orders,
                grouping_columns=required_grouping,
            )


def test_aggregate_orders_raises_for_missing_grouping_column() -> None:
    orders = make_orders()

    with pytest.raises(
        AggregationError,
        match="missing required columns",
    ):
        aggregate_orders(
            orders,
            grouping_columns=["unknown_column"],
        )


def test_aggregate_daily_sales_requires_datetime_column() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        AggregationError,
        match="created_at must be a datetime-like",
    ):
        aggregate_daily_sales(
            orders,
        )


def test_aggregate_daily_segment_sales_requires_datetime_column() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        AggregationError,
        match="created_at must be a datetime-like",
    ):
        aggregate_daily_segment_sales(
            orders,
        )


def test_aggregate_functions_do_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    aggregate_customer_sales(orders)
    aggregate_product_sales(orders)
    aggregate_daily_sales(orders)
    aggregate_segment_sales(orders)
    aggregate_daily_segment_sales(orders)
    aggregate_orders(
        orders,
        grouping_columns=["product_id"],
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_aggregate_daily_sales_counts_distinct_customers() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [100.0, 200.0, 300.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-01T12:00:00Z",
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

    result = aggregate_daily_sales(
        orders,
    )

    assert result.loc[0, "order_count"] == 3
    assert result.loc[0, "customer_count"] == 2
    assert result.loc[0, "revenue"] == 600.0
    assert result.loc[0, "average_order_value"] == 200.0


def test_aggregate_customer_sales_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-1"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
        }
    )

    result = aggregate_customer_sales(
        orders,
    )

    assert result.loc[0, "customer_id"] == "C-1"
    assert result.loc[0, "order_count"] == 2
    assert result.loc[0, "revenue"] == 300.0
    assert result.loc[0, "average_order_value"] == 150.0


def test_aggregate_product_sales_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-1", "P-1"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
        }
    )

    result = aggregate_product_sales(
        orders,
    )

    assert result.loc[0, "product_id"] == "P-1"
    assert result.loc[0, "order_count"] == 2
    assert result.loc[0, "revenue"] == 300.0
    assert result.loc[0, "average_order_value"] == 150.0


def test_aggregate_orders_supports_multiple_dimensions() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["segment", "product_id"],
    )

    assert set(
        map(
            tuple,
            result[["segment", "product_id"]].to_numpy(),
        )
    ) == {
        ("premium", "P-1"),
        ("premium", "P-2"),
        ("enterprise", "P-3"),
        ("standard", "P-2"),
    }


def test_aggregate_orders_accepts_tuple_grouping() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=("product_id",),
    )

    assert list(result.columns) == [
        "product_id",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_pipeline_metrics_uses_unique_customer_count() -> None:
    orders = make_orders()

    result = aggregate_pipeline_metrics(
        orders,
    )

    assert result["unique_customers"] == 4
    assert result["unique_orders"] == 5


def test_aggregation_functions_reject_non_dataframe_input() -> None:
    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_customer_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_product_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_daily_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_segment_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_daily_segment_sales([])  # type: ignore[arg-type]


def test_calculate_average_order_value_returns_zero_for_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    assert calculate_average_order_value(
        orders,
    ) == 0.0


def test_calculate_total_revenue_returns_zero_for_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    assert calculate_total_revenue(
        orders,
    ) == 0.0

from __future__ import annotations

import pandas as pd
import pytest

from src.aggregation import (
    AggregationError,
    aggregate_customer_sales,
    aggregate_daily_sales,
    aggregate_daily_segment_sales,
    aggregate_orders,
    aggregate_pipeline_metrics,
    aggregate_product_sales,
    aggregate_segment_sales,
    calculate_average_order_value,
    calculate_total_revenue,
)


def make_orders() -> pd.DataFrame:
    """Build representative enriched order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4", "O-5"],
            "customer_id": ["C-1", "C-1", "C-2", "C-3", "C-4"],
            "product_id": ["P-1", "P-2", "P-1", "P-3", "P-2"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "completed",
                "completed",
            ],
            "amount": [100.0, 200.0, 50.0, 300.0, 150.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-01T12:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T11:00:00Z",
                ],
                utc=True,
            ),
            "segment": [
                "premium",
                "premium",
                "standard",
                "enterprise",
                "standard",
            ],
        }
    )


def test_aggregate_customer_sales() -> None:
    result = aggregate_customer_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "customer_id": "C-3",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "customer_id": "C-4",
            "order_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
        {
            "customer_id": "C-1",
            "order_count": 2,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
    ]


def test_aggregate_customer_sales_excludes_cancelled_orders() -> None:
    result = aggregate_customer_sales(
        make_orders(),
    )

    assert "C-2" not in result["customer_id"].tolist()
    assert result["order_count"].sum() == 4
    assert result["revenue"].sum() == 750.0


def test_aggregate_product_sales() -> None:
    result = aggregate_product_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "product_id": "P-2",
            "order_count": 2,
            "revenue": 350.0,
            "average_order_value": 175.0,
        },
        {
            "product_id": "P-1",
            "order_count": 1,
            "revenue": 100.0,
            "average_order_value": 100.0,
        },
        {
            "product_id": "P-3",
            "order_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_aggregate_daily_sales() -> None:
    result = aggregate_daily_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "order_count": 2,
            "customer_count": 2,
            "revenue": 450.0,
            "average_order_value": 225.0,
        },
    ]


def test_aggregate_segment_sales() -> None:
    result = aggregate_segment_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "segment": "premium",
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
    ]


def test_aggregate_daily_segment_sales() -> None:
    result = aggregate_daily_segment_sales(
        make_orders(),
    )

    assert result.to_dict("records") == [
        {
            "order_date": pd.Timestamp("2026-01-01").date(),
            "segment": "premium",
            "order_count": 2,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 150.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
        {
            "order_date": pd.Timestamp("2026-01-02").date(),
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
    ]


def test_calculate_total_revenue() -> None:
    assert calculate_total_revenue(
        make_orders(),
    ) == 750.0


def test_calculate_total_revenue_returns_zero_when_no_completed_orders() -> None:
    orders = make_orders()
    orders["status"] = "cancelled"

    assert calculate_total_revenue(
        orders,
    ) == 0.0


def test_calculate_average_order_value() -> None:
    assert calculate_average_order_value(
        make_orders(),
    ) == 187.5


def test_calculate_average_order_value_uses_unique_order_grain() -> None:
    orders = make_orders()
    duplicate = orders.loc[[0]].copy()
    duplicate["product_id"] = "P-9"
    duplicate["amount"] = 25.0

    combined = pd.concat(
        [
            orders,
            duplicate,
        ],
        ignore_index=True,
    )

    assert calculate_average_order_value(
        combined,
    ) == 218.75


def test_aggregate_pipeline_metrics() -> None:
    result = aggregate_pipeline_metrics(
        make_orders(),
    )

    assert result == {
        "input_rows": 5,
        "completed_rows": 4,
        "unique_orders": 5,
        "unique_customers": 4,
        "total_revenue": 750.0,
        "average_order_value": 187.5,
    }


def test_aggregate_orders_supports_custom_grouping() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["product_id", "segment"],
    )

    assert result.to_dict("records") == [
        {
            "product_id": "P-1",
            "segment": "premium",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 100.0,
            "average_order_value": 100.0,
        },
        {
            "product_id": "P-2",
            "segment": "premium",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 200.0,
            "average_order_value": 200.0,
        },
        {
            "product_id": "P-2",
            "segment": "standard",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 150.0,
            "average_order_value": 150.0,
        },
        {
            "product_id": "P-3",
            "segment": "enterprise",
            "order_count": 1,
            "customer_count": 1,
            "revenue": 300.0,
            "average_order_value": 300.0,
        },
    ]


def test_aggregate_orders_excludes_cancelled_orders() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["product_id"],
    )

    assert result["revenue"].sum() == 750.0
    assert result["order_count"].sum() == 4


def test_aggregate_customer_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_customer_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "customer_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_product_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_product_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "product_id",
        "order_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_daily_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_daily_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "order_date",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_segment_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_segment_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "segment",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_daily_segment_sales_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_daily_segment_sales(
        orders,
    )

    assert result.empty
    assert list(result.columns) == [
        "order_date",
        "segment",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_orders_handles_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    result = aggregate_orders(
        orders,
        grouping_columns=["product_id"],
    )

    assert result.empty
    assert list(result.columns) == [
        "product_id",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


@pytest.mark.parametrize(
    "function,required_grouping",
    [
        (aggregate_customer_sales, None),
        (aggregate_product_sales, None),
        (aggregate_daily_sales, None),
        (aggregate_segment_sales, None),
        (aggregate_daily_segment_sales, None),
    ],
)
def test_aggregation_functions_raise_for_missing_columns(
    function,
    required_grouping,
) -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    with pytest.raises(
        AggregationError,
        match="missing required columns",
    ):
        if required_grouping is None:
            function(orders)
        else:
            function(
                orders,
                grouping_columns=required_grouping,
            )


def test_aggregate_orders_raises_for_missing_grouping_column() -> None:
    orders = make_orders()

    with pytest.raises(
        AggregationError,
        match="missing required columns",
    ):
        aggregate_orders(
            orders,
            grouping_columns=["unknown_column"],
        )


def test_aggregate_daily_sales_requires_datetime_column() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        AggregationError,
        match="created_at must be a datetime-like",
    ):
        aggregate_daily_sales(
            orders,
        )


def test_aggregate_daily_segment_sales_requires_datetime_column() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    with pytest.raises(
        AggregationError,
        match="created_at must be a datetime-like",
    ):
        aggregate_daily_segment_sales(
            orders,
        )


def test_aggregate_functions_do_not_mutate_input() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    aggregate_customer_sales(orders)
    aggregate_product_sales(orders)
    aggregate_daily_sales(orders)
    aggregate_segment_sales(orders)
    aggregate_daily_segment_sales(orders)
    aggregate_orders(
        orders,
        grouping_columns=["product_id"],
    )

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_aggregate_daily_sales_counts_distinct_customers() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [100.0, 200.0, 300.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-01T12:00:00Z",
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

    result = aggregate_daily_sales(
        orders,
    )

    assert result.loc[0, "order_count"] == 3
    assert result.loc[0, "customer_count"] == 2
    assert result.loc[0, "revenue"] == 600.0
    assert result.loc[0, "average_order_value"] == 200.0


def test_aggregate_customer_sales_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-1"],
            "product_id": ["P-1", "P-2", "P-3"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
        }
    )

    result = aggregate_customer_sales(
        orders,
    )

    assert result.loc[0, "customer_id"] == "C-1"
    assert result.loc[0, "order_count"] == 2
    assert result.loc[0, "revenue"] == 300.0
    assert result.loc[0, "average_order_value"] == 150.0


def test_aggregate_product_sales_counts_distinct_orders() -> None:
    orders = pd.DataFrame(
        {
            "order_id": ["O-1", "O-1", "O-2"],
            "customer_id": ["C-1", "C-1", "C-2"],
            "product_id": ["P-1", "P-1", "P-1"],
            "status": [
                "completed",
                "completed",
                "completed",
            ],
            "amount": [60.0, 40.0, 200.0],
        }
    )

    result = aggregate_product_sales(
        orders,
    )

    assert result.loc[0, "product_id"] == "P-1"
    assert result.loc[0, "order_count"] == 2
    assert result.loc[0, "revenue"] == 300.0
    assert result.loc[0, "average_order_value"] == 150.0


def test_aggregate_orders_supports_multiple_dimensions() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=["segment", "product_id"],
    )

    assert set(
        map(
            tuple,
            result[["segment", "product_id"]].to_numpy(),
        )
    ) == {
        ("premium", "P-1"),
        ("premium", "P-2"),
        ("enterprise", "P-3"),
        ("standard", "P-2"),
    }


def test_aggregate_orders_accepts_tuple_grouping() -> None:
    result = aggregate_orders(
        make_orders(),
        grouping_columns=("product_id",),
    )

    assert list(result.columns) == [
        "product_id",
        "order_count",
        "customer_count",
        "revenue",
        "average_order_value",
    ]


def test_aggregate_pipeline_metrics_uses_unique_customer_count() -> None:
    orders = make_orders()

    result = aggregate_pipeline_metrics(
        orders,
    )

    assert result["unique_customers"] == 4
    assert result["unique_orders"] == 5


def test_aggregation_functions_reject_non_dataframe_input() -> None:
    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_customer_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_product_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_daily_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_segment_sales([])  # type: ignore[arg-type]

    with pytest.raises(
        AggregationError,
        match="must be a pandas DataFrame",
    ):
        aggregate_daily_segment_sales([])  # type: ignore[arg-type]


def test_calculate_average_order_value_returns_zero_for_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    assert calculate_average_order_value(
        orders,
    ) == 0.0


def test_calculate_total_revenue_returns_zero_for_empty_input() -> None:
    orders = make_orders().iloc[0:0].copy()

    assert calculate_total_revenue(
        orders,
    ) == 0.0