"""Tests for the data lake Athena analytics query definitions.

These tests validate the checked-in SQL examples against the project's
Glue Catalog schema and representative event dataset. They run locally
without AWS credentials, Athena executions, or network access.

The tests focus on query structure, schema compatibility, partition-filter
usage, and consistency with the sample data. They do not claim that Athena
has executed or validated the queries against a deployed catalog.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SQL_EXAMPLES_PATH = (
    PROJECT_ROOT
    / "src"
    / "analytics"
    / "query_examples.sql"
)

SAMPLE_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "samples"
    / "sample_events.json"
)

GLUE_DATABASE_NAME = "data_lake_events"
GLUE_TABLE_NAME = "events"
QUALIFIED_TABLE_NAME = (
    f"{GLUE_DATABASE_NAME}.{GLUE_TABLE_NAME}"
)

EXPECTED_COLUMNS = {
    "event_id",
    "event_timestamp",
    "tenant_id",
    "event_type",
    "user_id",
    "amount",
    "currency",
    "source",
    "attributes",
    "event_date",
}

PARTITION_COLUMN = "event_date"


@pytest.fixture(scope="module")
def sql_source() -> str:
    """Load the project's Athena SQL examples."""
    assert SQL_EXAMPLES_PATH.is_file(), (
        f"SQL examples file not found: {SQL_EXAMPLES_PATH}"
    )

    return SQL_EXAMPLES_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sql_statements(sql_source: str) -> list[str]:
    """Return non-empty SQL statements after removing comments."""
    source_without_comments = re.sub(
        r"/\*.*?\*/",
        "",
        sql_source,
        flags=re.DOTALL,
    )

    source_without_comments = re.sub(
        r"--[^\n]*",
        "",
        source_without_comments,
    )

    return [
        statement.strip()
        for statement in source_without_comments.split(";")
        if statement.strip()
    ]


@pytest.fixture(scope="module")
def sample_events() -> list[dict[str, Any]]:
    """Load the representative event dataset."""
    assert SAMPLE_DATA_PATH.is_file(), (
        f"Sample event dataset not found: {SAMPLE_DATA_PATH}"
    )

    with SAMPLE_DATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as sample_file:
        events = json.load(sample_file)

    assert isinstance(events, list)

    return events


def normalize_sql(statement: str) -> str:
    """Normalize whitespace for SQL structure assertions."""
    return re.sub(
        r"\s+",
        " ",
        statement,
    ).strip().lower()


def table_references(statement: str) -> set[str]:
    """Extract simple database-qualified table references."""
    normalized_statement = normalize_sql(statement)

    matches = re.findall(
        r"\b(?:from|join)\s+"
        r"(?:\"?([a-zA-Z_][\w$]*)\"?\s*\.\s*)?"
        r"\"?([a-zA-Z_][\w$]*)\"?",
        normalized_statement,
    )

    return {
        f"{database}.{table}" if database else table
        for database, table in matches
    }


def test_sql_examples_file_contains_queries(
    sql_statements: list[str],
) -> None:
    """The analytics SQL file must contain executable query examples."""
    assert sql_statements
    assert all(
        statement.lower().startswith(("select", "with"))
        for statement in sql_statements
    )


def test_queries_target_the_project_glue_table(
    sql_statements: list[str],
) -> None:
    """Analytics examples must query the project's registered Glue table."""
    for statement in sql_statements:
        references = table_references(statement)

        assert QUALIFIED_TABLE_NAME in references, (
            "Every analytics query must reference "
            f"{QUALIFIED_TABLE_NAME!r}. "
            f"Found references: {sorted(references)}"
        )


def test_queries_do_not_use_select_star(
    sql_statements: list[str],
) -> None:
    """Queries should select explicit columns for predictable data access."""
    for statement in sql_statements:
        normalized_statement = normalize_sql(statement)

        assert re.search(
            r"\bselect\s+\*",
            normalized_statement,
        ) is None


def test_queries_reference_known_event_columns(
    sql_statements: list[str],
) -> None:
    """Known event columns must be used consistently in SQL examples."""
    combined_sql = normalize_sql(
        " ".join(sql_statements)
    )

    referenced_columns = {
        column
        for column in EXPECTED_COLUMNS
        if re.search(
            rf"\b{re.escape(column)}\b",
            combined_sql,
        )
    }

    assert referenced_columns
    assert "event_id" in referenced_columns
    assert "event_type" in referenced_columns


