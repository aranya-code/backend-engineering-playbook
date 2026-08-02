"""Redis feature examples and demonstrations."""

import uuid
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas import (
    PublishMessage,
    PublishResponse,
    StreamEvent,
    StreamResponse,
    CacheResponse,
    MessageResponse
)
from app.pubsub import pubsub_manager
from app.stream import order_stream, notification_stream
from app.locks import distributed_lock
from app.tasks import send_welcome_email, send_order_confirmation, process_payment
from app import redis_client

router = APIRouter(prefix="/redis", tags=["Redis Examples"])


@router.post("/publish", response_model=PublishResponse)
async def publish_message(message_data: PublishMessage):
    """
    Publish message to Redis Pub/Sub channel.
    
    Demonstrates Redis Pub/Sub for real-time messaging.
    
    - **channel**: Channel name
    - **message**: Message content
    """
    message = {
        "content": message_data.message,
        "timestamp": str(uuid.uuid4())
    }
    
    subscribers = await pubsub_manager.publish(message_data.channel, message)
    
    return PublishResponse(
        channel=message_data.channel,
        subscribers=subscribers,
        message=f"Message published to {subscribers} subscriber(s)"
    )


@router.post("/stream", response_model=StreamResponse)
async def add_to_stream(event: StreamEvent):
    """
    Add event to Redis Stream.
    
    Demonstrates Redis Streams for event sourcing and message queues.
    
    - **event_type**: Type of event (e.g., "order.created")
    - **data**: Event data as JSON object
    """
    event_id = await order_stream.add_event(
        event_type=event.event_type,
        data=event.data
    )
    
    return StreamResponse(
        stream_key="orders:events",
        event_id=event_id,
        event_type=event.event_type,
        message="Event added to stream successfully"
    )


@router.get("/stream/read")
async def read_stream(count: int = 10):
    """
    Read events from Redis Stream.
    
    Returns recent events from the order stream.
    """
    events = await order_stream.read_events(count=count)
    return {
        "stream": "orders:events",
        "count": len(events),
        "events": events
    }


@router.get("/stream/info")
async def stream_info():
    """
    Get Redis Stream information.
    
    Shows stream statistics and metadata.
    """
    info = await order_stream.get_stream_info()
    length = await order_stream.get_stream_length()
    
    return {
        "stream": "orders:events",
        "length": length,
        "info": info
    }


@router.post("/lock/demo", response_model=MessageResponse)
async def distributed_lock_demo(resource: str = "shared_resource"):
    """
    Demonstrate distributed locking.
    
    Uses Redis SET NX EX for distributed locks to prevent race conditions.
    
    - **resource**: Resource identifier to lock
    """
    try:
        async with distributed_lock(resource, ttl=10, timeout=5):
            # Simulate critical section
            import asyncio
            await asyncio.sleep(2)
            
            return MessageResponse(
                message=f"Successfully acquired and released lock for '{resource}'"
            )
    except TimeoutError:
        raise HTTPException(
            status_code=409,
            detail=f"Could not acquire lock for '{resource}' - resource is busy"
        )


@router.post("/cache/clear", response_model=CacheResponse)
async def clear_cache(pattern: str = "products:*"):
    """
    Clear cache by pattern.
    
    Deletes all keys matching the given pattern.
    
    - **pattern**: Key pattern to match (e.g., "products:*", "cart:*")
    """
    deleted = await redis_client.delete_cache(pattern)
    
    return CacheResponse(
        message=f"Cleared cache matching pattern: {pattern}",
        keys_deleted=deleted
    )


@router.post("/celery/welcome-email", response_model=MessageResponse)
async def trigger_welcome_email(
    background_tasks: BackgroundTasks,
    email: str,
    user_name: str
):
    """
    Trigger welcome email via Celery.
    
    Demonstrates background task processing using Celery with Redis broker.
    
    - **email**: Recipient email
    - **user_name**: User's name
    """
    # Queue task in Celery
    task = send_welcome_email.delay(email, user_name)
    
    return MessageResponse(
        message=f"Welcome email task queued with ID: {task.id}"
    )


@router.post("/celery/order-confirmation", response_model=MessageResponse)
async def trigger_order_confirmation(
    email: str,
    order_id: int,
    total: float
):
    """
    Trigger order confirmation email via Celery.
    
    - **email**: Recipient email
    - **order_id**: Order ID
    - **total**: Order total amount
    """
    task = send_order_confirmation.delay(email, order_id, total)
    
    return MessageResponse(
        message=f"Order confirmation task queued with ID: {task.id}"
    )


@router.post("/celery/process-payment", response_model=MessageResponse)
async def trigger_payment_processing(
    order_id: int,
    amount: float,
    payment_method: str = "credit_card"
):
    """
    Trigger payment processing via Celery.
    
    - **order_id**: Order ID
    - **amount**: Payment amount
    - **payment_method**: Payment method
    """
    task = process_payment.delay(order_id, amount, payment_method)
    
    return MessageResponse(
        message=f"Payment processing task queued with ID: {task.id}"
    )


@router.get("/stats")
async def redis_stats():
    """
    Get Redis statistics.
    
    Shows current Redis server information and statistics.
    """
    client = await redis_client.get_redis()
    
    # Get Redis info
    info = await client.info()
    
    # Extract relevant stats
    stats = {
        "redis_version": info.get("redis_version"),
        "used_memory_human": info.get("used_memory_human"),
        "connected_clients": info.get("connected_clients"),
        "total_commands_processed": info.get("total_commands_processed"),
        "uptime_in_seconds": info.get("uptime_in_seconds"),
        "uptime_in_days": info.get("uptime_in_days"),
    }
    
    # Get database stats
    db_stats = {}
    for key, value in info.items():
        if key.startswith("db"):
            db_stats[key] = value
    
    stats["databases"] = db_stats
    
    return stats


@router.get("/health")
async def redis_health_check():
    """
    Redis health check.
    
    Verifies Redis connectivity and responsiveness.
    """
    try:
        client = await redis_client.get_redis()
        await client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "message": "Redis is responding to PING"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Redis health check failed: {str(e)}"
        )
