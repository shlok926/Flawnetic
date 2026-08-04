from pydantic import BaseModel, ConfigDict, Field
import hashlib
from typing import Literal

class EvidenceId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ContentHash(BaseModel):
    model_config = ConfigDict(frozen=True)
    hash_value: str = Field(..., description="SHA-256 hash of the immutable raw content")
    
    @classmethod
    def generate(cls, raw_bytes: bytes) -> "ContentHash":
        return cls(hash_value=hashlib.sha256(raw_bytes).hexdigest())

class EvidenceMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    content_type: str = Field(..., description="MIME type, e.g., text/html, image/png")
    source_url: str
    byte_size: int
    capture_engine: str = Field(..., description="e.g., Playwright, Requests")

class CorrelationId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str = Field(..., description="Ties evidence to a specific Discovery Session")
