#!/usr/bin/env python3
"""Create or verify the AWS Glue table for the S3 event data lake."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


LOGGER = logging.getLogger("data_lake.catalog")

DEFAULT_REGION = os.getenv("AWS_REGION", "ap-south-1")
DEFAULT_DATABASE_NAME = os.getenv(
    "GLUE_DATABASE_NAME",
    "data_lake_events",
)
DEFAULT_TABLE_NAME = os.getenv(
    "GLUE_TABLE_NAME",
    "events",
)
DEFAULT_BUCKET_NAME = os.getenv("DATA_LAKE_BUCKET_NAME")
DEFAULT_RAW_PREFIX = os.getenv(
    "DATA_LAKE_RAW_PREFIX",
    "raw/events",
)

CATALOG_ID_PATTERN = re.compile(r"^\d{12}$")
DATABASE_NAME_PATTERN = re.compile(r"^[a-z0-9_]{1,255}$")
TABLE_NAME_PATTERN = re.compile(r"^[a-z0-9_]{1,255}$")
BUCKET_NAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"
)

INPUT_FORMAT = "org.apache.hadoop.mapred.TextInputFormat"
OUTPUT_FORMAT = (
    "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"
)
SERDE_LIBRARY = "org.openx.data.jsonserde.JsonSerDe"

TABLE_COLUMNS = [
    {
        "Name": "event_id",
        "Type": "string",
        "Comment": "Unique event identifier.",
    },
    {
        "Name": "event_timestamp",
        "Type": "string",
        "Comment": "ISO 8601 event timestamp with timezone.",
    },
    {
        "Name": "tenant_id",
        "Type": "string",
        "Comment": "Tenant associated with the event.",
    },
    {
        "Name": "event_type",
        "Type": "string",
        "Comment": "Event category.",
    },
    {
        "Name": "user_id",
        "Type": "string",
        "Comment": "User associated with the event.",
    },
    {
        "Name": "amount",
        "Type": "string",
        "Comment": "Decimal amount represented as a string.",
    },
    {
        "Name": "currency",
        "Type": "string",
        "Comment": "Three-letter currency code.",
    },
    {
        "Name": "source",
        "Type": "string",
        "Comment": "Origin of the event.",
    },
    {
        "Name": "attributes",
        "Type": "map<string,string>",
        "Comment": "Event-specific scalar attributes.",
    },
]

PARTITION_KEYS = [
    {
        "Name": "event_date",
        "Type": "string",
        "Comment": "Event calendar date in YYYY-MM-DD format.",
    }
]


class GlueTableError(RuntimeError):
    """Raised when Glue table provisioning cannot be completed."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def validate_catalog_id(catalog_id: str | None) -> str | None:
    """Validate an optional AWS account catalog identifier."""
    if catalog_id is None:
        return None

    normalized_id = catalog_id.strip()

    if not CATALOG_ID_PATTERN.fullmatch(normalized_id):
        raise ValueError(
            "Catalog ID must be a 12-digit AWS account identifier."
        )

    return normalized_id


def validate_glue_name(
    value: str,
    label: str,
    pattern: re.Pattern[str],
) -> str:
    """Normalize and validate a Glue database or table name."""
    normalized_value = value.strip().lower()

    if not pattern.fullmatch(normalized_value):
        raise ValueError(
            f"{label} must contain between 1 and 255 lowercase "
            "letters, digits, or underscores."
        )

    return normalized_value


def validate_bucket_name(bucket_name: str) -> str:
    """Validate the destination S3 bucket name."""
    normalized_name = bucket_name.strip()

    if not BUCKET_NAME_PATTERN.fullmatch(normalized_name):
        raise ValueError(
            "Bucket name must be a valid DNS-compatible S3 bucket name "
            "between 3 and 63 characters."
        )

    if ".." in normalized_name:
        raise ValueError(
            "Bucket name cannot contain consecutive periods."
        )

    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", normalized_name):
        raise ValueError(
            "Bucket name cannot be formatted as an IPv4 address."
        )

    if normalized_name.startswith("xn--"):
        raise ValueError(
            "Bucket names using the reserved xn-- prefix are not accepted."
        )

    if normalized_name.endswith("-s3alias"):
        raise ValueError(
            "Bucket names using the reserved -s3alias suffix "
            "are not accepted."
        )

    return normalized_name


