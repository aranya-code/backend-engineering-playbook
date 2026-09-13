from __future__ import annotations

import pandas as pd
import pytest

from src.validation import (
    CUSTOMER_REQUIRED_COLUMNS,
    ORDER_REQUIRED_COLUMNS,
    REPORT_REQUIRED_COLUMNS,
    ValidationIssue,
    ValidationResult,
    assert_valid,
    validate_customers,
    validate_order_customer_relationship,
    validate_order_schema,
    validate_orders,
    validate_pipeline_outputs,
    validate_report_reconciliation,
    validate_required_columns,
)


def make_orders() -> pd.DataFrame:
    """Build representative cleaned order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-2", "C-3", "C-1"],
            "product_id": ["P-1", "P-2", "P-3", "P-4"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "pending",
            ],
            "amount": [100.0, 200.0, 50.0, 150.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                    "2026-01-02T10:05:00Z",
                    "2026-01-02T11:05:00Z",
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


def make_daily_report() -> pd.DataFrame:
    """Build a report that reconciles with completed orders."""
    return pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
                pd.Timestamp("2026-01-02").date(),
            ],
            "order_count": [2, 0],
            "revenue": [300.0, 0.0],
        }
    )


def test_validate_required_columns_returns_valid_for_complete_schema() -> None:
    result = validate_required_columns(
        make_orders(),
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is True
    assert result.issues == ()
    assert result.issue_count == 0


def test_validate_required_columns_reports_missing_columns() -> None:
    orders = make_orders().drop(
        columns=["amount", "updated_at"],
    )

    result = validate_required_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is False
    assert result.issue_count == 1
    assert result.issues[0].rule == "required_columns"
    assert "amount" in result.issues[0].message
    assert "updated_at" in result.issues[0].message


def test_validate_required_columns_rejects_non_dataframe_input() -> None:
    result = validate_required_columns(
        [],
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is False
    assert result.issues[0].rule == "dataframe_type"


def test_validate_order_schema_accepts_valid_orders() -> None:
    result = validate_order_schema(
        make_orders(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_order_schema_detects_non_numeric_amount() -> None:
    orders = make_orders()
    orders["amount"] = orders["amount"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "amount_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_detects_invalid_created_at_dtype() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "created_at_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_detects_invalid_updated_at_dtype() -> None:
    orders = make_orders()
    orders["updated_at"] = orders["updated_at"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "updated_at_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_stops_when_required_columns_are_missing() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_orders_accepts_valid_orders() -> None:
    result = validate_orders(
        make_orders(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_orders_detects_null_required_values() -> None:
    orders = make_orders()
    orders.loc[1, "customer_id"] = None

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "required_values"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_duplicate_order_ids() -> None:
    orders = make_orders()
    orders.loc[3, "order_id"] = "O-1"

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "unique_order_id"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_invalid_status() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "shipped"

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "valid_status"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_negative_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "non_negative_amount"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_invalid_timestamp_order() -> None:
    orders = make_orders()
    orders.loc[0, "updated_at"] = pd.Timestamp(
        "2025-12-31T10:05:00Z"
    )

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "timestamp_order"
    )
    assert issue.row_count == 1


def test_validate_orders_reports_multiple_failures() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "invalid"
    orders.loc[1, "amount"] = -5.0
    orders.loc[2, "order_id"] = "O-1"
    orders.loc[3, "customer_id"] = None

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    rules = {issue.rule for issue in result.issues}

    assert {
        "required_values",
        "unique_order_id",
        "valid_status",
        "non_negative_amount",
    }.issubset(rules)


def test_validate_customers_accepts_valid_reference_data() -> None:
    result = validate_customers(
        make_customers(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_customers_detects_missing_required_columns() -> None:
    customers = make_customers().drop(
        columns=["segment"],
    )

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    assert result.issues[0].rule == "required_columns"


def test_validate_customers_detects_null_reference_values() -> None:
    customers = make_customers()
    customers.loc[0, "segment"] = None

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "customer_required_values"
    )
    assert issue.row_count == 1


def test_validate_customers_detects_duplicate_customer_ids() -> None:
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

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "unique_customer_id"
    )
    assert issue.row_count == 1


def test_validate_order_customer_relationship_accepts_valid_references() -> None:
    result = validate_order_customer_relationship(
        make_orders(),
        make_customers(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_order_customer_relationship_detects_missing_customers() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "customer_foreign_key"
    )
    assert issue.row_count == 1
    assert "C-999" in issue.message


def test_validate_order_customer_relationship_accepts_duplicate_order_customer_references() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-1"
    orders.loc[1, "customer_id"] = "C-1"

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is True


def test_validate_order_customer_relationship_detects_missing_order_column() -> None:
    orders = make_orders().drop(
        columns=["customer_id"],
    )

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_order_customer_relationship_detects_missing_customer_column() -> None:
    customers = make_customers().drop(
        columns=["customer_id"],
    )

    result = validate_order_customer_relationship(
        make_orders(),
        customers,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_report_reconciliation_accepts_matching_counts_and_revenue() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_report_reconciliation_detects_order_count_mismatch() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [1],
            "revenue": [300.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "report_order_count_reconciliation"
    )
    assert "expected 2" in issue.message
    assert "reported 1" in issue.message


def test_validate_report_reconciliation_detects_revenue_mismatch() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [250.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "report_revenue_reconciliation"
    )
    assert "expected 300.00" in issue.message
    assert "reported 250.00" in issue.message


def test_validate_report_reconciliation_allows_difference_within_tolerance() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.005],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
        tolerance=0.01,
    )

    assert result.valid is True


def test_validate_report_reconciliation_rejects_negative_tolerance() -> None:
    result = validate_report_reconciliation(
        make_orders(),
        make_daily_report(),
        tolerance=-0.01,
    )

    assert result.valid is False
    assert result.issues[0].rule == "reconciliation_tolerance"


def test_validate_report_reconciliation_detects_missing_report_columns() -> None:
    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
        }
    )

    result = validate_report_reconciliation(
        make_orders(),
        report,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_report_reconciliation_detects_missing_order_columns() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    result = validate_report_reconciliation(
        orders,
        make_daily_report(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_pipeline_outputs_accepts_valid_data() -> None:
    orders = make_orders()
    customers = make_customers()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.0],
        }
    )

    result = validate_pipeline_outputs(
        orders,
        customers,
        report,
    )

    assert result.valid is True
    assert result.issues == ()
    assert result.issue_count == 0


def test_validate_pipeline_outputs_collects_multiple_validation_failures() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "invalid"
    orders.loc[1, "customer_id"] = "C-999"

    customers = make_customers()
    customers.loc[0, "customer_id"] = "C-2"

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [1],
            "revenue": [100.0],
        }
    )

    result = validate_pipeline_outputs(
        orders,
        customers,
        report,
    )

    assert result.valid is False
    rules = {issue.rule for issue in result.issues}

    assert "valid_status" in rules
    assert "unique_customer_id" in rules
    assert "customer_foreign_key" in rules
    assert "report_order_count_reconciliation" in rules
    assert "report_revenue_reconciliation" in rules


def test_validation_result_issue_count_matches_issue_length() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="rule_one",
                message="First failure",
            ),
            ValidationIssue(
                rule="rule_two",
                message="Second failure",
            ),
        ),
    )

    assert result.issue_count == 2


def test_validation_result_raise_if_invalid_does_nothing_when_valid() -> None:
    result = ValidationResult(
        valid=True,
        issues=(),
    )

    result.raise_if_invalid()


def test_validation_result_raise_if_invalid_raises_with_details() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="required_columns",
                message="orders is missing required columns: amount",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Validation failed",
    ) as exc_info:
        result.raise_if_invalid()

    assert "required_columns" in str(exc_info.value)
    assert "amount" in str(exc_info.value)


def test_assert_valid_accepts_valid_result() -> None:
    result = ValidationResult(
        valid=True,
        issues=(),
    )

    assert_valid(result)


def test_assert_valid_raises_for_invalid_result() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="business_rule",
                message="Invalid business state",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Validation failed",
    ):
        assert_valid(result)


def test_validation_does_not_mutate_orders() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    validate_orders(orders)

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_validation_does_not_mutate_customers() -> None:
    customers = make_customers()
    original = customers.copy(deep=True)

    validate_customers(customers)

    pd.testing.assert_frame_equal(
        customers,
        original,
    )


def test_validation_does_not_mutate_report() -> None:
    orders = make_orders()
    report = make_daily_report()
    original = report.copy(deep=True)

    validate_report_reconciliation(
        orders,
        report,
    )

    pd.testing.assert_frame_equal(
        report,
        original,
    )


def test_required_column_constants_match_expected_schemas() -> None:
    assert ORDER_REQUIRED_COLUMNS == (
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    )

    assert CUSTOMER_REQUIRED_COLUMNS == (
        "customer_id",
        "segment",
    )

    assert REPORT_REQUIRED_COLUMNS == (
        "order_date",
        "order_count",
        "revenue",
    )


def test_validate_orders_rejects_non_dataframe_input() -> None:
    result = validate_orders(
        [],
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_customers_rejects_non_dataframe_input() -> None:
    result = validate_customers(
        [],
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_order_customer_relationship_rejects_non_dataframe_input() -> None:
    result = validate_order_customer_relationship(
        [],
        make_customers(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_report_reconciliation_rejects_non_dataframe_input() -> None:
    result = validate_report_reconciliation(
        [],
        make_daily_report(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )

from __future__ import annotations

import pandas as pd
import pytest

from src.validation import (
    CUSTOMER_REQUIRED_COLUMNS,
    ORDER_REQUIRED_COLUMNS,
    REPORT_REQUIRED_COLUMNS,
    ValidationIssue,
    ValidationResult,
    assert_valid,
    validate_customers,
    validate_order_customer_relationship,
    validate_order_schema,
    validate_orders,
    validate_pipeline_outputs,
    validate_report_reconciliation,
    validate_required_columns,
)


def make_orders() -> pd.DataFrame:
    """Build representative cleaned order data."""
    return pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "customer_id": ["C-1", "C-2", "C-3", "C-1"],
            "product_id": ["P-1", "P-2", "P-3", "P-4"],
            "status": [
                "completed",
                "completed",
                "cancelled",
                "pending",
            ],
            "amount": [100.0, 200.0, 50.0, 150.0],
            "created_at": pd.to_datetime(
                [
                    "2026-01-01T10:00:00Z",
                    "2026-01-01T11:00:00Z",
                    "2026-01-02T10:00:00Z",
                    "2026-01-02T11:00:00Z",
                ],
                utc=True,
            ),
            "updated_at": pd.to_datetime(
                [
                    "2026-01-01T10:05:00Z",
                    "2026-01-01T11:05:00Z",
                    "2026-01-02T10:05:00Z",
                    "2026-01-02T11:05:00Z",
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


def make_daily_report() -> pd.DataFrame:
    """Build a report that reconciles with completed orders."""
    return pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
                pd.Timestamp("2026-01-02").date(),
            ],
            "order_count": [2, 0],
            "revenue": [300.0, 0.0],
        }
    )


def test_validate_required_columns_returns_valid_for_complete_schema() -> None:
    result = validate_required_columns(
        make_orders(),
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is True
    assert result.issues == ()
    assert result.issue_count == 0


def test_validate_required_columns_reports_missing_columns() -> None:
    orders = make_orders().drop(
        columns=["amount", "updated_at"],
    )

    result = validate_required_columns(
        orders,
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is False
    assert result.issue_count == 1
    assert result.issues[0].rule == "required_columns"
    assert "amount" in result.issues[0].message
    assert "updated_at" in result.issues[0].message


def test_validate_required_columns_rejects_non_dataframe_input() -> None:
    result = validate_required_columns(
        [],
        ORDER_REQUIRED_COLUMNS,
        dataset_name="orders",
    )

    assert result.valid is False
    assert result.issues[0].rule == "dataframe_type"


def test_validate_order_schema_accepts_valid_orders() -> None:
    result = validate_order_schema(
        make_orders(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_order_schema_detects_non_numeric_amount() -> None:
    orders = make_orders()
    orders["amount"] = orders["amount"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "amount_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_detects_invalid_created_at_dtype() -> None:
    orders = make_orders()
    orders["created_at"] = orders["created_at"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "created_at_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_detects_invalid_updated_at_dtype() -> None:
    orders = make_orders()
    orders["updated_at"] = orders["updated_at"].astype(str)

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "updated_at_dtype"
        for issue in result.issues
    )


def test_validate_order_schema_stops_when_required_columns_are_missing() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    result = validate_order_schema(
        orders,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_orders_accepts_valid_orders() -> None:
    result = validate_orders(
        make_orders(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_orders_detects_null_required_values() -> None:
    orders = make_orders()
    orders.loc[1, "customer_id"] = None

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "required_values"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_duplicate_order_ids() -> None:
    orders = make_orders()
    orders.loc[3, "order_id"] = "O-1"

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "unique_order_id"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_invalid_status() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "shipped"

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "valid_status"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_negative_amount() -> None:
    orders = make_orders()
    orders.loc[0, "amount"] = -10.0

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "non_negative_amount"
    )
    assert issue.row_count == 1


def test_validate_orders_detects_invalid_timestamp_order() -> None:
    orders = make_orders()
    orders.loc[0, "updated_at"] = pd.Timestamp(
        "2025-12-31T10:05:00Z"
    )

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "timestamp_order"
    )
    assert issue.row_count == 1


def test_validate_orders_reports_multiple_failures() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "invalid"
    orders.loc[1, "amount"] = -5.0
    orders.loc[2, "order_id"] = "O-1"
    orders.loc[3, "customer_id"] = None

    result = validate_orders(
        orders,
    )

    assert result.valid is False
    rules = {issue.rule for issue in result.issues}

    assert {
        "required_values",
        "unique_order_id",
        "valid_status",
        "non_negative_amount",
    }.issubset(rules)


def test_validate_customers_accepts_valid_reference_data() -> None:
    result = validate_customers(
        make_customers(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_customers_detects_missing_required_columns() -> None:
    customers = make_customers().drop(
        columns=["segment"],
    )

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    assert result.issues[0].rule == "required_columns"


def test_validate_customers_detects_null_reference_values() -> None:
    customers = make_customers()
    customers.loc[0, "segment"] = None

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "customer_required_values"
    )
    assert issue.row_count == 1


def test_validate_customers_detects_duplicate_customer_ids() -> None:
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

    result = validate_customers(
        customers,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "unique_customer_id"
    )
    assert issue.row_count == 1


def test_validate_order_customer_relationship_accepts_valid_references() -> None:
    result = validate_order_customer_relationship(
        make_orders(),
        make_customers(),
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_order_customer_relationship_detects_missing_customers() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-999"

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "customer_foreign_key"
    )
    assert issue.row_count == 1
    assert "C-999" in issue.message


def test_validate_order_customer_relationship_accepts_duplicate_order_customer_references() -> None:
    orders = make_orders()
    orders.loc[0, "customer_id"] = "C-1"
    orders.loc[1, "customer_id"] = "C-1"

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is True


def test_validate_order_customer_relationship_detects_missing_order_column() -> None:
    orders = make_orders().drop(
        columns=["customer_id"],
    )

    result = validate_order_customer_relationship(
        orders,
        make_customers(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_order_customer_relationship_detects_missing_customer_column() -> None:
    customers = make_customers().drop(
        columns=["customer_id"],
    )

    result = validate_order_customer_relationship(
        make_orders(),
        customers,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_report_reconciliation_accepts_matching_counts_and_revenue() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is True
    assert result.issues == ()


def test_validate_report_reconciliation_detects_order_count_mismatch() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [1],
            "revenue": [300.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "report_order_count_reconciliation"
    )
    assert "expected 2" in issue.message
    assert "reported 1" in issue.message


def test_validate_report_reconciliation_detects_revenue_mismatch() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [250.0],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
    )

    assert result.valid is False
    issue = next(
        issue
        for issue in result.issues
        if issue.rule == "report_revenue_reconciliation"
    )
    assert "expected 300.00" in issue.message
    assert "reported 250.00" in issue.message


def test_validate_report_reconciliation_allows_difference_within_tolerance() -> None:
    orders = make_orders()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.005],
        }
    )

    result = validate_report_reconciliation(
        orders,
        report,
        tolerance=0.01,
    )

    assert result.valid is True


def test_validate_report_reconciliation_rejects_negative_tolerance() -> None:
    result = validate_report_reconciliation(
        make_orders(),
        make_daily_report(),
        tolerance=-0.01,
    )

    assert result.valid is False
    assert result.issues[0].rule == "reconciliation_tolerance"


def test_validate_report_reconciliation_detects_missing_report_columns() -> None:
    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
        }
    )

    result = validate_report_reconciliation(
        make_orders(),
        report,
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_report_reconciliation_detects_missing_order_columns() -> None:
    orders = make_orders().drop(
        columns=["amount"],
    )

    result = validate_report_reconciliation(
        orders,
        make_daily_report(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "required_columns"
        for issue in result.issues
    )


def test_validate_pipeline_outputs_accepts_valid_data() -> None:
    orders = make_orders()
    customers = make_customers()

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [2],
            "revenue": [300.0],
        }
    )

    result = validate_pipeline_outputs(
        orders,
        customers,
        report,
    )

    assert result.valid is True
    assert result.issues == ()
    assert result.issue_count == 0


def test_validate_pipeline_outputs_collects_multiple_validation_failures() -> None:
    orders = make_orders()
    orders.loc[0, "status"] = "invalid"
    orders.loc[1, "customer_id"] = "C-999"

    customers = make_customers()
    customers.loc[0, "customer_id"] = "C-2"

    report = pd.DataFrame(
        {
            "order_date": [
                pd.Timestamp("2026-01-01").date(),
            ],
            "order_count": [1],
            "revenue": [100.0],
        }
    )

    result = validate_pipeline_outputs(
        orders,
        customers,
        report,
    )

    assert result.valid is False
    rules = {issue.rule for issue in result.issues}

    assert "valid_status" in rules
    assert "unique_customer_id" in rules
    assert "customer_foreign_key" in rules
    assert "report_order_count_reconciliation" in rules
    assert "report_revenue_reconciliation" in rules


def test_validation_result_issue_count_matches_issue_length() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="rule_one",
                message="First failure",
            ),
            ValidationIssue(
                rule="rule_two",
                message="Second failure",
            ),
        ),
    )

    assert result.issue_count == 2


def test_validation_result_raise_if_invalid_does_nothing_when_valid() -> None:
    result = ValidationResult(
        valid=True,
        issues=(),
    )

    result.raise_if_invalid()


def test_validation_result_raise_if_invalid_raises_with_details() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="required_columns",
                message="orders is missing required columns: amount",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Validation failed",
    ) as exc_info:
        result.raise_if_invalid()

    assert "required_columns" in str(exc_info.value)
    assert "amount" in str(exc_info.value)


def test_assert_valid_accepts_valid_result() -> None:
    result = ValidationResult(
        valid=True,
        issues=(),
    )

    assert_valid(result)


def test_assert_valid_raises_for_invalid_result() -> None:
    result = ValidationResult(
        valid=False,
        issues=(
            ValidationIssue(
                rule="business_rule",
                message="Invalid business state",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Validation failed",
    ):
        assert_valid(result)


def test_validation_does_not_mutate_orders() -> None:
    orders = make_orders()
    original = orders.copy(deep=True)

    validate_orders(orders)

    pd.testing.assert_frame_equal(
        orders,
        original,
    )


def test_validation_does_not_mutate_customers() -> None:
    customers = make_customers()
    original = customers.copy(deep=True)

    validate_customers(customers)

    pd.testing.assert_frame_equal(
        customers,
        original,
    )


def test_validation_does_not_mutate_report() -> None:
    orders = make_orders()
    report = make_daily_report()
    original = report.copy(deep=True)

    validate_report_reconciliation(
        orders,
        report,
    )

    pd.testing.assert_frame_equal(
        report,
        original,
    )


def test_required_column_constants_match_expected_schemas() -> None:
    assert ORDER_REQUIRED_COLUMNS == (
        "order_id",
        "customer_id",
        "product_id",
        "status",
        "amount",
        "created_at",
        "updated_at",
    )

    assert CUSTOMER_REQUIRED_COLUMNS == (
        "customer_id",
        "segment",
    )

    assert REPORT_REQUIRED_COLUMNS == (
        "order_date",
        "order_count",
        "revenue",
    )


def test_validate_orders_rejects_non_dataframe_input() -> None:
    result = validate_orders(
        [],
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_customers_rejects_non_dataframe_input() -> None:
    result = validate_customers(
        [],
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_order_customer_relationship_rejects_non_dataframe_input() -> None:
    result = validate_order_customer_relationship(
        [],
        make_customers(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )


def test_validate_report_reconciliation_rejects_non_dataframe_input() -> None:
    result = validate_report_reconciliation(
        [],
        make_daily_report(),
    )

    assert result.valid is False
    assert any(
        issue.rule == "dataframe_type"
        for issue in result.issues
    )