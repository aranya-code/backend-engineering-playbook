from __future__ import annotations

import pandas as pd
import pytest

from src.validation import (
    ValidationError,
    ValidationIssue,
    ValidationResult,
    assert_valid,
    validate_allowed_values,
    validate_chunk,
    validate_datetime_columns,
    validate_foreign_key,
    validate_global_dataset,
    validate_memory_usage,
    validate_non_negative_columns,
    validate_not_empty,
    validate_numeric_columns,
    validate_required_columns,
    validate_required_values,
    validate_schema_consistency,
    validate_timestamp_order,
    validate_unique_keys,
)


def _orders() -> pd.DataFrame:
    """Build a representative transactional dataset."""
    return pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": [100.0, 250.0, 75.0],
            "quantity": [2, 5, 1],
            "status": ["paid", "pending", "paid"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:30:00Z",
                "2026-01-03T09:15:00Z",
            ],
        }
    )


def test_validation_issue_is_immutable_and_stores_metadata() -> None:
    issue = ValidationIssue(
        check="numeric",
        message="Invalid numeric values.",
        column="amount",
        row_count=3,
    )

    assert issue.check == "numeric"
    assert issue.message == "Invalid numeric values."
    assert issue.column == "amount"
    assert issue.row_count == 3

    with pytest.raises(
        AttributeError,
    ):
        issue.row_count = 5  # type: ignore[misc]


def test_validation_result_defaults_to_valid() -> None:
    result = ValidationResult()

    assert result.is_valid
    assert result.issue_count == 0
    assert result.issues == ()


def test_validation_result_reports_issues() -> None:
    issue = ValidationIssue(
        check="required_columns",
        message="Missing column.",
    )

    result = ValidationResult(
        issues=(issue,)
    )

    assert not result.is_valid
    assert result.issue_count == 1
    assert result.issues == (issue,)


def test_validation_result_extend_combines_issues() -> None:
    first = ValidationResult(
        issues=(
            ValidationIssue(
                check="required_columns",
                message="Missing order_id.",
            ),
        )
    )
    second = ValidationResult(
        issues=(
            ValidationIssue(
                check="numeric",
                message="Invalid amount.",
            ),
        )
    )

    combined = first.extend(
        second
    )

    assert combined.issue_count == 2
    assert [
        issue.check
        for issue in combined.issues
    ] == [
        "required_columns",
        "numeric",
    ]


def test_validate_required_columns_passes_when_schema_is_complete() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_required_columns_reports_missing_columns() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=(
            "order_id",
            "customer_id",
            "missing_column",
        ),
    )

    assert not result.is_valid
    assert result.issue_count == 2

    assert {
        issue.column
        for issue in result.issues
    } == {
        "customer_id",
        "missing_column",
    }


def test_validate_required_columns_reports_full_frame_row_count() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=("customer_id",),
    )

    issue = result.issues[0]

    assert issue.row_count == len(
        _orders()
    )


def test_validate_required_columns_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        ValidationError,
        match="DataFrame",
    ):
        validate_required_columns(
            "invalid",  # type: ignore[arg-type]
            required_columns=(),
        )


def test_validate_not_empty_passes_for_non_empty_frame() -> None:
    result = validate_not_empty(
        _orders()
    )

    assert result.is_valid


def test_validate_not_empty_reports_empty_frame() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_not_empty(
        frame
    )

    assert not result.is_valid
    assert result.issue_count == 1
    assert result.issues[0].row_count == 0