def normalize_s3_prefix(prefix: str) -> str:
    """Normalize a relative S3 prefix."""
    normalized_prefix = prefix.strip().strip("/")

    if not normalized_prefix:
        raise ValueError("S3 raw-data prefix cannot be empty.")

    segments = normalized_prefix.split("/")

    if any(segment in {".", ".."} for segment in segments):
        raise ValueError(
            "S3 prefix cannot contain relative path segments."
        )

    if any(not segment for segment in segments):
        raise ValueError(
            "S3 prefix cannot contain empty path segments."
        )

    return normalized_prefix


def build_table_location(
    bucket_name: str,
    raw_prefix: str,
) -> str:
    """Build the S3 location containing raw JSON Lines objects."""
    return f"s3://{bucket_name}/{raw_prefix}/"


def create_glue_client(region: str) -> Any:
    """Create a Glue client using the standard AWS credential chain."""
    client_config = Config(
        retries={
            "mode": "standard",
            "max_attempts": 5,
        },
        connect_timeout=10,
        read_timeout=30,
    )

    return boto3.client(
        "glue",
        region_name=region,
        config=client_config,
    )


def build_table_input(
    database_name: str,
    table_name: str,
    location: str,
    description: str,
) -> dict[str, Any]:
    """Build the Glue TableInput definition."""
    return {
        "Name": table_name,
        "Description": description,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "EXTERNAL": "TRUE",
            "classification": "json",
            "compressionType": "none",
            "typeOfData": "file",
        },
        "StorageDescriptor": {
            "Columns": TABLE_COLUMNS,
            "Location": location,
            "InputFormat": INPUT_FORMAT,
            "OutputFormat": OUTPUT_FORMAT,
            "Compressed": False,
            "NumberOfBuckets": -1,
            "SerdeInfo": {
                "SerializationLibrary": SERDE_LIBRARY,
                "Parameters": {
                    "ignore.malformed.json": "false",
                    "case.insensitive": "true",
                },
            },
            "StoredAsSubDirectories": False,
        },
        "PartitionKeys": PARTITION_KEYS,
    }


def get_existing_database(
    glue_client: Any,
    database_name: str,
    catalog_id: str | None = None,
) -> dict[str, Any] | None:
    """Return an existing Glue database or None when it is absent."""
    request: dict[str, Any] = {
        "Name": database_name,
    }

    if catalog_id:
        request["CatalogId"] = catalog_id

    try:
        response = glue_client.get_database(**request)
    except glue_client.exceptions.EntityNotFoundException:
        return None

    return response.get("Database")


def get_existing_table(
    glue_client: Any,
    database_name: str,
    table_name: str,
    catalog_id: str | None = None,
) -> dict[str, Any] | None:
    """Return an existing Glue table or None when it is absent."""
    request: dict[str, Any] = {
        "DatabaseName": database_name,
        "Name": table_name,
    }

    if catalog_id:
        request["CatalogId"] = catalog_id

    try:
        response = glue_client.get_table(**request)
    except glue_client.exceptions.EntityNotFoundException:
        return None

    return response.get("Table")


def normalize_columns(
    columns: list[dict[str, Any]] | None,
) -> list[tuple[str, str]]:
    """Return comparable column names and types."""
    if not columns:
        return []

    return [
        (
            column.get("Name", "").lower(),
            column.get("Type", "").lower(),
        )
        for column in columns
    ]


