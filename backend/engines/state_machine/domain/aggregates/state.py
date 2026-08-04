from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, timezone
from ..value_objects.identity import StateId, StructuralHash, ConfidenceScore, TransitionId

class ApplicationState(BaseModel):
    """Aggregate Root representing a deterministic application state."""
    model_config = ConfigDict(frozen=True)
    
    state_id: StateId
    application_id: str
    structural_hash: StructuralHash
    confidence: ConfidenceScore
    version: int = Field(default=1, ge=1)
    status: str = Field(default="Discovered", description="Discovered | Validated | Active | Deprecated")
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StateTransition(BaseModel):
    """Aggregate Root representing a deterministic edge between states."""
    model_config = ConfigDict(frozen=True)
    
    transition_id: TransitionId
    source_state_id: StateId
    destination_state_id: StateId
    trigger_action: str
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
