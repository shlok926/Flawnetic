import pytest
import uuid
from backend.engines.discovery.fingerprinting.engine import ApplicationFingerprintEngine

@pytest.fixture
def engine():
    return ApplicationFingerprintEngine(str(uuid.uuid4()), str(uuid.uuid4()))

def test_detect_nextjs_cloudflare(engine):
    html = '''
    <html>
    <body class='tw-bg-gray-900'>
        <div id='__next'>Next App</div>
    </body>
    </html>
    '''
    headers = {'Server': 'cloudflare', 'X-Powered-By': 'Next.js'}
    
    result = engine.analyze(html, headers)
    assert result.frontend_framework == 'React'
    assert result.build_tool == 'NextJS'
    assert result.css_framework == 'Tailwind'
    assert result.cdn_waf == 'Cloudflare'
    assert result.confidence.score == 0.8
    
def test_detect_angular(engine):
    html = '<html ng-app="myApp"><body>Hello</body></html>'
    headers = {}
    
    result = engine.analyze(html, headers)
    assert result.frontend_framework == 'Angular'
    assert result.confidence.score == 0.8

def test_malformed_html_attack(engine):
    # Tests that the parser doesn't crash on extremely malformed input
    html = '<html <<<<< >><<<< >< script>alert(1)</script>'
    headers = {}
    
    result = engine.analyze(html, headers)
    # Shouldn't throw an exception, and should return unknown gracefully
    assert result.frontend_framework == 'unknown'

def test_memory_exhaustion_attack(engine):
    # Create an excessively large DOM (over 5MB)
    html = '<div>a</div>' * 1000000 
    headers = {}
    
    result = engine.analyze(html, headers)
    # The engine should truncate it and log a warning in confidence sources
    assert any("truncated for safety" in source for source in result.confidence.sources)
