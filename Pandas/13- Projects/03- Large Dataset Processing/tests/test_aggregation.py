from __future__ import annotations

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.aggregation import (
    AggregationError,
    AggregationResult,
    aggregate_chunk,
    aggregate_distinct_counts,
    aggregate_multiple_metrics,
    aggregate_overall_metrics,
    aggregate_row_counts,
    aggregate_sum_and_count,
    aggregate_weighted_average,
    aggregate_with_metrics,
    calculate_derived_metrics,
    merge_chunk_aggregates,
)


def _sales_frame() -> pd.DataFrame:
    """Build a representative transactional dataset."""
    return pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "south",
                "south",
                "south",
            ],
            "product": [
                "laptop",
                "laptop",
                "phone",
                "phone",
                "tablet",
            ],
            "order_id": [
                "1001",
                "1002",
                "1003",
                "1004",
                "1005",
            ],
            "revenue": [
                1000.0,
                1200.0,
                800.0,
                900.0,
                500.0,
            ],
            "quantity": [
                2,
                3,
                4,
                5,
                2,
            ],
            "weight": [
                2.0,
                3.0,
                4.0,
                5.0,
                2.0,
            ],
        }
    )


def test_aggregate_chunk_groups_and_sums_by_dimension() -> None:
    result = aggregate_chunk(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation="sum",
    )

    expected = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue": [
                2200.0,
                2200.0,
            ],
        }
    )

    assert_frame_equal(
        result.sort_values("region").reset_index(drop=True),
        expected,
    )


@pytest.mark.parametrize(
    "aggregation,expected_north",
    [
        ("sum", 2200.0),
        ("mean", 1100.0),
        ("min", 1000.0),
        ("max", 1200.0),
        ("count", 2.0),
        ("median", 1100.0),
        ("std", pytest.approx(141.4213562373095)),
        ("var", pytest.approx(20000.0)),
    ],
)
def test_aggregate_chunk_supports_expected_aggregation_functions(
    aggregation: str,
    expected_north: float,
) -> None:
    result = aggregate_chunk(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation=aggregation,
    )

    north_value = result.loc[
        result["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north_value == expected_north


def test_aggregate_chunk_converts_numeric_values_before_aggregation() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north"],
            "revenue": ["100.50", "200.25"],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert result["revenue"].tolist() == [
        pytest.approx(300.75)
    ]


def test_aggregate_chunk_handles_invalid_numeric_values_as_missing() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north", "south"],
            "revenue": ["100.0", "invalid", "50.0"],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    north_value = result.loc[
        result["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north_value == pytest.approx(100.0)


def test_aggregate_chunk_requires_at_least_one_dimension() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=(),
            value_column="revenue",
        )


def test_aggregate_chunk_rejects_missing_columns() -> None:
    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("missing",),
            value_column="revenue",
        )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("region",),
            value_column="missing",
        )


def test_aggregate_chunk_rejects_unsupported_aggregation() -> None:
    with pytest.raises(
        AggregationError,
        match="Unsupported aggregation",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("region",),
            value_column="revenue",
            aggregation="unsupported",
        )


def test_aggregate_chunk_respects_dropna_false_for_groups() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                None,
                "north",
            ],
            "revenue": [
                100.0,
                200.0,
                50.0,
            ],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
        dropna=False,
    )

    assert result["revenue"].sum() == pytest.approx(
        350.0
    )
    assert result.loc[
        result["region"].isna(),
        "revenue",
    ].iloc[0] == pytest.approx(200.0)


def test_aggregate_multiple_metrics_produces_flat_column_names() -> None:
    result = aggregate_multiple_metrics(
        _sales_frame(),
        dimensions=("region",),
        aggregations={
            "revenue": ("sum", "mean"),
            "quantity": ("sum", "max"),
        },
    )

    assert result.columns.tolist() == [
        "region",
        "revenue_sum",
        "revenue_mean",
        "quantity_sum",
        "quantity_max",
    ]

    north = result.loc[
        result["region"].eq("north")
    ].iloc[0]

    assert north["revenue_sum"] == pytest.approx(2200.0)
    assert north["revenue_mean"] == pytest.approx(1100.0)
    assert north["quantity_sum"] == 5
    assert north["quantity_max"] == 3


