#!/usr/bin/env python3
"""Execute and validate Athena queries for the S3 event data lake."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from decimal import Decimal, InvalidOperation
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("data_lake.analytics")

DEFAULT_REGION = os.getenv("AWS_REGION", "ap-south-1")
DEFAULT_DATABASE = os.getenv("GLUE_DATABASE_NAME", "data_lake_events")
DEFAULT_TABLE = os.getenv("GLUE_TABLE_NAME", "events")
DEFAULT_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "primary")
DEFAULT_OUTPUT_LOCATION = os.getenv("ATHENA_QUERY_RESULTS_S3_URI")

DEFAULT_START_DATE = "2026-01-01"
DEFAULT_END_DATE = "2026-01-07"

IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

POLL_INTERVAL_SECONDS = 2
DEFAULT_TIMEOUT_SECONDS = 600
MAX_QUERY_ATTEMPTS = 5

EXPECTED_EVENT_COUNTS = {
    "purchase": 3,
    "page_view": 3,
    "refund": 2,
    "signup": 2,
}

EXPECTED_SOURCE_COUNTS = {
    "web": 4,
    "mobile": 3,
    "api": 3,
}

EXPECTED_CURRENCY_AMOUNTS = {
    "EUR": Decimal("89.00"),
    "GBP": Decimal("-25.00"),
    "INR": Decimal("275.50"),
    "USD": Decimal("100.00"),
}

EXPECTED_PARTITION_COUNTS = {
    "2026-01-01": 2,
    "2026-01-02": 1,
    "2026-01-03": 1,
    "2026-01-04": 1,
    "2026-01-05": 1,
    "2026-01-06": 1,
    "2026-01-07": 3,
}


class AnalyticsValidationError(RuntimeError):
    """Raised when Athena execution or result validation fails."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def validate_identifier(value: str, label: str) -> str:
    """Validate a Glue database or table identifier."""
    normalized_value = value.strip()

    if not IDENTIFIER_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{label} must contain only letters, digits, and underscores "
            "and must not begin with a digit."
        )

    return normalized_value


def validate_date(value: str, label: str) -> str:
    """Validate and normalize a YYYY-MM-DD date."""
    normalized_value = value.strip()

    if not DATE_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"{label} must use the YYYY-MM-DD format."
        )

    from datetime import date

    try:
        date.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(
            f"{label} is not a valid calendar date: {normalized_value}"
        ) from exc

    return normalized_value


def validate_date_range(
    start_date: str,
    end_date: str,
) -> tuple[str, str]:
    """Validate that the requested date range is ordered."""
    normalized_start = validate_date(start_date, "Start date")
    normalized_end = validate_date(end_date, "End date")

    if normalized_start > normalized_end:
        raise ValueError("Start date cannot be later than end date.")

    return normalized_start, normalized_end


def validate_s3_uri(value: str | None) -> str | None:
    """Validate an optional Athena query-results S3 URI."""
    if value is None:
        return None

    normalized_value = value.strip()

    if not normalized_value.startswith("s3://"):
        raise ValueError(
            "Athena output location must begin with s3://."
        )

    remainder = normalized_value[5:]

    if not remainder or "/" not in remainder and remainder == "":
        raise ValueError(
            "Athena output location must include an S3 bucket."
        )

    bucket_name = remainder.split("/", maxsplit=1)[0]

    if not bucket_name:
        raise ValueError(
            "Athena output location must include an S3 bucket."
        )

    return normalized_value.rstrip("/") + "/"


def create_athena_client(region: str) -> Any:
    """Create an Athena client using the standard AWS credential chain."""
    client_config = Config(
        retries={
            "mode": "standard",
            "max_attempts": MAX_QUERY_ATTEMPTS,
        },
        connect_timeout=10,
        read_timeout=60,
    )

    return boto3.client(
        "athena",
        region_name=region,
        config=client_config,
    )


