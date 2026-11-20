#!/usr/bin/env python3
"""Generate deterministic synthetic event data for the S3 data lake project.

The generated CSV dataset is suitable for local validation, S3 ingestion,
and downstream analytics with AWS Glue and Amazon Athena.

Default output:
    data/samples/events.csv

CSV schema:
    event_id
    event_timestamp
    event_date
    tenant_id
    event_type
    user_id
    amount
    currency
    source
    attributes

The generator uses only the Python standard library. A fixed random seed
produces reproducible datasets, making it suitable for repeatable tests.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import sys
import tempfile
import uuid

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence


LOGGER = logging.getLogger("sample_data_generator")

DEFAULT_ROWS = 1_000
DEFAULT_SEED = 42
DEFAULT_START_DATE = date(2026, 1, 1)
DEFAULT_DAYS = 7

EVENT_TYPES = (
    "purchase",
    "refund",
    "page_view",
    "signup",
)

EVENT_WEIGHTS = (
    0.30,
    0.05,
    0.50,
    0.15,
)

SOURCES = (
    "web",
    "mobile",
    "api",
)

TENANT_IDS = tuple(
    f"tenant-{index:03d}"
    for index in range(1, 11)
)

CURRENCIES = (
    "USD",
    "EUR",
    "GBP",
    "INR",
)

CSV_FIELDS = (
    "event_id",
    "event_timestamp",
    "event_date",
    "tenant_id",
    "event_type",
    "user_id",
    "amount",
    "currency",
    "source",
    "attributes",
)

EVENT_ID_NAMESPACE = uuid.UUID("d4b7b9b8-1e9e-4d12-a5f2-7b9f9a5d3c10")


def configure_logging(verbose: bool) -> None:
    """Configure command-line logging."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def parse_date(value: str) -> date:
    """Parse a date supplied in ISO 8601 YYYY-MM-DD format."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date {value!r}. Expected YYYY-MM-DD."
        ) from exc


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic synthetic event data for "
            "the Amazon S3 data lake project."
        )
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help=f"Number of events to generate (default: {DEFAULT_ROWS}).",
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=DEFAULT_START_DATE,
        help=(
            "First event date in YYYY-MM-DD format. "
            f"Default: {DEFAULT_START_DATE.isoformat()}."
        ),
    )

    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=(
            "Number of consecutive calendar days covered by the dataset. "
            f"Default: {DEFAULT_DAYS}."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducible output (default: {DEFAULT_SEED}).",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "events.csv",
        help=(
            "Output CSV path. Defaults to data/samples/events.csv "
            "relative to this script."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file if it already exists.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging.",
    )

    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate generator arguments before creating output."""
    if args.rows <= 0:
        raise ValueError("--rows must be greater than zero.")

    if args.days <= 0:
        raise ValueError("--days must be greater than zero.")

    if args.days > 3_650:
        raise ValueError("--days cannot exceed 3650.")

    try:
        args.start_date + timedelta(days=args.days - 1)
    except OverflowError as exc:
        raise ValueError(
            "The requested date range exceeds the supported date range."
        ) from exc

    if not isinstance(args.seed, int):
        raise ValueError("--seed must be an integer.")

    if args.output.suffix.lower() != ".csv":
        raise ValueError("The output file must use the .csv extension.")


def generate_event_id(seed: int, row_number: int) -> str:
    """Generate a stable event identifier for a seed and row number."""
    identifier = f"sample-event:{seed}:{row_number}"

    return str(
        uuid.uuid5(
            EVENT_ID_NAMESPACE,
            identifier,
        )
    )


def generate_event_timestamp(
    rng: random.Random,
    event_date: date,
) -> datetime:
    """Generate a timezone-aware UTC timestamp within a calendar day."""
    seconds_since_midnight = rng.randrange(24 * 60 * 60)

    timestamp = datetime.combine(
        event_date,
        time.min,
        tzinfo=timezone.utc,
    )

    return timestamp + timedelta(seconds=seconds_since_midnight)


def generate_event_attributes(
    rng: random.Random,
    event_type: str,
) -> dict[str, Any]:
    """Generate event-specific attributes with a consistent structure."""
    if event_type == "purchase":
        return {
            "product_id": f"product-{rng.randint(1, 100):04d}",
            "quantity": rng.randint(1, 5),
            "payment_method": rng.choice(
                ("card", "wallet", "bank_transfer")
            ),
        }

    if event_type == "refund":
        return {
            "order_id": f"order-{rng.randint(1, 50_000):06d}",
            "reason": rng.choice(
                (
                    "customer_request",
                    "duplicate_payment",
                    "product_return",
                )
            ),
        }

    if event_type == "page_view":
        return {
            "page": rng.choice(
                (
                    "/",
                    "/products",
                    "/products/details",
                    "/checkout",
                    "/account",
                )
            ),
            "device": rng.choice(
                ("desktop", "mobile", "tablet")
            ),
        }

    return {
        "registration_channel": rng.choice(
            ("organic", "campaign", "referral")
        ),
        "account_type": rng.choice(
            ("standard", "business")
        ),
    }


