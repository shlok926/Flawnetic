from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.evidence import ImmutableEvidence, EvidenceManifest
from ..value_objects.identity import EvidenceId, CorrelationId, ContentHash

class ICommandEvidenceRepository(ABC):
    """Write Repository for Evidence."""
    @abstractmethod
    async def save(self, evidence: ImmutableEvidence) -> None:
        pass
        
    @abstractmethod
    async def save_manifest(self, manifest: EvidenceManifest) -> None:
        pass

class IQueryEvidenceRepository(ABC):
    """Read Repository for Evidence Graph."""
    @abstractmethod
    async def get_by_id(self, evidence_id: EvidenceId) -> Optional[ImmutableEvidence]:
        pass
        
    @abstractmethod
    async def get_by_correlation(self, correlation_id: CorrelationId) -> List[ImmutableEvidence]:
        pass
        
    @abstractmethod
    async def search_by_metadata(self, tenant_id: str, content_type: str) -> List[ImmutableEvidence]:
        pass

class IImmutableStorage(ABC):
    """Contract for writing/reading raw bytes to a Storage Provider."""
    @abstractmethod
    async def write_bytes(self, content_hash: ContentHash, raw_bytes: bytes, tenant_id: str) -> str:
        """Writes bytes (possibly encrypted/compressed) and returns the StorageReference."""
        pass
        
    @abstractmethod
    async def read_bytes(self, storage_reference: str, tenant_id: str) -> bytes:
        pass
