"""Redis Pub/Sub implementation."""

import asyncio
import json
from typing import Callable, Optional, Dict, Any

from app.redis_client import get_redis


class PubSubManager:
    """Manager for Redis Pub/Sub operations."""

    def __init__(self):
        """Initialize PubSubManager."""
        self.subscribers: Dict[str, asyncio.Task] = {}

    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Publish message to channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            int: Number of subscribers that received the message
        """
        client = await get_redis()
        message_json = json.dumps(message)
        return await client.publish(channel, message_json)

    async def subscribe(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to channel and process messages.
        
        Args:
            channel: Channel name
            callback: Function to call when message received
        """
        client = await get_redis()
        pubsub = client.pubsub()
        
        await pubsub.subscribe(channel)
        
        print(f"Subscribed to channel: {channel}")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await callback(data)
                    except json.JSONDecodeError:
                        print(f"Failed to decode message: {message['data']}")
                    except Exception as e:
                        print(f"Error processing message: {e}")
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            print(f"Unsubscribed from channel: {channel}")
            raise

    def start_subscriber(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Start background subscriber task.
        
        Args:
            channel: Channel name
            callback: Function to call when message received
        """
        if channel in self.subscribers:
            print(f"Subscriber already running for channel: {channel}")
            return
        
        task = asyncio.create_task(self.subscribe(channel, callback))
        self.subscribers[channel] = task
        print(f"Started subscriber for channel: {channel}")

    def stop_subscriber(self, channel: str) -> None:
        """
        Stop subscriber for channel.
        
        Args:
            channel: Channel name
        """
        if channel not in self.subscribers:
            print(f"No subscriber running for channel: {channel}")
            return
        
        task = self.subscribers.pop(channel)
        task.cancel()
        print(f"Stopped subscriber for channel: {channel}")

    async def stop_all_subscribers(self) -> None:
        """Stop all active subscribers."""
        for channel, task in self.subscribers.items():
            task.cancel()
        
        # Wait for all tasks to complete
        if self.subscribers:
            await asyncio.gather(*self.subscribers.values(), return_exceptions=True)
        
        self.subscribers.clear()
        print("Stopped all subscribers")


# Global PubSub manager instance
pubsub_manager = PubSubManager()


# Example callback functions

async def order_event_handler(message: Dict[str, Any]) -> None:
    """
    Handle order events.
    
    Args:
        message: Order event message
    """
    print(f"[ORDER EVENT] Received: {message}")
    
    event_type = message.get("event_type")
    order_id = message.get("order_id")
    
    if event_type == "created":
        print(f"New order created: {order_id}")
    elif event_type == "updated":
        print(f"Order updated: {order_id}")
    elif event_type == "cancelled":
        print(f"Order cancelled: {order_id}")
    else:
        print(f"Unknown order event: {event_type}")


async def notification_handler(message: Dict[str, Any]) -> None:
    """
    Handle notification events.
    
    Args:
        message: Notification message
    """
    print(f"[NOTIFICATION] {message.get('title', 'No Title')}: {message.get('body', 'No Body')}")


async def product_update_handler(message: Dict[str, Any]) -> None:
    """
    Handle product update events.
    
    Args:
        message: Product update message
    """
    print(f"[PRODUCT UPDATE] Product {message.get('product_id')} - {message.get('action')}")
