#!/usr/bin/env python3
"""Create or verify the AWS Glue database for the S3 data lake."""

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
DEFAULT_DESCRIPTION = (
    "AWS Glue database for the Amazon S3 event data lake."
)

DATABASE_NAME_PATTERN = re.compile(r"^[a-z0-9_]{1,255}$")
CATALOG_ID_PATTERN = re.compile(r"^\d{12}$")


class GlueDatabaseError(RuntimeError):
    """Raised when Glue database provisioning cannot be completed."""


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def validate_database_name(database_name: str) -> str:
    """Validate and normalize the Glue database name."""
    normalized_name = database_name.strip().lower()

    if not DATABASE_NAME_PATTERN.fullmatch(normalized_name):
        raise ValueError(
            "Database name must contain between 1 and 255 lowercase "
            "letters, digits, or underscores."
        )

    return normalized_name


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


def validate_location_uri(location_uri: str | None) -> str | None:
    """Validate an optional S3 location URI."""
    if location_uri is None:
        return None

    normalized_uri = location_uri.strip()

    if not normalized_uri.startswith("s3://"):
        raise ValueError(
            "Database location must be an S3 URI beginning with s3://."
        )

    if normalized_uri == "s3://":
        raise ValueError(
            "Database location must include a bucket name."
        )

    return normalized_uri.rstrip("/") + "/"


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


def get_existing_database(
    glue_client: Any,
    database_name: str,
    catalog_id: str | None = None,
) -> dict[str, Any] | None:
    """Return an existing database or None when it does not exist."""
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


def build_database_input(
    database_name: str,
    description: str,
    location_uri: str | None,
) -> dict[str, Any]:
    """Build the Glue DatabaseInput request."""
    database_input: dict[str, Any] = {
        "Name": database_name,
        "Description": description,
    }

    if location_uri:
        database_input["LocationUri"] = location_uri

    return database_input


def create_database(
    glue_client: Any,
    database_input: dict[str, Any],
    catalog_id: str | None = None,
) -> bool:
    """
    Create the Glue database.

    Return True when this invocation creates the database.
    Return False when the database already exists.
    """
    database_name = database_input["Name"]

    existing_database = get_existing_database(
        glue_client,
        database_name,
        catalog_id,
    )

    if existing_database:
        LOGGER.info(
            "Glue database already exists: %s",
            database_name,
        )
        return False

    request: dict[str, Any] = {
        "DatabaseInput": database_input,
    }

    if catalog_id:
        request["CatalogId"] = catalog_id

    try:
        glue_client.create_database(**request)
    except glue_client.exceptions.AlreadyExistsException:
        # Another deployment may have created the database concurrently.
        existing_database = get_existing_database(
            glue_client,
            database_name,
            catalog_id,
        )

        if existing_database:
            LOGGER.info(
                "Glue database was created concurrently: %s",
                database_name,
            )
            return False

        raise GlueDatabaseError(
            "Glue reported that the database already exists, "
            "but it could not be retrieved."
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        error_message = exc.response.get("Error", {}).get(
            "Message",
            str(exc),
        )

        raise GlueDatabaseError(
            f"Unable to create Glue database {database_name!r}: "
            f"{error_code}: {error_message}"
        ) from exc

    LOGGER.info(
        "Created Glue database: %s",
        database_name,
    )
    return True


def provision_database(
    region: str,
    database_name: str,
    description: str,
    location_uri: str | None = None,
    catalog_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create the Glue database or verify that it already exists."""
    normalized_name = validate_database_name(database_name)
    normalized_catalog_id = validate_catalog_id(catalog_id)
    normalized_location_uri = validate_location_uri(location_uri)

    database_input = build_database_input(
        database_name=normalized_name,
        description=description,
        location_uri=normalized_location_uri,
    )

    if dry_run:
        return {
            "status": "dry_run",
            "database_name": normalized_name,
            "catalog_id": normalized_catalog_id,
            "region": region,
            "database_input": database_input,
        }

    glue_client = create_glue_client(region)

    created = create_database(
        glue_client=glue_client,
        database_input=database_input,
        catalog_id=normalized_catalog_id,
    )

    existing_database = get_existing_database(
        glue_client=glue_client,
        database_name=normalized_name,
        catalog_id=normalized_catalog_id,
    )

    if existing_database is None:
        raise GlueDatabaseError(
            f"Database {normalized_name!r} was not found after "
            "the create operation."
        )

    return {
        "status": "created" if created else "already_exists",
        "database_name": normalized_name,
        "catalog_id": normalized_catalog_id,
        "region": region,
        "location_uri": existing_database.get("LocationUri"),
        "description": existing_database.get("Description"),
        "create_time": (
            existing_database["CreateTime"].isoformat()
            if existing_database.get("CreateTime")
            else None
        ),
    }


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Create or verify the AWS Glue database used by the "
            "Amazon S3 data lake project."
        )
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_NAME,
        help=(
            "Glue database name. "
            f"Default: {DEFAULT_DATABASE_NAME}"
        ),
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
        default=DEFAULT_DESCRIPTION,
        help="Glue database description.",
    )
    parser.add_argument(
        "--location",
        default=None,
        help=(
            "Optional S3 location URI for the database. "
            "Example: s3://example-bucket/raw/events/"
        ),
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
    """Execute Glue database provisioning."""
    arguments = parse_arguments()
    configure_logging(arguments.verbose)

    if not arguments.region.strip():
        LOGGER.error("AWS Region cannot be empty.")
        return 1

    if not arguments.description.strip():
        LOGGER.error("Database description cannot be empty.")
        return 1

    try:
        result = provision_database(
            region=arguments.region.strip(),
            database_name=arguments.database,
            description=arguments.description.strip(),
            location_uri=arguments.location,
            catalog_id=arguments.catalog_id,
            dry_run=arguments.dry_run,
        )
    except ValueError as exc:
        LOGGER.error("Invalid configuration: %s", exc)
        return 1
    except GlueDatabaseError as exc:
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