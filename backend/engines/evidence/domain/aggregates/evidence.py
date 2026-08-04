from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from ..value_objects.identity import (
    EvidenceId, LogicalEvidenceId, StorageObjectId, 
    ContentHash, ContentSignature, VerificationStatus, 
    EvidenceMetadata, CorrelationId
)
from typing import List, Optional, Literal

class ImmutableEvidence(BaseModel):
    """Aggregate Root representing a single, immutable piece of collected evidence (v3.0)."""
    model_config = ConfigDict(frozen=True)
    
    evidence_id: EvidenceId
    logical_evidence_id: LogicalEvidenceId
    storage_object_id: StorageObjectId
    correlation_id: CorrelationId
    application_id: str
    tenant_id: str
    
    metadata: EvidenceMetadata
    content_hash: ContentHash
    content_signature: ContentSignature
    verification_status: VerificationStatus = Field(default_factory=lambda: VerificationStatus(status="Unverified"))
    
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET"] = "INTERNAL"
    legal_hold: bool = False
    storage_reference: str = Field(..., description="Abstract reference, e.g., s3://, gcs://, local://")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["Collected", "Verified", "Referenced", "Archived", "Expired", "Deleted"] = "Collected"
    
class EvidenceBundle(BaseModel):
    """Groups related evidence (e.g., DOM, HAR, Screenshot) logically."""
    model_config = ConfigDict(frozen=True)
    
    bundle_id: str
    correlation_id: CorrelationId
    evidence_items: List[EvidenceId] = Field(default_factory=list)

class EvidenceManifest(BaseModel):
    """The signed, definitive audit entry for a complete Discovery Session."""
    model_config = ConfigDict(frozen=True)
    
    manifest_id: str
    correlation_id: CorrelationId
    session_id: str
    evidence_ids: List[EvidenceId]
    manifest_hash: ContentHash
    manifest_signature: ContentSignature
    finalized_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
