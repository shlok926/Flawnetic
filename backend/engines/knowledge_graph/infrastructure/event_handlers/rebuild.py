from typing import List, Optional, Dict
from pydantic import BaseModel
from abc import ABC, abstractmethod
from ...domain.events.events import KnowledgeAssertionCreated
from ...domain.aggregates.graph import KnowledgeAssertion
from ...domain.services.repositories import IKnowledgeProjectionRepository, IKnowledgeAssertionRepository
import asyncio

class ReplayCheckpoint(BaseModel):
    tenant_id: str
    last_event_id: str
    processed_count: int

class IReplayCursorStore(ABC):
    @abstractmethod
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        pass
        
    @abstractmethod
    def get_checkpoint(self, tenant_id: str) -> Optional[ReplayCheckpoint]:
        pass

class InMemoryReplayCursorStore(IReplayCursorStore):
    def __init__(self):
        self.store = {}
        
    def save_checkpoint(self, tenant_id: str, event_id: str, count: int) -> None:
        self.store[tenant_id] = ReplayCheckpoint(tenant_id=tenant_id, last_event_id=event_id, processed_count=count)
        
    def get_checkpoint(self, tenant_id: str) -> Optional[ReplayCheckpoint]:
        return self.store.get(tenant_id)

class KnowledgeProjectionHandlers:
    def __init__(self, projection_repo: IKnowledgeProjectionRepository, assertion_repo: IKnowledgeAssertionRepository):
        self.projection_repo = projection_repo
        self.assertion_repo = assertion_repo

    async def handle_assertion_created(self, event: KnowledgeAssertionCreated, batch: List[KnowledgeAssertion] = None):
        # Fetch the assertion from the source of truth
        assertion = await self.assertion_repo.get_assertion(event.assertion_id, event.tenant_id)
        if assertion:
            if batch is not None:
                batch.append(assertion)
            else:
                await self.projection_repo.save_assertions_bulk([assertion], event.tenant_id)

class IDistributedLock(ABC):
    @abstractmethod
    def acquire(self, lock_key: str) -> bool:
        pass
        
    @abstractmethod
    def release(self, lock_key: str) -> None:
        pass

class InMemoryDistributedLock(IDistributedLock):
    def __init__(self):
        self.locks = set()
        
    def acquire(self, lock_key: str) -> bool:
        if lock_key in self.locks:
            return False
        self.locks.add(lock_key)
        return True
        
    def release(self, lock_key: str) -> None:
        self.locks.discard(lock_key)

class RedisDistributedLock(IDistributedLock):
    def acquire(self, lock_key: str) -> bool:
        raise NotImplementedError("Redis driver deferred.")
        
    def release(self, lock_key: str) -> None:
        raise NotImplementedError("Redis driver deferred.")

class ProjectionRebuildService:
    def __init__(self, handlers: KnowledgeProjectionHandlers, cursor_repo: IReplayCursorStore, lock: IDistributedLock, checkpoint_interval: int = 100):
        self.handlers = handlers
        self.cursor_repo = cursor_repo
        self.lock = lock
        self.checkpoint_interval = checkpoint_interval
        self.processed_event_ids = set() # Idempotency guard
        self._async_lock = asyncio.Lock()
        
    async def rebuild_from_events(self, events: List[KnowledgeAssertionCreated]):
        if not events:
            return
            
        tenant_id = events[0].tenant_id
        lock_key = f"lock:replay:{tenant_id}"
        
        if not self.lock.acquire(lock_key):
            # Another worker is already rebuilding this tenant
            return
            
        try:
            checkpoint = self.cursor_repo.get_checkpoint(tenant_id)
            
            start_idx = 0
            processed_count = 0
            
            if checkpoint:
                # Find cursor
                for i, event in enumerate(events):
                    if event.event_id == checkpoint.last_event_id:
                        start_idx = i + 1
                        processed_count = checkpoint.processed_count
                        break
                        
            batch = []
            async with self._async_lock:
                for i in range(start_idx, len(events)):
                    event = events[i]
                    if event.event_id in self.processed_event_ids:
                        continue
                        
                    await self.handlers.handle_assertion_created(event, batch)
                    self.processed_event_ids.add(event.event_id)
                    processed_count += 1
                    
                    # Bulk save every checkpoint interval
                    if processed_count % self.checkpoint_interval == 0 and batch:
                        await self.handlers.projection_repo.save_assertions_bulk(batch, tenant_id)
                        batch.clear()
                        self.cursor_repo.save_checkpoint(tenant_id, event.event_id, processed_count)
                
                # Flush remaining
                if batch:
                    await self.handlers.projection_repo.save_assertions_bulk(batch, tenant_id)
                    self.cursor_repo.save_checkpoint(tenant_id, events[-1].event_id, processed_count)
        finally:
            self.lock.release(lock_key)