def test_aggregate_multiple_metrics_supports_multiple_dimensions() -> None:
    result = aggregate_multiple_metrics(
        _sales_frame(),
        dimensions=("region", "product"),
        aggregations={
            "revenue": ("sum",),
            "quantity": ("sum",),
        },
    )

    assert set(
        result[["region", "product"]]
        .itertuples(index=False, name=None)
    ) == {
        ("north", "laptop"),
        ("south", "phone"),
        ("south", "tablet"),
    }


def test_aggregate_multiple_metrics_requires_aggregations() -> None:
    with pytest.raises(
        AggregationError,
        match="aggregation specification",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={},
        )


def test_aggregate_multiple_metrics_rejects_missing_value_columns() -> None:
    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={
                "missing": ("sum",),
            },
        )


def test_aggregate_multiple_metrics_rejects_unsupported_method() -> None:
    with pytest.raises(
        AggregationError,
        match="Unsupported aggregation",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={
                "revenue": ("unsupported",),
            },
        )


def test_aggregate_row_counts_calculates_group_sizes() -> None:
    result = aggregate_row_counts(
        _sales_frame(),
        dimensions=("region",),
    )

    north_count = result.loc[
        result["region"].eq("north"),
        "row_count",
    ].iloc[0]
    south_count = result.loc[
        result["region"].eq("south"),
        "row_count",
    ].iloc[0]

    assert north_count == 2
    assert south_count == 3


def test_aggregate_row_counts_supports_custom_output_column() -> None:
    result = aggregate_row_counts(
        _sales_frame(),
        dimensions=("region",),
        output_column="orders",
    )

    assert "orders" in result.columns
    assert "row_count" not in result.columns


def test_aggregate_row_counts_requires_dimension() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_row_counts(
            _sales_frame(),
            dimensions=(),
        )


def test_aggregate_distinct_counts_counts_unique_values() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "north",
                "south",
            ],
            "customer_id": [
                "C001",
                "C001",
                "C002",
                "C003",
            ],
        }
    )

    result = aggregate_distinct_counts(
        frame,
        dimensions=("region",),
        value_column="customer_id",
    )

    north_count = result.loc[
        result["region"].eq("north"),
        "unique_count",
    ].iloc[0]
    south_count = result.loc[
        result["region"].eq("south"),
        "unique_count",
    ].iloc[0]

    assert north_count == 2
    assert south_count == 1


def test_aggregate_distinct_counts_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "north",
            ],
            "customer_id": [
                "C001",
                None,
                "C001",
            ],
        }
    )

    result = aggregate_distinct_counts(
        frame,
        dimensions=("region",),
        value_column="customer_id",
    )

    assert result["unique_count"].iloc[0] == 1


def test_aggregate_weighted_average_calculates_expected_result() -> None:
    result = aggregate_weighted_average(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        weight_column="quantity",
    )

    north = result.loc[
        result["region"].eq("north"),
        "weighted_average",
    ].iloc[0]

    expected = (
        (1000.0 * 2) + (1200.0 * 3)
    ) / 5

    assert north == pytest.approx(
        expected
    )


def test_aggregate_weighted_average_returns_missing_for_zero_weight() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north"],
            "revenue": [100.0],
            "weight": [0.0],
        }
    )

    result = aggregate_weighted_average(
        frame,
        dimensions=("region",),
        value_column="revenue",
        weight_column="weight",
    )

    assert pd.isna(
        result["weighted_average"].iloc[0]
    )


def test_aggregate_weighted_average_supports_custom_output_column() -> None:
    result = aggregate_weighted_average(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        weight_column="quantity",
        output_column="weighted_revenue",
    )

    assert "weighted_revenue" in result.columns
    assert "weighted_average" not in result.columns


def test_aggregate_weighted_average_requires_dimensions() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_weighted_average(
            _sales_frame(),
            dimensions=(),
            value_column="revenue",
            weight_column="quantity",
        )


def test_merge_chunk_aggregates_combines_partial_sums() -> None:
    first = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                100.0,
                200.0,
            ],
        }
    )

    second = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                50.0,
                300.0,
            ],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=("revenue_sum",),
    )

    expected = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                150.0,
                500.0,
            ],
        }
    )

    assert_frame_equal(
        result.sort_values("region").reset_index(drop=True),
        expected,
    )


def test_merge_chunk_aggregates_returns_expected_schema_for_empty_input() -> None:
    result = merge_chunk_aggregates(
        [],
        dimensions=("region",),
        value_columns=("revenue_sum",),
    )

    assert result.empty
    assert result.columns.tolist() == [
        "region",
        "revenue_sum",
    ]


