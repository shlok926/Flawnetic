import pytest
from backend.engines.knowledge_graph.domain.aggregates.graph import KnowledgeAssertion
from backend.engines.knowledge_graph.domain.value_objects.identity import (
    AssertionId, DomainId, NodeId, ConfidenceMetrics, AssertionState
)
from backend.engines.knowledge_graph.domain.services.services import ConflictResolutionService, KnowledgeFreshnessEngine

def create_assertion(a_id: str, rel: str, base_conf: float, time_decay: float = 0.0) -> KnowledgeAssertion:
    return KnowledgeAssertion(
        assertion_id=AssertionId(value=a_id),
        domain_id=DomainId(value="d1"),
        subject_node_id=NodeId(value="n1"),
        relationship_type=rel,
        object_node_id=NodeId(value="n2"),
        state=AssertionState(state="Proposed"),
        confidence=ConfidenceMetrics(
            base_confidence=base_conf,
            time_decay=time_decay,
            adjusted_confidence=max(0.0, base_conf - time_decay)
        ),
        evidence_lineage_ids=["ev1"]
    )

def test_conflict_resolution_resolves_deterministic_winner():
    svc = ConflictResolutionService()
    
    a1 = create_assertion("a1", "CONTAINS_PII", 0.9)
    a2 = create_assertion("a2", "DOES_NOT_CONTAIN_PII", 0.6)
    
    # Conflict detected
    assert svc.detect_conflict(a1, a2) is True
    
    conflict = svc.create_conflict(a1, a2)
    resolved = svc.resolve_conflict(conflict, a1, a2)
    
    assert resolved.status == "Resolved"
    assert resolved.resolved_assertion_id.value == "a1"

def test_conflict_resolution_escalates_ties():
    svc = ConflictResolutionService()
    
    a1 = create_assertion("a1", "CONTAINS_PII", 0.8)
    a2 = create_assertion("a2", "DOES_NOT_CONTAIN_PII", 0.8)
    
    conflict = svc.create_conflict(a1, a2)
    resolved = svc.resolve_conflict(conflict, a1, a2)
    
    assert resolved.status == "Escalated"
    assert resolved.resolved_assertion_id is None

def test_knowledge_freshness_engine_decays_confidence():
    svc = KnowledgeFreshnessEngine()
    
    a1 = create_assertion("a1", "HAS_VULNERABILITY", 1.0)
    
    decayed = svc.decay_assertion(a1, 0.3)
    assert decayed.confidence.adjusted_confidence == 0.7
    assert decayed.confidence.time_decay == 0.3
    
    # Cap at 0.0
    decayed_fully = svc.decay_assertion(a1, 1.5)
    assert decayed_fully.confidence.adjusted_confidence == 0.0

def test_universal_provenance_rule_enforced_by_pydantic():
    with pytest.raises(Exception): # ValidationError for empty list
        KnowledgeAssertion(
            assertion_id=AssertionId(value="a1"),
            domain_id=DomainId(value="d1"),
            subject_node_id=NodeId(value="n1"),
            relationship_type="TEST",
            object_node_id=NodeId(value="n2"),
            state=AssertionState(state="Proposed"),
            confidence=ConfidenceMetrics(base_confidence=1.0, time_decay=0.0, adjusted_confidence=1.0),
            evidence_lineage_ids=[] # Fails min_length=1
        )
