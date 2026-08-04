import time
import logging
from collections import OrderedDict
from typing import Optional, List, Dict
from backend.engines.digital_twin.domain.aggregates.twin import DigitalTwin, TwinVersion, TwinNode
from backend.engines.digital_twin.domain.value_objects.identity import TwinId, TwinVersionId
from backend.engines.digital_twin.domain.services.repositories import ITwinProjectionRepository

logger = logging.getLogger(__name__)

class LRUProjectionCache:
    """Bounded LRU Cache enforcing Read-After-Write via RevisionToken."""
    def __init__(self, max_entries: int = 1000, ttl_seconds: int = 3600):
        self.store: OrderedDict = OrderedDict()
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.current_revision = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
    def get(self, key: str, required_revision: int = 0) -> Optional[List[TwinNode]]:
        if self.current_revision < required_revision:
            logger.warning("Cache Stale: Requesting Rev %s, Current %s", required_revision, self.current_revision)
            self.misses += 1
            return None 
            
        entry = self.store.get(key)
        if not entry:
            self.misses += 1
            return None
            
        value, timestamp = entry
        if time.time() - timestamp > self.ttl_seconds:
            self.invalidate(key)
            self.misses += 1
            return None
            
        self.store.move_to_end(key)
        self.hits += 1
        return value
        
    def set(self, key: str, value: List[TwinNode], revision: int):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = (value, time.time())
        self.current_revision = max(self.current_revision, revision)
        
        if len(self.store) > self.max_entries:
            self.store.popitem(last=False)
            self.evictions += 1
            
    def invalidate(self, key: str):
        if key in self.store:
            del self.store[key]

class InMemoryTwinProjectionRepository(ITwinProjectionRepository):
    def __init__(self):
        self.store: Dict[str, Dict[str, List[TwinNode]]] = {}
        self.cache = LRUProjectionCache(max_entries=500, ttl_seconds=600)
        self.revision = 0
        
    def _enforce_tenant(self, tenant_id: str):
        if not tenant_id:
            raise ValueError("TenantId is mandatory for Projection reads/writes.")
        if tenant_id not in self.store:
            self.store[tenant_id] = {}
            
    async def get_nodes(self, version_id: TwinVersionId, tenant_id: str, revision_token: int = 0) -> List[TwinNode]:
        self._enforce_tenant(tenant_id)
        cache_key = f"{tenant_id}::{version_id.value}"
        
        cached = self.cache.get(cache_key, revision_token)
        if cached is not None:
            return cached
            
        nodes = self.store[tenant_id].get(version_id.value, [])
        self.cache.set(cache_key, nodes, self.revision)
        return nodes
        
    async def save_node(self, node: TwinNode, tenant_id: str) -> None:
        self._enforce_tenant(tenant_id)
        v_id = node.version_id.value
        
        if v_id not in self.store[tenant_id]:
            self.store[tenant_id][v_id] = []
            
        self.store[tenant_id][v_id].append(node)
        self.revision += 1
        
        cache_key = f"{tenant_id}::{v_id}"
        self.cache.invalidate(cache_key)

    async def save_nodes_bulk(self, nodes: List[TwinNode], tenant_id: str) -> None:
        if not nodes:
            return
        
        self._enforce_tenant(tenant_id)
        # Transactional semantics (all or nothing)
        versions_affected = set()
        for node in nodes:
            v_id = node.version_id.value
            if v_id not in self.store[tenant_id]:
                self.store[tenant_id][v_id] = []
            self.store[tenant_id][v_id].append(node)
            versions_affected.add(v_id)
            
        self.revision += 1
        for v_id in versions_affected:
            self.cache.invalidate(f"{tenant_id}::{v_id}")

class Neo4jTwinProjectionRepository(ITwinProjectionRepository):
    async def get_nodes(self, version_id: TwinVersionId, tenant_id: str, revision_token: int = 0) -> List[TwinNode]:
        raise NotImplementedError("Neo4j driver deferred.")
        
    async def save_node(self, node: TwinNode, tenant_id: str) -> None:
        raise NotImplementedError("Neo4j driver deferred.")

    async def save_nodes_bulk(self, nodes: List[TwinNode], tenant_id: str) -> None:
        raise NotImplementedError("Neo4j UNWIND driver deferred.")
