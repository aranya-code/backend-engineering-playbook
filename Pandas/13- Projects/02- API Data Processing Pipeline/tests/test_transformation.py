from __future__ import annotations

import pandas as pd
import pytest

from src.transformation import (
    TransformationError,
    TransformationResult,
    add_datetime_features,
    add_numeric_metrics,
    add_status_flags,
    aggregate_by_dimension,
    calculate_percentage,
    deduplicate_records,
    filter_valid_records,
    transform_records,
)


def test_filter_valid_records_removes_rows_missing_required_columns() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "customer_id": "customer-1"},
            {"order_id": None, "customer_id": "customer-2"},
            {"order_id": "order-3", "customer_id": None},
        ]
    )

    result = filter_valid_records(
        frame,
        required_columns=("order_id", "customer_id"),
    )

    assert result["order_id"].tolist() == ["order-1"]
    assert result["customer_id"].tolist() == ["customer-1"]
    assert result.index.tolist() == [0]


def test_filter_valid_records_returns_copy_when_no_required_columns() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-2"},
        ]
    )

    result = filter_valid_records(frame)

    assert result.equals(frame)
    assert result is not frame


def test_filter_valid_records_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "customer_id": "customer-1"},
            {"order_id": None, "customer_id": "customer-2"},
        ]
    )
    original = frame.copy(deep=True)

    filter_valid_records(
        frame,
        required_columns=("order_id",),
    )

    pd.testing.assert_frame_equal(frame, original)


def test_filter_valid_records_requires_dataframe() -> None:
    with pytest.raises(
        TransformationError,
        match="pandas DataFrame",
    ):
        filter_valid_records(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
        )


def test_filter_valid_records_rejects_missing_columns() -> None:
    frame = pd.DataFrame(
        [{"order_id": "order-1"}]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        filter_valid_records(
            frame,
            required_columns=("order_id", "customer_id"),
        )


def test_add_numeric_metrics_calculates_value_without_quantity() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 100.0},
            {"amount": 250.5},
            {"amount": None},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="amount",
    )

    assert result["value"].tolist()[:2] == [100.0, 250.5]
    assert pd.isna(result.loc[2, "value"])


def test_add_numeric_metrics_multiplies_value_by_quantity() -> None:
    frame = pd.DataFrame(
        [
            {"price": 25.0, "quantity": 2},
            {"price": 12.5, "quantity": 4},
            {"price": 100.0, "quantity": 1},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert result["line_total"].tolist() == [
        50.0,
        50.0,
        100.0,
    ]


def test_add_numeric_metrics_coerces_numeric_strings() -> None:
    frame = pd.DataFrame(
        [
            {"price": "10.50", "quantity": "2"},
            {"price": "20", "quantity": "3"},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert result["line_total"].tolist() == [
        21.0,
        60.0,
    ]


def test_add_numeric_metrics_produces_missing_result_for_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        [
            {"price": "invalid", "quantity": 2},
            {"price": "10", "quantity": "invalid"},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert pd.isna(result.loc[0, "line_total"])
    assert pd.isna(result.loc[1, "line_total"])


def test_add_numeric_metrics_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"price": 10.0, "quantity": 2},
        ]
    )
    original = frame.copy(deep=True)

    add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    pd.testing.assert_frame_equal(frame, original)


def test_add_numeric_metrics_rejects_missing_value_column() -> None:
    frame = pd.DataFrame(
        [
            {"quantity": 2},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_numeric_metrics(
            frame,
            value_column="price",
        )


def test_add_numeric_metrics_rejects_missing_quantity_column() -> None:
    frame = pd.DataFrame(
        [
            {"price": 10.0},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_numeric_metrics(
            frame,
            value_column="price",
            quantity_column="quantity",
        )


def test_add_datetime_features_creates_calendar_attributes() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-09-12T10:30:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
        prefix="event",
    )

    assert result.loc[0, "event_date"] == pd.Timestamp(
        "2026-09-12"
    ).date()
    assert result.loc[0, "event_year"] == 2026
    assert result.loc[0, "event_month"] == 9
    assert result.loc[0, "event_quarter"] == 3
    assert result.loc[0, "event_day_of_week"] == 5


def test_add_datetime_features_supports_custom_prefix() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
        prefix="order",
    )

    assert {
        "order_date",
        "order_year",
        "order_month",
        "order_quarter",
        "order_day_of_week",
    }.issubset(result.columns)


def test_add_datetime_features_accepts_timezone_aware_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00+05:30",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
    )

    assert result.loc[0, "event_year"] == 2026
    assert result.loc[0, "event_month"] == 1


def test_add_datetime_features_rejects_missing_timestamp_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_datetime_features(
            frame,
            timestamp_column="updated_at",
        )


def test_add_datetime_features_rejects_completely_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "invalid",
            },
            {
                "created_at": "not-a-date",
            },
        ]
    )

    with pytest.raises(
        TransformationError,
        match="contains no valid timestamps",
    ):
        add_datetime_features(
            frame,
            timestamp_column="created_at",
        )