def test_validate_required_values_passes_for_complete_values() -> None:
    result = validate_required_values(
        _orders(),
        columns=(
            "order_id",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_required_values_detects_null_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                None,
                "1003",
            ],
        }
    )

    result = validate_required_values(
        frame,
        columns=("order_id",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "order_id"


def test_validate_required_values_detects_blank_strings() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                "   ",
                "",
                "pending",
            ]
        }
    )

    result = validate_required_values(
        frame,
        columns=("status",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2


def test_validate_required_values_allows_non_string_zero_values() -> None:
    frame = pd.DataFrame(
        {
            "quantity": [0, 1, 2],
        }
    )

    result = validate_required_values(
        frame,
        columns=("quantity",),
    )

    assert result.is_valid


def test_validate_unique_keys_passes_for_unique_keys() -> None:
    result = validate_unique_keys(
        _orders(),
        columns=("order_id",),
    )

    assert result.is_valid


def test_validate_unique_keys_detects_duplicate_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                120.0,
                200.0,
            ],
        }
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "order_id"


def test_validate_unique_keys_supports_composite_keys() -> None:
    frame = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C001",
                "C002",
            ],
            "order_id": [
                "1001",
                "1002",
                "1001",
            ],
        }
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid


def test_validate_unique_keys_empty_key_configuration_is_valid() -> None:
    result = validate_unique_keys(
        _orders(),
        columns=(),
    )

    assert result.is_valid


def test_validate_numeric_columns_passes_for_numeric_values() -> None:
    result = validate_numeric_columns(
        _orders(),
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid


def test_validate_numeric_columns_accepts_numeric_strings() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.50",
                "250",
                "75.25",
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_numeric_columns_detects_invalid_non_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.50",
                "invalid",
                None,
                "250",
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "amount"


def test_validate_numeric_columns_validates_requested_columns() -> None:
    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_numeric_columns(
            _orders(),
            columns=("missing",),
        )


def test_validate_non_negative_columns_passes_for_non_negative_values() -> None:
    result = validate_non_negative_columns(
        _orders(),
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid


def test_validate_non_negative_columns_detects_negative_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                -25.0,
                -10.0,
                50.0,
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2


def test_validate_non_negative_columns_treats_invalid_strings_as_non_negative_after_coercion() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.0",
                "invalid",
                "-50.0",
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1


def test_validate_datetime_columns_passes_for_valid_timestamps() -> None:
    result = validate_datetime_columns(
        _orders(),
        columns=("created_at",),
    )

    assert result.is_valid


def test_validate_datetime_columns_detects_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "created_at": [
                "2026-01-01T10:00:00Z",
                "not-a-timestamp",
                None,
            ]
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "created_at"


def test_validate_datetime_columns_accepts_timezone_aware_values() -> None:
    frame = pd.DataFrame(
        {
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-02T10:00:00+05:30",
                ],
                utc=True,
            )
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid


def test_validate_timestamp_order_passes_when_end_follows_start() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert result.is_valid


def test_validate_timestamp_order_detects_end_before_start() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-02T11:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "ended_at"


def test_validate_timestamp_order_ignores_rows_with_missing_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                None,
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-01T09:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert result.is_valid


def test_validate_allowed_values_passes_for_valid_values() -> None:
    result = validate_allowed_values(
        _orders(),
        column="status",
        allowed_values=(
            "paid",
            "pending",
            "cancelled",
        ),
    )

    assert result.is_valid


def test_validate_allowed_values_detects_invalid_values() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                "pending",
                "failed",
                "unknown",
            ]
        }
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values=(
            "paid",
            "pending",
            "cancelled",
        ),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "status"
    assert "failed" in result.issues[0].message
    assert "unknown" in result.issues[0].message


def test_validate_allowed_values_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                None,
            ]
        }
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values=("paid",),
    )

    assert result.is_valid


def test_validate_foreign_key_passes_when_all_references_exist() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
                "C001",
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
                "C003",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid


def test_validate_foreign_key_detects_orphan_values() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C999",
                "C999",
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "customer_id"


def test_validate_foreign_key_ignores_null_foreign_keys() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                None,
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid


def test_validate_schema_consistency_passes_for_matching_schema() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
            "status": ["paid"],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_schema_consistency_detects_missing_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert not result.is_valid
    assert any(
        "status" in issue.message
        for issue in result.issues
    )


