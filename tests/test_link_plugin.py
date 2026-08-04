import pytest
import uuid
import asyncio
from backend.engines.discovery.plugins.link import LinkDiscoveryPlugin

@pytest.fixture
def plugin():
    return LinkDiscoveryPlugin(str(uuid.uuid4()), str(uuid.uuid4()), "https://example.com")

@pytest.mark.asyncio
async def test_link_discovery_and_normalization(plugin):
    html = '''
    <html>
        <body>
            <a href="/about">About Us</a>
            <a href="https://example.com/contact/">Contact</a>
            <a href="/about?utm_source=twitter&sort=desc">About Us (Tracked)</a>
            <div role="link" data-href="/features">Features</div>
            <a href="javascript:alert(1)">Click Me</a>
            <a href="mailto:admin@example.com">Email</a>
        </body>
    </html>
    '''
    # Execute the strict lifecycle
    entities = await plugin.execute(html)
    
    urls = [e.url for e in entities]
    
    # 1. Base URL resolution
    assert "https://example.com/about" in urls
    # 2. Trailing slash removal
    assert "https://example.com/contact" in urls
    # 3. Tracking parameter stripping (but keeps valid ones)
    assert "https://example.com/about?sort=desc" in urls
    # 4. Buttons acting as links
    assert "https://example.com/features" in urls
    # 5. Dangerous schemas (javascript, mailto) removed
    assert "javascript:alert(1)" not in urls
    assert "mailto:admin@example.com" not in urls
    
    # 6. Deduplication (the 1st and 3rd link resolve to different paths because of sort=desc, let's test strict dedup)
    html_dupes = '<a href="/about">A</a> <a href="/about/">B</a> <a href="https://example.com/about?utm_medium=cpc">C</a>'
    dupe_entities = await plugin.execute(html_dupes)
    assert len(dupe_entities) == 1
    assert dupe_entities[0].url == "https://example.com/about"
