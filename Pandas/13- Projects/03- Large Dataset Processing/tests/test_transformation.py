from __future__ import annotations

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.transformation import (
    TransformationError,
    add_ratio_column,
    aggregate_chunk,
    filter_rows,
    make_transformer,
    summarize_chunk,
    transform_chunk,
)


def _config(**overrides: object) -> PipelineConfig:
    """Create a deterministic configuration for transformation tests."""
    values: dict[str, object] = {
        "timestamp_columns": ("created_at",),
        "numeric_columns": ("amount", "quantity"),
        "identifier_columns": ("order_id",),
        "required_columns": ("order_id",),
        "categorical_columns": ("status",),
        "timestamp_timezone": "UTC",
        "drop_invalid_records": True,
        "drop_duplicates": True,
    }
    values.update(overrides)
    return PipelineConfig(**values)


def _orders() -> pd.DataFrame:
    """Build a representative order dataset."""
    return pd.DataFrame(
        {
            "Order ID": ["1001", "1002", "1003"],
            "Amount": ["100.50", "250.00", "75.25"],
            "Quantity": ["2", "5", "1"],
            "Status": ["paid", "pending", "paid"],
            "Created At": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:30:00Z",
                "2026-01-03T09:15:00Z",
            ],
        }
    )


def test_transform_chunk_normalizes_column_names() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "order_id" in result.columns
    assert "amount" in result.columns
    assert "quantity" in result.columns
    assert "created_at" in result.columns
    assert "Order ID" not in result.columns
    assert "Created At" not in result.columns


def test_transform_chunk_strips_string_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [" 1001 ", "1002"],
            "status": [" paid ", " pending "],
            "amount": [100, 200],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]
    assert result["status"].tolist() == [
        "paid",
        "pending",
    ]


def test_transform_chunk_normalizes_identifier_columns_to_strings() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [1001, 1002],
            "amount": [100.0, 200.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].dtype.name == "string"
    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]


def test_transform_chunk_converts_numeric_columns() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert pd.api.types.is_numeric_dtype(
        result["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result["quantity"]
    )
    assert result["amount"].tolist() == [
        pytest.approx(100.50),
        pytest.approx(250.00),
        pytest.approx(75.25),
    ]
    assert result["quantity"].tolist() == [2, 5, 1]


def test_transform_chunk_converts_timestamps_to_configured_timezone() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "created_at": ["2026-01-01T10:00:00Z"],
            "amount": [100],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_timezone="Asia/Kolkata",
        ),
    )

    timestamp = result["created_at"].iloc[0]

    assert str(timestamp.tz) == "Asia/Kolkata"
    assert timestamp.hour == 15
    assert timestamp.minute == 30


def test_transform_chunk_adds_datetime_features() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "created_at_date" in result.columns
    assert "created_at_year" in result.columns
    assert "created_at_month" in result.columns
    assert "created_at_day" in result.columns
    assert "created_at_day_of_week" in result.columns
    assert "created_at_hour" in result.columns

    assert result["created_at_year"].tolist() == [
        2026,
        2026,
        2026,
    ]
    assert result["created_at_month"].tolist() == [
        1,
        1,
        1,
    ]


def test_transform_chunk_adds_numeric_value_metric() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "numeric_value" in result.columns
    assert result["numeric_value"].tolist() == [
        pytest.approx(100.50),
        pytest.approx(250.00),
        pytest.approx(75.25),
    ]


def test_transform_chunk_coerces_categorical_columns() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert isinstance(
        result["status"].dtype,
        pd.CategoricalDtype,
    )
    assert result["status"].tolist() == [
        "paid",
        "pending",
        "paid",
    ]


def test_transform_chunk_drops_fully_empty_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", None, "1003"],
            "amount": [100.0, None, 50.0],
            "quantity": [1, None, 2],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount", "quantity"),
        ),
    )

    assert len(result) == 2
    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]


def test_transform_chunk_drops_rows_missing_required_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", None, "1003"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]


def test_transform_chunk_drops_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": ["100.00", "invalid", "250.00"],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]
    assert result["amount"].tolist() == [
        pytest.approx(100.0),
        pytest.approx(250.0),
    ]