def test_validate_schema_consistency_detects_unexpected_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
            "internal_flag": [True],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
        ),
    )

    assert not result.is_valid
    assert any(
        "internal_flag" in issue.message
        for issue in result.issues
    )


def test_validate_memory_usage_passes_when_within_budget() -> None:
    frame = _orders()

    memory_bytes = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    result = validate_memory_usage(
        frame,
        maximum_bytes=memory_bytes,
    )

    assert result.is_valid


def test_validate_memory_usage_detects_budget_exceeded() -> None:
    frame = _orders()

    result = validate_memory_usage(
        frame,
        maximum_bytes=1,
    )

    assert not result.is_valid
    assert result.issues[0].check == "memory_usage"
    assert result.issues[0].row_count == len(frame)


def test_validate_memory_usage_rejects_non_positive_limit() -> None:
    with pytest.raises(
        ValidationError,
        match="greater than zero",
    ):
        validate_memory_usage(
            _orders(),
            maximum_bytes=0,
        )

    with pytest.raises(
        ValidationError,
        match="greater than zero",
    ):
        validate_memory_usage(
            _orders(),
            maximum_bytes=-1,
        )


def test_validate_chunk_runs_requested_checks() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                -25.0,
                "invalid",
            ],
            "status": [
                "paid",
                "pending",
                "unknown",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T11:00:00Z",
                "not-a-timestamp",
            ],
        }
    )

    result = validate_chunk(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
        required_value_columns=(
            "order_id",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
    )

    assert not result.is_valid

    checks = {
        issue.check
        for issue in result.issues
    }

    assert checks >= {
        "unique_keys",
        "numeric",
        "non_negative",
        "datetime",
        "allowed_values",
    }


def test_validate_chunk_can_require_non_empty_data() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_chunk(
        frame,
        require_non_empty=True,
    )

    assert not result.is_valid
    assert any(
        issue.check == "not_empty"
        for issue in result.issues
    )


def test_validate_chunk_can_enforce_memory_budget() -> None:
    frame = _orders()

    result = validate_chunk(
        frame,
        maximum_memory_bytes=1,
    )

    assert not result.is_valid
    assert any(
        issue.check == "memory_usage"
        for issue in result.issues
    )


def test_validate_chunk_returns_valid_result_for_clean_data() -> None:
    result = validate_chunk(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
            "created_at",
        ),
        required_value_columns=(
            "order_id",
            "status",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        non_negative_columns=(
            "amount",
            "quantity",
        ),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
        require_non_empty=True,
    )

    assert result.is_valid


def test_validate_global_dataset_passes_for_valid_dataset() -> None:
    result = validate_global_dataset(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
            "created_at",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        non_negative_columns=(
            "amount",
            "quantity",
        ),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
    )

    assert result.is_valid


def test_validate_global_dataset_detects_duplicate_keys() -> None:
    frame = pd.concat(
        [
            _orders(),
            _orders().iloc[[0]],
        ],
        ignore_index=True,
    )

    result = validate_global_dataset(
        frame,
        required_columns=("order_id",),
        unique_key_columns=("order_id",),
    )

    assert not result.is_valid
    assert any(
        issue.check == "unique_keys"
        for issue in result.issues
    )


def test_validate_global_dataset_requires_non_empty_output() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
        ]
    )

    result = validate_global_dataset(
        frame,
        required_columns=("order_id",),
    )

    assert not result.is_valid
    assert any(
        issue.check == "not_empty"
        for issue in result.issues
    )


def test_assert_valid_returns_original_result_when_valid() -> None:
    result = ValidationResult()

    returned = assert_valid(
        result
    )

    assert returned is result


def test_assert_valid_raises_for_invalid_result() -> None:
    result = ValidationResult(
        issues=(
            ValidationIssue(
                check="numeric",
                message="Invalid amount values.",
                column="amount",
                row_count=2,
            ),
            ValidationIssue(
                check="required_values",
                message="Missing order IDs.",
                column="order_id",
                row_count=1,
            ),
        )
    )

    with pytest.raises(
        ValidationError,
        match=r"\[numeric\].*\[required_values\]",
    ):
        assert_valid(result)


