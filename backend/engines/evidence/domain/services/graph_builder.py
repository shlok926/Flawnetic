import uuid
import hmac
import hashlib
import logging
from typing import List
from ..value_objects.identity import (
    ContentHash, EvidenceId, CorrelationId, EvidenceMetadata,
    LogicalEvidenceId, StorageObjectId, ContentSignature, VerificationStatus
)
from ..aggregates.evidence import ImmutableEvidence, EvidenceManifest
from .repositories import ICommandEvidenceRepository, IImmutableStorage

logger = logging.getLogger(__name__)

class CryptographicService:
    """Domain service for handling HMAC-SHA256 signatures (simulating Envelope/KMS encryption for now)."""
    def __init__(self, tenant_secret: str):
        self.tenant_secret = tenant_secret.encode('utf-8')
        
    def sign_hash(self, content_hash: ContentHash) -> ContentSignature:
        signature = hmac.new(self.tenant_secret, content_hash.hash_value.encode('utf-8'), hashlib.sha256).hexdigest()
        return ContentSignature(signature=signature, algorithm="HMAC-SHA256")
        
    def verify_signature(self, content_hash: ContentHash, signature: ContentSignature) -> bool:
        expected = self.sign_hash(content_hash)
        return hmac.compare_digest(expected.signature, signature.signature)

class EvidenceGraphBuilder:
    """Domain service responsible for securely archiving raw evidence into the Immutable Graph (v3.0)."""
    
    def __init__(self, repo: ICommandEvidenceRepository, storage: IImmutableStorage, crypto: CryptographicService):
        self.repo = repo
        self.storage = storage
        self.crypto = crypto

    async def ingest_evidence(self, 
                              app_id: str,
                              tenant_id: str,
                              correlation_id: str, 
                              raw_bytes: bytes, 
                              metadata: EvidenceMetadata,
                              logical_id_str: str) -> ImmutableEvidence:
        """
        Calculates hash, generates cryptographic signature, writes to storage, and persists the Node.
        """
        # 1. Identity & Hashing
        content_hash = ContentHash.generate(raw_bytes)
        signature = self.crypto.sign_hash(content_hash)
        
        ev_id = EvidenceId(value=str(uuid.uuid4()))
        corr_id = CorrelationId(value=correlation_id)
        logical_id = LogicalEvidenceId(value=logical_id_str)
        storage_obj_id = StorageObjectId(value=str(uuid.uuid4()))
        
        # 2. Storage
        storage_ref = await self.storage.write_bytes(content_hash, raw_bytes, tenant_id)
        
        # 3. Aggregate creation
        evidence = ImmutableEvidence(
            evidence_id=ev_id,
            logical_evidence_id=logical_id,
            storage_object_id=storage_obj_id,
            correlation_id=corr_id,
            application_id=app_id,
            tenant_id=tenant_id,
            metadata=metadata,
            content_hash=content_hash,
            content_signature=signature,
            verification_status=VerificationStatus(status="Valid"),
            storage_reference=storage_ref,
            status="Collected"
        )
        
        # 4. Save to Repository (Graph Node)
        await self.repo.save(evidence)
        
        return evidence
