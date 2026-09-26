"""Tests for MongoDB index management and index-related query optimization."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.database.indexes import create_indexes
from src.queries.optimized import find_recent_orders


def test_create_indexes_creates_expected_query_indexes() -> None:
    collection = MagicMock()

    create_indexes(collection)

    calls = collection.create_index.call_args_list

    assert len(calls) >= 2

    index_definitions = [call.args[0] for call in calls]

    assert [
        ("customer_id", 1),
        ("status", 1),
        ("created_at", -1),
    ] in index_definitions

    assert [
        ("status", 1),
        ("created_at", -1),
    ] in index_definitions


def test_find_recent_orders_matches_compound_index_prefix() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    find_recent_orders(
        collection,
        "customer-123",
        limit=20,
    )

    filter_query = collection.find.call_args.args[0]

    assert set(filter_query) == {"customer_id", "status"}
    assert filter_query["customer_id"] == "customer-123"
    assert filter_query["status"] == "completed"

    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(20)


def test_create_indexes_uses_stable_index_names() -> None:
    collection = MagicMock()

    create_indexes(collection)

    index_names = {
        call.kwargs.get("name")
        for call in collection.create_index.call_args_list
    }

    assert "customer_status_created_at" in index_names
    assert "status_created_at" in index_names


def test_create_indexes_is_idempotent_at_index_definition_level() -> None:
    collection = MagicMock()

    create_indexes(collection)
    first_call_count = collection.create_index.call_count

    create_indexes(collection)
    second_call_count = collection.create_index.call_count

    assert first_call_count > 0
    assert second_call_count == first_call_count * 2

"""Tests for MongoDB index management and index-related query optimization."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.database.indexes import create_indexes
from src.queries.optimized import find_recent_orders


def test_create_indexes_creates_expected_query_indexes() -> None:
    collection = MagicMock()

    create_indexes(collection)

    calls = collection.create_index.call_args_list

    assert len(calls) >= 2

    index_definitions = [call.args[0] for call in calls]

    assert [
        ("customer_id", 1),
        ("status", 1),
        ("created_at", -1),
    ] in index_definitions

    assert [
        ("status", 1),
        ("created_at", -1),
    ] in index_definitions


def test_find_recent_orders_matches_compound_index_prefix() -> None:
    collection = MagicMock()
    cursor = collection.find.return_value
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.__iter__.return_value = iter([])

    find_recent_orders(
        collection,
        "customer-123",
        limit=20,
    )

    filter_query = collection.find.call_args.args[0]

    assert set(filter_query) == {"customer_id", "status"}
    assert filter_query["customer_id"] == "customer-123"
    assert filter_query["status"] == "completed"

    cursor.sort.assert_called_once_with("created_at", -1)
    cursor.limit.assert_called_once_with(20)


def test_create_indexes_uses_stable_index_names() -> None:
    collection = MagicMock()

    create_indexes(collection)

    index_names = {
        call.kwargs.get("name")
        for call in collection.create_index.call_args_list
    }

    assert "customer_status_created_at" in index_names
    assert "status_created_at" in index_names


def test_create_indexes_is_idempotent_at_index_definition_level() -> None:
    collection = MagicMock()

    create_indexes(collection)
    first_call_count = collection.create_index.call_count

    create_indexes(collection)
    second_call_count = collection.create_index.call_count

    assert first_call_count > 0
    assert second_call_count == first_call_count * 2