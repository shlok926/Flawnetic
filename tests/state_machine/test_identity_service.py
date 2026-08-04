import pytest
import uuid
from backend.engines.state_machine.domain.services.identity_service import StateIdentityService
from backend.engines.state_machine.domain.services.repositories import IStateRepository
from backend.engines.state_machine.domain.value_objects.identity import StateId, StructuralHash
from backend.engines.state_machine.domain.aggregates.state import ApplicationState

class MockStateRepository(IStateRepository):
    def __init__(self):
        self.store = {}
        
    async def get_by_id(self, state_id: StateId):
        return self.store.get(state_id.value)
        
    async def get_by_structural_hash(self, app_id: str, struct_hash: StructuralHash):
        for state in self.store.values():
            if state.structural_hash.hash_value == struct_hash.hash_value and state.application_id == app_id:
                return state
        return None
        
    async def save(self, state: ApplicationState):
        self.store[state.state_id.value] = state

@pytest.fixture
def identity_service():
    repo = MockStateRepository()
    return StateIdentityService(repo)

@pytest.mark.asyncio
async def test_canonicalize_dom_strips_text_and_dynamic_ids(identity_service):
    html1 = '<div id="rand_123"><h2>Product 1</h2></div>'
    html2 = '<div id="rand_999"><h2>Product 2</h2></div>'
    
    can1 = identity_service.canonicalize_dom(html1)
    can2 = identity_service.canonicalize_dom(html2)
    
    assert can1 == can2 # Identical structure!

@pytest.mark.asyncio
async def test_resolve_identity_creates_new_state(identity_service):
    app_id = str(uuid.uuid4())
    html = '<div>Login</div>'
    
    state = await identity_service.resolve_identity(app_id, html)
    assert state.status == "Discovered"
    assert state.confidence.value == 0.2
    
    # Save it to repo
    await identity_service.state_repo.save(state)
    
    # Resolve again with same structure but different text
    html2 = '<div>Logout</div>'
    state2 = await identity_service.resolve_identity(app_id, html2)
    
    assert state.state_id.value == state2.state_id.value # Duplicate avoided
