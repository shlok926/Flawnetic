import hmac
import hashlib
import json
import base64
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class IKeyProvider(ABC):
    @abstractmethod
    def get_current_key_version(self) -> str:
        pass
        
    @abstractmethod
    def get_key_material(self, version: str) -> Optional[bytes]:
        pass

class SnapshotSignatureService:
    def __init__(self, key_provider: IKeyProvider):
        self.key_provider = key_provider
        
    def sign_payload(self, canonical_payload: bytes, version: str) -> str:
        secret = self.key_provider.get_key_material(version)
        if not secret:
            raise ValueError(f"Key version {version} not found or disabled.")
        signature = hmac.new(secret, canonical_payload, hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')
        
    def verify_payload(self, canonical_payload: bytes, provided_signature: str, version: str) -> bool:
        try:
            expected = self.sign_payload(canonical_payload, version)
            return hmac.compare_digest(expected.encode('utf-8'), provided_signature.encode('utf-8'))
        except ValueError:
            raise
        except Exception:
            return False

class KnowledgeSnapshotEngine:
    def __init__(self, signature_service: SnapshotSignatureService):
        self.signature_service = signature_service
        
    def _canonicalize(self, data: Dict[str, Any]) -> bytes:
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
    def generate_snapshot(self, graph_id: str, tenant_id: str, version_id: str, relationships: list) -> str:
        payload = {
            "graph_id": graph_id,
            "tenant_id": tenant_id,
            "version_id": version_id,
            "relationships": relationships
        }
        
        canonical = self._canonicalize(payload)
        key_version = self.signature_service.key_provider.get_current_key_version()
        sig = self.signature_service.sign_payload(canonical, key_version)
        
        snapshot = {
            "payload": payload,
            "signature": sig,
            "algorithm": "HMAC-SHA256",
            "key_version": key_version
        }
        return json.dumps(snapshot)
        
    def load_snapshot(self, snapshot_json: str) -> Dict[str, Any]:
        snapshot = json.loads(snapshot_json)
        payload = snapshot['payload']
        sig = snapshot['signature']
        key_version = snapshot.get('key_version', 'v1') # Fallback for legacy
        
        canonical = self._canonicalize(payload)
        
        if not self.signature_service.verify_payload(canonical, sig, key_version):
            raise ValueError("Cryptographic signature mismatch. Knowledge Graph Snapshot is corrupted or forged.")
            
        return payload
