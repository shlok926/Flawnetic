from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.graph import (
    KnowledgeGraph, KnowledgeVersion, SemanticOntology,
    KnowledgeAssertion, KnowledgeInference, KnowledgeConflict,
    KnowledgeDomain
)
from ..value_objects.identity import (
    GraphId, VersionId, OntologyVersionId, DomainId,
    AssertionId, InferenceId, ConflictId
)

class IKnowledgeGraphRepository(ABC):
    @abstractmethod
    async def get_by_id(self, graph_id: GraphId, tenant_id: str) -> Optional[KnowledgeGraph]:
        pass
    
    @abstractmethod
    async def save(self, graph: KnowledgeGraph) -> None:
        pass

class IKnowledgeVersionRepository(ABC):
    @abstractmethod
    async def get_version(self, version_id: VersionId, tenant_id: str) -> Optional[KnowledgeVersion]:
        pass
        
    @abstractmethod
    async def save_version(self, version: KnowledgeVersion) -> None:
        pass

class IOntologyRepository(ABC):
    @abstractmethod
    async def get_ontology(self, ontology_id: OntologyVersionId) -> Optional[SemanticOntology]:
        pass

class IKnowledgeAssertionRepository(ABC):
    @abstractmethod
    async def get_assertion(self, assertion_id: AssertionId, tenant_id: str) -> Optional[KnowledgeAssertion]:
        pass
        
    @abstractmethod
    async def save_assertion(self, assertion: KnowledgeAssertion) -> None:
        pass

class IKnowledgeInferenceRepository(ABC):
    @abstractmethod
    async def save_inference(self, inference: KnowledgeInference) -> None:
        pass

class IKnowledgeConflictRepository(ABC):
    @abstractmethod
    async def save_conflict(self, conflict: KnowledgeConflict) -> None:
        pass

class IKnowledgeProjectionRepository(ABC):
    """The Read-Model Graph Repository for fast traversals."""
    @abstractmethod
    async def get_relationships(self, node_id: str, tenant_id: str) -> List[dict]:
        pass
