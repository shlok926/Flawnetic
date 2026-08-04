import pytest
from backend.engines.knowledge_graph.infrastructure.repositories.adapters import InMemoryKnowledgeProjectionRepository, LRUProjectionCache
from backend.engines.knowledge_graph.infrastructure.event_handlers.rebuild import KnowledgeProjectionHandlers, ProjectionRebuildService, InMemoryReplayCursorStore, InMemoryDistributedLock
from backend.engines.knowledge_graph.infrastructure.snapshot.snapshot import KnowledgeSnapshotEngine, SnapshotSignatureService, IKeyProvider
from backend.engines.knowledge_graph.domain.aggregates.graph import KnowledgeAssertion
from backend.engines.knowledge_graph.domain.events.events import KnowledgeAssertionCreated
from backend.engines.knowledge_graph.domain.value_objects.identity import AssertionId, DomainId, NodeId, ConfidenceMetrics, AssertionState, GraphId

def create_assertion(a_id: str, rel: str) -> KnowledgeAssertion:
    return KnowledgeAssertion(
        assertion_id=AssertionId(value=a_id),
        domain_id=DomainId(value="d1"),
        subject_node_id=NodeId(value="n1"),
        relationship_type=rel,
        object_node_id=NodeId(value="n2"),
        state=AssertionState(state="Proposed"),
        confidence=ConfidenceMetrics(
            base_confidence=1.0,
            time_decay=0.0,
            adjusted_confidence=1.0
        ),
        evidence_lineage_ids=["ev1"]
    )

@pytest.mark.asyncio
async def test_bulk_ingestion_transactional_semantics():
    cache = LRUProjectionCache()
    repo = InMemoryKnowledgeProjectionRepository(cache)
    
    a1 = create_assertion("a1", "CONTAINS_PII")
    a2 = create_assertion("a2", "EXPOSES_API")
    
    await repo.save_assertions_bulk([a1, a2], "tenant-A")
    
    rels = await repo.get_relationships("n1", "tenant-A", revision_token=1)
    assert len(rels) == 2
    assert rels[0]["assertion_id"] == "a1"
    assert rels[1]["assertion_id"] == "a2"

@pytest.mark.asyncio
async def test_replay_cursor_checkpointing():
    # Mock assertion repo
    class MockAssertionRepo:
        async def get_assertion(self, assertion_id, tenant_id):
            return create_assertion(assertion_id.value, "TEST_REL")
            
    assertion_repo = MockAssertionRepo()
    projection_repo = InMemoryKnowledgeProjectionRepository(LRUProjectionCache())
    cursor_repo = InMemoryReplayCursorStore()
    lock = InMemoryDistributedLock()
    
    handlers = KnowledgeProjectionHandlers(projection_repo, assertion_repo)
    engine = ProjectionRebuildService(handlers, cursor_repo, lock, checkpoint_interval=2)
    
    events = [
        KnowledgeAssertionCreated(event_id="e1", tenant_id="tenant-A", graph_id=GraphId(value="g1"), assertion_id=AssertionId(value="a1")),
        KnowledgeAssertionCreated(event_id="e2", tenant_id="tenant-A", graph_id=GraphId(value="g1"), assertion_id=AssertionId(value="a2")),
        KnowledgeAssertionCreated(event_id="e3", tenant_id="tenant-A", graph_id=GraphId(value="g1"), assertion_id=AssertionId(value="a3")),
    ]
    
    await engine.rebuild_from_events(events)
    
    # 3 events processed, checkpoint should be at e3 with count 3
    checkpoint = cursor_repo.get_checkpoint("tenant-A")
    assert checkpoint.last_event_id == "e3"
    assert checkpoint.processed_count == 3
    
    # Re-running same events should skip them due to idempotency / cursor
    await engine.rebuild_from_events(events)
    assert len(engine.processed_event_ids) == 3

class MockKeyProvider(IKeyProvider):
    def __init__(self):
        self.keys = {"v1": b"secret123", "v2": b"newsecret456"}
        self.current = "v2"
        
    def get_current_key_version(self) -> str:
        return self.current
        
    def get_key_material(self, version: str) -> bytes:
        return self.keys.get(version)

def test_snapshot_cryptographic_integrity():
    key_prov = MockKeyProvider()
    key_prov.current = "v1" # simulate old snapshot
    sig_svc = SnapshotSignatureService(key_prov)
    engine = KnowledgeSnapshotEngine(sig_svc)
    
    snapshot_json = engine.generate_snapshot("g1", "tenant-A", "v1", [])
    
    # Switch active key to simulate rotation over time
    key_prov.current = "v2"
    
    # Should load fine because it uses the key_version in the JSON to find v1
    payload = engine.load_snapshot(snapshot_json)
    assert payload["graph_id"] == "g1"
    
    # Tamper payload
    tampered_json = snapshot_json.replace('"tenant-A"', '"tenant-B"')
    
    with pytest.raises(ValueError, match="Cryptographic signature mismatch"):
        engine.load_snapshot(tampered_json)

def test_disabled_key_rejected():
    key_prov = MockKeyProvider()
    sig_svc = SnapshotSignatureService(key_prov)
    engine = KnowledgeSnapshotEngine(sig_svc)
    
    snapshot_json = engine.generate_snapshot("g1", "tenant-A", "v1", [])
    
    # Delete the key material (simulate key disabled/revoked)
    del key_prov.keys["v2"]
    
    with pytest.raises(ValueError, match="not found or disabled"):
        engine.load_snapshot(snapshot_json)

@pytest.mark.asyncio
async def test_distributed_mutex_prevents_parallel_replay():
    class MockAssertionRepo:
        async def get_assertion(self, assertion_id, tenant_id):
            return create_assertion(assertion_id.value, "TEST_REL")
            
    handlers = KnowledgeProjectionHandlers(InMemoryKnowledgeProjectionRepository(LRUProjectionCache()), MockAssertionRepo())
    lock = InMemoryDistributedLock()
    engine = ProjectionRebuildService(handlers, InMemoryReplayCursorStore(), lock)
    
    events = [KnowledgeAssertionCreated(event_id="e1", tenant_id="tenant-A", graph_id=GraphId(value="g1"), assertion_id=AssertionId(value="a1"))]
    
    # Acquire lock manually to simulate another pod holding it
    lock.acquire("lock:replay:tenant-A")
    
    await engine.rebuild_from_events(events)
    # Should exit early, so processed events is 0
    assert len(engine.processed_event_ids) == 0
    
    # Release lock, now it should work
    lock.release("lock:replay:tenant-A")
    await engine.rebuild_from_events(events)
    assert len(engine.processed_event_ids) == 1

