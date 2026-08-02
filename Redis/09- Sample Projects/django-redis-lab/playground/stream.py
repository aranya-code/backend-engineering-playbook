"""
Redis Streams helpers.

Redis Streams provide an append-only, ordered log of events.
Unlike Pub/Sub, stream entries are PERSISTED and can be read later.

Key concepts:
- XADD: Append an entry to a stream
- XRANGE: Read entries by ID range
- XLEN: Count entries in a stream
- Consumer Groups: Distribute stream processing across multiple consumers
"""

from __future__ import annotations

import logging
from typing import Any

from .redis_service import get_redis_client

logger = logging.getLogger(__name__)

STREAM_KEY = "stream:orders"


def stream_add_event(
    order_id: int,
    event: str,
    data: dict[str, Any] | None = None,
) -> str:
    """
    Add an order event to the Redis Stream.

    Args:
        order_id: The order ID this event belongs to.
        event: Event type (e.g., "created", "paid", "shipped").
        data: Additional event data.

    Returns:
        The auto-generated entry ID (e.g., "1690000000000-0").
    """
    r = get_redis_client()

    fields = {
        "order_id": str(order_id),
        "event": event,
    }
    if data:
        for key, value in data.items():
            fields[key] = str(value)

    entry_id = r.xadd(STREAM_KEY, fields)
    logger.info(
        "Stream event added: id=%s order=%s event=%s",
        entry_id, order_id, event,
    )
    return entry_id


def stream_read_events(count: int = 50) -> list[dict[str, Any]]:
    """
    Read the most recent events from the order stream.

    Uses XREVRANGE to get entries in reverse chronological order.

    Args:
        count: Maximum number of entries to return.

    Returns:
        List of event dictionaries with 'id' and 'fields' keys.
    """
    r = get_redis_client()
    entries = r.xrevrange(STREAM_KEY, count=count)

    events = []
    for entry_id, fields in entries:
        events.append({
            "id": entry_id,
            "order_id": fields.get("order_id"),
            "event": fields.get("event"),
            "data": {
                k: v for k, v in fields.items()
                if k not in ("order_id", "event")
            },
        })

    return events


def stream_length() -> int:
    """Return the number of entries in the order stream."""
    r = get_redis_client()
    return r.xlen(STREAM_KEY)
