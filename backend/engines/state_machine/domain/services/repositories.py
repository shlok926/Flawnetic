from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.state import ApplicationState, StateTransition
from ..value_objects.identity import StateId, TransitionId, StructuralHash

class IStateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, state_id: StateId) -> Optional[ApplicationState]:
        pass
        
    @abstractmethod
    async def get_by_structural_hash(self, app_id: str, struct_hash: StructuralHash) -> Optional[ApplicationState]:
        pass

    @abstractmethod
    async def save(self, state: ApplicationState) -> None:
        pass

class ITransitionRepository(ABC):
    @abstractmethod
    async def save(self, transition: StateTransition) -> None:
        pass
        
    @abstractmethod
    async def get_outgoing_transitions(self, state_id: StateId) -> List[StateTransition]:
        pass