def test_validation_functions_reject_missing_requested_columns() -> None:
    frame = _orders()

    validators = (
        lambda: validate_required_values(
            frame,
            columns=("missing",),
        ),
        lambda: validate_unique_keys(
            frame,
            columns=("missing",),
        ),
        lambda: validate_numeric_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_non_negative_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_datetime_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_allowed_values(
            frame,
            column="missing",
            allowed_values=("x",),
        ),
    )

    for validator in validators:
        with pytest.raises(
            ValidationError,
            match="Missing required columns",
        ):
            validator()


def test_validate_foreign_key_rejects_missing_source_column() -> None:
    source = pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    )
    reference = pd.DataFrame(
        {
            "customer_id": ["C001"],
        }
    )

    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_foreign_key(
            source,
            column="customer_id",
            reference=reference,
            reference_column="customer_id",
        )


def test_validate_foreign_key_rejects_missing_reference_column() -> None:
    source = pd.DataFrame(
        {
            "customer_id": ["C001"],
        }
    )
    reference = pd.DataFrame(
        {
            "id": ["C001"],
        }
    )

    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_foreign_key(
            source,
            column="customer_id",
            reference=reference,
            reference_column="missing",
        )


def test_validate_timestamp_order_rejects_missing_timestamp_column() -> None:
    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_timestamp_order(
            _orders(),
            start_column="missing",
            end_column="created_at",
        )


def test_validate_schema_consistency_handles_empty_expected_schema() -> None:
    frame = pd.DataFrame()

    result = validate_schema_consistency(
        frame,
        expected_columns=(),
    )

    assert result.is_valid


def test_validate_schema_consistency_detects_both_missing_and_unexpected_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "unexpected": [True],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
        ),
    )

    assert not result.is_valid
    assert result.issue_count == 2

    messages = [
        issue.message
        for issue in result.issues
    ]

    assert any(
        "amount" in message
        for message in messages
    )
    assert any(
        "unexpected" in message
        for message in messages
    )


def test_validate_numeric_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                None,
                200.0,
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_non_negative_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                None,
                200.0,
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_datetime_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "created_at": [
                "2026-01-01T10:00:00Z",
                None,
            ]
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid

from __future__ import annotations

import pandas as pd
import pytest

from src.validation import (
    ValidationError,
    ValidationIssue,
    ValidationResult,
    assert_valid,
    validate_allowed_values,
    validate_chunk,
    validate_datetime_columns,
    validate_foreign_key,
    validate_global_dataset,
    validate_memory_usage,
    validate_non_negative_columns,
    validate_not_empty,
    validate_numeric_columns,
    validate_required_columns,
    validate_required_values,
    validate_schema_consistency,
    validate_timestamp_order,
    validate_unique_keys,
)


def _orders() -> pd.DataFrame:
    """Build a representative transactional dataset."""
    return pd.DataFrame(
        {
            "order_id": ["1001", "1002", "1003"],
            "amount": [100.0, 250.0, 75.0],
            "quantity": [2, 5, 1],
            "status": ["paid", "pending", "paid"],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T11:30:00Z",
                "2026-01-03T09:15:00Z",
            ],
        }
    )


def test_validation_issue_is_immutable_and_stores_metadata() -> None:
    issue = ValidationIssue(
        check="numeric",
        message="Invalid numeric values.",
        column="amount",
        row_count=3,
    )

    assert issue.check == "numeric"
    assert issue.message == "Invalid numeric values."
    assert issue.column == "amount"
    assert issue.row_count == 3

    with pytest.raises(
        AttributeError,
    ):
        issue.row_count = 5  # type: ignore[misc]


def test_validation_result_defaults_to_valid() -> None:
    result = ValidationResult()

    assert result.is_valid
    assert result.issue_count == 0
    assert result.issues == ()


