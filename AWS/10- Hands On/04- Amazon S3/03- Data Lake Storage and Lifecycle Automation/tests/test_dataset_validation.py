"""Unit tests for the data lake event dataset validator.

These tests exercise schema validation, required fields, field types,
timestamp and date consistency, event identifiers, and dataset-level
integrity constraints without requiring AWS credentials or network access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from src.ingestion.validate_dataset import validate_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "samples"
    / "sample_events.json"
)

REQUIRED_EVENT_FIELDS = {
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
}


@pytest.fixture
def sample_events() -> list[dict[str, Any]]:
    """Load the project's representative event dataset."""
    with SAMPLE_DATA_PATH.open("r", encoding="utf-8") as sample_file:
        events = json.load(sample_file)

    return events


@pytest.fixture
def valid_event(sample_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an independent valid event from the sample dataset."""
    return copy.deepcopy(sample_events[0])


def validation_errors(dataset: Any) -> list[str]:
    """Return validation errors from the validator's report."""
    result = validate_dataset(dataset)

    assert isinstance(result, dict)
    assert "errors" in result
    assert isinstance(result["errors"], list)

    return result["errors"]


def test_sample_dataset_is_valid(
    sample_events: list[dict[str, Any]],
) -> None:
    """The checked-in sample dataset must satisfy the event schema."""
    result = validate_dataset(sample_events)

    assert result["is_valid"] is True
    assert result["errors"] == []


def test_sample_dataset_contains_expected_number_of_events(
    sample_events: list[dict[str, Any]],
) -> None:
    """The sample dataset should contain all ten representative events."""
    assert len(sample_events) == 10


def test_sample_events_contain_required_fields(
    sample_events: list[dict[str, Any]],
) -> None:
    """Every event must contain the complete ingestion schema."""
    for event in sample_events:
        assert REQUIRED_EVENT_FIELDS.issubset(event.keys())


def test_sample_event_identifiers_are_unique(
    sample_events: list[dict[str, Any]],
) -> None:
    """Duplicate event identifiers must not occur in the sample dataset."""
    event_ids = [event["event_id"] for event in sample_events]

    assert len(event_ids) == len(set(event_ids))


def test_sample_event_dates_match_timestamp_dates(
    sample_events: list[dict[str, Any]],
) -> None:
    """Partition dates must agree with the UTC event timestamps."""
    from datetime import datetime

    for event in sample_events:
        timestamp = datetime.fromisoformat(
            event["event_timestamp"].replace("Z", "+00:00")
        )

        assert timestamp.date().isoformat() == event["event_date"]


@pytest.mark.parametrize(
    "missing_field",
    sorted(REQUIRED_EVENT_FIELDS),
)
def test_missing_required_field_is_rejected(
    valid_event: dict[str, Any],
    missing_field: str,
) -> None:
    """An event missing any required field must fail validation."""
    del valid_event[missing_field]

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        "",
        123,
        [],
        {},
    ],
)
def test_event_id_must_be_a_non_empty_string(
    valid_event: dict[str, Any],
    invalid_value: Any,
) -> None:
    """Event identifiers must be present as non-empty strings."""
    valid_event["event_id"] = invalid_value

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        "",
        123,
        [],
        {},
    ],
)
def test_tenant_id_must_be_a_non_empty_string(
    valid_event: dict[str, Any],
    invalid_value: Any,
) -> None:
    """Tenant identifiers must be valid strings."""
    valid_event["tenant_id"] = invalid_value

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_value",
    [
        None,
        "",
        123,
        [],
        {},
    ],
)
def test_event_type_must_be_a_non_empty_string(
    valid_event: dict[str, Any],
    invalid_value: Any,
) -> None:
    """Event types must be represented by non-empty strings."""
    valid_event["event_type"] = invalid_value

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_timestamp",
    [
        "",
        "not-a-timestamp",
        "2026-13-01T10:00:00Z",
        "2026-01-01",
        None,
        123,
    ],
)
def test_invalid_event_timestamp_is_rejected(
    valid_event: dict[str, Any],
    invalid_timestamp: Any,
) -> None:
    """Timestamps must use a valid timestamp representation."""
    valid_event["event_timestamp"] = invalid_timestamp

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_date",
    [
        "",
        "not-a-date",
        "2026-13-01",
        "2026/01/01",
        None,
        123,
    ],
)
def test_invalid_event_date_is_rejected(
    valid_event: dict[str, Any],
    invalid_date: Any,
) -> None:
    """Partition dates must use the expected ISO date representation."""
    valid_event["event_date"] = invalid_date

    errors = validation_errors([valid_event])

    assert errors