def build_validation_queries(
    database: str,
    table: str,
    start_date: str,
    end_date: str,
) -> dict[str, str]:
    """Build read-only Athena queries for the expected sample dataset."""
    qualified_table = f'"{database}"."{table}"'

    date_filter = (
        f"event_date BETWEEN '{start_date}' AND '{end_date}'"
    )

    return {
        "total_events": f"""
            SELECT COUNT(*) AS total_events
            FROM {qualified_table}
            WHERE {date_filter}
        """,
        "event_type_counts": f"""
            SELECT
                COUNT_IF(event_type = 'purchase') AS purchase_count,
                COUNT_IF(event_type = 'page_view') AS page_view_count,
                COUNT_IF(event_type = 'refund') AS refund_count,
                COUNT_IF(event_type = 'signup') AS signup_count
            FROM {qualified_table}
            WHERE {date_filter}
        """,
        "source_counts": f"""
            SELECT
                COUNT_IF(source = 'web') AS web_count,
                COUNT_IF(source = 'mobile') AS mobile_count,
                COUNT_IF(source = 'api') AS api_count
            FROM {qualified_table}
            WHERE {date_filter}
        """,
        "distinct_entities": f"""
            SELECT
                COUNT(DISTINCT event_id) AS distinct_event_ids,
                COUNT(DISTINCT tenant_id) AS distinct_tenants,
                COUNT(DISTINCT user_id) AS distinct_users
            FROM {qualified_table}
            WHERE {date_filter}
        """,
        "currency_amounts": f"""
            SELECT
                currency,
                SUM(TRY_CAST(amount AS DECIMAL(18, 2))) AS total_amount
            FROM {qualified_table}
            WHERE {date_filter}
            GROUP BY currency
            ORDER BY currency
        """,
        "partition_counts": f"""
            SELECT
                event_date,
                COUNT(*) AS event_count
            FROM {qualified_table}
            WHERE {date_filter}
            GROUP BY event_date
            ORDER BY event_date
        """,
        "invalid_amounts": f"""
            SELECT COUNT(*) AS invalid_amount_count
            FROM {qualified_table}
            WHERE {date_filter}
              AND (
                  amount IS NULL
                  OR TRY_CAST(amount AS DECIMAL(18, 2)) IS NULL
              )
        """,
        "duplicate_event_ids": f"""
            SELECT COUNT(*) AS duplicate_event_group_count
            FROM (
                SELECT event_id
                FROM {qualified_table}
                WHERE {date_filter}
                GROUP BY event_id
                HAVING COUNT(*) > 1
            ) duplicate_events
        """,
        "invalid_required_fields": f"""
            SELECT COUNT(*) AS invalid_record_count
            FROM {qualified_table}
            WHERE {date_filter}
              AND (
                  event_id IS NULL
                  OR TRIM(event_id) = ''
                  OR event_timestamp IS NULL
                  OR TRIM(event_timestamp) = ''
                  OR event_date IS NULL
                  OR TRIM(event_date) = ''
                  OR tenant_id IS NULL
                  OR TRIM(tenant_id) = ''
                  OR event_type IS NULL
                  OR TRIM(event_type) = ''
                  OR user_id IS NULL
                  OR TRIM(user_id) = ''
                  OR currency IS NULL
                  OR TRIM(currency) = ''
                  OR source IS NULL
                  OR TRIM(source) = ''
              )
        """,
        "invalid_event_dates": f"""
            SELECT COUNT(*) AS invalid_event_date_count
            FROM {qualified_table}
            WHERE {date_filter}
              AND TRY_CAST(event_date AS DATE) <>
                  CAST(
                      from_iso8601_timestamp(event_timestamp)
                      AT TIME ZONE 'UTC'
                      AS DATE
                  )
        """,
    }