def test_add_datetime_features_preserves_original_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
    )

    assert result.loc[0, "order_id"] == "order-1"
    assert "created_at" in result.columns


def test_add_status_flags_creates_expected_boolean_flags() -> None:
    frame = pd.DataFrame(
        [
            {"status": "completed"},
            {"status": "cancelled"},
            {"status": "processing"},
            {"status": "pending"},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result["is_completed"].tolist() == [
        True,
        False,
        False,
        False,
    ]
    assert result["is_cancelled"].tolist() == [
        False,
        True,
        False,
        False,
    ]
    assert result["is_active"].tolist() == [
        False,
        False,
        True,
        True,
    ]


def test_add_status_flags_normalizes_status_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": " Completed "},
            {"status": "CANCELLED"},
            {"status": "Processing"},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result["is_completed"].tolist() == [
        True,
        False,
        False,
    ]
    assert result["is_cancelled"].tolist() == [
        False,
        True,
        False,
    ]
    assert result["is_active"].tolist() == [
        False,
        False,
        True,
    ]


def test_add_status_flags_handles_missing_status() -> None:
    frame = pd.DataFrame(
        [
            {"status": None},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result.loc[0, "is_completed"] is False
    assert result.loc[0, "is_cancelled"] is False
    assert result.loc[0, "is_active"] is False


def test_add_status_flags_rejects_missing_status_column() -> None:
    frame = pd.DataFrame(
        [
            {"state": "completed"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_status_flags(
            frame,
            status_column="status",
        )


def test_calculate_percentage_returns_expected_values() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 80, "total": 100},
            {"completed": 25, "total": 50},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert result["completion_rate"].tolist() == [
        80.0,
        50.0,
    ]


def test_calculate_percentage_handles_zero_denominator() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 5, "total": 0},
            {"completed": 10, "total": 20},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert pd.isna(result.loc[0, "completion_rate"])
    assert result.loc[1, "completion_rate"] == 50.0


def test_calculate_percentage_handles_missing_numerator() -> None:
    frame = pd.DataFrame(
        [
            {"completed": None, "total": 100},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert pd.isna(result.loc[0, "completion_rate"])


def test_calculate_percentage_handles_numeric_strings() -> None:
    frame = pd.DataFrame(
        [
            {"completed": "25", "total": "100"},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert result.loc[0, "completion_rate"] == 25.0


def test_calculate_percentage_rejects_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 10},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        calculate_percentage(
            frame,
            numerator_column="completed",
            denominator_column="total",
            output_column="completion_rate",
        )


def test_aggregate_by_dimension_groups_records_and_sums_values() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
            {"region": "APAC", "revenue": 200.0},
            {"region": "EMEA", "revenue": 50.0},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="revenue",
        aggregation="sum",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "revenue",
    ].iloc[0]
    emea = result.loc[
        result["region"] == "EMEA",
        "revenue",
    ].iloc[0]

    assert apac == 300.0
    assert emea == 50.0


def test_aggregate_by_dimension_supports_mean() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
            {"region": "APAC", "revenue": 300.0},
            {"region": "EMEA", "revenue": 200.0},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="revenue",
        aggregation="mean",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "revenue",
    ].iloc[0]

    assert apac == 200.0


def test_aggregate_by_dimension_supports_count() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "order_id": "1"},
            {"region": "APAC", "order_id": "2"},
            {"region": "EMEA", "order_id": "3"},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="order_id",
        aggregation="count",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "order_id",
    ].iloc[0]

    emea = result.loc[
        result["region"] == "EMEA",
        "order_id",
    ].iloc[0]

    assert apac == 2
    assert emea == 1


def test_aggregate_by_dimension_preserves_grouping_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "region": "APAC",
                "channel": "web",
                "revenue": 100.0,
            },
            {
                "region": "APAC",
                "channel": "store",
                "revenue": 50.0,
            },
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region", "channel"),
        value_column="revenue",
        aggregation="sum",
    )

    assert {"region", "channel", "revenue"}.issubset(
        result.columns
    )
    assert len(result) == 2


def test_aggregate_by_dimension_rejects_missing_dimension_column() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        aggregate_by_dimension(
            frame,
            dimensions=("country",),
            value_column="revenue",
            aggregation="sum",
        )


def test_aggregate_by_dimension_rejects_missing_value_column() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        aggregate_by_dimension(
            frame,
            dimensions=("region",),
            value_column="revenue",
            aggregation="sum",
        )


def test_deduplicate_records_keeps_first_record_without_sort_column() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
            {"order_id": "order-2", "amount": 200},
        ]
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    assert result["order_id"].tolist() == [
        "order-1",
        "order-2",
    ]
    assert result["amount"].tolist() == [
        100,
        200,
    ]


def test_deduplicate_records_keeps_latest_record_when_sorted() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
                "updated_at": "2026-01-01",
            },
            {
                "order_id": "order-1",
                "amount": 125,
                "updated_at": "2026-01-02",
            },
            {
                "order_id": "order-2",
                "amount": 200,
                "updated_at": "2026-01-01",
            },
        ]
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
        sort_column="updated_at",
    )

    order_one = result.loc[
        result["order_id"] == "order-1",
        "amount",
    ].iloc[0]

    assert order_one == 125
    assert len(result) == 2


