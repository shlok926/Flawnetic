import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from engines.crawler.crawler import FlawneticCrawler
from engines.crawler.models import SiteGraph, PageNode, ElementInfo

def test_crawler_normalize_url():
    crawler = FlawneticCrawler(base_url="https://example.com/")
    
    assert crawler._normalize_url("https://EXAMPLE.com/path/?utm_source=google&q=1#frag") == "https://example.com/path?q=1"
    assert crawler._normalize_url("http://example.com/") == "http://example.com/"

def test_crawler_is_same_origin():
    crawler = FlawneticCrawler(base_url="https://example.com")
    
    assert crawler._is_same_origin("https://example.com/login") is True
    assert crawler._is_same_origin("https://otherdomain.com/login") is False
    assert crawler._is_same_origin("ftp://example.com/file") is False

def test_crawler_is_private_ip():
    crawler = FlawneticCrawler(base_url="https://example.com")
    
    assert crawler._is_private_ip("localhost") is True
    assert crawler._is_private_ip("127.0.0.1") is True
    assert crawler._is_private_ip("8.8.8.8") is False

@pytest.mark.asyncio
async def test_crawler_ssrf_private_ip_blocking():
    crawler = FlawneticCrawler(base_url="http://127.0.0.1:8000")
    site_graph = await crawler.crawl()
    
    assert isinstance(site_graph, SiteGraph)
    assert site_graph.total_pages == 0
    assert site_graph.crawl_duration_seconds == 0.0

@pytest.mark.asyncio
async def test_crawler_discover_links():
    crawler = FlawneticCrawler(base_url="https://example.com")
    
    mock_locator = AsyncMock()
    mock_loc1 = AsyncMock()
    mock_loc1.get_attribute.return_value = "/about"
    mock_loc2 = AsyncMock()
    mock_loc2.get_attribute.return_value = "https://external.com"
    
    mock_locator.all.return_value = [mock_loc1, mock_loc2]
    
    mock_page = MagicMock()
    mock_page.url = "https://example.com/"
    mock_page.locator.return_value = mock_locator
    
    discovered = await crawler.discover_links(mock_page, "https://example.com")
    assert isinstance(discovered, list)
    assert "https://example.com/about" in discovered
    assert "https://external.com" not in discovered

@pytest.mark.asyncio
async def test_crawler_extract_elements():
    crawler = FlawneticCrawler(base_url="https://example.com")
    
    mock_element = AsyncMock()
    mock_element.is_visible.return_value = True
    mock_element.inner_text.return_value = "Submit Button"
    mock_element.get_attribute.side_effect = lambda attr: "submit" if attr == "type" else None
    
    mock_locator = AsyncMock()
    mock_locator.count.return_value = 1
    mock_locator.nth = MagicMock(return_value=mock_element)
    
    mock_page = MagicMock()
    mock_page.url = "https://example.com"
    mock_page.locator.return_value = mock_locator
    
    elements = await crawler.extract_elements(mock_page)
    assert isinstance(elements, list)
    assert len(elements) > 0

@pytest.mark.asyncio
@patch("engines.crawler.crawler.async_playwright")
async def test_crawler_full_crawl_execution(mock_async_playwright):
    crawler = FlawneticCrawler(base_url="https://example.com", max_pages=1)
    
    mock_page = AsyncMock()
    mock_page.url = "https://example.com"
    mock_page.title.return_value = "Example Title"
    
    mock_locator = AsyncMock()
    mock_locator.count.return_value = 0
    mock_locator.all.return_value = []
    
    mock_page_sync = MagicMock()
    mock_page_sync.url = "https://example.com"
    mock_page_sync.goto = mock_page.goto
    mock_page_sync.title = mock_page.title
    mock_page_sync.screenshot = mock_page.screenshot
    mock_page_sync.close = mock_page.close
    mock_page_sync.on = MagicMock()
    mock_page_sync.locator.return_value = mock_locator
    
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page_sync
    
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_async_playwright.return_value.__aenter__.return_value = mock_playwright

    site_graph = await crawler.crawl()
    assert isinstance(site_graph, SiteGraph)
    assert site_graph.total_pages == 1
    assert site_graph.pages[0].title == "Example Title"
