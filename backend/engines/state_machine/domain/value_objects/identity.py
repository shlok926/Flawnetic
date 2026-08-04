from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
import hashlib

class StructuralHash(BaseModel):
    model_config = ConfigDict(frozen=True)
    hash_value: str = Field(..., description="SHA-256 hash of canonicalized DOM")
    
    @classmethod
    def generate(cls, canonical_dom: str) -> "StructuralHash":
        return cls(hash_value=hashlib.sha256(canonical_dom.encode('utf-8')).hexdigest())

class ConfidenceScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: float = Field(..., ge=0.0, le=1.0)
    
class SemanticIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)
    label: str = Field(..., description="AI inferred label, e.g. 'Checkout Page'")

class StateId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class TransitionId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str
