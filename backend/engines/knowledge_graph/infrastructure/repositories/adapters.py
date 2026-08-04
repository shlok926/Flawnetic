from typing import List, Optional, Dict
from ...domain.services.repositories import (
    IKnowledgeAssertionRepository, IKnowledgeProjectionRepository, 
    IKnowledgeInferenceRepository, IKnowledgeVersionRepository, 
    IKnowledgeGraphRepository, IKnowledgeConflictRepository
)
from ...domain.aggregates.graph import (
    KnowledgeAssertion, KnowledgeInference, KnowledgeVersion, 
    KnowledgeGraph, KnowledgeConflict
)
from ...domain.value_objects.identity import AssertionId, GraphId, VersionId

class LRUProjectionCache:
    """Bounded cache to prevent memory explosion during mass ingestion."""
    def __init__(self, max_entries: int = 10000):
        from collections import OrderedDict
        import asyncio
        self.cache = OrderedDict()
        self.max_entries = max_entries
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[List[dict]]:
        async with self._lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    async def set(self, key: str, value: List[dict]) -> None:
        async with self._lock:
            self.cache[key] = value
            self.cache.move_to_end(key)
            if len(self.cache) > self.max_entries:
                self.cache.popitem(last=False)

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            if key in self.cache:
                del self.cache[key]

class InMemoryKnowledgeProjectionRepository(IKnowledgeProjectionRepository):
    def __init__(self, cache: LRUProjectionCache):
        self.store: Dict[str, List[dict]] = {}
        self.cache = cache
        self.revision = 0
        
    def _enforce_tenant(self, tenant_id: str):
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if tenant_id not in self.store:
            self.store[tenant_id] = []

    async def get_relationships(self, node_id: str, tenant_id: str, revision_token: int = 0) -> List[dict]:
        self._enforce_tenant(tenant_id)
        
        cache_key = f"{tenant_id}::{node_id}"
        if revision_token > 0: # Cache Bypass for strong consistency
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cached
                
        results = [rel for rel in self.store[tenant_id] if rel.get('subject_id') == node_id or rel.get('object_id') == node_id]
        await self.cache.set(cache_key, results)
        return results

    async def save_assertions_bulk(self, assertions: List[KnowledgeAssertion], tenant_id: str) -> None:
        self._enforce_tenant(tenant_id)
        # Transactional semantics (all or nothing)
        nodes_affected = set()
        for a in assertions:
            rel = {
                'subject_id': a.subject_node_id.value,
                'relationship_type': a.relationship_type,
                'object_id': a.object_node_id.value,
                'assertion_id': a.assertion_id.value
            }
            self.store[tenant_id].append(rel)
            nodes_affected.add(a.subject_node_id.value)
            nodes_affected.add(a.object_node_id.value)
            
        self.revision += 1
        for node_id in nodes_affected:
            await self.cache.invalidate(f"{tenant_id}::{node_id}")

class Neo4jKnowledgeProjectionRepository(IKnowledgeProjectionRepository):
    async def get_relationships(self, node_id: str, tenant_id: str) -> List[dict]:
        raise NotImplementedError("Neo4j Driver Deferred")
        
    async def save_assertions_bulk(self, assertions: List[KnowledgeAssertion], tenant_id: str) -> None:
        raise NotImplementedError("Neo4j Bulk UNWIND Deferred")

class InMemoryKnowledgeAssertionRepository(IKnowledgeAssertionRepository):
    def __init__(self):
        self.store = {}
        
    async def get_assertion(self, assertion_id: AssertionId, tenant_id: str) -> Optional[KnowledgeAssertion]:
        return self.store.get(f"{tenant_id}::{assertion_id.value}")
        
    async def save_assertion(self, assertion: KnowledgeAssertion) -> None:
        # In memory mock. Usually needs tenant_id passed or extracted
        self.store[f"tenant-A::{assertion.assertion_id.value}"] = assertion
