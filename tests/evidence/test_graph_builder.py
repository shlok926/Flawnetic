import pytest
import uuid
import hashlib
from backend.engines.evidence.domain.services.graph_builder import EvidenceGraphBuilder, CryptographicService
from backend.engines.evidence.domain.services.repositories import ICommandEvidenceRepository, IImmutableStorage
from backend.engines.evidence.domain.aggregates.evidence import ImmutableEvidence, EvidenceManifest
from backend.engines.evidence.domain.value_objects.identity import EvidenceMetadata, ContentHash

class MockCommandEvidenceRepository(ICommandEvidenceRepository):
    def __init__(self):
        self.store = {}
        
    async def save(self, evidence: ImmutableEvidence):
        self.store[evidence.evidence_id.value] = evidence
        
    async def save_manifest(self, manifest: EvidenceManifest):
        pass

class MockStorage(IImmutableStorage):
    def __init__(self):
        self.blobs = {}
        
    async def write_bytes(self, content_hash: ContentHash, raw_bytes: bytes, tenant_id: str) -> str:
        path = f"s3://mock-bucket-{tenant_id}/{content_hash.hash_value}"
        self.blobs[path] = raw_bytes
        return path
        
    async def read_bytes(self, storage_reference: str, tenant_id: str) -> bytes:
        return self.blobs[storage_reference]

@pytest.fixture
def crypto_service():
    return CryptographicService(tenant_secret="test-secret-key-1234")

@pytest.fixture
def builder(crypto_service):
    return EvidenceGraphBuilder(MockCommandEvidenceRepository(), MockStorage(), crypto_service)

@pytest.mark.asyncio
async def test_ingest_evidence_with_signatures_and_storage(builder, crypto_service):
    app_id = str(uuid.uuid4())
    tenant_id = "tenant-A"
    correlation_id = str(uuid.uuid4())
    logical_id_str = "logical-home-page-dom"
    raw_payload = b"<html>Test Payload v3</html>"
    
    metadata = EvidenceMetadata(
        content_type="text/html",
        source_url="https://test.com",
        byte_size=len(raw_payload),
        capture_engine="Playwright"
    )
    
    evidence = await builder.ingest_evidence(app_id, tenant_id, correlation_id, raw_payload, metadata, logical_id_str)
    
    # Verify hash identity
    expected_hash = hashlib.sha256(raw_payload).hexdigest()
    assert evidence.content_hash.hash_value == expected_hash
    
    # Verify cryptographic signature
    assert crypto_service.verify_signature(evidence.content_hash, evidence.content_signature) is True
    assert evidence.content_signature.algorithm == "HMAC-SHA256"
    
    # Verify decoupled identities
    assert evidence.logical_evidence_id.value == logical_id_str
    assert evidence.storage_reference == f"s3://mock-bucket-{tenant_id}/{expected_hash}"
    
    # Verify validation status
    assert evidence.verification_status.status == "Valid"
