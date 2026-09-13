from __future__ import annotations

import pandas as pd
import pytest

from src.ingestion import IngestionError, IngestionResult
from src.validation import (
    ValidationError,
    ValidationResult,
    assert_valid,
    validate_allowed_values,
    validate_dataframe,
    validate_datetime_columns,
    validate_foreign_key,
    validate_ingestion_result,
    validate_non_negative_columns,
    validate_not_empty,
    validate_numeric_columns,
    validate_required_columns,
    validate_required_values,
    validate_timestamp_order,
    validate_transformed_data,
    validate_unique_keys,
)


def test_validation_result_is_valid_when_no_issues_exist() -> None:
    result = ValidationResult()

    assert result.is_valid is True
    assert result.issues == []


def test_validation_result_is_invalid_when_issue_exists() -> None:
    result = ValidationResult()
    result.add_error(
        "order_id",
        "order_id is required",
    )

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].column == "order_id"
    assert result.issues[0].message == "order_id is required"


def test_validation_result_tracks_multiple_issues() -> None:
    result = ValidationResult()

    result.add_error(
        "order_id",
        "missing values",
    )
    result.add_error(
        "amount",
        "negative values",
    )

    assert result.is_valid is False
    assert len(result.issues) == 2


def test_validation_error_is_a_value_error() -> None:
    assert issubclass(
        ValidationError,
        ValueError,
    )


def test_validate_required_columns_accepts_complete_schema() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "amount": 100.0,
            }
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_required_columns_reports_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "customer_id",
        "amount",
    }


def test_validate_required_columns_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_not_empty_accepts_non_empty_dataframe() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_not_empty(frame)

    assert result.is_valid is True


def test_validate_not_empty_rejects_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=["order_id"]
    )

    result = validate_not_empty(frame)

    assert result.is_valid is False
    assert len(result.issues) == 1


def test_validate_required_values_accepts_complete_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
            },
            {
                "order_id": "order-2",
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_required_values_rejects_missing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": None,
            },
            {
                "order_id": None,
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "order_id",
        "customer_id",
    }


def test_validate_required_values_detects_blank_strings() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": " ",
            },
            {
                "order_id": "\t",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is False


def test_validate_unique_keys_accepts_unique_values() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-2"},
            {"order_id": "order-3"},
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is True


def test_validate_unique_keys_rejects_duplicate_values() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-1"},
            {"order_id": "order-2"},
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is False
    assert len(result.issues) >= 1


def test_validate_unique_keys_supports_composite_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
            {
                "customer_id": "customer-1",
                "order_id": "order-2",
            },
            {
                "customer_id": "customer-2",
                "order_id": "order-1",
            },
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid is True


def test_validate_unique_keys_rejects_duplicate_composite_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid is False


def test_validate_numeric_columns_accepts_numeric_data() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
                "quantity": 2,
            },
            {
                "amount": 50.5,
                "quantity": 1,
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid is True


def test_validate_numeric_columns_rejects_non_numeric_data() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": "100",
            },
            {
                "amount": "invalid",
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is False


def test_validate_numeric_columns_handles_missing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
            },
            {
                "amount": None,
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_non_negative_columns_accepts_zero_and_positive_values() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 0.0},
            {"amount": 100.0},
            {"amount": 50.0},
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_non_negative_columns_rejects_negative_values() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 100.0},
            {"amount": -5.0},
            {"amount": 50.0},
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is False
    assert any(
        "negative" in issue.message.lower()
        for issue in result.issues
    )


def test_validate_datetime_columns_accepts_valid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_datetime_columns_rejects_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-01T10:00:00Z",
            },
            {
                "created_at": "not-a-timestamp",
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_datetime_columns_allows_missing_timestamps_when_present_as_null() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "created_at": pd.NaT,
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_timestamp_order_accepts_correct_order() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-01T12:00:00Z"
                ),
            },
            {
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-02T11:00:00Z"
                ),
            },
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is True


