"""MongoDB collection and index statistics helpers for performance analysis."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database


def get_database_statistics(database: Database[Any]) -> dict[str, Any]:
    """Return database-level statistics from MongoDB."""
    return database.command("dbStats")


def get_collection_statistics(
    collection: Collection[dict[str, Any]],
) -> dict[str, Any]:
    """Return collection-level storage and document statistics."""
    return collection.database.command(
        "collStats",
        collection.name,
    )


def get_index_statistics(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return usage statistics for indexes on a collection."""
    pipeline = [
        {"$indexStats": {}},
    ]

    return list(collection.aggregate(pipeline))


def get_collection_indexes(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return index definitions configured on a collection."""
    return list(collection.list_indexes())


def get_collection_size(
    collection: Collection[dict[str, Any]],
) -> dict[str, int]:
    """Return document and storage size information for a collection."""
    stats = get_collection_statistics(collection)

    return {
        "document_count": int(stats.get("count", 0)),
        "data_size_bytes": int(stats.get("size", 0)),
        "storage_size_bytes": int(stats.get("storageSize", 0)),
        "total_index_size_bytes": int(stats.get("totalIndexSize", 0)),
    }


def find_unused_indexes(
    collection: Collection[dict[str, Any]],
) -> list[str]:
    """Return indexes that have no recorded operations since statistics reset."""
    unused_indexes: list[str] = []

    for index_stat in get_index_statistics(collection):
        accesses = index_stat.get("accesses", {})
        if accesses.get("ops", 0) == 0:
            name = index_stat.get("name")
            if name:
                unused_indexes.append(name)

    return unused_indexes

"""MongoDB collection and index statistics helpers for performance analysis."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database


def get_database_statistics(database: Database[Any]) -> dict[str, Any]:
    """Return database-level statistics from MongoDB."""
    return database.command("dbStats")


def get_collection_statistics(
    collection: Collection[dict[str, Any]],
) -> dict[str, Any]:
    """Return collection-level storage and document statistics."""
    return collection.database.command(
        "collStats",
        collection.name,
    )


def get_index_statistics(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return usage statistics for indexes on a collection."""
    pipeline = [
        {"$indexStats": {}},
    ]

    return list(collection.aggregate(pipeline))


def get_collection_indexes(
    collection: Collection[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return index definitions configured on a collection."""
    return list(collection.list_indexes())


def get_collection_size(
    collection: Collection[dict[str, Any]],
) -> dict[str, int]:
    """Return document and storage size information for a collection."""
    stats = get_collection_statistics(collection)

    return {
        "document_count": int(stats.get("count", 0)),
        "data_size_bytes": int(stats.get("size", 0)),
        "storage_size_bytes": int(stats.get("storageSize", 0)),
        "total_index_size_bytes": int(stats.get("totalIndexSize", 0)),
    }


def find_unused_indexes(
    collection: Collection[dict[str, Any]],
) -> list[str]:
    """Return indexes that have no recorded operations since statistics reset."""
    unused_indexes: list[str] = []

    for index_stat in get_index_statistics(collection):
        accesses = index_stat.get("accesses", {})
        if accesses.get("ops", 0) == 0:
            name = index_stat.get("name")
            if name:
                unused_indexes.append(name)

    return unused_indexes