def test_merge_chunk_aggregates_merges_multiple_value_columns() -> None:
    first = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [100.0],
            "order_count": [2],
        }
    )

    second = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [200.0],
            "order_count": [3],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=("revenue_sum", "order_count"),
    )

    north = result.iloc[0]

    assert north["revenue_sum"] == pytest.approx(300.0)
    assert north["order_count"] == 5


def test_merge_chunk_aggregates_deduplicates_dimension_rows_when_no_values() -> None:
    first = pd.DataFrame(
        {
            "region": ["north", "south"],
        }
    )

    second = pd.DataFrame(
        {
            "region": ["north", "west"],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=(),
    )

    assert set(
        result["region"]
    ) == {
        "north",
        "south",
        "west",
    }


def test_merge_chunk_aggregates_rejects_missing_columns() -> None:
    invalid = pd.DataFrame(
        {
            "region": ["north"],
        }
    )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        merge_chunk_aggregates(
            [invalid],
            dimensions=("region",),
            value_columns=("revenue_sum",),
        )


def test_aggregate_sum_and_count_produces_both_metrics() -> None:
    result = aggregate_sum_and_count(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    north = result.loc[
        result["region"].eq("north")
    ].iloc[0]

    assert north["value_sum"] == pytest.approx(2200.0)
    assert north["row_count"] == 2


def test_aggregate_sum_and_count_supports_custom_output_columns() -> None:
    result = aggregate_sum_and_count(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        value_sum_column="revenue_total",
        row_count_column="orders",
    )

    assert "revenue_total" in result.columns
    assert "orders" in result.columns


def test_aggregate_sum_and_count_counts_only_numeric_non_null_values() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north", "north"],
            "revenue": ["100.0", None, "invalid"],
        }
    )

    result = aggregate_sum_and_count(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    north = result.iloc[0]

    assert north["value_sum"] == pytest.approx(100.0)
    assert north["row_count"] == 1


def test_calculate_derived_metrics_adds_average_order_value() -> None:
    aggregate = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                2200.0,
                1500.0,
            ],
            "order_count": [
                2,
                3,
            ],
        }
    )

    result = calculate_derived_metrics(
        aggregate
    )

    assert result["average_order_value"].tolist() == [
        pytest.approx(1100.0),
        pytest.approx(500.0),
    ]


def test_calculate_derived_metrics_returns_missing_for_zero_orders() -> None:
    aggregate = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [2200.0],
            "order_count": [0],
        }
    )

    result = calculate_derived_metrics(
        aggregate
    )

    assert pd.isna(
        result["average_order_value"].iloc[0]
    )


def test_calculate_derived_metrics_supports_custom_column_name() -> None:
    aggregate = pd.DataFrame(
        {
            "revenue_sum": [1000.0],
            "order_count": [10],
        }
    )

    result = calculate_derived_metrics(
        aggregate,
        average_order_value_column="aov",
    )

    assert "aov" in result.columns
    assert "average_order_value" not in result.columns


def test_calculate_derived_metrics_validates_required_columns() -> None:
    aggregate = pd.DataFrame(
        {
            "revenue_sum": [1000.0],
        }
    )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        calculate_derived_metrics(
            aggregate
        )


def test_aggregate_overall_metrics_calculates_dataset_statistics() -> None:
    result = aggregate_overall_metrics(
        _sales_frame(),
        value_column="revenue",
    )

    assert result["row_count"] == 5
    assert result["non_null_count"] == 5
    assert result["numeric_sum"] == pytest.approx(
        4400.0
    )
    assert result["numeric_mean"] == pytest.approx(
        880.0
    )
    assert result["numeric_min"] == pytest.approx(
        500.0
    )
    assert result["numeric_max"] == pytest.approx(
        1200.0
    )


def test_aggregate_overall_metrics_ignores_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [
                "100.0",
                "invalid",
                "300.0",
            ]
        }
    )

    result = aggregate_overall_metrics(
        frame,
        value_column="revenue",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 2
    assert result["numeric_sum"] == pytest.approx(
        400.0
    )
    assert result["numeric_mean"] == pytest.approx(
        200.0
    )


def test_aggregate_overall_metrics_returns_zero_statistics_for_no_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [
                None,
                None,
            ]
        }
    )

    result = aggregate_overall_metrics(
        frame,
        value_column="revenue",
    )

    assert result["row_count"] == 2
    assert result["non_null_count"] == 0
    assert result["numeric_sum"] == pytest.approx(
        0.0
    )
    assert result["numeric_mean"] == pytest.approx(
        0.0
    )
    assert result["numeric_min"] == pytest.approx(
        0.0
    )
    assert result["numeric_max"] == pytest.approx(
        0.0
    )