def test_deduplicate_records_resets_index() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
        ],
        index=[10, 20],
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    assert result.index.tolist() == [0]


def test_deduplicate_records_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
        ]
    )
    original = frame.copy(deep=True)

    deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    pd.testing.assert_frame_equal(frame, original)


def test_deduplicate_records_rejects_missing_key_column() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        deduplicate_records(
            frame,
            key_columns=("customer_id",),
        )


def test_transform_records_returns_transformation_result() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "status": "completed",
                "amount": "100.00",
                "created_at": "2026-01-01T10:00:00Z",
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        timestamp_column="created_at",
        status_column="status",
    )

    assert isinstance(result, TransformationResult)
    assert isinstance(result.data, pd.DataFrame)
    assert isinstance(result.metrics, dict)


def test_transform_records_filters_missing_required_ids() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
            },
            {
                "order_id": None,
                "amount": 200,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 1
    assert result.data.iloc[0]["order_id"] == "order-1"


def test_transform_records_deduplicates_by_primary_identifier() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
            },
            {
                "order_id": "order-1",
                "amount": 150,
            },
            {
                "order_id": "order-2",
                "amount": 200,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 2
    assert result.data["order_id"].tolist() == [
        "order-1",
        "order-2",
    ]


def test_transform_records_adds_datetime_features() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "created_at": "2026-09-12T10:00:00Z",
                "amount": 100.0,
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        timestamp_column="created_at",
    )

    assert {
        "event_date",
        "event_year",
        "event_month",
        "event_quarter",
        "event_day_of_week",
    }.issubset(result.data.columns)


def test_transform_records_adds_status_flags() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "status": "completed",
                "amount": 100.0,
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        status_column="status",
    )

    assert result.data.loc[0, "is_completed"] is True
    assert result.data.loc[0, "is_cancelled"] is False


def test_transform_records_converts_numeric_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "100.50",
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.data.loc[0, "amount"] == 100.5
    assert pd.api.types.is_numeric_dtype(
        result.data["amount"]
    )


def test_transform_records_raises_when_numeric_column_is_entirely_invalid() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "invalid",
            },
            {
                "order_id": "order-2",
                "amount": "also-invalid",
            },
        ]
    )

    with pytest.raises(
        TransformationError,
        match="numeric",
    ):
        transform_records(
            frame,
            id_columns=("order_id",),
            numeric_columns=("amount",),
        )


