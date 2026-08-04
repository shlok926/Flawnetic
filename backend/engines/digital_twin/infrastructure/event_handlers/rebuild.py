import logging
from typing import List, Any, Set
from pydantic import BaseModel
from backend.engines.digital_twin.domain.events.events import TwinUpdated, TwinCertified
from backend.engines.digital_twin.domain.services.repositories import ITwinProjectionRepository

logger = logging.getLogger(__name__)

class ReplayCheckpoint(BaseModel):
    tenant_id: str
    last_event_id: str
    processed_count: int

from abc import ABC, abstractmethod

class IReplayCursorStore(ABC):
    @abstractmethod
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        pass
        
    @abstractmethod
    def get_checkpoint(self, tenant_id: str) -> ReplayCheckpoint | None:
        pass

class InMemoryReplayCursorStore(IReplayCursorStore):
    def __init__(self):
        self.store = {}
        
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        self.store[tenant_id] = ReplayCheckpoint(tenant_id=tenant_id, last_event_id=event_id, processed_count=count)
        
    def get_checkpoint(self, tenant_id: str) -> ReplayCheckpoint | None:
        return self.store.get(tenant_id)

class RedisReplayCursorStore(IReplayCursorStore):
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        raise NotImplementedError("Redis deferred")
        
    def get_checkpoint(self, tenant_id: str) -> ReplayCheckpoint | None:
        raise NotImplementedError("Redis deferred")

class PostgresReplayCursorStore(IReplayCursorStore):
    def __init__(self, db_session):
        self.db = db_session
        
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        raise NotImplementedError("Postgres deferred")
        
    def get_checkpoint(self, tenant_id: str) -> ReplayCheckpoint | None:
        raise NotImplementedError("Postgres deferred")

class TwinProjectionHandlers:
    def __init__(self, projection_repo: ITwinProjectionRepository):
        self.repo = projection_repo
        
    async def handle_twin_updated(self, event: TwinUpdated):
        pass
        
    async def handle_twin_certified(self, event: TwinCertified):
        pass

class ProjectionRebuildService:
    def __init__(self, handlers: TwinProjectionHandlers, cursor_repo: IReplayCursorStore, checkpoint_interval: int = 100):
        self.handlers = handlers
        self.cursor_repo = cursor_repo
        self.checkpoint_interval = checkpoint_interval
        self.processed_event_ids: Set[str] = set()
        
    async def rebuild_from_events(self, events: List[Any], tenant_id: str):
        checkpoint = self.cursor_repo.get_checkpoint(tenant_id)
        start_index = 0
        processed_count = checkpoint.processed_count if checkpoint else 0
        
        # Fast-forward to checkpoint (simplified logic for list, normally querying Kafka offset)
        if checkpoint:
            for i, e in enumerate(events):
                if e.event_id == checkpoint.last_event_id:
                    start_index = i + 1
                    break
                    
        for i in range(start_index, len(events)):
            event = events[i]
            if event.tenant_id != tenant_id:
                raise PermissionError("Cross-Tenant Event Stream Detected during Rebuild!")
                
            if event.event_id in self.processed_event_ids:
                logger.warning(f"Duplicate event {event.event_id} skipped.")
                continue
                
            if isinstance(event, TwinUpdated):
                await self.handlers.handle_twin_updated(event)
            elif isinstance(event, TwinCertified):
                await self.handlers.handle_twin_certified(event)
                
            self.processed_event_ids.add(event.event_id)
            processed_count += 1
            
            if processed_count % self.checkpoint_interval == 0:
                self.cursor_repo.save_checkpoint(tenant_id, event.event_id, processed_count)
                
        # Final checkpoint
        if events:
            self.cursor_repo.save_checkpoint(tenant_id, events[-1].event_id, processed_count)
            
        logger.info(f"Rebuild completed. Processed {processed_count} events total.")
