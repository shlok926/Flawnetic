from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class GraphId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class VersionId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class OntologyVersionId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class DomainId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class AssertionId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class InferenceId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class NodeId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class RelationshipId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ConflictId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ConfidenceMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    base_confidence: float = Field(..., ge=0.0, le=1.0)
    time_decay: float = Field(default=0.0, ge=0.0, le=1.0)
    adjusted_confidence: float = Field(..., ge=0.0, le=1.0)

class AssertionState(BaseModel):
    model_config = ConfigDict(frozen=True)
    state: Literal["Proposed", "Verified", "Disputed", "Superseded", "Rejected", "Deprecated"]