def test_transform_records_populates_metrics() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-1",
                "amount": 125.0,
            },
            {
                "order_id": "order-2",
                "amount": 200.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.metrics["input_rows"] == 3
    assert result.metrics["output_rows"] == 2
    assert result.metrics["rows_removed"] == 1
    assert result.metrics["numeric_total"] == 325.0


def test_transform_records_handles_empty_input() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert isinstance(result, TransformationResult)
    assert result.data.empty
    assert result.metrics["input_rows"] == 0
    assert result.metrics["output_rows"] == 0


def test_transform_records_requires_dataframe() -> None:
    with pytest.raises(
        TransformationError,
        match="pandas DataFrame",
    ):
        transform_records(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
            id_columns=("order_id",),
        )


def test_transform_records_rejects_missing_identifier_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "amount": 100.0,
            }
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        transform_records(
            frame,
            id_columns=("order_id",),
            numeric_columns=("amount",),
        )


def test_transform_records_uses_business_key_before_secondary_identifiers() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "event_id": "event-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-1",
                "event_id": "event-2",
                "amount": 125.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id", "event_id"),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 1
    assert result.data.iloc[0]["order_id"] == "order-1"


def test_transform_records_calculates_aggregation_row_metric() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-2",
                "amount": 200.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        dimension_columns=("order_id",),
    )

    assert result.metrics["aggregation_rows"] == 2


def test_transform_records_preserves_original_input_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "100.00",
                "status": "completed",
            }
        ]
    )
    original = frame.copy(deep=True)

    transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        status_column="status",
    )

    pd.testing.assert_frame_equal(frame, original)

from __future__ import annotations

import pandas as pd
import pytest

from src.transformation import (
    TransformationError,
    TransformationResult,
    add_datetime_features,
    add_numeric_metrics,
    add_status_flags,
    aggregate_by_dimension,
    calculate_percentage,
    deduplicate_records,
    filter_valid_records,
    transform_records,
)


def test_filter_valid_records_removes_rows_missing_required_columns() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "customer_id": "customer-1"},
            {"order_id": None, "customer_id": "customer-2"},
            {"order_id": "order-3", "customer_id": None},
        ]
    )

    result = filter_valid_records(
        frame,
        required_columns=("order_id", "customer_id"),
    )

    assert result["order_id"].tolist() == ["order-1"]
    assert result["customer_id"].tolist() == ["customer-1"]
    assert result.index.tolist() == [0]


def test_filter_valid_records_returns_copy_when_no_required_columns() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-2"},
        ]
    )

    result = filter_valid_records(frame)

    assert result.equals(frame)
    assert result is not frame


def test_filter_valid_records_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "customer_id": "customer-1"},
            {"order_id": None, "customer_id": "customer-2"},
        ]
    )
    original = frame.copy(deep=True)

    filter_valid_records(
        frame,
        required_columns=("order_id",),
    )

    pd.testing.assert_frame_equal(frame, original)


def test_filter_valid_records_requires_dataframe() -> None:
    with pytest.raises(
        TransformationError,
        match="pandas DataFrame",
    ):
        filter_valid_records(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
        )


def test_filter_valid_records_rejects_missing_columns() -> None:
    frame = pd.DataFrame(
        [{"order_id": "order-1"}]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        filter_valid_records(
            frame,
            required_columns=("order_id", "customer_id"),
        )


def test_add_numeric_metrics_calculates_value_without_quantity() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 100.0},
            {"amount": 250.5},
            {"amount": None},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="amount",
    )

    assert result["value"].tolist()[:2] == [100.0, 250.5]
    assert pd.isna(result.loc[2, "value"])


def test_add_numeric_metrics_multiplies_value_by_quantity() -> None:
    frame = pd.DataFrame(
        [
            {"price": 25.0, "quantity": 2},
            {"price": 12.5, "quantity": 4},
            {"price": 100.0, "quantity": 1},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert result["line_total"].tolist() == [
        50.0,
        50.0,
        100.0,
    ]


def test_add_numeric_metrics_coerces_numeric_strings() -> None:
    frame = pd.DataFrame(
        [
            {"price": "10.50", "quantity": "2"},
            {"price": "20", "quantity": "3"},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert result["line_total"].tolist() == [
        21.0,
        60.0,
    ]


def test_add_numeric_metrics_produces_missing_result_for_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        [
            {"price": "invalid", "quantity": 2},
            {"price": "10", "quantity": "invalid"},
        ]
    )

    result = add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    assert pd.isna(result.loc[0, "line_total"])
    assert pd.isna(result.loc[1, "line_total"])


def test_add_numeric_metrics_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"price": 10.0, "quantity": 2},
        ]
    )
    original = frame.copy(deep=True)

    add_numeric_metrics(
        frame,
        value_column="price",
        quantity_column="quantity",
        output_column="line_total",
    )

    pd.testing.assert_frame_equal(frame, original)


