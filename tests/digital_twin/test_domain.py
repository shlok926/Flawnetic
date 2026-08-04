import pytest
import uuid
from backend.engines.digital_twin.domain.aggregates.twin import DigitalTwin, TwinVersion, TwinNode, TwinComponent
from backend.engines.digital_twin.domain.value_objects.identity import TwinId, TwinVersionId, ComponentId, NodeId, ConfidenceMetrics, FreshnessMetrics
from backend.engines.digital_twin.domain.services.services import TwinBuilder, TwinVersionService, ChangeDetectionEngine, TwinCertificationService
from backend.engines.digital_twin.domain.services.repositories import IDigitalTwinRepository, ITwinVersionRepository

class MockTwinRepo(IDigitalTwinRepository):
    def __init__(self):
        self.store = {}
    async def get_by_id(self, twin_id, tenant_id):
        return self.store.get(twin_id.value)
    async def get_by_application(self, app_id, tenant_id):
        for t in self.store.values():
            if t.application_id == app_id and t.tenant_id == tenant_id:
                return t
        return None
    async def save(self, twin):
        self.store[twin.twin_id.value] = twin

class MockVersionRepo(ITwinVersionRepository):
    def __init__(self):
        self.store = {}
    async def get_version(self, v_id, tenant_id):
        return self.store.get(v_id.value)
    async def save_version(self, v):
        self.store[v.version_id.value] = v

@pytest.mark.asyncio
async def test_twin_builder_creates_immutable_aggregate():
    repo = MockTwinRepo()
    builder = TwinBuilder(repo)
    
    twin = await builder.create_twin("app-1", "tenant-A")
    assert twin.application_id == "app-1"
    assert twin.tenant_id == "tenant-A"
    
    # Immutability check
    with pytest.raises(Exception): # Pydantic ValidationError for frozen models
        twin.application_id = "hacked"

@pytest.mark.asyncio
async def test_change_detection_engine_finds_diffs():
    engine = ChangeDetectionEngine()
    
    comp1 = TwinComponent(component_id=ComponentId(value="c1"), origin_evidence_id="ev1")
    comp2 = TwinComponent(component_id=ComponentId(value="c2"), origin_evidence_id="ev2")
    
    v1_node = TwinNode(node_id=NodeId(value="n1"), version_id=TwinVersionId(value="v1"), state_id_ref="s1", components=[comp1])
    v2_node = TwinNode(node_id=NodeId(value="n2"), version_id=TwinVersionId(value="v2"), state_id_ref="s2", components=[comp2])
    
    diff = engine.compute_diff([v1_node], [v2_node])
    
    assert diff.severity == "MAJOR"
    assert diff.new_components[0].value == "c2"
    assert diff.removed_components[0].value == "c1"

def test_certification_engine_upgrades_status():
    engine = TwinCertificationService()
    
    v = TwinVersion(
        version_id=TwinVersionId(value="v1"),
        twin_id=TwinId(value="t1"),
        version_name="v1.0",
        status="Validated"
    )
    
    conf = ConfidenceMetrics(structural_confidence=1.0, evidence_confidence=1.0, semantic_confidence=0.9)
    fresh = FreshnessMetrics(temporal_freshness=0.8, velocity_drift=0.1)
    
    v_certified = engine.evaluate_certification(v, conf, fresh)
    assert v_certified.status == "Certified"
