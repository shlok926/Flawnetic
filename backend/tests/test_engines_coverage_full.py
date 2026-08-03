import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from engines.security.engine import SecurityEngine
from engines.accessibility.engine import AccessibilityEngine
from engines.visual.engine import VisualEngine
from engines.usability.engine import UsabilityEngine
from engines.ai.analyzer import AIAnalyzer

@pytest.mark.asyncio
async def test_security_engine_check_zap_status_offline():
    engine = SecurityEngine(zap_base_url="http://localhost:9999")
    status = await engine._check_zap_status()
    assert status is False

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_security_engine_scan_headers(mock_get):
    mock_resp = MagicMock()
    mock_resp.headers = {
        "server": "Apache/2.4.41",
        "set-cookie": "session_id=123"
    }
    mock_resp.cookies = {"session_id": "123"}
    mock_get.return_value = mock_resp

    engine = SecurityEngine()
    findings = await engine.scan_security_headers("https://example.com")
    assert isinstance(findings, list)
    assert any(f["title"] == "Missing HSTS Header" for f in findings)
    assert any("Server Information Disclosure" in f["title"] for f in findings)

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_security_engine_dast_scan_fallback(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.headers = {}
    mock_resp.cookies = {}
    mock_get.return_value = mock_resp

    engine = SecurityEngine()
    findings = await engine.run_zap_dast_scan("https://example.com")
    assert isinstance(findings, list)

@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_security_engine_zap_online_alerts(mock_get):
    mock_version_resp = MagicMock(status_code=200)
    mock_alerts_resp = MagicMock(
        status_code=200, 
        json=lambda: {"alerts": [{"name": "SQL Injection DAST", "description": "ZAP found SQLi", "risk": "High", "url": "https://example.com", "param": "id"}]}
    )
    mock_get.side_effect = [mock_version_resp, MagicMock(status_code=200), mock_alerts_resp, MagicMock(headers={}, cookies={})]

    engine = SecurityEngine()
    findings = await engine.run_zap_dast_scan("https://example.com")
    assert isinstance(findings, list)
    assert any(f["title"] == "SQL Injection DAST" for f in findings)

@pytest.mark.asyncio
@patch("engines.accessibility.engine.async_playwright")
async def test_accessibility_engine_scan_page(mock_async_playwright):
    engine = AccessibilityEngine()
    
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = {
        "violations": [
            {"id": "color-contrast", "impact": "serious", "help": "Elements must have sufficient color contrast", "nodes": [{"html": "<button>Submit</button>"}]}
        ]
    }
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.scan_page("https://example.com")
    assert isinstance(findings, list)
    assert len(findings) == 1
    assert findings[0]["title"] == "WCAG Violation: Elements must have sufficient color contrast"

@pytest.mark.asyncio
@patch("engines.visual.engine.async_playwright")
async def test_visual_engine_audit_rendering(mock_async_playwright):
    engine = VisualEngine(output_dir="/tmp/flawnetic-test-vis")
    
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = 0
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_playwright.firefox.launch.return_value = mock_browser
    mock_playwright.webkit.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.audit_visual_rendering("https://example.com")
    assert isinstance(findings, list)

@pytest.mark.asyncio
@patch("engines.usability.engine.async_playwright")
async def test_usability_engine_analyze_page(mock_async_playwright):
    engine = UsabilityEngine()
    
    mock_locator = AsyncMock()
    mock_locator.count.return_value = 0
    
    mock_page = MagicMock()
    mock_page.title = AsyncMock(return_value="")
    mock_page.goto = AsyncMock()
    mock_page.evaluate = AsyncMock(side_effect=[
        "utf-8",
        True,
        1.5,
        15,
        150
    ])
    mock_page.locator.return_value = mock_locator
    mock_page.on = MagicMock()
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.analyze_page("https://example.com")
    assert isinstance(findings, list)
    assert any(f["title"] == "Missing Document Title Tag" for f in findings)

@patch("engines.ai.analyzer.AsyncAnthropic")
def test_ai_analyzer_analyze_finding_fallback(mock_async_anthropic):
    analyzer = AIAnalyzer()
    assert analyzer is not None