def get_table_schema_differences(
    existing_table: dict[str, Any],
    expected_table: dict[str, Any],
) -> list[str]:
    """Identify differences between existing and expected table metadata."""
    differences: list[str] = []

    existing_descriptor = existing_table.get("StorageDescriptor", {})
    expected_descriptor = expected_table.get("StorageDescriptor", {})

    if normalize_columns(
        existing_descriptor.get("Columns")
    ) != normalize_columns(
        expected_descriptor.get("Columns")
    ):
        differences.append("storage descriptor columns")

    if normalize_columns(
        existing_table.get("PartitionKeys")
    ) != normalize_columns(
        expected_table.get("PartitionKeys")
    ):
        differences.append("partition keys")

    if existing_descriptor.get("Location", "").rstrip("/") != (
        expected_descriptor.get("Location", "").rstrip("/")
    ):
        differences.append("S3 location")

    if existing_descriptor.get("InputFormat") != (
        expected_descriptor.get("InputFormat")
    ):
        differences.append("input format")

    if existing_descriptor.get("OutputFormat") != (
        expected_descriptor.get("OutputFormat")
    ):
        differences.append("output format")

    existing_serde = existing_descriptor.get("SerdeInfo", {})
    expected_serde = expected_descriptor.get("SerdeInfo", {})

    if existing_serde.get("SerializationLibrary") != (
        expected_serde.get("SerializationLibrary")
    ):
        differences.append("SerDe library")

    return differences


