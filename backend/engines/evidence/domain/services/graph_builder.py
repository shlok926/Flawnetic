import uuid
import logging
from typing import List, Tuple
from ..value_objects.identity import ContentHash, EvidenceId, CorrelationId, EvidenceMetadata
from ..aggregates.evidence import ImmutableEvidence
from .repositories import IEvidenceRepository, IImmutableStorage

logger = logging.getLogger(__name__)

class EvidenceGraphBuilder:
    """Domain service responsible for securely archiving raw evidence into the Immutable Graph."""
    
    def __init__(self, repo: IEvidenceRepository, storage: IImmutableStorage):
        self.repo = repo
        self.storage = storage

    async def ingest_evidence(self, 
                              app_id: str, 
                              correlation_id: str, 
                              raw_bytes: bytes, 
                              metadata: EvidenceMetadata) -> ImmutableEvidence:
        """
        Calculates hash, writes bytes to immutable storage, and persists the Evidence node.
        Event-Sourcing pattern: This triggers EvidenceVerified downstream.
        """
        # 1. Generate identity and hash
        content_hash = ContentHash.generate(raw_bytes)
        ev_id = EvidenceId(value=str(uuid.uuid4()))
        corr_id = CorrelationId(value=correlation_id)
        
        # 2. Write to immutable storage (S3)
        storage_path = await self.storage.write_bytes(content_hash, raw_bytes)
        
        # 3. Create aggregate
        evidence = ImmutableEvidence(
            evidence_id=ev_id,
            correlation_id=corr_id,
            application_id=app_id,
            metadata=metadata,
            content_hash=content_hash,
            storage_path=storage_path
        )
        
        # 4. Save to Repository (Graph Node)
        await self.repo.save(evidence)
        
        return evidence