def test_aggregate_with_metrics_returns_aggregation_result() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    assert isinstance(
        result,
        AggregationResult,
    )
    assert result.metrics.input_rows == 5
    assert result.metrics.output_rows == 2
    assert result.metrics.groups == 2
    assert result.metrics.numeric_total == pytest.approx(
        4400.0
    )
    assert result.metrics.memory_bytes > 0


def test_aggregate_with_metrics_contains_expected_data() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    assert set(
        result.data["region"]
    ) == {
        "north",
        "south",
    }


def test_aggregate_with_metrics_supports_non_sum_aggregation() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation="mean",
    )

    north = result.data.loc[
        result.data["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north == pytest.approx(
        1100.0
    )


def test_aggregation_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        AggregationError,
        match="DataFrame",
    ):
        aggregate_chunk(
            "invalid",  # type: ignore[arg-type]
            dimensions=("region",),
            value_column="revenue",
        )


def test_aggregation_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        {
            "region": pd.Series(dtype="string"),
            "revenue": pd.Series(dtype="float64"),
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert result.empty
    assert result.columns.tolist() == [
        "region",
        "revenue",
    ]


def test_aggregation_preserves_dimension_values() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "south"],
            "revenue": [100.0, 200.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert set(
        result["region"]
    ) == {
        "north",
        "south",
    }

from __future__ import annotations

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.aggregation import (
    AggregationError,
    AggregationResult,
    aggregate_chunk,
    aggregate_distinct_counts,
    aggregate_multiple_metrics,
    aggregate_overall_metrics,
    aggregate_row_counts,
    aggregate_sum_and_count,
    aggregate_weighted_average,
    aggregate_with_metrics,
    calculate_derived_metrics,
    merge_chunk_aggregates,
)


def _sales_frame() -> pd.DataFrame:
    """Build a representative transactional dataset."""
    return pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "south",
                "south",
                "south",
            ],
            "product": [
                "laptop",
                "laptop",
                "phone",
                "phone",
                "tablet",
            ],
            "order_id": [
                "1001",
                "1002",
                "1003",
                "1004",
                "1005",
            ],
            "revenue": [
                1000.0,
                1200.0,
                800.0,
                900.0,
                500.0,
            ],
            "quantity": [
                2,
                3,
                4,
                5,
                2,
            ],
            "weight": [
                2.0,
                3.0,
                4.0,
                5.0,
                2.0,
            ],
        }
    )


def test_aggregate_chunk_groups_and_sums_by_dimension() -> None:
    result = aggregate_chunk(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation="sum",
    )

    expected = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue": [
                2200.0,
                2200.0,
            ],
        }
    )

    assert_frame_equal(
        result.sort_values("region").reset_index(drop=True),
        expected,
    )


@pytest.mark.parametrize(
    "aggregation,expected_north",
    [
        ("sum", 2200.0),
        ("mean", 1100.0),
        ("min", 1000.0),
        ("max", 1200.0),
        ("count", 2.0),
        ("median", 1100.0),
        ("std", pytest.approx(141.4213562373095)),
        ("var", pytest.approx(20000.0)),
    ],
)
def test_aggregate_chunk_supports_expected_aggregation_functions(
    aggregation: str,
    expected_north: float,
) -> None:
    result = aggregate_chunk(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation=aggregation,
    )

    north_value = result.loc[
        result["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north_value == expected_north


def test_aggregate_chunk_converts_numeric_values_before_aggregation() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north"],
            "revenue": ["100.50", "200.25"],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert result["revenue"].tolist() == [
        pytest.approx(300.75)
    ]


def test_aggregate_chunk_handles_invalid_numeric_values_as_missing() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north", "south"],
            "revenue": ["100.0", "invalid", "50.0"],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    north_value = result.loc[
        result["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north_value == pytest.approx(100.0)


def test_aggregate_chunk_requires_at_least_one_dimension() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=(),
            value_column="revenue",
        )


def test_aggregate_chunk_rejects_missing_columns() -> None:
    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("missing",),
            value_column="revenue",
        )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("region",),
            value_column="missing",
        )


def test_aggregate_chunk_rejects_unsupported_aggregation() -> None:
    with pytest.raises(
        AggregationError,
        match="Unsupported aggregation",
    ):
        aggregate_chunk(
            _sales_frame(),
            dimensions=("region",),
            value_column="revenue",
            aggregation="unsupported",
        )


def test_aggregate_chunk_respects_dropna_false_for_groups() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                None,
                "north",
            ],
            "revenue": [
                100.0,
                200.0,
                50.0,
            ],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
        dropna=False,
    )

    assert result["revenue"].sum() == pytest.approx(
        350.0
    )
    assert result.loc[
        result["region"].isna(),
        "revenue",
    ].iloc[0] == pytest.approx(200.0)