def create_table(
    glue_client: Any,
    database_name: str,
    table_input: dict[str, Any],
    catalog_id: str | None = None,
) -> bool:
    """
    Create the Glue table when absent.

    Return True when this invocation creates the table.
    Return False when an existing table matches the expected definition.

    Existing tables with incompatible schemas are not modified.
    """
    table_name = table_input["Name"]

    existing_table = get_existing_table(
        glue_client=glue_client,
        database_name=database_name,
        table_name=table_name,
        catalog_id=catalog_id,
    )

    if existing_table:
        differences = get_table_schema_differences(
            existing_table=existing_table,
            expected_table=table_input,
        )

        if differences:
            difference_list = ", ".join(differences)
            raise GlueTableError(
                f"Glue table {database_name}.{table_name} already exists "
                f"with incompatible metadata: {difference_list}. "
                "Review the existing table before changing its schema."
            )

        LOGGER.info(
            "Glue table already exists and matches the expected schema: "
            "%s.%s",
            database_name,
            table_name,
        )
        return False

    request: dict[str, Any] = {
        "DatabaseName": database_name,
        "TableInput": table_input,
    }

    if catalog_id:
        request["CatalogId"] = catalog_id

    try:
        glue_client.create_table(**request)
    except glue_client.exceptions.AlreadyExistsException:
        # Another deployment may have created the table concurrently.
        existing_table = get_existing_table(
            glue_client=glue_client,
            database_name=database_name,
            table_name=table_name,
            catalog_id=catalog_id,
        )

        if existing_table:
            differences = get_table_schema_differences(
                existing_table=existing_table,
                expected_table=table_input,
            )

            if not differences:
                LOGGER.info(
                    "Glue table was created concurrently: %s.%s",
                    database_name,
                    table_name,
                )
                return False

            difference_list = ", ".join(differences)
            raise GlueTableError(
                "A concurrent deployment created an incompatible Glue "
                f"table: {difference_list}."
            )

        raise GlueTableError(
            "Glue reported that the table already exists, "
            "but it could not be retrieved."
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        error_message = exc.response.get("Error", {}).get(
            "Message",
            str(exc),
        )

        raise GlueTableError(
            f"Unable to create Glue table {database_name}.{table_name}: "
            f"{error_code}: {error_message}"
        ) from exc

    LOGGER.info(
        "Created Glue table: %s.%s",
        database_name,
        table_name,
    )
    return True


def provision_table(
    region: str,
    database_name: str,
    table_name: str,
    bucket_name: str,
    raw_prefix: str,
    description: str,
    catalog_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create or verify the Glue table for the raw event dataset."""
    normalized_database = validate_glue_name(
        database_name,
        "Database name",
        DATABASE_NAME_PATTERN,
    )
    normalized_table = validate_glue_name(
        table_name,
        "Table name",
        TABLE_NAME_PATTERN,
    )
    normalized_catalog_id = validate_catalog_id(catalog_id)
    normalized_bucket = validate_bucket_name(bucket_name)
    normalized_prefix = normalize_s3_prefix(raw_prefix)

    if not description.strip():
        raise ValueError("Table description cannot be empty.")

    location = build_table_location(
        bucket_name=normalized_bucket,
        raw_prefix=normalized_prefix,
    )

    table_input = build_table_input(
        database_name=normalized_database,
        table_name=normalized_table,
        location=location,
        description=description.strip(),
    )

    if dry_run:
        return {
            "status": "dry_run",
            "database_name": normalized_database,
            "table_name": normalized_table,
            "catalog_id": normalized_catalog_id,
            "region": region,
            "location": location,
            "table_input": table_input,
        }

    glue_client = create_glue_client(region)

    existing_database = get_existing_database(
        glue_client=glue_client,
        database_name=normalized_database,
        catalog_id=normalized_catalog_id,
    )

    if existing_database is None:
        raise GlueTableError(
            f"Glue database {normalized_database!r} does not exist. "
            "Create it first using create_glue_database.py."
        )

    created = create_table(
        glue_client=glue_client,
        database_name=normalized_database,
        table_input=table_input,
        catalog_id=normalized_catalog_id,
    )

    existing_table = get_existing_table(
        glue_client=glue_client,
        database_name=normalized_database,
        table_name=normalized_table,
        catalog_id=normalized_catalog_id,
    )

    if existing_table is None:
        raise GlueTableError(
            f"Table {normalized_database}.{normalized_table} "
            "was not found after the create operation."
        )

    return {
        "status": "created" if created else "already_exists",
        "database_name": normalized_database,
        "table_name": normalized_table,
        "catalog_id": normalized_catalog_id,
        "region": region,
        "location": existing_table.get(
            "StorageDescriptor",
            {},
        ).get("Location"),
        "table_type": existing_table.get("TableType"),
        "columns": normalize_columns(
            existing_table.get(
                "StorageDescriptor",
                {},
            ).get("Columns")
        ),
        "partition_keys": normalize_columns(
            existing_table.get("PartitionKeys")
        ),
        "create_time": (
            existing_table["CreateTime"].isoformat()
            if existing_table.get("CreateTime")
            else None
        ),
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Create or verify the AWS Glue external table for the "
            "partitioned S3 event dataset."
        )
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_NAME,
        help=f"Glue database name. Default: {DEFAULT_DATABASE_NAME}",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE_NAME,
        help=f"Glue table name. Default: {DEFAULT_TABLE_NAME}",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET_NAME,
        help=(
            "S3 data lake bucket. Defaults to DATA_LAKE_BUCKET_NAME."
        ),
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_RAW_PREFIX,
        help=f"Raw-data prefix. Default: {DEFAULT_RAW_PREFIX}",
    )
    parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help=f"AWS Region. Default: {DEFAULT_REGION}",
    )
    parser.add_argument(
        "--catalog-id",
        default=os.getenv("AWS_ACCOUNT_ID"),
        help=(
            "Optional 12-digit AWS account ID. "
            "Defaults to AWS_ACCOUNT_ID when configured."
        ),
    )
    parser.add_argument(
        "--description",
        default=(
            "External Glue table for partitioned JSON Lines event data."
        ),
        help="Glue table description.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without calling AWS Glue.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser.parse_args()


def main() -> int:
    """Execute Glue table provisioning."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    if not arguments.region.strip():
        LOGGER.error("AWS Region cannot be empty.")
        return 1

    if not arguments.bucket:
        LOGGER.error(
            "An S3 bucket is required. Set DATA_LAKE_BUCKET_NAME "
            "or provide --bucket."
        )
        return 1

    try:
        result = provision_table(
            region=arguments.region.strip(),
            database_name=arguments.database,
            table_name=arguments.table,
            bucket_name=arguments.bucket,
            raw_prefix=arguments.prefix,
            description=arguments.description,
            catalog_id=arguments.catalog_id,
            dry_run=arguments.dry_run,
        )
    except ValueError as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 1
    except GlueTableError as exc:
        LOGGER.error("%s", exc)
        return 1
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        error_message = exc.response.get("Error", {}).get(
            "Message",
            str(exc),
        )
        LOGGER.error(
            "AWS Glue request failed: %s: %s",
            error_code,
            error_message,
        )
        return 1
    except BotoCoreError as exc:
        LOGGER.error("AWS SDK request failed: %s", exc)
        return 1

    print(json.dumps(result, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())