def test_transform_chunk_can_fail_instead_of_dropping_invalid_records() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": ["100.00", "invalid"],
        }
    )

    with pytest.raises(
        TransformationError,
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
                drop_invalid_records=False,
            ),
        )


def test_transform_chunk_deduplicates_identifier_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1001", "1002"],
            "amount": [100.0, 150.0, 200.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=True,
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]
    assert result["amount"].tolist() == [
        pytest.approx(100.0),
        pytest.approx(200.0),
    ]


def test_transform_chunk_can_preserve_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1001"],
            "amount": [100.0, 150.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=False,
        ),
    )

    assert len(result) == 2


def test_transform_chunk_downcasts_numeric_columns_when_safe() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [1.0, 2.0],
            "quantity": [1.0, 2.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount", "quantity"),
        ),
    )

    assert pd.api.types.is_numeric_dtype(
        result["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result["quantity"]
    )
    assert result["amount"].tolist() == [
        pytest.approx(1.0),
        pytest.approx(2.0),
    ]


def test_transform_chunk_resets_index() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
        },
        index=[10, 20],
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result.index.tolist() == [0, 1]


def test_transform_chunk_does_not_mutate_input() -> None:
    frame = _orders()
    original = frame.copy(deep=True)

    transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_transform_chunk_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        TransformationError,
        match="DataFrame",
    ):
        transform_chunk(
            ["invalid"],  # type: ignore[arg-type]
            pipeline_config=_config(),
        )


def test_transform_chunk_rejects_missing_required_numeric_column() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    )

    with pytest.raises(
        TransformationError,
        match="amount",
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
            ),
        )


def test_filter_rows_returns_filtered_copy() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "pending", "paid"],
            "amount": [100.0, 50.0, 200.0],
        }
    )

    result = filter_rows(
        frame,
        lambda data: data["status"].eq("paid"),
    )

    expected = pd.DataFrame(
        {
            "status": ["paid", "paid"],
            "amount": [100.0, 200.0],
        },
        index=[0, 2],
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )
    assert result is not frame


def test_filter_rows_can_filter_numeric_threshold() -> None:
    frame = pd.DataFrame(
        {
            "amount": [50.0, 100.0, 250.0],
        }
    )

    result = filter_rows(
        frame,
        lambda data: data["amount"].ge(100),
    )

    assert result["amount"].tolist() == [
        100.0,
        250.0,
    ]


def test_filter_rows_rejects_invalid_frame() -> None:
    with pytest.raises(
        TransformationError,
        match="DataFrame",
    ):
        filter_rows(
            "invalid",  # type: ignore[arg-type]
            lambda data: pd.Series(dtype=bool),
        )


def test_add_ratio_column_calculates_vectorized_ratio() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0, 200.0, 300.0],
            "orders": [10.0, 20.0, 30.0],
        }
    )

    result = add_ratio_column(
        frame,
        numerator="revenue",
        denominator="orders",
        output_column="average_order_value",
    )

    assert result["average_order_value"].tolist() == [
        pytest.approx(10.0),
        pytest.approx(10.0),
        pytest.approx(10.0),
    ]


def test_add_ratio_column_returns_missing_for_zero_denominator() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0, 200.0],
            "orders": [10.0, 0.0],
        }
    )

    result = add_ratio_column(
        frame,
        numerator="revenue",
        denominator="orders",
        output_column="average_order_value",
    )

    assert result["average_order_value"].iloc[0] == pytest.approx(
        10.0
    )
    assert pd.isna(
        result["average_order_value"].iloc[1]
    )


def test_add_ratio_column_validates_columns() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0],
        }
    )

    with pytest.raises(
        TransformationError,
        match="orders",
    ):
        add_ratio_column(
            frame,
            numerator="revenue",
            denominator="orders",
            output_column="ratio",
        )


def test_aggregate_chunk_groups_and_sums() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "paid", "pending"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("status",),
        value_column="amount",
        aggregation="sum",
    )

    result = result.sort_values(
        "status"
    ).reset_index(drop=True)

    expected = pd.DataFrame(
        {
            "status": ["paid", "pending"],
            "amount": [150.0, 25.0],
        }
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )


