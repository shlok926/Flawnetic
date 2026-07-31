import logging
from typing import List, Dict, Any
from pathlib import Path
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

VIEWPORT_PRESETS = [
    {"name": "Desktop (1920x1080)", "width": 1920, "height": 1080, "is_mobile": False},
    {"name": "Tablet (768x1024)", "width": 768, "height": 1024, "is_mobile": False},
    {"name": "Mobile Portrait (390x844 - iPhone 14)", "width": 390, "height": 844, "is_mobile": True}
]

class VisualEngine:
    """
    Cross-Browser & Multi-Viewport Visual Rendering Audit Engine for Flawnetic.
    Tests page layout across Chromium, Firefox, WebKit and responsive viewports.
    """

    def __init__(self, headless: bool = True, output_dir: str = "/tmp/flawnetic-visual"):
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def audit_visual_rendering(self, url: str) -> List[Dict[str, Any]]:
        findings = []
        async with async_playwright() as p:
            for browser_type in [p.chromium, p.firefox, p.webkit]:
                browser_name = browser_type.name
                try:
                    browser = await browser_type.launch(headless=self.headless)
                    for vp in VIEWPORT_PRESETS:
                        context = await browser.new_context(
                            viewport={"width": vp["width"], "height": vp["height"]},
                            is_mobile=vp["is_mobile"],
                            ignore_https_errors=True
                        )
                        page = await context.new_page()

                        try:
                            response = await page.goto(url, wait_until="networkidle", timeout=15000)
                            status = response.status if response else 0

                            # Detect overflow/scroll issues (horizontal scrollbar on mobile)
                            has_horizontal_overflow = await page.evaluate("""
                                () => document.documentElement.scrollWidth > window.innerWidth
                            """)

                            if vp["is_mobile"] and has_horizontal_overflow:
                                findings.append({
                                    "module": "visual",
                                    "title": f"Responsive Layout Overflow ({browser_name.upper()} - {vp['name']})",
                                    "description": f"Page content at {url} exceeds viewport width on {vp['name']}, causing undesirable horizontal scrolling.",
                                    "severity": "medium",
                                    "priority": "medium",
                                    "steps_to_reproduce": {"browser": browser_name, "viewport": vp["name"]}
                                })

                        except Exception as e:
                            logger.warning(f"Visual audit failed on {browser_name} ({vp['name']}) for {url}: {e}")
                        finally:
                            await context.close()

                    await browser.close()
                except Exception as e:
                    logger.warning(f"Browser launch failed for {browser_type.name}: {e}")

        return findings
