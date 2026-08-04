import re
from typing import Any, List, Dict, Set
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
import logging

from plugins.base import BaseDiscoveryPlugin
from models.entities import LinkEntity, ConfidenceProvenance
from core.event_bus import event_bus

logger = logging.getLogger(__name__)

class LinkDiscoveryPlugin(BaseDiscoveryPlugin):
    """
    Gold Standard Discovery Plugin for finding navigation paths.
    """
    name = "LinkDiscoveryPlugin"
    version = "1.0.0"

    # Tracking parameters to strip for normalization
    TRACKING_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'ref', 'source'}
    # Malicious schemas to ignore
    DANGEROUS_SCHEMAS = {'javascript', 'data', 'blob', 'file', 'vbscript'}
    
    def __init__(self, session_id: str, application_id: str, base_url: str):
        super().__init__(session_id, application_id)
        self.base_url = base_url

    async def initialize(self, context: Any) -> None:
        """Setup logic."""
        pass

    async def discover(self, context: Any) -> Any:
        """
        Extract raw links from HTML content.
        context is expected to be a string of HTML.
        """
        html_content = str(context)
        # Limit DOM size to 5MB to prevent memory exhaustion
        if len(html_content) > 5 * 1024 * 1024:
            html_content = html_content[:5 * 1024 * 1024]
            
        soup = BeautifulSoup(html_content, "lxml")
        raw_links = []

        # 1. Standard anchors
        for a in soup.find_all('a', href=True):
            raw_links.append({"href": a['href'], "type": "a_tag", "text": a.get_text(strip=True)[:100]})

        # 2. Buttons behaving as links
        for btn in soup.find_all(lambda tag: tag.has_attr('role') and tag['role'] == 'link' and tag.has_attr('data-href')):
            raw_links.append({"href": btn['data-href'], "type": "button_link", "text": btn.get_text(strip=True)[:100]})
            
        # 3. IFrames
        for iframe in soup.find_all('iframe', src=True):
            raw_links.append({"href": iframe['src'], "type": "iframe", "text": "iframe_source"})

        return raw_links

    def validate(self, raw_data: Any) -> bool:
        """Ensure raw_data is a list."""
        return isinstance(raw_data, list)

    def normalize(self, raw_data: List[Dict[str, str]]) -> List[LinkEntity]:
        """
        Normalize URLs and remove duplicates/dangerous schemas.
        """
        seen_urls: Set[str] = set()
        entities: List[LinkEntity] = []

        for item in raw_data:
            raw_href = item['href'].strip()
            if not raw_href or raw_href.startswith('#'): # Skip pure fragment links for now
                continue

            # Resolve relative URLs
            try:
                full_url = urljoin(self.base_url, raw_href)
                parsed = urlparse(full_url)
            except ValueError:
                continue # Malformed URL

            # Security: Filter dangerous schemas (javascript:, data:, etc.)
            if parsed.scheme.lower() in self.DANGEROUS_SCHEMAS:
                continue

            # Ignore mailto/tel
            if parsed.scheme.lower() in {'mailto', 'tel'}:
                continue

            # Normalize: strip tracking params, fragments, trailing slashes
            query_pairs = parsed.query.split('&') if parsed.query else []
            clean_query = '&'.join([q for q in query_pairs if q.split('=')[0] not in self.TRACKING_PARAMS])
            
            clean_path = parsed.path.rstrip('/')
            if clean_path == '':
                clean_path = '/'
                
            normalized_url = urlunparse((parsed.scheme, parsed.netloc, clean_path, parsed.params, clean_query, ''))
            
            # Deduplication
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            entity = LinkEntity(
                session_id=self.session_id,
                application_id=self.application_id,
                url=normalized_url,
                link_type=item['type'],
                text=item['text'] or "unknown",
                confidence=ConfidenceProvenance(score=0.9, sources=["DOM static analysis"])
            )
            entities.append(entity)

        return entities

    async def cleanup(self) -> None:
        """Cleanup logic."""
        pass