def test_aggregate_chunk_supports_mean() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "paid", "pending"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("status",),
        value_column="amount",
        aggregation="mean",
    )

    paid = result.loc[
        result["status"].eq("paid"),
        "amount",
    ].iloc[0]

    assert paid == pytest.approx(75.0)


def test_aggregate_chunk_rejects_empty_dimensions() -> None:
    with pytest.raises(
        TransformationError,
        match="dimension",
    ):
        aggregate_chunk(
            _orders(),
            dimensions=(),
            value_column="amount",
        )


def test_aggregate_chunk_rejects_missing_value_column() -> None:
    with pytest.raises(
        TransformationError,
        match="missing",
    ):
        aggregate_chunk(
            _orders(),
            dimensions=("status",),
            value_column="missing",
        )


def test_summarize_chunk_returns_operational_metrics() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": [100.0, 200.0, 300.0],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 3
    assert result["numeric_sum"] == pytest.approx(600.0)
    assert result["numeric_mean"] == pytest.approx(200.0)
    assert result["numeric_min"] == pytest.approx(100.0)
    assert result["numeric_max"] == pytest.approx(300.0)


def test_summarize_chunk_handles_missing_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [100.0, None, 300.0],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 2
    assert result["numeric_sum"] == pytest.approx(400.0)
    assert result["numeric_mean"] == pytest.approx(200.0)


def test_summarize_chunk_returns_zero_for_all_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [None, None],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 2
    assert result["non_null_count"] == 0
    assert result["numeric_sum"] == pytest.approx(0.0)
    assert result["numeric_mean"] == pytest.approx(0.0)


def test_make_transformer_returns_callable() -> None:
    transformer = make_transformer(
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        )
    )

    assert callable(transformer)


def test_make_transformer_applies_configured_transformation() -> None:
    transformer = make_transformer(
        pipeline_config=_config()
    )

    frame = _orders()

    transformed = transformer(
        frame,
        None,
    )

    assert isinstance(
        transformed,
        pd.DataFrame,
    )
    assert "order_id" in transformed.columns
    assert "numeric_value" in transformed.columns


def test_make_transformer_can_be_used_as_chunk_processor_callback() -> None:
    transformer = make_transformer(
        pipeline_config=_config()
    )

    frame = _orders()

    transformed = transformer(
        frame,
        None,
    )

    assert len(transformed) == len(frame)
    assert transformed["order_id"].tolist() == [
        "1001",
        "1002",
        "1003",
    ]


def test_transform_chunk_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
            "quantity",
            "status",
            "created_at",
        ]
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert result.empty
    assert "order_id" in result.columns


def test_transform_chunk_preserves_expected_row_order() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1003", "1001", "1002"],
            "amount": [30.0, 10.0, 20.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=False,
        ),
    )

    assert result["order_id"].tolist() == [
        "1003",
        "1001",
        "1002",
    ]


def test_transform_chunk_handles_missing_optional_timestamp_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                None,
            ],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    assert len(result) == 2
    assert result["created_at"].notna().sum() == 1


def test_transform_chunk_handles_mixed_case_column_names() -> None:
    frame = pd.DataFrame(
        {
            "ORDER_ID": ["1001"],
            "AMOUNT": ["125.50"],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
        ),
    )

    assert "order_id" in result.columns
    assert "amount" in result.columns
    assert result["amount"].iloc[0] == pytest.approx(
        125.50
    )


def test_transform_chunk_rejects_all_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": ["invalid", "also-invalid"],
        }
    )

    with pytest.raises(
        TransformationError,
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
                drop_invalid_records=True,
            ),
        )

from __future__ import annotations

import pandas as pd
import pytest

from src.config import PipelineConfig
from src.transformation import (
    TransformationError,
    add_ratio_column,
    aggregate_chunk,
    filter_rows,
    make_transformer,
    summarize_chunk,
    transform_chunk,
)


def _config(**overrides: object) -> PipelineConfig:
    """Create a deterministic configuration for transformation tests."""
    values: dict[str, object] = {
        "timestamp_columns": ("created_at",),
        "numeric_columns": ("amount", "quantity"),
        "identifier_columns": ("order_id",),
        "required_columns": ("order_id",),
        "categorical_columns": ("status",),
        "timestamp_timezone": "UTC",
        "drop_invalid_records": True,
        "drop_duplicates": True,
    }
    values.update(overrides)
    return PipelineConfig(**values)


