import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

AXE_CORE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js"

class AccessibilityEngine:
    """
    WCAG 2.1 AA Automated Accessibility Audit Engine using axe-core and Playwright.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scan_page(self, url: str) -> List[Dict[str, Any]]:
        """Injects axe-core script into Playwright page and runs WCAG 2.1 AA audit."""
        findings = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)

                # Inject axe-core library
                await page.add_script_tag(url=AXE_CORE_CDN)

                # Run axe accessibility scan
                results = await page.evaluate("""
                    async () => {
                        if (typeof axe === 'undefined') return { violations: [] };
                        return await axe.run(document, {
                            runOnly: {
                                type: 'tag',
                                values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                            }
                        });
                    }
                """)

                violations = results.get("violations", [])
                for v in violations:
                    impact = v.get("impact", "moderate")
                    severity_map = {"critical": "critical", "serious": "high", "moderate": "medium", "minor": "low"}
                    severity = severity_map.get(impact, "medium")

                    nodes = v.get("nodes", [])
                    selectors = [n.get("target", [""])[0] for n in nodes if n.get("target")]

                    findings.append({
                        "module": "accessibility",
                        "title": f"WCAG Violation: {v.get('help', 'Accessibility Flaw')}",
                        "description": f"{v.get('description', '')}. Impacted elements: {', '.join(selectors[:3])}",
                        "severity": severity,
                        "priority": severity if severity in ["high", "medium", "low"] else "medium",
                        "steps_to_reproduce": {
                            "rule_id": v.get("id"),
                            "help_url": v.get("helpUrl"),
                            "selectors": selectors[:5]
                        }
                    })

            except Exception as e:
                logger.warning(f"Accessibility scan failed for {url}: {e}")
            finally:
                await browser.close()

        return findings
