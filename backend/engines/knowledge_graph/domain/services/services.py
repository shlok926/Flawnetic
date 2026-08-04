import uuid
from typing import List, Tuple
from ..aggregates.graph import KnowledgeAssertion, KnowledgeConflict
from ..value_objects.identity import ConflictId, AssertionState, ConfidenceMetrics

class ConflictResolutionService:
    """Evaluates contradictory assertions to resolve truth."""
    
    def detect_conflict(self, a1: KnowledgeAssertion, a2: KnowledgeAssertion) -> bool:
        # A conflict occurs if subject and object are the same, but the relationship is mutually exclusive
        # For simplicity in this implementation, if they have the same subject/object but different relationships
        if a1.subject_node_id == a2.subject_node_id and a1.object_node_id == a2.object_node_id:
            if a1.relationship_type != a2.relationship_type:
                return True
        return False

    def create_conflict(self, a1: KnowledgeAssertion, a2: KnowledgeAssertion) -> KnowledgeConflict:
        return KnowledgeConflict(
            conflict_id=ConflictId(value=str(uuid.uuid4())),
            domain_id=a1.domain_id,
            assertion_a_id=a1.assertion_id,
            assertion_b_id=a2.assertion_id,
            status="Open"
        )
        
    def resolve_conflict(self, conflict: KnowledgeConflict, a1: KnowledgeAssertion, a2: KnowledgeAssertion) -> KnowledgeConflict:
        # Simple deterministic resolution: Highest adjusted confidence wins
        if a1.confidence.adjusted_confidence > a2.confidence.adjusted_confidence:
            winner = a1.assertion_id
        elif a2.confidence.adjusted_confidence > a1.confidence.adjusted_confidence:
            winner = a2.assertion_id
        else:
            # Escalated if tie
            return KnowledgeConflict(
                conflict_id=conflict.conflict_id,
                domain_id=conflict.domain_id,
                assertion_a_id=conflict.assertion_a_id,
                assertion_b_id=conflict.assertion_b_id,
                status="Escalated"
            )
            
        return KnowledgeConflict(
            conflict_id=conflict.conflict_id,
            domain_id=conflict.domain_id,
            assertion_a_id=conflict.assertion_a_id,
            assertion_b_id=conflict.assertion_b_id,
            status="Resolved",
            resolved_assertion_id=winner
        )

class KnowledgeFreshnessEngine:
    """Evaluates temporal rot and downgrades confidence deterministically."""
    
    def decay_assertion(self, assertion: KnowledgeAssertion, decay_amount: float) -> KnowledgeAssertion:
        new_time_decay = min(1.0, assertion.confidence.time_decay + decay_amount)
        new_adjusted = max(0.0, assertion.confidence.base_confidence - new_time_decay)
        
        new_confidence = ConfidenceMetrics(
            base_confidence=assertion.confidence.base_confidence,
            time_decay=new_time_decay,
            adjusted_confidence=new_adjusted
        )
        
        # Pydantic is frozen, so we construct a new object
        return KnowledgeAssertion(
            assertion_id=assertion.assertion_id,
            domain_id=assertion.domain_id,
            subject_node_id=assertion.subject_node_id,
            relationship_type=assertion.relationship_type,
            object_node_id=assertion.object_node_id,
            state=assertion.state,
            confidence=new_confidence,
            evidence_lineage_ids=assertion.evidence_lineage_ids,
            created_at=assertion.created_at
        )
