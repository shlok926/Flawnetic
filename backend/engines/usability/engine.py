import logging
import time
from typing import List, Dict, Any
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class UsabilityEngine:
    """
    Usability, Performance Metrics, and SEO Audit Engine for Flawnetic.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def analyze_page(self, url: str) -> List[Dict[str, Any]]:
        findings = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error", "warning"] else None)

            start_time = time.time()
            try:
                response = await page.goto(url, wait_until="networkidle", timeout=20000)
                load_duration = time.time() - start_time

                # 1. Slow Page Performance Load Check
                if load_duration > 3.0:
                    findings.append({
                        "module": "usability",
                        "title": f"Slow Page Load Performance ({load_duration:.2f}s)",
                        "description": f"Target page '{url}' took {load_duration:.2f} seconds to reach networkidle state (budget target: < 3.0s).",
                        "severity": "medium" if load_duration < 5.0 else "high",
                        "priority": "medium",
                        "steps_to_reproduce": {"step": f"Measure page load timing for {url}"}
                    })

                # 2. Browser Console Errors
                if console_errors:
                    findings.append({
                        "module": "usability",
                        "title": f"Uncaught Browser Console Errors ({len(console_errors)})",
                        "description": f"Page emitted {len(console_errors)} JavaScript errors/warnings. First error: '{console_errors[0][:200]}'",
                        "severity": "medium",
                        "priority": "medium",
                        "steps_to_reproduce": {"errors": console_errors[:5]}
                    })

                # 3. SEO & Usability checks: Missing page title, description, or viewport meta
                title = await page.title()
                if not title or len(title.strip()) == 0:
                    findings.append({
                        "module": "usability",
                        "title": "Missing Document Title Tag",
                        "description": f"Page at {url} does not have a `<title>` tag for usability and SEO.",
                        "severity": "low",
                        "priority": "low",
                        "steps_to_reproduce": {"step": "Inspect <head> element"}
                    })

                meta_desc = await page.locator("meta[name='description']").get_attribute("content") if await page.locator("meta[name='description']").count() > 0 else None
                if not meta_desc:
                    findings.append({
                        "module": "usability",
                        "title": "Missing Meta Description Tag",
                        "description": f"Page at {url} is missing meta description tag for search indexing.",
                        "severity": "low",
                        "priority": "low",
                        "steps_to_reproduce": {"step": "Inspect meta tags"}
                    })

                # 4. Missing Image ALT Attributes
                images_without_alt = await page.locator("img:not([alt]), img[alt='']").count()
                if images_without_alt > 0:
                    findings.append({
                        "module": "usability",
                        "title": f"Images Missing ALT Text ({images_without_alt})",
                        "description": f"Found {images_without_alt} `<img>` elements on {url} lacking descriptive alt attributes.",
                        "severity": "low",
                        "priority": "low",
                        "steps_to_reproduce": {"step": "Locate uncaptioned images"}
                    })

            except Exception as e:
                logger.warning(f"Usability audit failed for {url}: {e}")
            finally:
                await browser.close()

        return findings