def test_add_numeric_metrics_rejects_missing_value_column() -> None:
    frame = pd.DataFrame(
        [
            {"quantity": 2},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_numeric_metrics(
            frame,
            value_column="price",
        )


def test_add_numeric_metrics_rejects_missing_quantity_column() -> None:
    frame = pd.DataFrame(
        [
            {"price": 10.0},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_numeric_metrics(
            frame,
            value_column="price",
            quantity_column="quantity",
        )


def test_add_datetime_features_creates_calendar_attributes() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-09-12T10:30:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
        prefix="event",
    )

    assert result.loc[0, "event_date"] == pd.Timestamp(
        "2026-09-12"
    ).date()
    assert result.loc[0, "event_year"] == 2026
    assert result.loc[0, "event_month"] == 9
    assert result.loc[0, "event_quarter"] == 3
    assert result.loc[0, "event_day_of_week"] == 5


def test_add_datetime_features_supports_custom_prefix() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
        prefix="order",
    )

    assert {
        "order_date",
        "order_year",
        "order_month",
        "order_quarter",
        "order_day_of_week",
    }.issubset(result.columns)


def test_add_datetime_features_accepts_timezone_aware_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00+05:30",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
    )

    assert result.loc[0, "event_year"] == 2026
    assert result.loc[0, "event_month"] == 1


def test_add_datetime_features_rejects_missing_timestamp_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_datetime_features(
            frame,
            timestamp_column="updated_at",
        )


def test_add_datetime_features_rejects_completely_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "invalid",
            },
            {
                "created_at": "not-a-date",
            },
        ]
    )

    with pytest.raises(
        TransformationError,
        match="contains no valid timestamps",
    ):
        add_datetime_features(
            frame,
            timestamp_column="created_at",
        )


def test_add_datetime_features_preserves_original_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "created_at": "2026-01-05T10:00:00Z",
            }
        ]
    )

    result = add_datetime_features(
        frame,
        timestamp_column="created_at",
    )

    assert result.loc[0, "order_id"] == "order-1"
    assert "created_at" in result.columns


