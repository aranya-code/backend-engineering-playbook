"""MongoDB explain-plan analysis helpers for query performance diagnostics."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection


def explain_query(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any],
    *,
    projection: dict[str, int] | None = None,
    sort: list[tuple[str, int]] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return execution statistics for a MongoDB query.

    The returned explain document can be used to inspect the winning plan,
    execution stages, keys examined, documents examined, and execution time.
    """
    cursor = collection.find(filter_query, projection)

    if sort:
        cursor = cursor.sort(sort)

    if limit is not None:
        cursor = cursor.limit(limit)

    return cursor.explain("executionStats")


def analyze_execution_stats(explain_result: dict[str, Any]) -> dict[str, Any]:
    """Extract the most useful query-performance metrics from explain output."""
    execution_stats = explain_result.get("executionStats", {})
    query_planner = explain_result.get("queryPlanner", {})

    return {
        "execution_time_ms": execution_stats.get("executionTimeMillis"),
        "n_returned": execution_stats.get("nReturned"),
        "total_keys_examined": execution_stats.get("totalKeysExamined"),
        "total_docs_examined": execution_stats.get("totalDocsExamined"),
        "winning_stage": query_planner.get("winningPlan", {}).get("stage"),
        "winning_plan": query_planner.get("winningPlan"),
    }


def is_likely_collection_scan(explain_result: dict[str, Any]) -> bool:
    """Detect whether the winning query plan contains a collection scan."""
    winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
    return _contains_stage(winning_plan, "COLLSCAN")


def _contains_stage(plan: dict[str, Any], target_stage: str) -> bool:
    """Recursively search an explain-plan tree for a specific stage."""
    if plan.get("stage") == target_stage:
        return True

    for value in plan.values():
        if isinstance(value, dict) and _contains_stage(value, target_stage):
            return True

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _contains_stage(item, target_stage):
                    return True

    return False

"""MongoDB explain-plan analysis helpers for query performance diagnostics."""

from __future__ import annotations

from typing import Any

from pymongo.collection import Collection


def explain_query(
    collection: Collection[dict[str, Any]],
    filter_query: dict[str, Any],
    *,
    projection: dict[str, int] | None = None,
    sort: list[tuple[str, int]] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return execution statistics for a MongoDB query.

    The returned explain document can be used to inspect the winning plan,
    execution stages, keys examined, documents examined, and execution time.
    """
    cursor = collection.find(filter_query, projection)

    if sort:
        cursor = cursor.sort(sort)

    if limit is not None:
        cursor = cursor.limit(limit)

    return cursor.explain("executionStats")


def analyze_execution_stats(explain_result: dict[str, Any]) -> dict[str, Any]:
    """Extract the most useful query-performance metrics from explain output."""
    execution_stats = explain_result.get("executionStats", {})
    query_planner = explain_result.get("queryPlanner", {})

    return {
        "execution_time_ms": execution_stats.get("executionTimeMillis"),
        "n_returned": execution_stats.get("nReturned"),
        "total_keys_examined": execution_stats.get("totalKeysExamined"),
        "total_docs_examined": execution_stats.get("totalDocsExamined"),
        "winning_stage": query_planner.get("winningPlan", {}).get("stage"),
        "winning_plan": query_planner.get("winningPlan"),
    }


def is_likely_collection_scan(explain_result: dict[str, Any]) -> bool:
    """Detect whether the winning query plan contains a collection scan."""
    winning_plan = explain_result.get("queryPlanner", {}).get("winningPlan", {})
    return _contains_stage(winning_plan, "COLLSCAN")


def _contains_stage(plan: dict[str, Any], target_stage: str) -> bool:
    """Recursively search an explain-plan tree for a specific stage."""
    if plan.get("stage") == target_stage:
        return True

    for value in plan.values():
        if isinstance(value, dict) and _contains_stage(value, target_stage):
            return True

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _contains_stage(item, target_stage):
                    return True

    return False