def test_partition_column_is_used_in_analytics_queries(
    sql_statements: list[str],
) -> None:
    """At least one query must demonstrate event-date partition filtering."""
    partition_filter_found = any(
        re.search(
            rf"\bwhere\b[\s\S]*?\b{PARTITION_COLUMN}\b\s*"
            r"(?:=|>=|<=|>|<|between|in\b)",
            statement,
            flags=re.IGNORECASE,
        )
        for statement in sql_statements
    )

    assert partition_filter_found, (
        "At least one query must filter on event_date to demonstrate "
        "partition pruning."
    )


def test_queries_do_not_reference_unknown_project_tables(
    sql_statements: list[str],
) -> None:
    """SQL examples must not silently depend on unrelated tables."""
    for statement in sql_statements:
        references = table_references(statement)

        assert references == {QUALIFIED_TABLE_NAME}, (
            "Unexpected table dependency in analytics query: "
            f"{sorted(references)}"
        )


def test_sample_dataset_contains_expected_event_types(
    sample_events: list[dict[str, Any]],
) -> None:
    """The representative dataset must cover its documented event types."""
    event_types = {
        event["event_type"]
        for event in sample_events
    }

    assert event_types == {
        "purchase",
        "page_view",
        "refund",
        "signup",
    }


def test_sample_dataset_contains_multiple_tenants(
    sample_events: list[dict[str, Any]],
) -> None:
    """Sample data must support tenant-level analytics examples."""
    tenant_ids = {
        event["tenant_id"]
        for event in sample_events
    }

    assert len(tenant_ids) > 1


def test_sample_dataset_contains_multiple_partition_dates(
    sample_events: list[dict[str, Any]],
) -> None:
    """Sample data must span multiple event-date partitions."""
    event_dates = {
        event["event_date"]
        for event in sample_events
    }

    assert len(event_dates) > 1


def test_sample_dataset_contains_multiple_currencies(
    sample_events: list[dict[str, Any]],
) -> None:
    """Sample data must support currency-aware analytics."""
    currencies = {
        event["currency"]
        for event in sample_events
    }

    assert len(currencies) > 1


def test_sample_dataset_has_numeric_amount_values(
    sample_events: list[dict[str, Any]],
) -> None:
    """Amount values must be convertible for analytical aggregation."""
    for event in sample_events:
        amount = event["amount"]

        assert isinstance(amount, str)
        assert re.fullmatch(
            r"-?\d+(?:\.\d+)?",
            amount,
        )


def test_sample_dataset_contains_positive_and_negative_amounts(
    sample_events: list[dict[str, Any]],
) -> None:
    """Sample data must exercise purchases and refund-style amounts."""
    amounts = [
        float(event["amount"])
        for event in sample_events
    ]

    assert any(amount > 0 for amount in amounts)
    assert any(amount < 0 for amount in amounts)


def test_sample_dataset_contains_zero_amount_events(
    sample_events: list[dict[str, Any]],
) -> None:
    """Non-financial events must be represented by zero-valued amounts."""
    assert any(
        float(event["amount"]) == 0
        for event in sample_events
    )


def test_sample_event_dates_match_timestamp_dates(
    sample_events: list[dict[str, Any]],
) -> None:
    """Partition dates must agree with UTC event timestamp dates."""
    from datetime import datetime

    for event in sample_events:
        timestamp = datetime.fromisoformat(
            event["event_timestamp"].replace(
                "Z",
                "+00:00",
            )
        )

        assert timestamp.date().isoformat() == event["event_date"]


def test_sample_event_identifiers_are_unique(
    sample_events: list[dict[str, Any]],
) -> None:
    """Analytics input data must not contain duplicate event identifiers."""
    event_ids = [
        event["event_id"]
        for event in sample_events
    ]

    assert len(event_ids) == len(set(event_ids))


def test_sample_dataset_is_jsonl_compatible(
    sample_events: list[dict[str, Any]],
) -> None:
    """Each event must be independently serializable as a JSON record."""
    for event in sample_events:
        serialized_event = json.dumps(event)

        deserialized_event = json.loads(serialized_event)

        assert deserialized_event == event


@pytest.mark.parametrize(
    "required_column",
    sorted(EXPECTED_COLUMNS),
)
def test_glue_schema_columns_are_represented_in_sample_data(
    sample_events: list[dict[str, Any]],
    required_column: str,
) -> None:
    """Sample records must contain the columns expected by the Glue table."""
    for event in sample_events:
        assert required_column in event