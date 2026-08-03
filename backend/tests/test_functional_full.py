import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from engines.functional.engine import FunctionalEngine

@pytest.mark.asyncio
async def test_functional_check_api_response():
    engine = FunctionalEngine()
    
    # HTTP 200 should not record a finding
    res_200 = MagicMock(status=200, url="https://example.com/api/data")
    await engine.check_api_response(res_200)
    assert len(engine.findings) == 0
    
    # HTTP 500 should record a High severity finding
    res_500 = MagicMock(status=500, url="https://example.com/api/broken")
    await engine.check_api_response(res_500)
    assert len(engine.findings) == 1
    assert engine.findings[0]["title"] == "API Internal Server Error (500)"

@pytest.mark.asyncio
async def test_functional_submit_form_strategies():
    engine = FunctionalEngine()
    
    # Strategy 1: Submit button in form
    mock_btn = AsyncMock()
    mock_btn.is_visible.return_value = True
    
    mock_form = AsyncMock()
    mock_form.query_selector.return_value = mock_btn
    
    mock_form_handle = MagicMock()
    mock_form_handle.as_element.return_value = mock_form
    
    mock_input = AsyncMock()
    mock_input.evaluate_handle.return_value = mock_form_handle
    
    mock_page = AsyncMock()
    await engine._submit_form(mock_page, mock_input)
    assert mock_btn.click.called

@pytest.mark.asyncio
async def test_functional_submit_form_strategy_enter_key():
    engine = FunctionalEngine()
    
    # Strategy 3: Enter key fallback when no form/buttons exist
    mock_input = AsyncMock()
    mock_input.evaluate_handle.return_value = None
    
    mock_page = AsyncMock()
    mock_page.query_selector.return_value = None
    
    await engine._submit_form(mock_page, mock_input)
    assert mock_input.press.called

@pytest.mark.asyncio
@patch("engines.functional.engine.async_playwright")
async def test_functional_analyze_and_test_full(mock_async_playwright):
    engine = FunctionalEngine()
    
    # Mocking form GET login vulnerability and dead links
    mock_form = AsyncMock()
    mock_form.get_attribute.side_effect = lambda attr: "/login" if attr == "action" else "GET"
    
    mock_input = AsyncMock()
    mock_input.is_visible.return_value = True
    mock_input.is_disabled.return_value = False
    mock_input.get_attribute.side_effect = lambda attr: "username" if attr == "name" else "text"
    
    mock_locator = AsyncMock()
    mock_locator.all.return_value = [mock_input]
    mock_locator.count.return_value = 2 # Dead links count
    
    mock_page = AsyncMock()
    mock_page.url = "https://example.com/login"
    mock_page.content.return_value = "<html><body>You have an error in your SQL syntax</body></html>"
    mock_page.evaluate.return_value = False
    
    mock_page_sync = MagicMock()
    mock_page_sync.url = "https://example.com/login"
    mock_page_sync.goto = mock_page.goto
    mock_page_sync.content = mock_page.content
    mock_page_sync.evaluate = mock_page.evaluate
    mock_page_sync.wait_for_load_state = mock_page.wait_for_load_state
    mock_page_sync.close = mock_page.close
    mock_page_sync.on = MagicMock()
    
    def locator_side_effect(selector):
        loc = AsyncMock()
        if selector == "form":
            loc.all.return_value = [mock_form]
            loc.count.return_value = 1
        elif selector == "a[href=''], a[href='#']":
            loc.count.return_value = 2
            loc.all.return_value = []
        else:
            loc.all.return_value = [mock_input]
            loc.count.return_value = 1
        return loc

    mock_page_sync.locator.side_effect = locator_side_effect
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page_sync
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.analyze_and_test("https://example.com/login")
    assert isinstance(findings, list)
    assert any(f["title"] == "Insecure Login Form (GET)" for f in findings)
    assert any(f["title"] == "Possible SQL Injection Vulnerability" for f in findings)
    assert any(f["title"] == "Empty or Dead Links Detected" for f in findings)

@pytest.mark.asyncio
@patch("engines.functional.engine.async_playwright")
async def test_functional_xss_execution_and_page_error(mock_async_playwright):
    engine = FunctionalEngine()
    
    mock_page = AsyncMock()
    mock_page.goto.side_effect = RuntimeError("Playwright Timeout Navigation Error")
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.analyze_and_test("https://example.com/error")
    assert len(findings) == 1
    assert findings[0]["title"] == "Functional Testing Page Load Error"

@pytest.mark.asyncio
@patch("engines.functional.engine.async_playwright")
async def test_functional_xss_detection_variations(mock_async_playwright):
    engine = FunctionalEngine()
    
    mock_input = AsyncMock()
    mock_input.is_visible.return_value = True
    mock_input.is_disabled.return_value = False
    mock_input.get_attribute.side_effect = lambda attr: "comment" if attr == "name" else "text"
    
    mock_page = AsyncMock()
    mock_page.url = "https://example.com/blog"
    mock_page.content.return_value = "<html><body><script>window.__flawnetic_xss__=1</script></body></html>"
    mock_page.evaluate.return_value = True # Executed XSS
    
    mock_page_sync = MagicMock()
    mock_page_sync.url = "https://example.com/blog"
    mock_page_sync.goto = mock_page.goto
    mock_page_sync.content = mock_page.content
    mock_page_sync.evaluate = mock_page.evaluate
    mock_page_sync.wait_for_load_state = mock_page.wait_for_load_state
    mock_page_sync.close = mock_page.close
    mock_page_sync.on = MagicMock()
    
    def locator_side_effect(selector):
        loc = AsyncMock()
        if selector == "form":
            loc.all.return_value = []
            loc.count.return_value = 0
        elif selector == "a[href=''], a[href='#']":
            loc.count.return_value = 0
            loc.all.return_value = []
        else:
            loc.all.return_value = [mock_input]
            loc.count.return_value = 1
        return loc

    mock_page_sync.locator.side_effect = locator_side_effect
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page_sync
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    findings = await engine.analyze_and_test("https://example.com/blog")
    assert isinstance(findings, list)
    assert any(f["title"] == "Cross-Site Scripting (XSS) Execution" for f in findings)
