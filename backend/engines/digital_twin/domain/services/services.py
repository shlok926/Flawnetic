import uuid
import logging
from typing import List, Optional
from ..aggregates.twin import (
    DigitalTwin, TwinVersion, TwinNode, TwinComponent, TwinChangeSet
)
from ..value_objects.identity import (
    TwinId, TwinVersionId, ChangeSetId, NodeId, ComponentId, 
    ConfidenceMetrics, FreshnessMetrics
)
from ..events.events import TwinCreated, TwinVersionCreated, TwinUpdated, TwinCertified
from .repositories import IDigitalTwinRepository, ITwinVersionRepository, ITwinProjectionRepository

logger = logging.getLogger(__name__)

class TwinBuilder:
    def __init__(self, repo: IDigitalTwinRepository):
        self.repo = repo
        
    async def create_twin(self, app_id: str, tenant_id: str) -> DigitalTwin:
        existing = await self.repo.get_by_application(app_id, tenant_id)
        if existing:
            return existing
            
        twin = DigitalTwin(
            twin_id=TwinId(value=str(uuid.uuid4())),
            application_id=app_id,
            tenant_id=tenant_id
        )
        await self.repo.save(twin)
        return twin

class TwinVersionService:
    def __init__(self, repo: ITwinVersionRepository):
        self.repo = repo
        
    async def create_new_version(self, twin: DigitalTwin, version_name: str) -> TwinVersion:
        version = TwinVersion(
            version_id=TwinVersionId(value=str(uuid.uuid4())),
            twin_id=twin.twin_id,
            version_name=version_name,
            status="Building"
        )
        await self.repo.save_version(version)
        return version

class ChangeDetectionEngine:
    """Computes the diff between two Twin versions."""
    def compute_diff(self, old_nodes: List[TwinNode], new_nodes: List[TwinNode]) -> TwinChangeSet:
        old_components = {c.component_id.value for node in old_nodes for c in node.components}
        new_components = {c.component_id.value for node in new_nodes for c in node.components}
        
        new_comps = list(new_components - old_components)
        removed_comps = list(old_components - new_components)
        
        # Simplified logic for drift severity
        severity = "MINOR"
        auth_drift = False
        if new_comps or removed_comps:
            severity = "MAJOR"
            
        # Example hardcoded heuristic: if more than 50% changed, it's critical
        if len(new_comps) > 5:
            severity = "CRITICAL"
            auth_drift = True
            
        return TwinChangeSet(
            changeset_id=ChangeSetId(value=str(uuid.uuid4())),
            from_version=TwinVersionId(value="v-old"),
            to_version=TwinVersionId(value="v-new"),
            severity=severity,
            new_components=[ComponentId(value=c) for c in new_comps],
            removed_components=[ComponentId(value=c) for c in removed_comps],
            authentication_drift_detected=auth_drift
        )

class TwinCertificationService:
    """Evaluates Twin health metrics and updates status."""
    def evaluate_certification(self, version: TwinVersion, confidence: ConfidenceMetrics, freshness: FreshnessMetrics) -> TwinVersion:
        status = version.status
        
        if status == "Building":
            status = "Validated"
            
        if status == "Validated":
            if confidence.semantic_confidence > 0.8 and freshness.temporal_freshness > 0.5:
                status = "Certified"
                
        # Return a copy with new status to preserve immutability
        return TwinVersion(
            version_id=version.version_id,
            twin_id=version.twin_id,
            version_name=version.version_name,
            status=status,
            nodes=version.nodes,
            created_at=version.created_at
        )
