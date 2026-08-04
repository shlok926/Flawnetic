import hmac
import hashlib
import json
import base64
from typing import Dict, Any

class SnapshotSignatureService:
    def __init__(self, secret_key: str):
        self.secret = secret_key.encode('utf-8')
        
    def sign_payload(self, canonical_payload: bytes) -> str:
        signature = hmac.new(self.secret, canonical_payload, hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')
        
    def verify_payload(self, canonical_payload: bytes, provided_signature: str) -> bool:
        try:
            expected = self.sign_payload(canonical_payload)
            return hmac.compare_digest(expected.encode('utf-8'), provided_signature.encode('utf-8'))
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
        sig = self.signature_service.sign_payload(canonical)
        
        snapshot = {
            "payload": payload,
            "signature": sig,
            "algorithm": "HMAC-SHA256"
        }
        return json.dumps(snapshot)
        
    def load_snapshot(self, snapshot_json: str) -> Dict[str, Any]:
        snapshot = json.loads(snapshot_json)
        payload = snapshot['payload']
        sig = snapshot['signature']
        
        canonical = self._canonicalize(payload)
        
        if not self.signature_service.verify_payload(canonical, sig):
            raise ValueError("Cryptographic signature mismatch. Knowledge Graph Snapshot is corrupted or forged.")
            
        return payload
