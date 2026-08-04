from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Optional
import json
import logging
import hmac
import hashlib
from backend.engines.digital_twin.domain.aggregates.twin import TwinNode
from backend.engines.digital_twin.domain.value_objects.identity import TwinVersionId

logger = logging.getLogger(__name__)

class SnapshotSignatureService:
    """Provides HMAC-SHA256 signature generation and constant-time verification."""
    def __init__(self, tenant_key: str):
        self.tenant_key = tenant_key.encode('utf-8')
        
    def sign_payload(self, canonical_payload: bytes) -> str:
        return hmac.new(self.tenant_key, canonical_payload, hashlib.sha256).hexdigest()
        
    def verify_signature(self, canonical_payload: bytes, signature: str) -> bool:
        expected = self.sign_payload(canonical_payload)
        return hmac.compare_digest(expected, signature)

class ProjectionSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    version_id: TwinVersionId
    tenant_id: str
    nodes_serialized: List[Dict]
    last_event_revision: int
    signature: Optional[str] = None
    algorithm: str = "HMAC-SHA256"

class SnapshotEngine:
    def __init__(self, signature_service: SnapshotSignatureService):
        self.signature_service = signature_service
        
    def _canonicalize(self, data: dict) -> bytes:
        # Removes the signature itself before calculating hash, ensuring deterministic order
        clean_data = {k: v for k, v in data.items() if k != "signature"}
        return json.dumps(clean_data, sort_keys=True).encode('utf-8')

    def build_snapshot(self, version_id: TwinVersionId, tenant_id: str, nodes: List[TwinNode], revision: int) -> ProjectionSnapshot:
        serialized_nodes = [node.model_dump() for node in nodes]
        
        snapshot_dict = {
            "version_id": version_id.model_dump(),
            "tenant_id": tenant_id,
            "nodes_serialized": serialized_nodes,
            "last_event_revision": revision,
            "algorithm": "HMAC-SHA256"
        }
        
        canonical_bytes = self._canonicalize(snapshot_dict)
        sig = self.signature_service.sign_payload(canonical_bytes)
        
        snapshot = ProjectionSnapshot(
            **snapshot_dict,
            signature=sig
        )
        logger.info(f"Built and Signed Snapshot for Version {version_id.value}")
        return snapshot
        
    def load_snapshot(self, snapshot_json: str) -> ProjectionSnapshot:
        data = json.loads(snapshot_json)
        
        if "signature" not in data:
            raise ValueError("SnapshotRejected: Missing cryptographic signature.")
            
        canonical_bytes = self._canonicalize(data)
        if not self.signature_service.verify_signature(canonical_bytes, data["signature"]):
            raise ValueError("SnapshotRejected: Cryptographic signature mismatch. Possible tampering.")
            
        logger.info("SnapshotVerified successfully.")
        return ProjectionSnapshot(**data)