def _orders() -> pd.DataFrame:
    """Build a representative order dataset."""
    return pd.DataFrame(
        {
            "Order ID": ["1001", "1002", "1003"],
            "Amount": ["100.50", "250.00", "75.25"],
            "Quantity": ["2", "5", "1"],
            "Status": ["paid", "pending", "paid"],
            "Created At": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:30:00Z",
                "2026-01-03T09:15:00Z",
            ],
        }
    )


def test_transform_chunk_normalizes_column_names() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "order_id" in result.columns
    assert "amount" in result.columns
    assert "quantity" in result.columns
    assert "created_at" in result.columns
    assert "Order ID" not in result.columns
    assert "Created At" not in result.columns


def test_transform_chunk_strips_string_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [" 1001 ", "1002"],
            "status": [" paid ", " pending "],
            "amount": [100, 200],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]
    assert result["status"].tolist() == [
        "paid",
        "pending",
    ]


def test_transform_chunk_normalizes_identifier_columns_to_strings() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [1001, 1002],
            "amount": [100.0, 200.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].dtype.name == "string"
    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]


def test_transform_chunk_converts_numeric_columns() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert pd.api.types.is_numeric_dtype(
        result["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result["quantity"]
    )
    assert result["amount"].tolist() == [
        pytest.approx(100.50),
        pytest.approx(250.00),
        pytest.approx(75.25),
    ]
    assert result["quantity"].tolist() == [2, 5, 1]


def test_transform_chunk_converts_timestamps_to_configured_timezone() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "created_at": ["2026-01-01T10:00:00Z"],
            "amount": [100],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_timezone="Asia/Kolkata",
        ),
    )

    timestamp = result["created_at"].iloc[0]

    assert str(timestamp.tz) == "Asia/Kolkata"
    assert timestamp.hour == 15
    assert timestamp.minute == 30


def test_transform_chunk_adds_datetime_features() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "created_at_date" in result.columns
    assert "created_at_year" in result.columns
    assert "created_at_month" in result.columns
    assert "created_at_day" in result.columns
    assert "created_at_day_of_week" in result.columns
    assert "created_at_hour" in result.columns

    assert result["created_at_year"].tolist() == [
        2026,
        2026,
        2026,
    ]
    assert result["created_at_month"].tolist() == [
        1,
        1,
        1,
    ]


def test_transform_chunk_adds_numeric_value_metric() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert "numeric_value" in result.columns
    assert result["numeric_value"].tolist() == [
        pytest.approx(100.50),
        pytest.approx(250.00),
        pytest.approx(75.25),
    ]


def test_transform_chunk_coerces_categorical_columns() -> None:
    result = transform_chunk(
        _orders(),
        pipeline_config=_config(),
    )

    assert isinstance(
        result["status"].dtype,
        pd.CategoricalDtype,
    )
    assert result["status"].tolist() == [
        "paid",
        "pending",
        "paid",
    ]


def test_transform_chunk_drops_fully_empty_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", None, "1003"],
            "amount": [100.0, None, 50.0],
            "quantity": [1, None, 2],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount", "quantity"),
        ),
    )

    assert len(result) == 2
    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]


def test_transform_chunk_drops_rows_missing_required_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", None, "1003"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]


def test_transform_chunk_drops_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": ["100.00", "invalid", "250.00"],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1003",
    ]
    assert result["amount"].tolist() == [
        pytest.approx(100.0),
        pytest.approx(250.0),
    ]


def test_transform_chunk_can_fail_instead_of_dropping_invalid_records() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": ["100.00", "invalid"],
        }
    )

    with pytest.raises(
        TransformationError,
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
                drop_invalid_records=False,
            ),
        )


def test_transform_chunk_deduplicates_identifier_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1001", "1002"],
            "amount": [100.0, 150.0, 200.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=True,
        ),
    )

    assert result["order_id"].tolist() == [
        "1001",
        "1002",
    ]
    assert result["amount"].tolist() == [
        pytest.approx(100.0),
        pytest.approx(200.0),
    ]


