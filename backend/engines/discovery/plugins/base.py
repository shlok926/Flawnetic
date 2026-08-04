from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from models.entities import BaseDiscoveryEntity
from core.event_bus import event_bus
import logging

logger = logging.getLogger(__name__)

class BaseDiscoveryPlugin(ABC):
    """
    Abstract Base Class for all Discovery Plugins.
    Enforces a strict lifecycle: Initialize -> Discover -> Validate -> Normalize -> Emit -> Cleanup.
    """
    
    # Plugin Meta
    name: str = "BasePlugin"
    version: str = "1.0.0"
    
    def __init__(self, session_id: str, application_id: str):
        self.session_id = session_id
        self.application_id = application_id

    async def execute(self, context: Any) -> List[BaseDiscoveryEntity]:
        """
        The main execution wrapper that enforces the plugin lifecycle.
        Do not override this method. Override the lifecycle methods instead.
        """
        await event_bus.publish("PluginStarted", {"plugin": self.name, "version": self.version})
        
        try:
            await self.initialize(context)
            raw_data = await self.discover(context)
            entities: List[BaseDiscoveryEntity] = []
            if self.validate(raw_data):
                entities = self.normalize(raw_data)
                await self.emit(entities)
            
            await event_bus.publish("PluginCompleted", {"plugin": self.name, "entities_found": len(entities)})
            return entities
        except Exception as e:
            logger.error(f"Plugin {self.name} failed: {e}")
            await event_bus.publish("PluginFailed", {"plugin": self.name, "error": str(e)})
            raise
        finally:
            await self.cleanup()

    @abstractmethod
    async def initialize(self, context: Any) -> None:
        """Setup logic (e.g., injecting scripts into the page)."""
        pass

    @abstractmethod
    async def discover(self, context: Any) -> Any:
        """Core discovery logic. Can return raw, unstructured data."""
        pass

    @abstractmethod
    def validate(self, raw_data: Any) -> bool:
        """Sanity check on raw data before normalization."""
        pass

    @abstractmethod
    def normalize(self, raw_data: Any) -> List[BaseDiscoveryEntity]:
        """Convert raw data into strictly typed Canonical Entities."""
        pass

    async def emit(self, entities: List[BaseDiscoveryEntity]) -> None:
        """Publish discovered entities to the Event Bus / Storage."""
        for entity in entities:
            await event_bus.publish("EntityDiscovered", entity.model_dump(mode='json'))

    @abstractmethod
    async def cleanup(self) -> None:
        """Resource cleanup (e.g., removing injected scripts)."""
        pass
