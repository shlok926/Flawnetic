import pytest
import uuid
import hashlib
from backend.engines.evidence.domain.services.graph_builder import EvidenceGraphBuilder
from backend.engines.evidence.domain.services.repositories import IEvidenceRepository, IImmutableStorage
from backend.engines.evidence.domain.aggregates.evidence import ImmutableEvidence
from backend.engines.evidence.domain.value_objects.identity import EvidenceMetadata, ContentHash, EvidenceId, CorrelationId

class MockEvidenceRepository(IEvidenceRepository):
    def __init__(self):
        self.store = {}
        
    async def get_by_id(self, evidence_id: EvidenceId):
        return self.store.get(evidence_id.value)
        
    async def get_by_correlation(self, correlation_id: CorrelationId):
        return [e for e in self.store.values() if e.correlation_id == correlation_id]
        
    async def save(self, evidence: ImmutableEvidence):
        self.store[evidence.evidence_id.value] = evidence

class MockStorage(IImmutableStorage):
    def __init__(self):
        self.blobs = {}
        
    async def write_bytes(self, content_hash: ContentHash, raw_bytes: bytes) -> str:
        path = f"s3://mock-bucket/{content_hash.hash_value}"
        self.blobs[path] = raw_bytes
        return path
        
    async def read_bytes(self, storage_path: str) -> bytes:
        return self.blobs[storage_path]

@pytest.fixture
def builder():
    return EvidenceGraphBuilder(MockEvidenceRepository(), MockStorage())

@pytest.mark.asyncio
async def test_ingest_evidence_stores_immutable_blob_and_node(builder):
    app_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    raw_payload = b"<html>Test Payload</html>"
    
    metadata = EvidenceMetadata(
        content_type="text/html",
        source_url="https://test.com",
        byte_size=len(raw_payload),
        capture_engine="Playwright"
    )
    
    evidence = await builder.ingest_evidence(app_id, correlation_id, raw_payload, metadata)
    
    # Verify hash identity
    expected_hash = hashlib.sha256(raw_payload).hexdigest()
    assert evidence.content_hash.hash_value == expected_hash
    
    # Verify storage path
    assert evidence.storage_path == f"s3://mock-bucket/{expected_hash}"
    
    # Verify DB save
    saved = await builder.repo.get_by_id(evidence.evidence_id)
    assert saved is not None
    assert saved.metadata.content_type == "text/html"