def test_add_status_flags_creates_expected_boolean_flags() -> None:
    frame = pd.DataFrame(
        [
            {"status": "completed"},
            {"status": "cancelled"},
            {"status": "processing"},
            {"status": "pending"},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result["is_completed"].tolist() == [
        True,
        False,
        False,
        False,
    ]
    assert result["is_cancelled"].tolist() == [
        False,
        True,
        False,
        False,
    ]
    assert result["is_active"].tolist() == [
        False,
        False,
        True,
        True,
    ]


def test_add_status_flags_normalizes_status_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": " Completed "},
            {"status": "CANCELLED"},
            {"status": "Processing"},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result["is_completed"].tolist() == [
        True,
        False,
        False,
    ]
    assert result["is_cancelled"].tolist() == [
        False,
        True,
        False,
    ]
    assert result["is_active"].tolist() == [
        False,
        False,
        True,
    ]


def test_add_status_flags_handles_missing_status() -> None:
    frame = pd.DataFrame(
        [
            {"status": None},
        ]
    )

    result = add_status_flags(
        frame,
        status_column="status",
    )

    assert result.loc[0, "is_completed"] is False
    assert result.loc[0, "is_cancelled"] is False
    assert result.loc[0, "is_active"] is False


def test_add_status_flags_rejects_missing_status_column() -> None:
    frame = pd.DataFrame(
        [
            {"state": "completed"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        add_status_flags(
            frame,
            status_column="status",
        )


def test_calculate_percentage_returns_expected_values() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 80, "total": 100},
            {"completed": 25, "total": 50},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert result["completion_rate"].tolist() == [
        80.0,
        50.0,
    ]


def test_calculate_percentage_handles_zero_denominator() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 5, "total": 0},
            {"completed": 10, "total": 20},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert pd.isna(result.loc[0, "completion_rate"])
    assert result.loc[1, "completion_rate"] == 50.0


def test_calculate_percentage_handles_missing_numerator() -> None:
    frame = pd.DataFrame(
        [
            {"completed": None, "total": 100},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert pd.isna(result.loc[0, "completion_rate"])


def test_calculate_percentage_handles_numeric_strings() -> None:
    frame = pd.DataFrame(
        [
            {"completed": "25", "total": "100"},
        ]
    )

    result = calculate_percentage(
        frame,
        numerator_column="completed",
        denominator_column="total",
        output_column="completion_rate",
    )

    assert result.loc[0, "completion_rate"] == 25.0


def test_calculate_percentage_rejects_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {"completed": 10},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        calculate_percentage(
            frame,
            numerator_column="completed",
            denominator_column="total",
            output_column="completion_rate",
        )


def test_aggregate_by_dimension_groups_records_and_sums_values() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
            {"region": "APAC", "revenue": 200.0},
            {"region": "EMEA", "revenue": 50.0},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="revenue",
        aggregation="sum",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "revenue",
    ].iloc[0]
    emea = result.loc[
        result["region"] == "EMEA",
        "revenue",
    ].iloc[0]

    assert apac == 300.0
    assert emea == 50.0


def test_aggregate_by_dimension_supports_mean() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
            {"region": "APAC", "revenue": 300.0},
            {"region": "EMEA", "revenue": 200.0},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="revenue",
        aggregation="mean",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "revenue",
    ].iloc[0]

    assert apac == 200.0


def test_aggregate_by_dimension_supports_count() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "order_id": "1"},
            {"region": "APAC", "order_id": "2"},
            {"region": "EMEA", "order_id": "3"},
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region",),
        value_column="order_id",
        aggregation="count",
    )

    apac = result.loc[
        result["region"] == "APAC",
        "order_id",
    ].iloc[0]

    emea = result.loc[
        result["region"] == "EMEA",
        "order_id",
    ].iloc[0]

    assert apac == 2
    assert emea == 1


def test_aggregate_by_dimension_preserves_grouping_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "region": "APAC",
                "channel": "web",
                "revenue": 100.0,
            },
            {
                "region": "APAC",
                "channel": "store",
                "revenue": 50.0,
            },
        ]
    )

    result = aggregate_by_dimension(
        frame,
        dimensions=("region", "channel"),
        value_column="revenue",
        aggregation="sum",
    )

    assert {"region", "channel", "revenue"}.issubset(
        result.columns
    )
    assert len(result) == 2


def test_aggregate_by_dimension_rejects_missing_dimension_column() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC", "revenue": 100.0},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        aggregate_by_dimension(
            frame,
            dimensions=("country",),
            value_column="revenue",
            aggregation="sum",
        )


def test_aggregate_by_dimension_rejects_missing_value_column() -> None:
    frame = pd.DataFrame(
        [
            {"region": "APAC"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        aggregate_by_dimension(
            frame,
            dimensions=("region",),
            value_column="revenue",
            aggregation="sum",
        )


def test_deduplicate_records_keeps_first_record_without_sort_column() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
            {"order_id": "order-2", "amount": 200},
        ]
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    assert result["order_id"].tolist() == [
        "order-1",
        "order-2",
    ]
    assert result["amount"].tolist() == [
        100,
        200,
    ]


def test_deduplicate_records_keeps_latest_record_when_sorted() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
                "updated_at": "2026-01-01",
            },
            {
                "order_id": "order-1",
                "amount": 125,
                "updated_at": "2026-01-02",
            },
            {
                "order_id": "order-2",
                "amount": 200,
                "updated_at": "2026-01-01",
            },
        ]
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
        sort_column="updated_at",
    )

    order_one = result.loc[
        result["order_id"] == "order-1",
        "amount",
    ].iloc[0]

    assert order_one == 125
    assert len(result) == 2


def test_deduplicate_records_resets_index() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
        ],
        index=[10, 20],
    )

    result = deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    assert result.index.tolist() == [0]