def test_event_date_must_match_utc_timestamp_date(
    valid_event: dict[str, Any],
) -> None:
    """An event must not be assigned to an inconsistent date partition."""
    valid_event["event_timestamp"] = "2026-01-01T23:30:00Z"
    valid_event["event_date"] = "2026-01-02"

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_amount",
    [
        None,
        "",
        "not-a-number",
        [],
        {},
    ],
)
def test_amount_must_be_a_numeric_string(
    valid_event: dict[str, Any],
    invalid_amount: Any,
) -> None:
    """Amounts in the sample schema are represented as decimal strings."""
    valid_event["amount"] = invalid_amount

    errors = validation_errors([valid_event])

    assert errors


@pytest.mark.parametrize(
    "invalid_currency",
    [
        "",
        "US",
        "USDD",
        123,
        None,
    ],
)
def test_currency_must_be_a_three_character_code(
    valid_event: dict[str, Any],
    invalid_currency: Any,
) -> None:
    """Currency values must use three-character currency codes."""
    valid_event["currency"] = invalid_currency

    errors = validation_errors([valid_event])

    assert errors


def test_attributes_must_be_a_dictionary(
    valid_event: dict[str, Any],
) -> None:
    """Event attributes must be represented as a JSON object."""
    valid_event["attributes"] = ["invalid", "attributes"]

    errors = validation_errors([valid_event])

    assert errors


def test_duplicate_event_ids_are_rejected(
    valid_event: dict[str, Any],
) -> None:
    """Duplicate identifiers must be detected across the dataset."""
    duplicate_event = copy.deepcopy(valid_event)

    errors = validation_errors(
        [
            valid_event,
            duplicate_event,
        ]
    )

    assert errors


@pytest.mark.parametrize(
    "invalid_dataset",
    [
        None,
        {},
        "invalid-dataset",
        123,
    ],
)
def test_dataset_must_be_a_list(
    invalid_dataset: Any,
) -> None:
    """The dataset input must be a collection of event records."""
    errors = validation_errors(invalid_dataset)

    assert errors


def test_empty_dataset_is_rejected() -> None:
    """An empty dataset must not be accepted as a valid ingestion batch."""
    errors = validation_errors([])

    assert errors


@pytest.mark.parametrize(
    "invalid_event",
    [
        None,
        "invalid-event",
        123,
        [],
    ],
)
def test_dataset_rejects_non_object_records(
    invalid_event: Any,
) -> None:
    """Every dataset record must be a JSON object."""
    errors = validation_errors([invalid_event])

    assert errors


def test_validation_does_not_modify_input_dataset(
    sample_events: list[dict[str, Any]],
) -> None:
    """Validation must not mutate caller-owned event records."""
    original_dataset = copy.deepcopy(sample_events)

    validate_dataset(sample_events)

    assert sample_events == original_dataset


def test_validation_handles_multiple_invalid_records(
    valid_event: dict[str, Any],
) -> None:
    """The validator should report invalid records across a complete batch."""
    first_invalid_event = copy.deepcopy(valid_event)
    first_invalid_event["event_id"] = ""

    second_invalid_event = copy.deepcopy(valid_event)
    second_invalid_event["event_id"] = "event-invalid-002"
    second_invalid_event["tenant_id"] = None

    errors = validation_errors(
        [
            first_invalid_event,
            second_invalid_event,
        ]
    )

    assert errors
    assert len(errors) >= 2