def generate_amount(
    rng: random.Random,
    event_type: str,
) -> str:
    """Generate a decimal amount represented as a CSV-safe string."""
    if event_type == "purchase":
        amount = rng.randint(500, 100_000) / 100
    elif event_type == "refund":
        amount = -(rng.randint(500, 50_000) / 100)
    else:
        amount = 0.0

    return f"{amount:.2f}"


def generate_event(
    rng: random.Random,
    seed: int,
    row_number: int,
    start_date: date,
    days: int,
) -> dict[str, str]:
    """Generate one synthetic event record."""
    event_type = rng.choices(
        EVENT_TYPES,
        weights=EVENT_WEIGHTS,
        k=1,
    )[0]

    event_date = start_date + timedelta(
        days=rng.randrange(days)
    )

    timestamp = generate_event_timestamp(
        rng,
        event_date,
    )

    attributes = generate_event_attributes(
        rng,
        event_type,
    )

    return {
        "event_id": generate_event_id(seed, row_number),
        "event_timestamp": timestamp.isoformat().replace(
            "+00:00",
            "Z",
        ),
        "event_date": event_date.isoformat(),
        "tenant_id": rng.choice(TENANT_IDS),
        "event_type": event_type,
        "user_id": f"user-{rng.randint(1, 100_000):06d}",
        "amount": generate_amount(rng, event_type),
        "currency": rng.choice(CURRENCIES),
        "source": rng.choice(SOURCES),
        "attributes": json.dumps(
            attributes,
            sort_keys=True,
            separators=(",", ":"),
        ),
    }


def generate_events(
    rows: int,
    seed: int,
    start_date: date,
    days: int,
) -> list[dict[str, str]]:
    """Generate a reproducible collection of synthetic event records."""
    rng = random.Random(seed)

    return [
        generate_event(
            rng=rng,
            seed=seed,
            row_number=row_number,
            start_date=start_date,
            days=days,
        )
        for row_number in range(rows)
    ]


def write_csv_atomically(
    output_path: Path,
    events: Sequence[dict[str, str]],
    overwrite: bool,
) -> None:
    """Write CSV data through a temporary file and atomically replace."""
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_path}. "
            "Use --overwrite to replace it."
        )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            suffix=".tmp",
            prefix=f".{output_path.name}.",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            writer = csv.DictWriter(
                temporary_file,
                fieldnames=CSV_FIELDS,
                extrasaction="raise",
            )

            writer.writeheader()
            writer.writerows(events)

            temporary_file.flush()

        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"Output already exists: {output_path}. "
                "Use --overwrite to replace it."
            )

        temporary_path.replace(output_path)
        temporary_path = None

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def log_generation_summary(
    output_path: Path,
    events: Sequence[dict[str, str]],
) -> None:
    """Log useful dataset statistics without printing event contents."""
    event_counts: dict[str, int] = {}

    for event in events:
        event_type = event["event_type"]
        event_counts[event_type] = (
            event_counts.get(event_type, 0) + 1
        )

    LOGGER.info("Generated %d event records.", len(events))
    LOGGER.info("Output file: %s", output_path)
    LOGGER.info("Event counts: %s", json.dumps(event_counts, sort_keys=True))

    if events:
        LOGGER.info(
            "Event date range: %s to %s",
            min(event["event_date"] for event in events),
            max(event["event_date"] for event in events),
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the sample data generation workflow."""
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    configure_logging(args.verbose)

    try:
        validate_arguments(args)

        LOGGER.info(
            "Generating %d events with seed %d.",
            args.rows,
            args.seed,
        )

        events = generate_events(
            rows=args.rows,
            seed=args.seed,
            start_date=args.start_date,
            days=args.days,
        )

        output_path = args.output.expanduser().resolve()

        write_csv_atomically(
            output_path=output_path,
            events=events,
            overwrite=args.overwrite,
        )

        log_generation_summary(
            output_path=output_path,
            events=events,
        )

        return 0

    except (OSError, ValueError) as exc:
        LOGGER.error("Sample data generation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())