def test_validate_timestamp_order_rejects_updated_before_created() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T12:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is False


def test_validate_timestamp_order_accepts_equal_timestamps() -> None:
    timestamp = pd.Timestamp(
        "2026-01-01T10:00:00Z"
    )

    frame = pd.DataFrame(
        [
            {
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is True


def test_validate_allowed_values_accepts_valid_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "pending"},
            {"status": "processing"},
            {"status": "completed"},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={
            "pending",
            "processing",
            "completed",
        },
    )

    assert result.is_valid is True


def test_validate_allowed_values_rejects_unknown_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "pending"},
            {"status": "completed"},
            {"status": "unknown"},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={
            "pending",
            "completed",
        },
    )

    assert result.is_valid is False
    assert any(
        "unknown" in issue.message.lower()
        or "allowed" in issue.message.lower()
        for issue in result.issues
    )


def test_validate_allowed_values_handles_null_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "completed"},
            {"status": None},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={"completed"},
    )

    assert result.is_valid is True


def test_validate_foreign_key_accepts_matching_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
            {"customer_id": "customer-3"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_foreign_key_rejects_orphan_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-999"},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is False
    assert any(
        "customer-999" in issue.message
        for issue in result.issues
    )


def test_validate_foreign_key_ignores_null_foreign_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": None},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_dataframe_combines_schema_and_quality_checks() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "status": "completed",
            },
            {
                "order_id": "order-2",
                "amount": 50.0,
                "status": "pending",
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
        required_value_columns=("order_id",),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        allowed_values={
            "status": {
                "pending",
                "processing",
                "completed",
            }
        },
    )

    assert result.is_valid is True
    assert result.issues == []


def test_validate_dataframe_reports_multiple_quality_failures() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": -100.0,
                "status": "completed",
            },
            {
                "order_id": "order-1",
                "amount": "invalid",
                "status": "unknown",
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        allowed_values={
            "status": {
                "pending",
                "completed",
            }
        },
    )

    assert result.is_valid is False
    assert len(result.issues) >= 3


def test_validate_dataframe_rejects_empty_frame_when_requested() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
        require_non_empty=True,
    )

    assert result.is_valid is False


def test_validate_dataframe_accepts_empty_frame_without_non_empty_requirement() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
    )

    assert result.is_valid is True


def test_validate_ingestion_result_accepts_valid_result() -> None:
    result = IngestionResult(
        records=[
            {"id": "1"},
            {"id": "2"},
        ],
        pages_fetched=2,
        records_fetched=2,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is True


def test_validate_ingestion_result_rejects_negative_page_count() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=-1,
        records_fetched=0,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_rejects_negative_record_count() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=1,
        records_fetched=-1,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_rejects_inconsistent_record_count() -> None:
    result = IngestionResult(
        records=[
            {"id": "1"},
        ],
        pages_fetched=1,
        records_fetched=2,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


@pytest.mark.parametrize(
    "records",
    [
        [None],
        ["invalid"],
        [123],
        [object()],
    ],
)
def test_validate_ingestion_result_rejects_non_mapping_records(
    records: list[object],
) -> None:
    result = IngestionResult(
        records=records,  # type: ignore[arg-type]
        pages_fetched=1,
        records_fetched=len(records),
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_handles_empty_successful_ingestion() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=0,
        records_fetched=0,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is True


def test_validate_transformed_data_accepts_valid_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-2",
                "amount": 50.0,
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
            },
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_transformed_data_rejects_duplicate_ids() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-1",
                "amount": 150.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T11:00:00Z"
                ),
            },
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_negative_numeric_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": -10.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_invalid_datetime_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": "invalid",
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_missing_identifier_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": None,
                "amount": 100.0,
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_accepts_empty_frame() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.is_valid is True


def test_assert_valid_returns_valid_result() -> None:
    result = ValidationResult()

    returned = assert_valid(result)

    assert returned is result