def test_validation_result_reports_issues() -> None:
    issue = ValidationIssue(
        check="required_columns",
        message="Missing column.",
    )

    result = ValidationResult(
        issues=(issue,)
    )

    assert not result.is_valid
    assert result.issue_count == 1
    assert result.issues == (issue,)


def test_validation_result_extend_combines_issues() -> None:
    first = ValidationResult(
        issues=(
            ValidationIssue(
                check="required_columns",
                message="Missing order_id.",
            ),
        )
    )
    second = ValidationResult(
        issues=(
            ValidationIssue(
                check="numeric",
                message="Invalid amount.",
            ),
        )
    )

    combined = first.extend(
        second
    )

    assert combined.issue_count == 2
    assert [
        issue.check
        for issue in combined.issues
    ] == [
        "required_columns",
        "numeric",
    ]


def test_validate_required_columns_passes_when_schema_is_complete() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_required_columns_reports_missing_columns() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=(
            "order_id",
            "customer_id",
            "missing_column",
        ),
    )

    assert not result.is_valid
    assert result.issue_count == 2

    assert {
        issue.column
        for issue in result.issues
    } == {
        "customer_id",
        "missing_column",
    }


def test_validate_required_columns_reports_full_frame_row_count() -> None:
    result = validate_required_columns(
        _orders(),
        required_columns=("customer_id",),
    )

    issue = result.issues[0]

    assert issue.row_count == len(
        _orders()
    )


def test_validate_required_columns_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        ValidationError,
        match="DataFrame",
    ):
        validate_required_columns(
            "invalid",  # type: ignore[arg-type]
            required_columns=(),
        )


def test_validate_not_empty_passes_for_non_empty_frame() -> None:
    result = validate_not_empty(
        _orders()
    )

    assert result.is_valid


def test_validate_not_empty_reports_empty_frame() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_not_empty(
        frame
    )

    assert not result.is_valid
    assert result.issue_count == 1
    assert result.issues[0].row_count == 0


def test_validate_required_values_passes_for_complete_values() -> None:
    result = validate_required_values(
        _orders(),
        columns=(
            "order_id",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_required_values_detects_null_values() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                None,
                "1003",
            ],
        }
    )

    result = validate_required_values(
        frame,
        columns=("order_id",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "order_id"


def test_validate_required_values_detects_blank_strings() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                "   ",
                "",
                "pending",
            ]
        }
    )

    result = validate_required_values(
        frame,
        columns=("status",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2


def test_validate_required_values_allows_non_string_zero_values() -> None:
    frame = pd.DataFrame(
        {
            "quantity": [0, 1, 2],
        }
    )

    result = validate_required_values(
        frame,
        columns=("quantity",),
    )

    assert result.is_valid


def test_validate_unique_keys_passes_for_unique_keys() -> None:
    result = validate_unique_keys(
        _orders(),
        columns=("order_id",),
    )

    assert result.is_valid


def test_validate_unique_keys_detects_duplicate_rows() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                120.0,
                200.0,
            ],
        }
    )

    result = validate_unique_keys(
        frame,
        columns=("order_id",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "order_id"


def test_validate_unique_keys_supports_composite_keys() -> None:
    frame = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C001",
                "C002",
            ],
            "order_id": [
                "1001",
                "1002",
                "1001",
            ],
        }
    )

    result = validate_unique_keys(
        frame,
        columns=(
            "customer_id",
            "order_id",
        ),
    )

    assert result.is_valid


def test_validate_unique_keys_empty_key_configuration_is_valid() -> None:
    result = validate_unique_keys(
        _orders(),
        columns=(),
    )

    assert result.is_valid


