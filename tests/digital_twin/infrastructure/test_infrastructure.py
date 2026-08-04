import pytest
import uuid
import json
from backend.engines.digital_twin.infrastructure.repositories.adapters import InMemoryTwinProjectionRepository, LRUProjectionCache
from backend.engines.digital_twin.infrastructure.event_handlers.rebuild import TwinProjectionHandlers, ProjectionRebuildService, InMemoryReplayCursorStore
from backend.engines.digital_twin.infrastructure.snapshot.snapshot import SnapshotEngine, SnapshotSignatureService, ProjectionSnapshot
from backend.engines.digital_twin.domain.aggregates.twin import TwinNode
from backend.engines.digital_twin.domain.events.events import TwinUpdated
from backend.engines.digital_twin.domain.value_objects.identity import TwinId, TwinVersionId, ChangeSetId, NodeId

@pytest.mark.asyncio
async def test_lru_cache_eviction_and_tenant_isolation():
    # Cache size 2 to test eviction
    cache = LRUProjectionCache(max_entries=2, ttl_seconds=600)
    cache.set("tenant-A::v1", [], 1)
    cache.set("tenant-A::v2", [], 1)
    
    # Exceeds max entries (2), v1 should be evicted (LRU)
    cache.set("tenant-B::v3", [], 1)
    
    assert cache.get("tenant-A::v1") is None # Evicted
    assert cache.get("tenant-A::v2") is not None # Hit
    assert cache.get("tenant-B::v3") is not None # Hit
    assert cache.evictions == 1

@pytest.mark.asyncio
async def test_replay_cursor_checkpointing_and_duplicate_protection():
    cursor_repo = InMemoryReplayCursorStore()
    handlers = TwinProjectionHandlers(None)
    # Checkpoint every 2 events
    engine = ProjectionRebuildService(handlers, cursor_repo, checkpoint_interval=2)
    
    e1 = TwinUpdated(event_id="e1", tenant_id="tenant-A", twin_id=TwinId(value="t"), version_id=TwinVersionId(value="v"), changeset_id=ChangeSetId(value="c"))
    e2 = TwinUpdated(event_id="e2", tenant_id="tenant-A", twin_id=TwinId(value="t"), version_id=TwinVersionId(value="v"), changeset_id=ChangeSetId(value="c"))
    e3 = TwinUpdated(event_id="e3", tenant_id="tenant-A", twin_id=TwinId(value="t"), version_id=TwinVersionId(value="v"), changeset_id=ChangeSetId(value="c"))
    
    # Send duplicate event
    await engine.rebuild_from_events([e1, e1, e2, e3], "tenant-A")
    
    # Processed count should be 3 (duplicate e1 ignored)
    checkpoint = cursor_repo.get_checkpoint("tenant-A")
    assert checkpoint.processed_count == 3
    assert checkpoint.last_event_id == "e3"

def test_snapshot_cryptographic_integrity():
    sig_service = SnapshotSignatureService("secret-key")
    engine = SnapshotEngine(sig_service)
    
    v_id = TwinVersionId(value="v2")
    node = TwinNode(node_id=NodeId(value="n2"), version_id=v_id, state_id_ref="s2")
    
    # 1. Build Snapshot
    snapshot = engine.build_snapshot(v_id, "tenant-A", [node], 5)
    assert snapshot.signature is not None
    
    snapshot_json = snapshot.model_dump_json()
    
    # 2. Verify Valid Load
    loaded = engine.load_snapshot(snapshot_json)
    assert loaded.version_id.value == "v2"
    
    # 3. Simulate Attack (Tampered Payload)
    attack_data = json.loads(snapshot_json)
    attack_data["tenant_id"] = "tenant-B" # Forgery attempt
    attack_json = json.dumps(attack_data)
    
    with pytest.raises(ValueError, match="Cryptographic signature mismatch"):
        engine.load_snapshot(attack_json)

@pytest.mark.asyncio
async def test_bulk_node_ingestion_transactional_semantics():
    repo = InMemoryTwinProjectionRepository()
    v_id = TwinVersionId(value="v_bulk")
    
    n1 = TwinNode(node_id=NodeId(value="n1"), version_id=v_id, state_id_ref="s1")
    n2 = TwinNode(node_id=NodeId(value="n2"), version_id=v_id, state_id_ref="s2")
    
    await repo.save_nodes_bulk([n1, n2], "tenant-A")
    
    nodes = await repo.get_nodes(v_id, "tenant-A", revision_token=1)
    assert len(nodes) == 2
    assert nodes[0].node_id.value == "n1"
    assert nodes[1].node_id.value == "n2"