def test_assert_valid_raises_validation_error_for_invalid_result() -> None:
    result = ValidationResult()
    result.add_error(
        "amount",
        "amount cannot be negative",
    )

    with pytest.raises(
        ValidationError,
        match="amount cannot be negative",
    ):
        assert_valid(result)


def test_assert_valid_includes_all_validation_issues() -> None:
    result = ValidationResult()
    result.add_error(
        "order_id",
        "duplicate order id",
    )
    result.add_error(
        "amount",
        "negative amount",
    )

    with pytest.raises(
        ValidationError,
    ) as exc_info:
        assert_valid(result)

    message = str(exc_info.value)

    assert "duplicate order id" in message
    assert "negative amount" in message


def test_validation_errors_are_actionable_for_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
        ),
    )

    assert result.is_valid is False

    messages = " ".join(
        issue.message
        for issue in result.issues
    )

    assert "customer_id" in messages
    assert "amount" in messages


def test_validate_foreign_key_handles_duplicate_reference_rows() -> None:
    orders = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-2",
            },
        ]
    )
    customers = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_numeric_columns_reports_each_invalid_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": "invalid",
                "quantity": "also-invalid",
            }
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "amount",
        "quantity",
    }


def test_validate_non_negative_columns_allows_null_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
            },
            {
                "amount": None,
            },
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_datetime_columns_reports_each_invalid_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "invalid",
                "updated_at": "also-invalid",
            }
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=(
            "created_at",
            "updated_at",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "created_at",
        "updated_at",
    }


def test_validate_required_columns_requires_dataframe() -> None:
    with pytest.raises(
        (TypeError, ValueError),
    ):
        validate_required_columns(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
            required_columns=("order_id",),
        )


def test_validate_dataframe_preserves_validity_for_reproducible_pipeline_contract() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "amount": 250.0,
                "status": "completed",
                "created_at": pd.Timestamp(
                    "2026-09-01T09:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-09-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-2",
                "customer_id": "customer-2",
                "amount": 125.0,
                "status": "processing",
                "created_at": pd.Timestamp(
                    "2026-09-02T09:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-09-02T09:30:00Z"
                ),
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
            "status",
            "created_at",
            "updated_at",
        ),
        required_value_columns=(
            "order_id",
            "customer_id",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        datetime_columns=(
            "created_at",
            "updated_at",
        ),
        allowed_values={
            "status": {
                "pending",
                "processing",
                "completed",
                "cancelled",
            }
        },
    )

    assert result.is_valid is True
    assert result.issues == []

from __future__ import annotations

import pandas as pd
import pytest

from src.ingestion import IngestionError, IngestionResult
from src.validation import (
    ValidationError,
    ValidationResult,
    assert_valid,
    validate_allowed_values,
    validate_dataframe,
    validate_datetime_columns,
    validate_foreign_key,
    validate_ingestion_result,
    validate_non_negative_columns,
    validate_not_empty,
    validate_numeric_columns,
    validate_required_columns,
    validate_required_values,
    validate_timestamp_order,
    validate_transformed_data,
    validate_unique_keys,
)


def test_validation_result_is_valid_when_no_issues_exist() -> None:
    result = ValidationResult()

    assert result.is_valid is True
    assert result.issues == []


def test_validation_result_is_invalid_when_issue_exists() -> None:
    result = ValidationResult()
    result.add_error(
        "order_id",
        "order_id is required",
    )

    assert result.is_valid is False
    assert len(result.issues) == 1
    assert result.issues[0].column == "order_id"
    assert result.issues[0].message == "order_id is required"


def test_validation_result_tracks_multiple_issues() -> None:
    result = ValidationResult()

    result.add_error(
        "order_id",
        "missing values",
    )
    result.add_error(
        "amount",
        "negative values",
    )

    assert result.is_valid is False
    assert len(result.issues) == 2


