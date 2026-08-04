from typing import Dict, List, Any
from pydantic import Field, ConfigDict
from .entities import BaseDiscoveryEntity

class TechnologyFingerprintEntity(BaseDiscoveryEntity):
    """
    Knowledge Contract for Application Fingerprinting.
    Represents the detected technology stack of the target application.
    """
    model_config = ConfigDict(frozen=True)
    entity_type: str = "TechnologyFingerprint"
    
    frontend_framework: str = Field("unknown", description="e.g., React, Angular, Vue")
    rendering_strategy: str = Field("unknown", description="e.g., CSR, SSR, SSG")
    routing_strategy: str = Field("unknown", description="e.g., History API, Hash")
    state_management: str = Field("unknown", description="e.g., Redux, MobX, Context")
    build_tool: str = Field("unknown", description="e.g., Webpack, Vite")
    css_framework: str = Field("unknown", description="e.g., Tailwind, Bootstrap")
    cdn_waf: str = Field("unknown", description="e.g., Cloudflare, Akamai")
    apis_detected: List[str] = Field(default_factory=list, description="e.g., REST, GraphQL, WebSocket")
    auth_mechanisms: List[str] = Field(default_factory=list, description="e.g., JWT, Cookie, OAuth")
    analytics: List[str] = Field(default_factory=list, description="e.g., Google Analytics, Segment")
    pwa_features: List[str] = Field(default_factory=list, description="e.g., Service Workers, Manifest")
    browser_capabilities: List[str] = Field(default_factory=list, description="e.g., Push, WebAuthn, IndexedDB")
    
    raw_headers: Dict[str, str] = Field(default_factory=dict, description="Captured headers used for inference")
    raw_scripts: List[str] = Field(default_factory=list, description="Script URLs or inline patterns found")
