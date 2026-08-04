from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from ..value_objects.identity import TwinId, TwinVersionId, ChangeSetId

class BaseDomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    event_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TwinCreated(BaseDomainEvent):
    twin_id: TwinId
    application_id: str

class TwinVersionCreated(BaseDomainEvent):
    twin_id: TwinId
    version_id: TwinVersionId

class TwinUpdated(BaseDomainEvent):
    twin_id: TwinId
    version_id: TwinVersionId
    changeset_id: ChangeSetId

class TwinCertified(BaseDomainEvent):
    version_id: TwinVersionId

class TwinHealthDegraded(BaseDomainEvent):
    version_id: TwinVersionId
    reason: str
