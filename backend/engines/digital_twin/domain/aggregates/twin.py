from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime, timezone
from ..value_objects.identity import (
    TwinId, TwinVersionId, NodeId, ComponentId, BehaviorId, 
    ChangeSetId, ConfidenceMetrics, FreshnessMetrics
)

class TwinBehavior(BaseModel):
    model_config = ConfigDict(frozen=True)
    behavior_id: BehaviorId
    name: str

class TwinComponent(BaseModel):
    model_config = ConfigDict(frozen=True)
    component_id: ComponentId
    origin_evidence_id: str
    behaviors: List[TwinBehavior] = Field(default_factory=list)

class TwinNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    node_id: NodeId
    version_id: TwinVersionId
    components: List[TwinComponent] = Field(default_factory=list)
    state_id_ref: str
    
class TwinVersion(BaseModel):
    model_config = ConfigDict(frozen=True)
    version_id: TwinVersionId
    twin_id: TwinId
    version_name: str
    status: Literal["Building", "Validated", "Certified", "Current", "Deprecated", "Archived"] = "Building"
    nodes: List[NodeId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DigitalTwin(BaseModel):
    model_config = ConfigDict(frozen=True)
    twin_id: TwinId
    application_id: str
    tenant_id: str
    active_version_id: Optional[TwinVersionId] = None
    
class TwinChangeSet(BaseModel):
    model_config = ConfigDict(frozen=True)
    changeset_id: ChangeSetId
    from_version: TwinVersionId
    to_version: TwinVersionId
    severity: Literal["MINOR", "MAJOR", "CRITICAL"]
    new_components: List[ComponentId] = Field(default_factory=list)
    removed_components: List[ComponentId] = Field(default_factory=list)
    changed_components: List[ComponentId] = Field(default_factory=list)
    authentication_drift_detected: bool = False