def test_validation_error_is_a_value_error() -> None:
    assert issubclass(
        ValidationError,
        ValueError,
    )


def test_validate_required_columns_accepts_complete_schema() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "amount": 100.0,
            }
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_required_columns_reports_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "customer_id",
        "amount",
    }


def test_validate_required_columns_handles_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "customer_id",
        ]
    )

    result = validate_required_columns(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_not_empty_accepts_non_empty_dataframe() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_not_empty(frame)

    assert result.is_valid is True


def test_validate_not_empty_rejects_empty_dataframe() -> None:
    frame = pd.DataFrame(
        columns=["order_id"]
    )

    result = validate_not_empty(frame)

    assert result.is_valid is False
    assert len(result.issues) == 1


def test_validate_required_values_accepts_complete_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
            },
            {
                "order_id": "order-2",
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is True


def test_validate_required_values_rejects_missing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": None,
            },
            {
                "order_id": None,
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=(
            "order_id",
            "customer_id",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "order_id",
        "customer_id",
    }


def test_validate_required_values_detects_blank_strings() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": " ",
            },
            {
                "order_id": "\t",
            },
        ]
    )

    result = validate_required_values(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is False


def test_validate_unique_keys_accepts_unique_values() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-2"},
            {"order_id": "order-3"},
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is True


def test_validate_unique_keys_rejects_duplicate_values() -> None:
    frame = pd.DataFrame(
        [
            {"order_id": "order-1"},
            {"order_id": "order-1"},
            {"order_id": "order-2"},
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert result.is_valid is False
    assert len(result.issues) >= 1


def test_validate_unique_keys_supports_composite_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
            {
                "customer_id": "customer-1",
                "order_id": "order-2",
            },
            {
                "customer_id": "customer-2",
                "order_id": "order-1",
            },
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid is True


def test_validate_unique_keys_rejects_duplicate_composite_keys() -> None:
    frame = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
            {
                "customer_id": "customer-1",
                "order_id": "order-1",
            },
        ]
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid is False


def test_validate_numeric_columns_accepts_numeric_data() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
                "quantity": 2,
            },
            {
                "amount": 50.5,
                "quantity": 1,
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid is True


def test_validate_numeric_columns_rejects_non_numeric_data() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": "100",
            },
            {
                "amount": "invalid",
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is False


def test_validate_numeric_columns_handles_missing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
            },
            {
                "amount": None,
            },
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_non_negative_columns_accepts_zero_and_positive_values() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 0.0},
            {"amount": 100.0},
            {"amount": 50.0},
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_non_negative_columns_rejects_negative_values() -> None:
    frame = pd.DataFrame(
        [
            {"amount": 100.0},
            {"amount": -5.0},
            {"amount": 50.0},
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is False
    assert any(
        "negative" in issue.message.lower()
        for issue in result.issues
    )


def test_validate_datetime_columns_accepts_valid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_datetime_columns_rejects_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "2026-01-01T10:00:00Z",
            },
            {
                "created_at": "not-a-timestamp",
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_datetime_columns_allows_missing_timestamps_when_present_as_null() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "created_at": pd.NaT,
            },
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_timestamp_order_accepts_correct_order() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-01T12:00:00Z"
                ),
            },
            {
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-02T11:00:00Z"
                ),
            },
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is True


def test_validate_timestamp_order_rejects_updated_before_created() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": pd.Timestamp(
                    "2026-01-01T12:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is False


def test_validate_timestamp_order_accepts_equal_timestamps() -> None:
    timestamp = pd.Timestamp(
        "2026-01-01T10:00:00Z"
    )

    frame = pd.DataFrame(
        [
            {
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        ]
    )

    result = validate_timestamp_order(
        frame,
        start_column="created_at",
        end_column="updated_at",
    )

    assert result.is_valid is True


def test_validate_allowed_values_accepts_valid_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "pending"},
            {"status": "processing"},
            {"status": "completed"},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={
            "pending",
            "processing",
            "completed",
        },
    )

    assert result.is_valid is True