def start_query(
    athena_client: Any,
    query: str,
    database: str,
    region: str,
    workgroup: str,
    output_location: str | None,
) -> str:
    """Submit a query and return its Athena execution identifier."""
    request: dict[str, Any] = {
        "QueryString": query,
        "QueryExecutionContext": {
            "Database": database,
            "Catalog": "AwsDataCatalog",
        },
        "WorkGroup": workgroup,
    }

    if output_location:
        request["ResultConfiguration"] = {
            "OutputLocation": output_location,
        }

    try:
        response = athena_client.start_query_execution(**request)
    except ClientError as exc:
        error = exc.response.get("Error", {})
        raise AnalyticsValidationError(
            "Unable to submit Athena query: "
            f"{error.get('Code', 'Unknown')}: "
            f"{error.get('Message', str(exc))}"
        ) from exc

    execution_id = response.get("QueryExecutionId")

    if not execution_id:
        raise AnalyticsValidationError(
            "Athena did not return a query execution identifier."
        )

    LOGGER.debug(
        "Submitted Athena query execution: %s",
        execution_id,
    )

    return execution_id


def wait_for_query(
    athena_client: Any,
    execution_id: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Wait for an Athena query to finish or fail."""
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        try:
            response = athena_client.get_query_execution(
                QueryExecutionId=execution_id,
            )
        except ClientError as exc:
            error = exc.response.get("Error", {})
            raise AnalyticsValidationError(
                "Unable to inspect Athena query execution "
                f"{execution_id}: {error.get('Code', 'Unknown')}: "
                f"{error.get('Message', str(exc))}"
            ) from exc

        execution = response.get("QueryExecution", {})
        status = execution.get("Status", {})
        state = status.get("State")

        if state == "SUCCEEDED":
            return execution

        if state in {"FAILED", "CANCELLED"}:
            reason = status.get("StateChangeReason", "No reason provided.")
            raise AnalyticsValidationError(
                f"Athena query {execution_id} ended with state "
                f"{state}: {reason}"
            )

        if state not in {"QUEUED", "RUNNING"}:
            raise AnalyticsValidationError(
                f"Athena query {execution_id} returned an unexpected "
                f"state: {state!r}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)

    try:
        athena_client.stop_query_execution(
            QueryExecutionId=execution_id,
        )
    except ClientError:
        LOGGER.exception(
            "Unable to cancel timed-out Athena query %s",
            execution_id,
        )

    raise AnalyticsValidationError(
        f"Athena query {execution_id} exceeded the "
        f"{timeout_seconds}-second timeout."
    )


def fetch_query_rows(
    athena_client: Any,
    execution_id: str,
) -> list[dict[str, str | None]]:
    """Fetch all query result rows and map them to column names."""
    rows: list[dict[str, str | None]] = []
    column_names: list[str] | None = None
    next_token: str | None = None

    while True:
        request: dict[str, Any] = {
            "QueryExecutionId": execution_id,
            "MaxResults": 1000,
        }

        if next_token:
            request["NextToken"] = next_token

        try:
            response = athena_client.get_query_results(**request)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            raise AnalyticsValidationError(
                "Unable to retrieve Athena query results "
                f"{execution_id}: {error.get('Code', 'Unknown')}: "
                f"{error.get('Message', str(exc))}"
            ) from exc

        result_set = response.get("ResultSet", {})
        result_metadata = result_set.get("ResultSetMetadata", {})
        columns = result_metadata.get("ColumnInfo", [])

        if column_names is None:
            column_names = [
                column.get("Name", f"column_{index}")
                for index, column in enumerate(columns)
            ]

        page_rows = result_set.get("Rows", [])

        for row_index, row in enumerate(page_rows):
            data = row.get("Data", [])

            # Athena includes column names as the first row of the first page.
            if not rows and not next_token and row_index == 0:
                continue

            values: list[str | None] = []

            for cell in data:
                values.append(cell.get("VarCharValue"))

            values.extend(
                [None] * (len(column_names) - len(values))
            )

            rows.append(
                dict(zip(column_names, values))
            )

        next_token = response.get("NextToken")

        if not next_token:
            break

    return rows


def execute_validation_query(
    athena_client: Any,
    query_name: str,
    query: str,
    database: str,
    region: str,
    workgroup: str,
    output_location: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute one validation query and return its results and metrics."""
    LOGGER.info("Executing validation query: %s", query_name)

    execution_id = start_query(
        athena_client=athena_client,
        query=query,
        database=database,
        region=region,
        workgroup=workgroup,
        output_location=output_location,
    )

    execution = wait_for_query(
        athena_client=athena_client,
        execution_id=execution_id,
        timeout_seconds=timeout_seconds,
    )

    rows = fetch_query_rows(
        athena_client=athena_client,
        execution_id=execution_id,
    )

    statistics = execution.get("Statistics", {})

    result = {
        "query_name": query_name,
        "execution_id": execution_id,
        "rows": rows,
        "statistics": {
            "data_scanned_bytes": statistics.get(
                "DataScannedInBytes",
                0,
            ),
            "engine_execution_time_ms": statistics.get(
                "EngineExecutionTimeInMillis",
                0,
            ),
            "total_execution_time_ms": statistics.get(
                "TotalExecutionTimeInMillis",
                0,
            ),
        },
    }

    LOGGER.info(
        "Completed query %s: scanned %s bytes in %s ms",
        query_name,
        result["statistics"]["data_scanned_bytes"],
        result["statistics"]["total_execution_time_ms"],
    )

    return result


def parse_integer(
    value: str | None,
    field_name: str,
) -> int:
    """Convert an Athena result value to an integer."""
    if value is None:
        raise AnalyticsValidationError(
            f"Athena returned NULL for {field_name}."
        )

    try:
        return int(value)
    except ValueError as exc:
        raise AnalyticsValidationError(
            f"Athena returned a non-integer value for "
            f"{field_name}: {value!r}"
        ) from exc


def parse_decimal(
    value: str | None,
    field_name: str,
) -> Decimal:
    """Convert an Athena result value to Decimal."""
    if value is None:
        raise AnalyticsValidationError(
            f"Athena returned NULL for {field_name}."
        )

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise AnalyticsValidationError(
            f"Athena returned an invalid decimal value for "
            f"{field_name}: {value!r}"
        ) from exc


def require_single_row(
    query_result: dict[str, Any],
    query_name: str,
) -> dict[str, str | None]:
    """Require exactly one result row for an aggregate query."""
    rows = query_result["rows"]

    if len(rows) != 1:
        raise AnalyticsValidationError(
            f"Expected exactly one row from {query_name}, "
            f"received {len(rows)}."
        )

    return rows[0]


def compare_value(
    actual: Any,
    expected: Any,
    field_name: str,
    failures: list[str],
) -> None:
    """Record a validation failure when values differ."""
    if actual != expected:
        failures.append(
            f"{field_name}: expected {expected!r}, received {actual!r}"
        )


def validate_total_events(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate the total number of ingested events."""
    row = require_single_row(query_result, "total_events")
    actual = parse_integer(
        row.get("total_events"),
        "total_events",
    )

    compare_value(
        actual,
        10,
        "total_events",
        failures,
    )


def validate_event_type_counts(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate event counts grouped by event type."""
    row = require_single_row(query_result, "event_type_counts")

    column_names = {
        "purchase": "purchase_count",
        "page_view": "page_view_count",
        "refund": "refund_count",
        "signup": "signup_count",
    }

    for event_type, expected_count in EXPECTED_EVENT_COUNTS.items():
        actual_count = parse_integer(
            row.get(column_names[event_type]),
            f"{event_type}_count",
        )

        compare_value(
            actual_count,
            expected_count,
            f"event_type_counts.{event_type}",
            failures,
        )


def validate_source_counts(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate event counts grouped by source."""
    row = require_single_row(query_result, "source_counts")

    column_names = {
        "web": "web_count",
        "mobile": "mobile_count",
        "api": "api_count",
    }

    for source, expected_count in EXPECTED_SOURCE_COUNTS.items():
        actual_count = parse_integer(
            row.get(column_names[source]),
            f"{source}_count",
        )

        compare_value(
            actual_count,
            expected_count,
            f"source_counts.{source}",
            failures,
        )


def validate_distinct_entities(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate event, tenant, and user uniqueness counts."""
    row = require_single_row(query_result, "distinct_entities")

    expected_values = {
        "distinct_event_ids": 10,
        "distinct_tenants": 9,
        "distinct_users": 9,
    }

    for field_name, expected_value in expected_values.items():
        actual_value = parse_integer(
            row.get(field_name),
            field_name,
        )

        compare_value(
            actual_value,
            expected_value,
            f"distinct_entities.{field_name}",
            failures,
        )


def validate_currency_amounts(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate transaction totals independently for each currency."""
    actual_values: dict[str, Decimal] = {}

    for row in query_result["rows"]:
        currency = row.get("currency")
        amount = parse_decimal(
            row.get("total_amount"),
            f"total_amount.{currency}",
        )

        if currency is None:
            failures.append(
                "currency_amounts contains a row without a currency."
            )
            continue

        actual_values[currency] = amount

    compare_value(
        actual_values,
        EXPECTED_CURRENCY_AMOUNTS,
        "currency_amounts",
        failures,
    )


def validate_partition_counts(
    query_result: dict[str, Any],
    failures: list[str],
) -> None:
    """Validate the event distribution across expected date partitions."""
    actual_values: dict[str, int] = {}

    for row in query_result["rows"]:
        event_date = row.get("event_date")

        if event_date is None:
            failures.append(
                "partition_counts contains a row without event_date."
            )
            continue

        actual_values[event_date] = parse_integer(
            row.get("event_count"),
            f"partition_counts.{event_date}",
        )

    compare_value(
        actual_values,
        EXPECTED_PARTITION_COUNTS,
        "partition_counts",
        failures,
    )


def validate_zero_count(
    query_result: dict[str, Any],
    query_name: str,
    field_name: str,
    failures: list[str],
) -> None:
    """Validate that a data-quality query returns zero invalid records."""
    row = require_single_row(query_result, query_name)
    actual_count = parse_integer(
        row.get(field_name),
        field_name,
    )

    compare_value(
        actual_count,
        0,
        f"{query_name}.{field_name}",
        failures,
    )


def validate_query_results(
    query_results: dict[str, dict[str, Any]],
) -> list[str]:
    """Run all expected-result and data-quality assertions."""
    failures: list[str] = []

    validate_total_events(
        query_results["total_events"],
        failures,
    )
    validate_event_type_counts(
        query_results["event_type_counts"],
        failures,
    )
    validate_source_counts(
        query_results["source_counts"],
        failures,
    )
    validate_distinct_entities(
        query_results["distinct_entities"],
        failures,
    )
    validate_currency_amounts(
        query_results["currency_amounts"],
        failures,
    )
    validate_partition_counts(
        query_results["partition_counts"],
        failures,
    )

    validate_zero_count(
        query_results["invalid_amounts"],
        "invalid_amounts",
        "invalid_amount_count",
        failures,
    )
    validate_zero_count(
        query_results["duplicate_event_ids"],
        "duplicate_event_ids",
        "duplicate_event_group_count",
        failures,
    )
    validate_zero_count(
        query_results["invalid_required_fields"],
        "invalid_required_fields",
        "invalid_record_count",
        failures,
    )
    validate_zero_count(
        query_results["invalid_event_dates"],
        "invalid_event_dates",
        "invalid_event_date_count",
        failures,
    )

    return failures


def build_report(
    query_results: dict[str, dict[str, Any]],
    failures: list[str],
    database: str,
    table: str,
    region: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Build a JSON-serializable validation report."""
    query_metrics = {}

    for query_name, query_result in query_results.items():
        query_metrics[query_name] = {
            "execution_id": query_result["execution_id"],
            **query_result["statistics"],
        }

    total_scanned_bytes = sum(
        result["statistics"]["data_scanned_bytes"]
        for result in query_results.values()
    )

    return {
        "status": "failed" if failures else "passed",
        "database": database,
        "table": table,
        "region": region,
        "date_range": {
            "start": start_date,
            "end": end_date,
        },
        "queries_executed": len(query_results),
        "total_data_scanned_bytes": total_scanned_bytes,
        "query_metrics": query_metrics,
        "failures": failures,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Execute Athena analytics queries and validate the "
            "S3 event data lake sample dataset."
        )
    )

    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE,
        help=f"Glue database name. Default: {DEFAULT_DATABASE}",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help=f"Glue table name. Default: {DEFAULT_TABLE}",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS Region. Default: {DEFAULT_REGION}",
    )
    parser.add_argument(
        "--workgroup",
        default=DEFAULT_WORKGROUP,
        help=f"Athena workgroup. Default: {DEFAULT_WORKGROUP}",
    )
    parser.add_argument(
        "--output-location",
        default=DEFAULT_OUTPUT_LOCATION,
        help=(
            "S3 URI for Athena query results. Defaults to "
            "ATHENA_QUERY_RESULTS_S3_URI. If omitted, the configured "
            "Athena workgroup must provide the result location."
        ),
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help=f"Inclusive partition start date. Default: {DEFAULT_START_DATE}",
    )
    parser.add_argument(
        "--end-date",
        default=DEFAULT_END_DATE,
        help=f"Inclusive partition end date. Default: {DEFAULT_END_DATE}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "Maximum execution time per Athena query in seconds. "
            f"Default: {DEFAULT_TIMEOUT_SECONDS}"
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def run_validation(
    database: str,
    table: str,
    region: str,
    workgroup: str,
    output_location: str | None,
    start_date: str,
    end_date: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute the analytics validation workflow."""
    normalized_database = validate_identifier(
        database,
        "Database name",
    )
    normalized_table = validate_identifier(
        table,
        "Table name",
    )

    normalized_start, normalized_end = validate_date_range(
        start_date,
        end_date,
    )

    normalized_output_location = validate_s3_uri(
        output_location,
    )

    if not region.strip():
        raise ValueError("AWS Region cannot be empty.")

    if not workgroup.strip():
        raise ValueError("Athena workgroup cannot be empty.")

    if timeout_seconds <= 0:
        raise ValueError("Query timeout must be greater than zero.")

    queries = build_validation_queries(
        database=normalized_database,
        table=normalized_table,
        start_date=normalized_start,
        end_date=normalized_end,
    )

    athena_client = create_athena_client(region.strip())
    query_results: dict[str, dict[str, Any]] = {}

    for query_name, query in queries.items():
        query_results[query_name] = execute_validation_query(
            athena_client=athena_client,
            query_name=query_name,
            query=query,
            database=normalized_database,
            region=region.strip(),
            workgroup=workgroup.strip(),
            output_location=normalized_output_location,
            timeout_seconds=timeout_seconds,
        )

    failures = validate_query_results(query_results)

    return build_report(
        query_results=query_results,
        failures=failures,
        database=normalized_database,
        table=normalized_table,
        region=region.strip(),
        start_date=normalized_start,
        end_date=normalized_end,
    )


def main() -> int:
    """Execute the validation command."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    try:
        report = run_validation(
            database=arguments.database,
            table=arguments.table,
            region=arguments.region,
            workgroup=arguments.workgroup,
            output_location=arguments.output_location,
            start_date=arguments.start_date,
            end_date=arguments.end_date,
            timeout_seconds=arguments.timeout,
        )
    except ValueError as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 1
    except AnalyticsValidationError as exc:
        LOGGER.error("Analytics validation could not complete: %s", exc)
        return 1
    except (ClientError, BotoCoreError) as exc:
        LOGGER.error("AWS SDK request failed: %s", exc)
        return 1

    print(json.dumps(report, indent=2, default=str))

    if report["failures"]:
        LOGGER.error(
            "Analytics validation failed with %s assertion error(s).",
            len(report["failures"]),
        )

        for failure in report["failures"]:
            LOGGER.error("Validation failure: %s", failure)

        return 1

    LOGGER.info(
        "Analytics validation passed. Executed %s queries and scanned "
        "%s bytes.",
        report["queries_executed"],
        report["total_data_scanned_bytes"],
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())