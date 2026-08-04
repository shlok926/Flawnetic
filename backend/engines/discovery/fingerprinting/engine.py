import re
import uuid
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from models.entities import ConfidenceProvenance
from models.fingerprint import TechnologyFingerprintEntity

logger = logging.getLogger(__name__)

class ApplicationFingerprintEngine:
    """
    Enterprise-grade Technology Detection Engine.
    Operates safely on static DOM and Headers to prevent JS sandbox escapes and infinite loops.
    """
    
    def __init__(self, session_id: str, application_id: str):
        self.session_id = session_id
        self.application_id = application_id
        # Define maximum bytes to read to prevent memory exhaustion (Billion Laughs / Large DOM attacks)
        self.MAX_DOM_BYTES = 5 * 1024 * 1024 # 5MB limit
        
    def _parse_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Detect tech based on headers (X-Powered-By, Server, Cookies)."""
        detected = {"cdn_waf": "unknown", "backend": "unknown"}
        server = headers.get("Server", "").lower()
        x_powered_by = headers.get("X-Powered-By", "").lower()
        
        # CDN / WAF
        if "cloudflare" in server:
            detected["cdn_waf"] = "Cloudflare"
        elif "nginx" in server:
            detected["cdn_waf"] = "Nginx"
            
        # Backend
        if "express" in x_powered_by:
            detected["backend"] = "Node.js (Express)"
        elif "next.js" in x_powered_by:
            detected["backend"] = "NextJS"
            
        return detected

    def _analyze_dom(self, html_content: str) -> Dict[str, Any]:
        """Safely parse DOM using BeautifulSoup to extract framework signatures."""
        detected = {
            "frontend_framework": "unknown",
            "rendering_strategy": "CSR", # Default assumption
            "build_tool": "unknown",
            "css_framework": "unknown",
            "confidence_sources": []
        }
        
        if len(html_content) > self.MAX_DOM_BYTES:
            logger.warning(f"DOM size exceeds {self.MAX_DOM_BYTES} bytes. Truncating to prevent memory exhaustion.")
            html_content = html_content[:self.MAX_DOM_BYTES]
            detected["confidence_sources"].append("Warning: DOM truncated for safety")

        try:
            # fast HTML parser to mitigate malformed HTML attacks
            soup = BeautifulSoup(html_content, "lxml")
        except Exception as e:
            logger.error(f"HTML Parsing failed (possible malformed attack): {e}")
            detected["confidence_sources"].append("Error: Malformed HTML")
            return detected

        # Framework Signatures (IDs, Data attributes)
        # React / NextJS
        if soup.find(id="__next") or soup.find(id="___gatsby"):
            detected["frontend_framework"] = "React"
            detected["rendering_strategy"] = "SSR/SSG"
            detected["confidence_sources"].append("DOM ID __next/___gatsby")
            if soup.find(id="__next"):
                detected["build_tool"] = "NextJS"
                
        # Angular
        elif soup.find(attrs={"ng-version": True}) or soup.find(attrs={"ng-app": True}):
            detected["frontend_framework"] = "Angular"
            detected["confidence_sources"].append("DOM attribute ng-version/ng-app")
            
        # Vue / Nuxt
        elif soup.find(id="__nuxt") or soup.find(attrs={"data-v-app": True}):
            detected["frontend_framework"] = "Vue"
            detected["confidence_sources"].append("DOM attribute data-v-app / __nuxt")
            if soup.find(id="__nuxt"):
                detected["build_tool"] = "Nuxt"

        # CSS Frameworks
        body_classes = " ".join(soup.body.get("class", [])) if soup.body and soup.body.get("class") else ""
        if "tw-" in body_classes or re.search(r"text-\w+ bg-\w+", html_content):
            detected["css_framework"] = "Tailwind"
            detected["confidence_sources"].append("Tailwind CSS class patterns")
        elif "container" in body_classes and "row" in html_content:
            detected["css_framework"] = "Bootstrap"

        # Routing Strategy
        if soup.find("base", href=True):
            detected["confidence_sources"].append("Base href routing detected")
            
        return detected

    def analyze(self, html_content: str, headers: Dict[str, str]) -> TechnologyFingerprintEntity:
        """Main entry point. Analyzes input and generates the immutable Knowledge Contract."""
        # Clean inputs to prevent basic poisoning
        safe_headers = {k: v[:500] for k, v in headers.items()} # truncate long headers
        
        header_tech = self._parse_headers(safe_headers)
        dom_tech = self._analyze_dom(html_content)
        
        # Determine final confidence
        confidence_score = 0.8 if len(dom_tech["confidence_sources"]) > 0 else 0.4
        
        # Map findings to the canonical entity
        entity = TechnologyFingerprintEntity(
            session_id=self.session_id,
            application_id=self.application_id,
            frontend_framework=dom_tech.get("frontend_framework", "unknown"),
            rendering_strategy=dom_tech.get("rendering_strategy", "unknown"),
            css_framework=dom_tech.get("css_framework", "unknown"),
            cdn_waf=header_tech.get("cdn_waf", "unknown"),
            build_tool=dom_tech.get("build_tool", header_tech.get("backend", "unknown")),
            raw_headers=safe_headers,
            confidence=ConfidenceProvenance(
                score=confidence_score,
                sources=dom_tech.get("confidence_sources", []) + ["HTTP Header analysis"]
            )
        )
        return entity