def test_validate_numeric_columns_passes_for_numeric_values() -> None:
    result = validate_numeric_columns(
        _orders(),
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid


def test_validate_numeric_columns_accepts_numeric_strings() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.50",
                "250",
                "75.25",
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_numeric_columns_detects_invalid_non_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.50",
                "invalid",
                None,
                "250",
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "amount"


def test_validate_numeric_columns_validates_requested_columns() -> None:
    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_numeric_columns(
            _orders(),
            columns=("missing",),
        )


def test_validate_non_negative_columns_passes_for_non_negative_values() -> None:
    result = validate_non_negative_columns(
        _orders(),
        columns=(
            "amount",
            "quantity",
        ),
    )

    assert result.is_valid


def test_validate_non_negative_columns_detects_negative_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                -25.0,
                -10.0,
                50.0,
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2


def test_validate_non_negative_columns_treats_invalid_strings_as_non_negative_after_coercion() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                "100.0",
                "invalid",
                "-50.0",
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1


def test_validate_datetime_columns_passes_for_valid_timestamps() -> None:
    result = validate_datetime_columns(
        _orders(),
        columns=("created_at",),
    )

    assert result.is_valid


def test_validate_datetime_columns_detects_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "created_at": [
                "2026-01-01T10:00:00Z",
                "not-a-timestamp",
                None,
            ]
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "created_at"


def test_validate_datetime_columns_accepts_timezone_aware_values() -> None:
    frame = pd.DataFrame(
        {
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-02T10:00:00+05:30",
                ],
                utc=True,
            )
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid


def test_validate_timestamp_order_passes_when_end_follows_start() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T10:00:00Z",
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert result.is_valid


def test_validate_timestamp_order_detects_end_before_start() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-02T12:00:00Z",
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-02T11:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 1
    assert result.issues[0].column == "ended_at"


def test_validate_timestamp_order_ignores_rows_with_missing_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "started_at": [
                "2026-01-01T10:00:00Z",
                None,
            ],
            "ended_at": [
                "2026-01-01T11:00:00Z",
                "2026-01-01T09:00:00Z",
            ],
        }
    )

    result = validate_timestamp_order(
        frame,
        start_column="started_at",
        end_column="ended_at",
    )

    assert result.is_valid


def test_validate_allowed_values_passes_for_valid_values() -> None:
    result = validate_allowed_values(
        _orders(),
        column="status",
        allowed_values=(
            "paid",
            "pending",
            "cancelled",
        ),
    )

    assert result.is_valid


def test_validate_allowed_values_detects_invalid_values() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                "pending",
                "failed",
                "unknown",
            ]
        }
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values=(
            "paid",
            "pending",
            "cancelled",
        ),
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "status"
    assert "failed" in result.issues[0].message
    assert "unknown" in result.issues[0].message


def test_validate_allowed_values_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "status": [
                "paid",
                None,
            ]
        }
    )

    result = validate_allowed_values(
        frame,
        column="status",
        allowed_values=("paid",),
    )

    assert result.is_valid


def test_validate_foreign_key_passes_when_all_references_exist() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
                "C001",
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
                "C003",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid


def test_validate_foreign_key_detects_orphan_values() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C999",
                "C999",
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert not result.is_valid
    assert result.issues[0].row_count == 2
    assert result.issues[0].column == "customer_id"


def test_validate_foreign_key_ignores_null_foreign_keys() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                None,
            ]
        }
    )
    customers = pd.DataFrame(
        {
            "customer_id": [
                "C001",
            ]
        }
    )

    result = validate_foreign_key(
        orders,
        column="customer_id",
        reference=customers,
        reference_column="customer_id",
    )

    assert result.is_valid


def test_validate_schema_consistency_passes_for_matching_schema() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
            "status": ["paid"],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert result.is_valid


def test_validate_schema_consistency_detects_missing_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
            "status",
        ),
    )

    assert not result.is_valid
    assert any(
        "status" in issue.message
        for issue in result.issues
    )


def test_validate_schema_consistency_detects_unexpected_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "amount": [100.0],
            "internal_flag": [True],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
        ),
    )

    assert not result.is_valid
    assert any(
        "internal_flag" in issue.message
        for issue in result.issues
    )