def test_deduplicate_records_does_not_mutate_input() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1", "amount": 100},
            {"order_id": "order-1", "amount": 125},
        ]
    )
    original = frame.copy(deep=True)

    deduplicate_records(
        frame,
        key_columns=("order_id",),
    )

    pd.testing.assert_frame_equal(frame, original)


def test_deduplicate_records_rejects_missing_key_column() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        deduplicate_records(
            frame,
            key_columns=("customer_id",),
        )


def test_transform_records_returns_transformation_result() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "status": "completed",
                "amount": "100.00",
                "created_at": "2026-01-01T10:00:00Z",
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        timestamp_column="created_at",
        status_column="status",
    )

    assert isinstance(result, TransformationResult)
    assert isinstance(result.data, pd.DataFrame)
    assert isinstance(result.metrics, dict)


def test_transform_records_filters_missing_required_ids() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
            },
            {
                "order_id": None,
                "amount": 200,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 1
    assert result.data.iloc[0]["order_id"] == "order-1"


def test_transform_records_deduplicates_by_primary_identifier() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100,
            },
            {
                "order_id": "order-1",
                "amount": 150,
            },
            {
                "order_id": "order-2",
                "amount": 200,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 2
    assert result.data["order_id"].tolist() == [
        "order-1",
        "order-2",
    ]


def test_transform_records_adds_datetime_features() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "created_at": "2026-09-12T10:00:00Z",
                "amount": 100.0,
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        timestamp_column="created_at",
    )

    assert {
        "event_date",
        "event_year",
        "event_month",
        "event_quarter",
        "event_day_of_week",
    }.issubset(result.data.columns)


def test_transform_records_adds_status_flags() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "status": "completed",
                "amount": 100.0,
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        status_column="status",
    )

    assert result.data.loc[0, "is_completed"] is True
    assert result.data.loc[0, "is_cancelled"] is False


def test_transform_records_converts_numeric_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "100.50",
            }
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.data.loc[0, "amount"] == 100.5
    assert pd.api.types.is_numeric_dtype(
        result.data["amount"]
    )


def test_transform_records_raises_when_numeric_column_is_entirely_invalid() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "invalid",
            },
            {
                "order_id": "order-2",
                "amount": "also-invalid",
            },
        ]
    )

    with pytest.raises(
        TransformationError,
        match="numeric",
    ):
        transform_records(
            frame,
            id_columns=("order_id",),
            numeric_columns=("amount",),
        )


def test_transform_records_populates_metrics() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-1",
                "amount": 125.0,
            },
            {
                "order_id": "order-2",
                "amount": 200.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.metrics["input_rows"] == 3
    assert result.metrics["output_rows"] == 2
    assert result.metrics["rows_removed"] == 1
    assert result.metrics["numeric_total"] == 325.0


def test_transform_records_handles_empty_input() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert isinstance(result, TransformationResult)
    assert result.data.empty
    assert result.metrics["input_rows"] == 0
    assert result.metrics["output_rows"] == 0


def test_transform_records_requires_dataframe() -> None:
    with pytest.raises(
        TransformationError,
        match="pandas DataFrame",
    ):
        transform_records(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
            id_columns=("order_id",),
        )


def test_transform_records_rejects_missing_identifier_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "amount": 100.0,
            }
        ]
    )

    with pytest.raises(
        TransformationError,
        match="missing required columns",
    ):
        transform_records(
            frame,
            id_columns=("order_id",),
            numeric_columns=("amount",),
        )


def test_transform_records_uses_business_key_before_secondary_identifiers() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "event_id": "event-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-1",
                "event_id": "event-2",
                "amount": 125.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id", "event_id"),
        numeric_columns=("amount",),
    )

    assert len(result.data) == 1
    assert result.data.iloc[0]["order_id"] == "order-1"


def test_transform_records_calculates_aggregation_row_metric() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
            },
            {
                "order_id": "order-2",
                "amount": 200.0,
            },
        ]
    )

    result = transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        dimension_columns=("order_id",),
    )

    assert result.metrics["aggregation_rows"] == 2


def test_transform_records_preserves_original_input_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": "100.00",
                "status": "completed",
            }
        ]
    )
    original = frame.copy(deep=True)

    transform_records(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        status_column="status",
    )

    pd.testing.assert_frame_equal(frame, original)