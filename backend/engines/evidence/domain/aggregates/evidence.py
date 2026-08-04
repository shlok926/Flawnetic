from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from ..value_objects.identity import EvidenceId, ContentHash, EvidenceMetadata, CorrelationId
from typing import Optional

class ImmutableEvidence(BaseModel):
    """Aggregate Root representing a single, immutable piece of collected evidence."""
    model_config = ConfigDict(frozen=True)
    
    evidence_id: EvidenceId
    correlation_id: CorrelationId
    application_id: str
    metadata: EvidenceMetadata
    content_hash: ContentHash
    storage_path: str = Field(..., description="URI to immutable storage, e.g., s3://flawnetic-evidence/...")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = Field(default="Hot", description="Hot | Warm | Cold | Archived")
