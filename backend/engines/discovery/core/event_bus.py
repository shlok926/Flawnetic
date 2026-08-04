import asyncio
from typing import Callable, Dict, List, Any
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseEventBus(ABC):
    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable):
        pass

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]):
        pass

class LocalMemoryEventBus(BaseEventBus):
    """
    Async In-Memory Event Bus for the Event-Driven Discovery Pipeline.
    In an enterprise deployment, this would be backed by Kafka or Redis Pub/Sub.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe an async callback to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        """Publish a structured event to all subscribers."""
        logger.info(f"Publishing Event: {event_type}")
        
        if event_type not in self._subscribers:
            return

        # Execute callbacks concurrently without blocking the publisher
        tasks = []
        for callback in self._subscribers[event_type]:
            tasks.append(asyncio.create_task(callback(payload)))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for callback, result in zip(self._subscribers[event_type], results):
                if isinstance(result, Exception):
                    logger.error(f"EventBus subscriber {callback.__name__} failed on {event_type}: {result}")

# Global Singleton instance for the Discovery Engine
event_bus: BaseEventBus = LocalMemoryEventBus()