def test_validate_allowed_values_rejects_unknown_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "pending"},
            {"status": "completed"},
            {"status": "unknown"},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={
            "pending",
            "completed",
        },
    )

    assert result.is_valid is False
    assert any(
        "unknown" in issue.message.lower()
        or "allowed" in issue.message.lower()
        for issue in result.issues
    )


def test_validate_allowed_values_handles_null_values() -> None:
    frame = pd.DataFrame(
        [
            {"status": "completed"},
            {"status": None},
        ]
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values={"completed"},
    )

    assert result.is_valid is True


def test_validate_foreign_key_accepts_matching_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
            {"customer_id": "customer-3"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_foreign_key_rejects_orphan_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-999"},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": "customer-2"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is False
    assert any(
        "customer-999" in issue.message
        for issue in result.issues
    )


def test_validate_foreign_key_ignores_null_foreign_keys() -> None:
    orders = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
            {"customer_id": None},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "customer-1"},
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_dataframe_combines_schema_and_quality_checks() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "status": "completed",
            },
            {
                "order_id": "order-2",
                "amount": 50.0,
                "status": "pending",
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
        required_value_columns=("order_id",),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        allowed_values={
            "status": {
                "pending",
                "processing",
                "completed",
            }
        },
    )

    assert result.is_valid is True
    assert result.issues == []


def test_validate_dataframe_reports_multiple_quality_failures() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": -100.0,
                "status": "completed",
            },
            {
                "order_id": "order-1",
                "amount": "invalid",
                "status": "unknown",
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        allowed_values={
            "status": {
                "pending",
                "completed",
            }
        },
    )

    assert result.is_valid is False
    assert len(result.issues) >= 3


def test_validate_dataframe_rejects_empty_frame_when_requested() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
        require_non_empty=True,
    )

    assert result.is_valid is False


def test_validate_dataframe_accepts_empty_frame_without_non_empty_requirement() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
    )

    assert result.is_valid is True


def test_validate_ingestion_result_accepts_valid_result() -> None:
    result = IngestionResult(
        records=[
            {"id": "1"},
            {"id": "2"},
        ],
        pages_fetched=2,
        records_fetched=2,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is True


def test_validate_ingestion_result_rejects_negative_page_count() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=-1,
        records_fetched=0,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_rejects_negative_record_count() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=1,
        records_fetched=-1,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_rejects_inconsistent_record_count() -> None:
    result = IngestionResult(
        records=[
            {"id": "1"},
        ],
        pages_fetched=1,
        records_fetched=2,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


@pytest.mark.parametrize(
    "records",
    [
        [None],
        ["invalid"],
        [123],
        [object()],
    ],
)
def test_validate_ingestion_result_rejects_non_mapping_records(
    records: list[object],
) -> None:
    result = IngestionResult(
        records=records,  # type: ignore[arg-type]
        pages_fetched=1,
        records_fetched=len(records),
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is False


def test_validate_ingestion_result_handles_empty_successful_ingestion() -> None:
    result = IngestionResult(
        records=[],
        pages_fetched=0,
        records_fetched=0,
    )

    validation = validate_ingestion_result(result)

    assert validation.is_valid is True


def test_validate_transformed_data_accepts_valid_frame() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-2",
                "amount": 50.0,
                "created_at": pd.Timestamp(
                    "2026-01-02T10:00:00Z"
                ),
            },
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is True


def test_validate_transformed_data_rejects_duplicate_ids() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-1",
                "amount": 150.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T11:00:00Z"
                ),
            },
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_negative_numeric_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": -10.0,
                "created_at": pd.Timestamp(
                    "2026-01-01T10:00:00Z"
                ),
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_invalid_datetime_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "amount": 100.0,
                "created_at": "invalid",
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
        datetime_columns=("created_at",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_rejects_missing_identifier_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": None,
                "amount": 100.0,
            }
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.is_valid is False