def test_transform_chunk_can_preserve_duplicates() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1001"],
            "amount": [100.0, 150.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=False,
        ),
    )

    assert len(result) == 2


def test_transform_chunk_downcasts_numeric_columns_when_safe() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [1.0, 2.0],
            "quantity": [1.0, 2.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount", "quantity"),
        ),
    )

    assert pd.api.types.is_numeric_dtype(
        result["amount"]
    )
    assert pd.api.types.is_numeric_dtype(
        result["quantity"]
    )
    assert result["amount"].tolist() == [
        pytest.approx(1.0),
        pytest.approx(2.0),
    ]


def test_transform_chunk_resets_index() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
        },
        index=[10, 20],
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        ),
    )

    assert result.index.tolist() == [0, 1]


def test_transform_chunk_does_not_mutate_input() -> None:
    frame = _orders()
    original = frame.copy(deep=True)

    transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    pd.testing.assert_frame_equal(
        frame,
        original,
    )


def test_transform_chunk_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        TransformationError,
        match="DataFrame",
    ):
        transform_chunk(
            ["invalid"],  # type: ignore[arg-type]
            pipeline_config=_config(),
        )


def test_transform_chunk_rejects_missing_required_numeric_column() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    )

    with pytest.raises(
        TransformationError,
        match="amount",
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
            ),
        )


def test_filter_rows_returns_filtered_copy() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "pending", "paid"],
            "amount": [100.0, 50.0, 200.0],
        }
    )

    result = filter_rows(
        frame,
        lambda data: data["status"].eq("paid"),
    )

    expected = pd.DataFrame(
        {
            "status": ["paid", "paid"],
            "amount": [100.0, 200.0],
        },
        index=[0, 2],
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )
    assert result is not frame


def test_filter_rows_can_filter_numeric_threshold() -> None:
    frame = pd.DataFrame(
        {
            "amount": [50.0, 100.0, 250.0],
        }
    )

    result = filter_rows(
        frame,
        lambda data: data["amount"].ge(100),
    )

    assert result["amount"].tolist() == [
        100.0,
        250.0,
    ]


def test_filter_rows_rejects_invalid_frame() -> None:
    with pytest.raises(
        TransformationError,
        match="DataFrame",
    ):
        filter_rows(
            "invalid",  # type: ignore[arg-type]
            lambda data: pd.Series(dtype=bool),
        )


def test_add_ratio_column_calculates_vectorized_ratio() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0, 200.0, 300.0],
            "orders": [10.0, 20.0, 30.0],
        }
    )

    result = add_ratio_column(
        frame,
        numerator="revenue",
        denominator="orders",
        output_column="average_order_value",
    )

    assert result["average_order_value"].tolist() == [
        pytest.approx(10.0),
        pytest.approx(10.0),
        pytest.approx(10.0),
    ]


def test_add_ratio_column_returns_missing_for_zero_denominator() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0, 200.0],
            "orders": [10.0, 0.0],
        }
    )

    result = add_ratio_column(
        frame,
        numerator="revenue",
        denominator="orders",
        output_column="average_order_value",
    )

    assert result["average_order_value"].iloc[0] == pytest.approx(
        10.0
    )
    assert pd.isna(
        result["average_order_value"].iloc[1]
    )


def test_add_ratio_column_validates_columns() -> None:
    frame = pd.DataFrame(
        {
            "revenue": [100.0],
        }
    )

    with pytest.raises(
        TransformationError,
        match="orders",
    ):
        add_ratio_column(
            frame,
            numerator="revenue",
            denominator="orders",
            output_column="ratio",
        )


def test_aggregate_chunk_groups_and_sums() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "paid", "pending"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("status",),
        value_column="amount",
        aggregation="sum",
    )

    result = result.sort_values(
        "status"
    ).reset_index(drop=True)

    expected = pd.DataFrame(
        {
            "status": ["paid", "pending"],
            "amount": [150.0, 25.0],
        }
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )


def test_aggregate_chunk_supports_mean() -> None:
    frame = pd.DataFrame(
        {
            "status": ["paid", "paid", "pending"],
            "amount": [100.0, 50.0, 25.0],
        }
    )

    result = aggregate_chunk(
        frame,
        dimensions=("status",),
        value_column="amount",
        aggregation="mean",
    )

    paid = result.loc[
        result["status"].eq("paid"),
        "amount",
    ].iloc[0]

    assert paid == pytest.approx(75.0)


