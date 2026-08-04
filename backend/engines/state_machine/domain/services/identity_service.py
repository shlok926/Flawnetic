import uuid
from typing import Optional
from bs4 import BeautifulSoup
import logging
from ..value_objects.identity import StructuralHash, StateId, ConfidenceScore
from ..aggregates.state import ApplicationState
from .repositories import IStateRepository

logger = logging.getLogger(__name__)

class StateIdentityService:
    """Domain service responsible for resolving State Identity from Raw DOM."""
    
    def __init__(self, state_repo: IStateRepository):
        self.state_repo = state_repo
        
    def canonicalize_dom(self, raw_html: str) -> str:
        """
        Implementation of the Formal Structural Hash Pipeline.
        1. Sanitize HTML
        2. Remove Dynamic IDs
        3. Remove Timestamps/Text Nodes
        """
        if not raw_html:
            return ""
            
        soup = BeautifulSoup(raw_html, "lxml")
        
        # Remove scripts and styles
        for tag in soup(["script", "style"]):
            tag.decompose()
            
        from bs4 import NavigableString
        
        # Strip dynamic IDs (e.g. rand_123)
        for tag in soup.find_all(True):
            if tag.has_attr("id") and "rand" in tag["id"]:
                del tag["id"]
                
        # Strip text nodes while preserving child tags
        for element in soup.find_all(string=True):
            if isinstance(element, NavigableString):
                element.extract()
                
        # Return canonicalized string
        return str(soup)

    async def resolve_identity(self, app_id: str, raw_html: str) -> ApplicationState:
        """Resolves identity. Returns existing state or creates a new Discovered state."""
        canonical_dom = self.canonicalize_dom(raw_html)
        struct_hash = StructuralHash.generate(canonical_dom)
        
        existing_state = await self.state_repo.get_by_structural_hash(app_id, struct_hash)
        
        if existing_state:
            return existing_state
            
        new_state = ApplicationState(
            state_id=StateId(value=str(uuid.uuid4())),
            application_id=app_id,
            structural_hash=struct_hash,
            confidence=ConfidenceScore(value=0.2), # Discovered confidence
            status="Discovered"
        )
        return new_state
