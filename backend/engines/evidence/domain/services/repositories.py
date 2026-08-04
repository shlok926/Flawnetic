from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.evidence import ImmutableEvidence
from ..value_objects.identity import EvidenceId, CorrelationId, ContentHash

class IEvidenceRepository(ABC):
    @abstractmethod
    async def get_by_id(self, evidence_id: EvidenceId) -> Optional[ImmutableEvidence]:
        pass
        
    @abstractmethod
    async def get_by_correlation(self, correlation_id: CorrelationId) -> List[ImmutableEvidence]:
        pass

    @abstractmethod
    async def save(self, evidence: ImmutableEvidence) -> None:
        pass

class IImmutableStorage(ABC):
    """Contract for writing raw bytes to an immutable datastore (S3, GCS, Blob)."""
    @abstractmethod
    async def write_bytes(self, content_hash: ContentHash, raw_bytes: bytes) -> str:
        """Writes bytes and returns the storage path (e.g. s3://...)."""
        pass
        
    @abstractmethod
    async def read_bytes(self, storage_path: str) -> bytes:
        pass