def test_aggregate_multiple_metrics_produces_flat_column_names() -> None:
    result = aggregate_multiple_metrics(
        _sales_frame(),
        dimensions=("region",),
        aggregations={
            "revenue": ("sum", "mean"),
            "quantity": ("sum", "max"),
        },
    )

    assert result.columns.tolist() == [
        "region",
        "revenue_sum",
        "revenue_mean",
        "quantity_sum",
        "quantity_max",
    ]

    north = result.loc[
        result["region"].eq("north")
    ].iloc[0]

    assert north["revenue_sum"] == pytest.approx(2200.0)
    assert north["revenue_mean"] == pytest.approx(1100.0)
    assert north["quantity_sum"] == 5
    assert north["quantity_max"] == 3


def test_aggregate_multiple_metrics_supports_multiple_dimensions() -> None:
    result = aggregate_multiple_metrics(
        _sales_frame(),
        dimensions=("region", "product"),
        aggregations={
            "revenue": ("sum",),
            "quantity": ("sum",),
        },
    )

    assert set(
        result[["region", "product"]]
        .itertuples(index=False, name=None)
    ) == {
        ("north", "laptop"),
        ("south", "phone"),
        ("south", "tablet"),
    }


def test_aggregate_multiple_metrics_requires_aggregations() -> None:
    with pytest.raises(
        AggregationError,
        match="aggregation specification",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={},
        )


def test_aggregate_multiple_metrics_rejects_missing_value_columns() -> None:
    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={
                "missing": ("sum",),
            },
        )


def test_aggregate_multiple_metrics_rejects_unsupported_method() -> None:
    with pytest.raises(
        AggregationError,
        match="Unsupported aggregation",
    ):
        aggregate_multiple_metrics(
            _sales_frame(),
            dimensions=("region",),
            aggregations={
                "revenue": ("unsupported",),
            },
        )


def test_aggregate_row_counts_calculates_group_sizes() -> None:
    result = aggregate_row_counts(
        _sales_frame(),
        dimensions=("region",),
    )

    north_count = result.loc[
        result["region"].eq("north"),
        "row_count",
    ].iloc[0]
    south_count = result.loc[
        result["region"].eq("south"),
        "row_count",
    ].iloc[0]

    assert north_count == 2
    assert south_count == 3


def test_aggregate_row_counts_supports_custom_output_column() -> None:
    result = aggregate_row_counts(
        _sales_frame(),
        dimensions=("region",),
        output_column="orders",
    )

    assert "orders" in result.columns
    assert "row_count" not in result.columns


def test_aggregate_row_counts_requires_dimension() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_row_counts(
            _sales_frame(),
            dimensions=(),
        )


def test_aggregate_distinct_counts_counts_unique_values() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "north",
                "south",
            ],
            "customer_id": [
                "C001",
                "C001",
                "C002",
                "C003",
            ],
        }
    )

    result = aggregate_distinct_counts(
        frame,
        dimensions=("region",),
        value_column="customer_id",
    )

    north_count = result.loc[
        result["region"].eq("north"),
        "unique_count",
    ].iloc[0]
    south_count = result.loc[
        result["region"].eq("south"),
        "unique_count",
    ].iloc[0]

    assert north_count == 2
    assert south_count == 1


def test_aggregate_distinct_counts_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "region": [
                "north",
                "north",
                "north",
            ],
            "customer_id": [
                "C001",
                None,
                "C001",
            ],
        }
    )

    result = aggregate_distinct_counts(
        frame,
        dimensions=("region",),
        value_column="customer_id",
    )

    assert result["unique_count"].iloc[0] == 1