def test_validate_memory_usage_passes_when_within_budget() -> None:
    frame = _orders()

    memory_bytes = int(
        frame.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    result = validate_memory_usage(
        frame,
        maximum_bytes=memory_bytes,
    )

    assert result.is_valid


def test_validate_memory_usage_detects_budget_exceeded() -> None:
    frame = _orders()

    result = validate_memory_usage(
        frame,
        maximum_bytes=1,
    )

    assert not result.is_valid
    assert result.issues[0].check == "memory_usage"
    assert result.issues[0].row_count == len(frame)


def test_validate_memory_usage_rejects_non_positive_limit() -> None:
    with pytest.raises(
        ValidationError,
        match="greater than zero",
    ):
        validate_memory_usage(
            _orders(),
            maximum_bytes=0,
        )

    with pytest.raises(
        ValidationError,
        match="greater than zero",
    ):
        validate_memory_usage(
            _orders(),
            maximum_bytes=-1,
        )


def test_validate_chunk_runs_requested_checks() -> None:
    frame = pd.DataFrame(
        {
            "order_id": [
                "1001",
                "1001",
                "1002",
            ],
            "amount": [
                100.0,
                -25.0,
                "invalid",
            ],
            "status": [
                "paid",
                "pending",
                "unknown",
            ],
            "created_at": [
                "2026-01-01T10:00:00Z",
                "2026-01-01T11:00:00Z",
                "not-a-timestamp",
            ],
        }
    )

    result = validate_chunk(
        frame,
        required_columns=(
            "order_id",
            "amount",
        ),
        required_value_columns=(
            "order_id",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=("amount",),
        non_negative_columns=("amount",),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
    )

    assert not result.is_valid

    checks = {
        issue.check
        for issue in result.issues
    }

    assert checks >= {
        "unique_keys",
        "numeric",
        "non_negative",
        "datetime",
        "allowed_values",
    }


def test_validate_chunk_can_require_non_empty_data() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
            "amount",
        ]
    )

    result = validate_chunk(
        frame,
        require_non_empty=True,
    )

    assert not result.is_valid
    assert any(
        issue.check == "not_empty"
        for issue in result.issues
    )


def test_validate_chunk_can_enforce_memory_budget() -> None:
    frame = _orders()

    result = validate_chunk(
        frame,
        maximum_memory_bytes=1,
    )

    assert not result.is_valid
    assert any(
        issue.check == "memory_usage"
        for issue in result.issues
    )


def test_validate_chunk_returns_valid_result_for_clean_data() -> None:
    result = validate_chunk(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
            "created_at",
        ),
        required_value_columns=(
            "order_id",
            "status",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        non_negative_columns=(
            "amount",
            "quantity",
        ),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
        require_non_empty=True,
    )

    assert result.is_valid


def test_validate_global_dataset_passes_for_valid_dataset() -> None:
    result = validate_global_dataset(
        _orders(),
        required_columns=(
            "order_id",
            "amount",
            "status",
            "created_at",
        ),
        unique_key_columns=("order_id",),
        numeric_columns=(
            "amount",
            "quantity",
        ),
        non_negative_columns=(
            "amount",
            "quantity",
        ),
        datetime_columns=("created_at",),
        allowed_values={
            "status": (
                "paid",
                "pending",
            )
        },
    )

    assert result.is_valid


def test_validate_global_dataset_detects_duplicate_keys() -> None:
    frame = pd.concat(
        [
            _orders(),
            _orders().iloc[[0]],
        ],
        ignore_index=True,
    )

    result = validate_global_dataset(
        frame,
        required_columns=("order_id",),
        unique_key_columns=("order_id",),
    )

    assert not result.is_valid
    assert any(
        issue.check == "unique_keys"
        for issue in result.issues
    )


