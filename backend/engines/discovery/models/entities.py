from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid
from pydantic import ConfigDict

class ConfidenceProvenance(BaseModel):
    score: float = Field(..., description="Overall confidence score between 0.0 and 1.0")
    sources: List[str] = Field(default_factory=list, description="Reasons/sources for this confidence score (e.g., 'DOM analysis', 'ARIA labels')")

class BaseDiscoveryEntity(BaseModel):
    """
    The Canonical Entity Model. 
    Every entity discovered by the platform MUST inherit from this base class.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Stable, structurally hashed ID or UUID")
    entity_type: str = Field(..., description="The type of entity (e.g., 'Component', 'State', 'Transition')")
    session_id: str = Field(..., description="The Discovery Session this entity was observed in")
    application_id: str = Field(..., description="The ID of the target application")
    version: str = Field(default="1.0", description="Version of the entity structural hash")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: ConfidenceProvenance
    evidence_ids: List[str] = Field(default_factory=list, description="List of S3 URLs/IDs pointing to raw evidence (e.g., screenshots, DOM dumps)")
    relationships: List[Dict[str, str]] = Field(default_factory=list, description="Edges connecting this entity to others (e.g., {'type': 'child_of', 'target_id': 'xyz'})")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata specific to the entity")

class ComponentEntity(BaseDiscoveryEntity):
    entity_type: str = "Component"
    tag_name: str
    attributes: Dict[str, str] = Field(default_factory=dict)
    
class StateEntity(BaseDiscoveryEntity):
    entity_type: str = "State"
    url: str
    dom_hash: str = Field(..., description="Structural hash of the state, ignoring dynamic content")

class BehaviorEntity(BaseDiscoveryEntity):
    entity_type: str = "Behavior"
    event_type: str = Field(..., description="e.g., 'click', 'hover', 'submit'")
    target_component_id: str

class LinkEntity(BaseDiscoveryEntity):
    entity_type: str = "Link"
    url: str = Field(..., description="The normalized absolute URL or routing path")
    link_type: str = Field(..., description="e.g., 'a_tag', 'button', 'spa_router', 'javascript'")
    text: str = Field(..., description="The text or aria-label of the link")