def test_aggregate_weighted_average_calculates_expected_result() -> None:
    result = aggregate_weighted_average(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        weight_column="quantity",
    )

    north = result.loc[
        result["region"].eq("north"),
        "weighted_average",
    ].iloc[0]

    expected = (
        (1000.0 * 2) + (1200.0 * 3)
    ) / 5

    assert north == pytest.approx(
        expected
    )


def test_aggregate_weighted_average_returns_missing_for_zero_weight() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north"],
            "revenue": [100.0],
            "weight": [0.0],
        }
    )

    result = aggregate_weighted_average(
        frame,
        dimensions=("region",),
        value_column="revenue",
        weight_column="weight",
    )

    assert pd.isna(
        result["weighted_average"].iloc[0]
    )


def test_aggregate_weighted_average_supports_custom_output_column() -> None:
    result = aggregate_weighted_average(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        weight_column="quantity",
        output_column="weighted_revenue",
    )

    assert "weighted_revenue" in result.columns
    assert "weighted_average" not in result.columns


def test_aggregate_weighted_average_requires_dimensions() -> None:
    with pytest.raises(
        AggregationError,
        match="dimension",
    ):
        aggregate_weighted_average(
            _sales_frame(),
            dimensions=(),
            value_column="revenue",
            weight_column="quantity",
        )


def test_merge_chunk_aggregates_combines_partial_sums() -> None:
    first = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                100.0,
                200.0,
            ],
        }
    )

    second = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                50.0,
                300.0,
            ],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=("revenue_sum",),
    )

    expected = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                150.0,
                500.0,
            ],
        }
    )

    assert_frame_equal(
        result.sort_values("region").reset_index(drop=True),
        expected,
    )


def test_merge_chunk_aggregates_returns_expected_schema_for_empty_input() -> None:
    result = merge_chunk_aggregates(
        [],
        dimensions=("region",),
        value_columns=("revenue_sum",),
    )

    assert result.empty
    assert result.columns.tolist() == [
        "region",
        "revenue_sum",
    ]


def test_merge_chunk_aggregates_merges_multiple_value_columns() -> None:
    first = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [100.0],
            "order_count": [2],
        }
    )

    second = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [200.0],
            "order_count": [3],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=("revenue_sum", "order_count"),
    )

    north = result.iloc[0]

    assert north["revenue_sum"] == pytest.approx(300.0)
    assert north["order_count"] == 5


def test_merge_chunk_aggregates_deduplicates_dimension_rows_when_no_values() -> None:
    first = pd.DataFrame(
        {
            "region": ["north", "south"],
        }
    )

    second = pd.DataFrame(
        {
            "region": ["north", "west"],
        }
    )

    result = merge_chunk_aggregates(
        [first, second],
        dimensions=("region",),
        value_columns=(),
    )

    assert set(
        result["region"]
    ) == {
        "north",
        "south",
        "west",
    }


def test_merge_chunk_aggregates_rejects_missing_columns() -> None:
    invalid = pd.DataFrame(
        {
            "region": ["north"],
        }
    )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        merge_chunk_aggregates(
            [invalid],
            dimensions=("region",),
            value_columns=("revenue_sum",),
        )


