import asyncio
import logging
import socket
import ipaddress
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, urljoin
import os
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext, Browser, Error
from .models import SiteGraph, PageNode, ElementInfo
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FlawneticCrawler:
    """Autonomous async crawler for Flawnetic using Playwright."""

    def __init__(
        self,
        base_url: str,
        max_pages: int = 50,
        max_depth: int = 4,
        screenshot_dir: str = "/tmp/flawnetic-screenshots",
        headless: bool = True,
        browser: str = "chromium"
    ):
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc.split(':')[0]
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.screenshot_dir = Path(screenshot_dir)
        self.headless = headless
        self.browser_name = browser
        self.visited_urls = set()
        
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        
        # Remove utm_ params
        query_params = parse_qsl(parsed.query)
        filtered_query = [(k, v) for k, v in query_params if not k.startswith('utm_')]
        query = urlencode(filtered_query)
        
        # Ignore fragment
        normalized = urlunparse((scheme, netloc, path, parsed.params, query, ''))
        return normalized

    def _is_same_origin(self, url: str) -> bool:
        parsed = urlparse(url)
        # Compare scheme and hostname, allowing empty scheme (relative urls) which are resolved by urljoin anyway
        base_parsed = urlparse(self.base_url)
        if parsed.netloc and parsed.netloc.lower() != base_parsed.netloc.lower():
            return False
        if parsed.scheme and parsed.scheme.lower() not in ('http', 'https'):
            return False
        return True

    def _is_private_ip(self, hostname: str) -> bool:
        try:
            if hostname == "localhost":
                return True
            ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except Exception:
            return False

    async def extract_elements(self, page: Page) -> list[ElementInfo]:
        elements = []
        
        # Helper to check visibility and add
        async def add_element(locator, element_type, extract_attrs=None):
            count = await locator.count()
            for i in range(count):
                el = locator.nth(i)
                if not await el.is_visible():
                    continue
                
                label = ""
                # Try getting inner text
                inner_text = await el.inner_text()
                if inner_text:
                    label = inner_text.strip()
                else:
                    label = await el.get_attribute("aria-label") or ""

                input_type = await el.get_attribute("type") if element_type == "input" else None
                is_req = await el.get_attribute("required") is not None
                href = await el.get_attribute("href") if element_type == "link" else None
                
                elements.append(ElementInfo(
                    selector=f"<{element_type}>", # Basic selector rep
                    element_type=element_type,
                    label=label[:100], # Truncate for sanity
                    input_type=input_type,
                    is_required=is_req,
                    href=href
                ))

        # Buttons
        await add_element(page.locator("button"), "button")
        await add_element(page.locator("[role='button']"), "button")
        
        # Inputs
        await add_element(page.locator("input"), "input")
        
        # Textareas
        await add_element(page.locator("textarea"), "textarea")
        
        # Selects
        await add_element(page.locator("select"), "dropdown")
        
        # Links (same origin only)
        count = await page.locator("a").count()
        for i in range(count):
            el = page.locator("a").nth(i)
            if not await el.is_visible():
                continue
            href = await el.get_attribute("href")
            if href:
                abs_url = urljoin(page.url, href)
                if self._is_same_origin(abs_url):
                    label = (await el.inner_text() or await el.get_attribute("aria-label") or "").strip()
                    elements.append(ElementInfo(
                        selector="<a>",
                        element_type="link",
                        label=label[:100],
                        input_type=None,
                        is_required=False,
                        href=abs_url
                    ))
        
        # Forms
        count = await page.locator("form").count()
        for i in range(count):
            el = page.locator("form").nth(i)
            if not await el.is_visible():
                continue
            action = await el.get_attribute("action") or ""
            method = await el.get_attribute("method") or "get"
            elements.append(ElementInfo(
                selector="<form>",
                element_type="form",
                label=f"{method.upper()} {action}",
                input_type=None,
                is_required=False,
                href=None
            ))
            
        return elements

    async def discover_links(self, page: Page, base_url: str) -> list[str]:
        links = []
        locators = await page.locator("a[href]").all()
        for loc in locators:
            href = await loc.get_attribute("href")
            if href:
                abs_url = urljoin(page.url, href)
                norm_url = self._normalize_url(abs_url)
                if self._is_same_origin(norm_url) and not norm_url.startswith("javascript:"):
                    links.append(norm_url)
        return list(set(links))

    async def crawl(self) -> SiteGraph:
        start_time = time.time()
        
        # Validate base url
        parsed_base = urlparse(self.base_url)
        if self._is_private_ip(parsed_base.netloc.split(':')[0]):
            logger.warning(f"Base URL {self.base_url} resolves to a private IP. SSRF protection prevents crawling.")
            return SiteGraph(base_url=self.base_url, pages=[], total_pages=0, max_depth_reached=0, crawl_duration_seconds=0.0)

        pages = []
        queue = [(self.base_url, 0, "root")] # url, depth, discovered_via
        self.visited_urls.add(self.base_url)
        max_depth_reached = 0

        async with async_playwright() as p:
            browser = None
            if self.browser_name == "chromium":
                browser = await p.chromium.launch(headless=self.headless)
            elif self.browser_name == "firefox":
                browser = await p.firefox.launch(headless=self.headless)
            elif self.browser_name == "webkit":
                browser = await p.webkit.launch(headless=self.headless)
            else:
                browser = await p.chromium.launch(headless=self.headless)

            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Flawnetic/1.0 QA Bot (authorized testing)",
                record_har_path=str(self.screenshot_dir / "crawl.har"),
                ignore_https_errors=True
            )

            try:
                while queue and len(pages) < self.max_pages:
                    url, depth, discovered_via = queue.pop(0)
                    
                    if depth > self.max_depth:
                        continue
                        
                    max_depth_reached = max(max_depth_reached, depth)
                    
                    logger.info(f"Crawling: {url} (Depth: {depth})")
                    
                    page = await context.new_page()
                    
                    http_status = 0
                    def handle_response(response):
                        nonlocal http_status
                        if response.url == url or response.url == url + "/":
                            http_status = response.status
                    page.on("response", handle_response)

                    title = ""
                    screenshot_path = None
                    elements = []
                    
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        title = await page.title()
                        
                        safe_filename = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_").replace("?", "_").replace("=", "_").replace("&", "_")[:50]
                        screenshot_file = f"{safe_filename}_{int(time.time())}.png"
                        screenshot_path_obj = self.screenshot_dir / screenshot_file
                        
                        await page.screenshot(path=str(screenshot_path_obj), full_page=True)
                        screenshot_path = str(screenshot_path_obj)
                        
                        elements = await self.extract_elements(page)
                        
                        # Discover links
                        new_links = await self.discover_links(page, self.base_url)
                        for link in new_links:
                            if link not in self.visited_urls:
                                parsed_link = urlparse(link)
                                if self._is_private_ip(parsed_link.netloc.split(':')[0]):
                                    logger.warning(f"Skipping private IP link: {link}")
                                    continue
                                
                                self.visited_urls.add(link)
                                if depth + 1 <= self.max_depth:
                                    queue.append((link, depth + 1, url))
                                    
                    except Error as e:
                        logger.warning(f"Error crawling {url}: {e}")
                    except Exception as e:
                        logger.warning(f"Unexpected error crawling {url}: {e}")
                    finally:
                        logger.info(f"Finished {url} - Status: {http_status}, Elements: {len(elements)}")
                        pages.append(PageNode(
                            url=url,
                            title=title,
                            http_status=http_status,
                            depth=depth,
                            discovered_via=discovered_via,
                            screenshot_path=screenshot_path,
                            elements=elements
                        ))
                        await page.close()
            finally:
                await context.close()
                await browser.close()
                
        duration = time.time() - start_time
        return SiteGraph(
            base_url=self.base_url,
            pages=pages,
            total_pages=len(pages),
            max_depth_reached=max_depth_reached,
            crawl_duration_seconds=duration
        )