def test_aggregate_chunk_rejects_empty_dimensions() -> None:
    with pytest.raises(
        TransformationError,
        match="dimension",
    ):
        aggregate_chunk(
            _orders(),
            dimensions=(),
            value_column="amount",
        )


def test_aggregate_chunk_rejects_missing_value_column() -> None:
    with pytest.raises(
        TransformationError,
        match="missing",
    ):
        aggregate_chunk(
            _orders(),
            dimensions=("status",),
            value_column="missing",
        )


def test_summarize_chunk_returns_operational_metrics() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": [100.0, 200.0, 300.0],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 3
    assert result["numeric_sum"] == pytest.approx(600.0)
    assert result["numeric_mean"] == pytest.approx(200.0)
    assert result["numeric_min"] == pytest.approx(100.0)
    assert result["numeric_max"] == pytest.approx(300.0)


def test_summarize_chunk_handles_missing_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [100.0, None, 300.0],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 3
    assert result["non_null_count"] == 2
    assert result["numeric_sum"] == pytest.approx(400.0)
    assert result["numeric_mean"] == pytest.approx(200.0)


def test_summarize_chunk_returns_zero_for_all_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [None, None],
        }
    )

    result = summarize_chunk(
        frame,
        value_column="amount",
    )

    assert result["row_count"] == 2
    assert result["non_null_count"] == 0
    assert result["numeric_sum"] == pytest.approx(0.0)
    assert result["numeric_mean"] == pytest.approx(0.0)


def test_make_transformer_returns_callable() -> None:
    transformer = make_transformer(
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
        )
    )

    assert callable(transformer)


def test_make_transformer_applies_configured_transformation() -> None:
    transformer = make_transformer(
        pipeline_config=_config()
    )

    frame = _orders()

    transformed = transformer(
        frame,
        None,
    )

    assert isinstance(
        transformed,
        pd.DataFrame,
    )
    assert "order_id" in transformed.columns
    assert "numeric_value" in transformed.columns


def test_make_transformer_can_be_used_as_chunk_processor_callback() -> None:
    transformer = make_transformer(
        pipeline_config=_config()
    )

    frame = _orders()

    transformed = transformer(
        frame,
        None,
    )

    assert len(transformed) == len(frame)
    assert transformed["order_id"].tolist() == [
        "1001",
        "1002",
        "1003",
    ]


def test_transform_chunk_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
            "quantity",
            "status",
            "created_at",
        ]
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
    assert result.empty
    assert "order_id" in result.columns


def test_transform_chunk_preserves_expected_row_order() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1003", "1001", "1002"],
            "amount": [30.0, 10.0, 20.0],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
            drop_duplicates=False,
        ),
    )

    assert result["order_id"].tolist() == [
        "1003",
        "1001",
        "1002",
    ]


def test_transform_chunk_handles_missing_optional_timestamp_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": [100.0, 200.0],
            "created_at": [
                "2026-01-01T10:00:00Z",
                None,
            ],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(),
    )

    assert len(result) == 2
    assert result["created_at"].notna().sum() == 1


def test_transform_chunk_handles_mixed_case_column_names() -> None:
    frame = pd.DataFrame(
        {
            "ORDER_ID": ["1001"],
            "AMOUNT": ["125.50"],
        }
    )

    result = transform_chunk(
        frame,
        pipeline_config=_config(
            timestamp_columns=(),
            numeric_columns=("amount",),
            required_columns=("order_id",),
        ),
    )

    assert "order_id" in result.columns
    assert "amount" in result.columns
    assert result["amount"].iloc[0] == pytest.approx(
        125.50
    )


def test_transform_chunk_rejects_all_invalid_numeric_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001", "1002"],
            "amount": ["invalid", "also-invalid"],
        }
    )

    with pytest.raises(
        TransformationError,
    ):
        transform_chunk(
            frame,
            pipeline_config=_config(
                timestamp_columns=(),
                numeric_columns=("amount",),
                drop_invalid_records=True,
            ),
        )