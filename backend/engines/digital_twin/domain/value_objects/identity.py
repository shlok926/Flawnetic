from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class TwinId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class TwinVersionId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class NodeId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ComponentId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class BehaviorId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ChangeSetId(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

class ConfidenceMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    structural_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_confidence: float = Field(..., ge=0.0, le=1.0)
    semantic_confidence: float = Field(..., ge=0.0, le=1.0)

class FreshnessMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    temporal_freshness: float = Field(..., ge=0.0, le=1.0)
    velocity_drift: float = Field(..., ge=0.0, le=1.0)
