from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.twin import DigitalTwin, TwinVersion, TwinNode, TwinChangeSet
from ..value_objects.identity import TwinId, TwinVersionId

class IDigitalTwinRepository(ABC):
    @abstractmethod
    async def get_by_id(self, twin_id: TwinId, tenant_id: str) -> Optional[DigitalTwin]:
        pass
        
    @abstractmethod
    async def get_by_application(self, application_id: str, tenant_id: str) -> Optional[DigitalTwin]:
        pass

    @abstractmethod
    async def save(self, twin: DigitalTwin) -> None:
        pass

class ITwinVersionRepository(ABC):
    @abstractmethod
    async def get_version(self, version_id: TwinVersionId, tenant_id: str) -> Optional[TwinVersion]:
        pass
        
    @abstractmethod
    async def save_version(self, version: TwinVersion) -> None:
        pass

class ITwinProjectionRepository(ABC):
    """The Read-Model Graph Repository for AI/Test TQL Engine."""
    @abstractmethod
    async def get_nodes(self, version_id: TwinVersionId, tenant_id: str) -> List[TwinNode]:
        pass
        
    @abstractmethod
    async def save_node(self, node: TwinNode, tenant_id: str) -> None:
        pass

    @abstractmethod
    async def save_nodes_bulk(self, nodes: List[TwinNode], tenant_id: str) -> None:
        pass
