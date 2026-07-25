"""Redis Streams implementation for event sourcing."""

import time
from typing import Dict, Any, List, Optional

from app.redis_client import get_redis


class StreamManager:
    """Manager for Redis Streams operations."""

    def __init__(self, stream_key: str = "events"):
        """
        Initialize StreamManager.
        
        Args:
            stream_key: Redis stream key
        """
        self.stream_key = stream_key

    async def add_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Add event to stream.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            str: Event ID
        """
        client = await get_redis()
        
        # Prepare stream data
        stream_data = {
            "event_type": event_type,
            "timestamp": str(int(time.time() * 1000)),
            **{k: str(v) for k, v in data.items()}
        }
        
        # Add to stream with auto-generated ID
        event_id = await client.xadd(self.stream_key, stream_data)
        return event_id

    async def read_events(
        self,
        count: int = 10,
        start_id: str = "-",
        block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Read events from stream.
        
        Args:
            count: Maximum number of events to read
            start_id: Start reading from this ID ("-" for oldest, "+" for newest)
            block: Block for this many milliseconds if no data (None = don't block)
            
        Returns:
            List[dict]: List of events
        """
        client = await get_redis()
        
        # Read from stream
        if block is not None:
            # Blocking read (wait for new messages)
            results = await client.xread(
                {self.stream_key: start_id},
                count=count,
                block=block
            )
        else:
            # Non-blocking read
            results = await client.xrange(self.stream_key, start_id, "+", count=count)
        
        events = []
        
        if block is not None and results:
            # Parse blocking read results
            for stream_name, messages in results:
                for event_id, data in messages:
                    events.append({
                        "id": event_id,
                        "stream": stream_name,
                        **data
                    })
        else:
            # Parse range read results
            for event_id, data in results:
                events.append({
                    "id": event_id,
                    **data
                })
        
        return events

    async def read_new_events(
        self,
        last_id: str = "$",
        count: int = 10,
        block: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Read new events (blocking).
        
        Args:
            last_id: Last event ID seen ("$" for latest)
            count: Maximum number of events to read
            block: Block for this many milliseconds
            
        Returns:
            List[dict]: List of new events
        """
        client = await get_redis()
        
        results = await client.xread(
            {self.stream_key: last_id},
            count=count,
            block=block
        )
        
        events = []
        
        if results:
            for stream_name, messages in results:
                for event_id, data in messages:
                    events.append({
                        "id": event_id,
                        "stream": stream_name,
                        **data
                    })
        
        return events

    async def create_consumer_group(
        self,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        Create consumer group for stream.
        
        Args:
            group_name: Consumer group name
            start_id: Start reading from this ID ("0" for beginning, "$" for new only)
            
        Returns:
            bool: True if created
        """
        client = await get_redis()
        
        try:
            await client.xgroup_create(
                self.stream_key,
                group_name,
                id=start_id,
                mkstream=True
            )
            return True
        except Exception as e:
            # Group might already exist
            print(f"Error creating consumer group: {e}")
            return False

    async def read_group(
        self,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Read events as consumer group member.
        
        Args:
            group_name: Consumer group name
            consumer_name: Consumer name
            count: Maximum number of events to read
            block: Block for this many milliseconds
            
        Returns:
            List[dict]: List of events
        """
        client = await get_redis()
        
        results = await client.xreadgroup(
            group_name,
            consumer_name,
            {self.stream_key: ">"},
            count=count,
            block=block
        )
        
        events = []
        
        if results:
            for stream_name, messages in results:
                for event_id, data in messages:
                    events.append({
                        "id": event_id,
                        "stream": stream_name,
                        **data
                    })
        
        return events

    async def ack_event(self, group_name: str, event_id: str) -> int:
        """
        Acknowledge event processing.
        
        Args:
            group_name: Consumer group name
            event_id: Event ID to acknowledge
            
        Returns:
            int: Number of messages acknowledged
        """
        client = await get_redis()
        return await client.xack(self.stream_key, group_name, event_id)

    async def get_stream_info(self) -> Dict[str, Any]:
        """
        Get stream information.
        
        Returns:
            dict: Stream information
        """
        client = await get_redis()
        info = await client.xinfo_stream(self.stream_key)
        return info

    async def get_stream_length(self) -> int:
        """
        Get stream length.
        
        Returns:
            int: Number of events in stream
        """
        client = await get_redis()
        return await client.xlen(self.stream_key)

    async def trim_stream(self, max_len: int = 1000) -> int:
        """
        Trim stream to maximum length.
        
        Args:
            max_len: Maximum length to keep
            
        Returns:
            int: Number of events removed
        """
        client = await get_redis()
        return await client.xtrim(self.stream_key, maxlen=max_len, approximate=True)


# Global stream managers
order_stream = StreamManager("orders:events")
notification_stream = StreamManager("notifications:events")
analytics_stream = StreamManager("analytics:events")
