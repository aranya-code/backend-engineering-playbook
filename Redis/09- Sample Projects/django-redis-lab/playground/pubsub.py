"""
Pub/Sub helpers for Redis publish/subscribe messaging.

Redis Pub/Sub provides fire-and-forget messaging:
- Publishers send messages to named channels
- Subscribers listen on channels and receive messages in real time
- Messages are NOT persisted — if no subscriber is listening, the message is lost

For persistent event streams, use Redis Streams (see stream.py).
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable

from .redis_service import get_redis_client

logger = logging.getLogger(__name__)


def publish_message(channel: str, message: str) -> int:
    """
    Publish a message to a Redis Pub/Sub channel.

    Args:
        channel: The channel name to publish to.
        message: The message content (string).

    Returns:
        Number of subscribers that received the message.
    """
    r = get_redis_client()
    payload = json.dumps({
        "channel": channel,
        "message": message,
    })
    receivers = r.publish(channel, payload)
    logger.info(
        "Published to channel=%s message=%s receivers=%s",
        channel, message[:50], receivers,
    )
    return receivers


def subscribe_to_channel(
    channel: str,
    callback: Callable[[dict[str, Any]], None],
) -> threading.Thread:
    """
    Subscribe to a Redis Pub/Sub channel in a background thread.

    The callback function is called for each message received.
    Returns the background thread (for testing/management).

    Usage:
        def handle_message(msg):
            print(f"Received: {msg['data']}")

        thread = subscribe_to_channel("notifications", handle_message)
    """
    r = get_redis_client()
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    logger.info("Subscribed to channel=%s", channel)

    def _listen() -> None:
        """Listen for messages in a loop."""
        for raw_message in pubsub.listen():
            if raw_message["type"] == "message":
                try:
                    data = json.loads(raw_message["data"])
                    callback(data)
                except json.JSONDecodeError:
                    callback({"message": raw_message["data"]})

    thread = threading.Thread(target=_listen, daemon=True)
    thread.start()
    return thread