def test_validate_transformed_data_accepts_empty_frame() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_transformed_data(
        frame,
        id_columns=("order_id",),
        numeric_columns=("amount",),
    )

    assert result.is_valid is True


def test_assert_valid_returns_valid_result() -> None:
    result = ValidationResult()

    returned = assert_valid(result)

    assert returned is result


def test_assert_valid_raises_validation_error_for_invalid_result() -> None:
    result = ValidationResult()
    result.add_error(
        "amount",
        "amount cannot be negative",
    )

    with pytest.raises(
        ValidationError,
        match="amount cannot be negative",
    ):
        assert_valid(result)


def test_assert_valid_includes_all_validation_issues() -> None:
    result = ValidationResult()
    result.add_error(
        "order_id",
        "duplicate order id",
    )
    result.add_error(
        "amount",
        "negative amount",
    )

    with pytest.raises(
        ValidationError,
    ) as exc_info:
        assert_valid(result)

    message = str(exc_info.value)

    assert "duplicate order id" in message
    assert "negative amount" in message


def test_validation_errors_are_actionable_for_missing_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
            }
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
        ),
    )

    assert result.is_valid is False

    messages = " ".join(
        issue.message
        for issue in result.issues
    )

    assert "customer_id" in messages
    assert "amount" in messages


def test_validate_foreign_key_handles_duplicate_reference_rows() -> None:
    orders = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-2",
            },
        ]
    )
    customers = pd.DataFrame(
        [
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-1",
            },
            {
                "customer_id": "customer-2",
            },
        ]
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid is True


def test_validate_numeric_columns_reports_each_invalid_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": "invalid",
                "quantity": "also-invalid",
            }
        ]
    )

    result = validate_numeric_columns(
        frame,
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "amount",
        "quantity",
    }


def test_validate_non_negative_columns_allows_null_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "amount": 100.0,
            },
            {
                "amount": None,
            },
        ]
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid is True


def test_validate_datetime_columns_reports_each_invalid_column() -> None:
    frame = pd.DataFrame(
        [
            {
                "created_at": "invalid",
                "updated_at": "also-invalid",
            }
        ]
    )

    result = validate_datetime_columns(
        frame,
        columns=(
            "created_at",
            "updated_at",
        ),
    )

    assert result.is_valid is False
    assert {
        issue.column
        for issue in result.issues
    } == {
        "created_at",
        "updated_at",
    }


def test_validate_required_columns_requires_dataframe() -> None:
    with pytest.raises(
        (TypeError, ValueError),
    ):
        validate_required_columns(
            [{"order_id": "order-1"}],  # type: ignore[arg-type]
            required_columns=("order_id",),
        )


def test_validate_dataframe_preserves_validity_for_reproducible_pipeline_contract() -> None:
    frame = pd.DataFrame(
        [
            {
                "order_id": "order-1",
                "customer_id": "customer-1",
                "amount": 250.0,
                "status": "completed",
                "created_at": pd.Timestamp(
                    "2026-09-01T09:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-09-01T10:00:00Z"
                ),
            },
            {
                "order_id": "order-2",
                "customer_id": "customer-2",
                "amount": 125.0,
                "status": "processing",
                "created_at": pd.Timestamp(
                    "2026-09-02T09:00:00Z"
                ),
                "updated_at": pd.Timestamp(
                    "2026-09-02T09:30:00Z"
                ),
            },
        ]
    )

    result = validate_dataframe(
        frame,
        required_columns=(
            "order_id",
            "customer_id",
            "amount",
            "status",
            "created_at",
            "updated_at",
        ),
        required_value_columns=(
            "order_id",
            "customer_id",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        datetime_columns=(
            "created_at",
            "updated_at",
        ),
        allowed_values={
            "status": {
                "pending",
                "processing",
                "completed",
                "cancelled",
            }
        },
    )

    assert result.is_valid is True
    assert result.issues == []