def test_validate_global_dataset_requires_non_empty_output() -> None:
    frame = pd.DataFrame(
        columns=[
            "order_id",
        ]
    )

    result = validate_global_dataset(
        frame,
        required_columns=("order_id",),
    )

    assert not result.is_valid
    assert any(
        issue.check == "not_empty"
        for issue in result.issues
    )


def test_assert_valid_returns_original_result_when_valid() -> None:
    result = ValidationResult()

    returned = assert_valid(
        result
    )

    assert returned is result


def test_assert_valid_raises_for_invalid_result() -> None:
    result = ValidationResult(
        issues=(
            ValidationIssue(
                check="numeric",
                message="Invalid amount values.",
                column="amount",
                row_count=2,
            ),
            ValidationIssue(
                check="required_values",
                message="Missing order IDs.",
                column="order_id",
                row_count=1,
            ),
        )
    )

    with pytest.raises(
        ValidationError,
        match=r"\[numeric\].*\[required_values\]",
    ):
        assert_valid(result)


def test_validation_functions_reject_missing_requested_columns() -> None:
    frame = _orders()

    validators = (
        lambda: validate_required_values(
            frame,
            columns=("missing",),
        ),
        lambda: validate_unique_keys(
            frame,
            columns=("missing",),
        ),
        lambda: validate_numeric_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_non_negative_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_datetime_columns(
            frame,
            columns=("missing",),
        ),
        lambda: validate_allowed_values(
            frame,
            column="missing",
            allowed_values=("x",),
        ),
    )

    for validator in validators:
        with pytest.raises(
            ValidationError,
            match="Missing required columns",
        ):
            validator()


def test_validate_foreign_key_rejects_missing_source_column() -> None:
    source = pd.DataFrame(
        {
            "order_id": ["1001"],
        }
    )
    reference = pd.DataFrame(
        {
            "customer_id": ["C001"],
        }
    )

    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_foreign_key(
            source,
            column="customer_id",
            reference=reference,
            reference_column="customer_id",
        )


def test_validate_foreign_key_rejects_missing_reference_column() -> None:
    source = pd.DataFrame(
        {
            "customer_id": ["C001"],
        }
    )
    reference = pd.DataFrame(
        {
            "id": ["C001"],
        }
    )

    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_foreign_key(
            source,
            column="customer_id",
            reference=reference,
            reference_column="missing",
        )


def test_validate_timestamp_order_rejects_missing_timestamp_column() -> None:
    with pytest.raises(
        ValidationError,
        match="Missing required columns",
    ):
        validate_timestamp_order(
            _orders(),
            start_column="missing",
            end_column="created_at",
        )


def test_validate_schema_consistency_handles_empty_expected_schema() -> None:
    frame = pd.DataFrame()

    result = validate_schema_consistency(
        frame,
        expected_columns=(),
    )

    assert result.is_valid


def test_validate_schema_consistency_detects_both_missing_and_unexpected_columns() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["1001"],
            "unexpected": [True],
        }
    )

    result = validate_schema_consistency(
        frame,
        expected_columns=(
            "order_id",
            "amount",
        ),
    )

    assert not result.is_valid
    assert result.issue_count == 2

    messages = [
        issue.message
        for issue in result.issues
    ]

    assert any(
        "amount" in message
        for message in messages
    )
    assert any(
        "unexpected" in message
        for message in messages
    )


def test_validate_numeric_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                None,
                200.0,
            ]
        }
    )

    result = validate_numeric_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_non_negative_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "amount": [
                100.0,
                None,
                200.0,
            ]
        }
    )

    result = validate_non_negative_columns(
        frame,
        columns=("amount",),
    )

    assert result.is_valid


def test_validate_datetime_columns_ignores_null_values() -> None:
    frame = pd.DataFrame(
        {
            "created_at": [
                "2026-01-01T10:00:00Z",
                None,
            ]
        }
    )

    result = validate_datetime_columns(
        frame,
        columns=("created_at",),
    )

    assert result.is_valid