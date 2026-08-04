from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from ..value_objects.identity import GraphId, VersionId, AssertionId, ConflictId, InferenceId

class BaseDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KnowledgeAssertionCreated(BaseDomainEvent):
    graph_id: GraphId
    assertion_id: AssertionId

class KnowledgeAssertionDisputed(BaseDomainEvent):
    graph_id: GraphId
    conflict_id: ConflictId
    assertion_id: AssertionId

class KnowledgeConflictResolved(BaseDomainEvent):
    graph_id: GraphId
    conflict_id: ConflictId
    winning_assertion_id: AssertionId

class KnowledgeFreshnessDegraded(BaseDomainEvent):
    graph_id: GraphId
    assertion_id: AssertionId
    new_confidence: float

class KnowledgeCertified(BaseDomainEvent):
    graph_id: GraphId
    version_id: VersionId
