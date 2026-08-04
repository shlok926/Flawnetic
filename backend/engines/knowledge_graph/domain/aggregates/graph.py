from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime, timezone
from ..value_objects.identity import (
    GraphId, VersionId, OntologyVersionId, DomainId,
    AssertionId, InferenceId, NodeId, RelationshipId,
    ConflictId, ConfidenceMetrics, AssertionState
)

class SemanticOntology(BaseModel):
    """Versioned taxonomy to ensure deterministic replay."""
    model_config = ConfigDict(frozen=True)
    ontology_id: OntologyVersionId
    domain_id: DomainId
    name: str
    node_types: List[str]
    relationship_types: List[str]

class KnowledgeDomain(BaseModel):
    """Bounded semantic area (e.g. Security, Compliance)."""
    model_config = ConfigDict(frozen=True)
    domain_id: DomainId
    name: str
    active_ontology_id: OntologyVersionId

class KnowledgeAssertion(BaseModel):
    """Atomic fact with lifecycle state."""
    model_config = ConfigDict(frozen=True)
    assertion_id: AssertionId
    domain_id: DomainId
    subject_node_id: NodeId
    relationship_type: str
    object_node_id: NodeId
    state: AssertionState
    confidence: ConfidenceMetrics
    evidence_lineage_ids: List[str] = Field(..., min_length=1) # Universal Provenance Rule
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class KnowledgeInference(BaseModel):
    """Derived knowledge proposal."""
    model_config = ConfigDict(frozen=True)
    inference_id: InferenceId
    domain_id: DomainId
    proposed_assertion: KnowledgeAssertion
    ai_model_reference: str
    explainability_score: float = Field(..., ge=0.0, le=1.0)
    # The evidence for this inference MUST NOT be another inference
    source_evidence_ids: List[str] = Field(..., min_length=1)

class KnowledgeConflict(BaseModel):
    """Explicit contradiction record."""
    model_config = ConfigDict(frozen=True)
    conflict_id: ConflictId
    domain_id: DomainId
    assertion_a_id: AssertionId
    assertion_b_id: AssertionId
    status: Literal["Open", "Resolved", "Escalated"] = "Open"
    resolved_assertion_id: Optional[AssertionId] = None

class KnowledgeVersion(BaseModel):
    """Immutable semantic snapshot."""
    model_config = ConfigDict(frozen=True)
    version_id: VersionId
    graph_id: GraphId
    ontology_id: OntologyVersionId
    status: Literal["Building", "Validated", "Certified", "Current", "Deprecated", "Archived"]
    assertions: List[AssertionId] = Field(default_factory=list)

class KnowledgeGraph(BaseModel):
    """Aggregate Root."""
    model_config = ConfigDict(frozen=True)
    graph_id: GraphId
    tenant_id: str
    active_version_id: Optional[VersionId] = None