def test_aggregate_sum_and_count_produces_both_metrics() -> None:
    result = aggregate_sum_and_count(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    north = result.loc[
        result["region"].eq("north")
    ].iloc[0]

    assert north["value_sum"] == pytest.approx(2200.0)
    assert north["row_count"] == 2


def test_aggregate_sum_and_count_supports_custom_output_columns() -> None:
    result = aggregate_sum_and_count(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        value_sum_column="revenue_total",
        row_count_column="orders",
    )

    assert "revenue_total" in result.columns
    assert "orders" in result.columns


def test_aggregate_sum_and_count_counts_only_numeric_non_null_values() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "north", "north"],
            "revenue": ["100.0", None, "invalid"],
        }
    )

    result = aggregate_sum_and_count(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    north = result.iloc[0]

    assert north["value_sum"] == pytest.approx(100.0)
    assert north["row_count"] == 1


def test_calculate_derived_metrics_adds_average_order_value() -> None:
    aggregate = pd.DataFrame(
        {
            "region": [
                "north",
                "south",
            ],
            "revenue_sum": [
                2200.0,
                1500.0,
            ],
            "order_count": [
                2,
                3,
            ],
        }
    )

    result = calculate_derived_metrics(
        aggregate
    )

    assert result["average_order_value"].tolist() == [
        pytest.approx(1100.0),
        pytest.approx(500.0),
    ]


def test_calculate_derived_metrics_returns_missing_for_zero_orders() -> None:
    aggregate = pd.DataFrame(
        {
            "region": ["north"],
            "revenue_sum": [2200.0],
            "order_count": [0],
        }
    )

    result = calculate_derived_metrics(
        aggregate
    )

    assert pd.isna(
        result["average_order_value"].iloc[0]
    )


def test_calculate_derived_metrics_supports_custom_column_name() -> None:
    aggregate = pd.DataFrame(
        {
            "revenue_sum": [1000.0],
            "order_count": [10],
        }
    )

    result = calculate_derived_metrics(
        aggregate,
        average_order_value_column="aov",
    )

    assert "aov" in result.columns
    assert "average_order_value" not in result.columns


def test_calculate_derived_metrics_validates_required_columns() -> None:
    aggregate = pd.DataFrame(
        {
            "revenue_sum": [1000.0],
        }
    )

    with pytest.raises(
        AggregationError,
        match="Missing required columns",
    ):
        calculate_derived_metrics(
            aggregate
        )


def test_aggregate_overall_metrics_calculates_dataset_statistics() -> None:
    result = aggregate_overall_metrics(
        _sales_frame(),
        value_column="revenue",
    )

    assert result["row_count"] == 5
    assert result["non_null_count"] == 5
    assert result["numeric_sum"] == pytest.approx(
        4400.0
    )
    assert result["numeric_mean"] == pytest.approx(
        880.0
    )
    assert result["numeric_min"] == pytest.approx(
        500.0
    )
    assert result["numeric_max"] == pytest.approx(
        1200.0
    )


def test_aggregate_overall_metrics_ignores_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [
                "100.0",
                "invalid",
                "300.0",
            ]
        }
    )

    result = aggregate_overall_metrics(
        frame,
        value_column="revenue",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 2
    assert result["numeric_sum"] == pytest.approx(
        400.0
    )
    assert result["numeric_mean"] == pytest.approx(
        200.0
    )


def test_aggregate_overall_metrics_returns_zero_statistics_for_no_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [
                None,
                None,
            ]
        }
    )

    result = aggregate_overall_metrics(
        frame,
        value_column="revenue",
    )

    assert result["row_count"] == 2
    assert result["non_null_count"] == 0
    assert result["numeric_sum"] == pytest.approx(
        0.0
    )
    assert result["numeric_mean"] == pytest.approx(
        0.0
    )
    assert result["numeric_min"] == pytest.approx(
        0.0
    )
    assert result["numeric_max"] == pytest.approx(
        0.0
    )


def test_aggregate_with_metrics_returns_aggregation_result() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    assert isinstance(
        result,
        AggregationResult,
    )
    assert result.metrics.input_rows == 5
    assert result.metrics.output_rows == 2
    assert result.metrics.groups == 2
    assert result.metrics.numeric_total == pytest.approx(
        4400.0
    )
    assert result.metrics.memory_bytes > 0


def test_aggregate_with_metrics_contains_expected_data() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
    )

    assert set(
        result.data["region"]
    ) == {
        "north",
        "south",
    }


def test_aggregate_with_metrics_supports_non_sum_aggregation() -> None:
    result = aggregate_with_metrics(
        _sales_frame(),
        dimensions=("region",),
        value_column="revenue",
        aggregation="mean",
    )

    north = result.data.loc[
        result.data["region"].eq("north"),
        "revenue",
    ].iloc[0]

    assert north == pytest.approx(
        1100.0
    )


def test_aggregation_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        AggregationError,
        match="DataFrame",
    ):
        aggregate_chunk(
            "invalid",  # type: ignore[arg-type]
            dimensions=("region",),
            value_column="revenue",
        )


def test_aggregation_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        {
            "region": pd.Series(dtype="string"),
            "revenue": pd.Series(dtype="float64"),
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert result.empty
    assert result.columns.tolist() == [
        "region",
        "revenue",
    ]


def test_aggregation_preserves_dimension_values() -> None:
    frame = pd.DataFrame(
        {
            "region": ["north", "south"],
            "revenue": [100.0, 200.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("region",),
        value_column="revenue",
    )

    assert set(
        result["region"]
    ) == {
        "north",
        "south",
    }