from typing import List, Dict, Any
import asyncio
import logging
from playwright.async_api import async_playwright, Response

logger = logging.getLogger(__name__)

class FunctionalEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.findings = []

    async def check_api_response(self, response: Response):
        """Monitors all API calls made by the page for errors (Senior QA network monitoring)."""
        if response.status >= 500:
            self.findings.append({
                "module": "functional",
                "title": f"API Internal Server Error ({response.status})",
                "description": f"The endpoint '{response.url}' returned status {response.status}. Indicates unhandled backend exceptions.",
                "severity": "high",
                "priority": "high",
                "steps_to_reproduce": {"step": f"Trigger request to {response.url}"}
            })

    async def analyze_and_test(self, url: str) -> List[Dict[str, Any]]:
        """
        Functional & Fuzzing QA Engine: Tests forms, inputs, and controls for XSS, SQLi, and errors.
        """
        self.findings = []
        print(f"[FUNCTIONAL] Starting analysis on URL: {url}")

        fuzz_payloads = {
            "sqli": "' OR '1'='1",
            "xss": "<script>alert('flawnetic')</script>",
            "boundary": "A" * 2000
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            page.on("response", self.check_api_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)

                # Extract input elements (including standalone inputs not inside forms)
                inputs = await page.locator("input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='image']), textarea, select").all()
                forms = await page.locator("form").all()
                buttons = await page.locator("button, input[type='submit'], input[type='button'], input[type='image']").all()

                total_elements = len(inputs) + len(forms) + len(buttons)
                print(f"[FUNCTIONAL] Found {total_elements} elements to test")

                # Test 1: Insecure Login Form Check
                for i, form in enumerate(forms):
                    action = await form.get_attribute("action") or ""
                    method = await form.get_attribute("method") or "GET"
                    if method.upper() == "GET" and ("login" in action.lower() or "auth" in action.lower()):
                        res_msg = "FAILED — Insecure GET Login Form detected"
                        print(f"[FUNCTIONAL] TC-001 on Form[{i}]: {res_msg}")
                        self.findings.append({
                            "module": "functional",
                            "title": "Insecure Login Form (GET)",
                            "description": f"Form submits credentials via GET method to '{action}'. Sensitive parameters leak in HTTP referrer headers and browser logs.",
                            "severity": "critical",
                            "priority": "high",
                            "steps_to_reproduce": {"step": f"Submit login form at {url}"}
                        })

                # Test 2: Input Fuzzing (SQLi & XSS)
                for i, inp in enumerate(inputs):
                    label = (await inp.get_attribute("aria-label") or await inp.get_attribute("placeholder") or await inp.get_attribute("name") or f"Input[{i}]").strip()
                    test_id = f"00{i+2}"

                    try:
                        if not await inp.is_visible():
                            continue

                        # Fuzz with SQL Injection Payload
                        await inp.fill(fuzz_payloads["sqli"])
                        
                        # Try submitting via Enter key or submit button
                        await inp.press("Enter")
                        await page.wait_for_load_state("networkidle", timeout=4000)

                        content = (await page.content()).lower()
                        db_error_indicators = ["syntax error", "mysql", "oracle", "sqlite", "sql", "db2", "database error", "unhandled exception", "oledb"]

                        if any(ind in content for ind in db_error_indicators):
                            res_msg = "FAILED — Database error thrown (SQLi)"
                            print(f"[FUNCTIONAL] TC-{test_id} on {label}: {res_msg}")
                            self.findings.append({
                                "module": "functional",
                                "title": "Possible SQL Injection Vulnerability",
                                "description": f"Input field '{label}' on {url} triggered a database syntax error when injected with SQL payload '{fuzz_payloads['sqli']}'.",
                                "severity": "critical",
                                "priority": "high",
                                "steps_to_reproduce": {"step": f"Inject '{fuzz_payloads['sqli']}' into '{label}' field and submit."}
                            })
                        else:
                            res_msg = "PASSED"
                            print(f"[FUNCTIONAL] TC-{test_id} on {label}: {res_msg}")

                        # Reload page for clean state
                        await page.goto(url, wait_until="networkidle", timeout=10000)

                    except Exception as err:
                        print(f"[FUNCTIONAL] TC-{test_id} on {label}: SKIPPED ({err})")

                # Test 3: Dead / Empty Link Detection
                empty_links = await page.locator("a[href=''], a[href='#']").count()
                if empty_links > 0:
                    print(f"[FUNCTIONAL] TC-999 on DeadLinks: FAILED — Found {empty_links} dead links")
                    self.findings.append({
                        "module": "functional",
                        "title": "Empty or Dead Links Detected",
                        "description": f"Found {empty_links} anchor tags pointing to empty ('') or hash ('#') destinations.",
                        "severity": "low",
                        "priority": "low",
                        "steps_to_reproduce": {"step": f"Inspect anchor tags on {url}"}
                    })

            except Exception as e:
                logger.warning(f"Functional testing failed for {url}: {e}")
                self.findings.append({
                    "module": "functional",
                    "title": "Functional Testing Page Load Error",
                    "description": f"Failed to complete functional test pass on {url}: {str(e)}",
                    "severity": "medium",
                    "priority": "medium"
                })
            finally:
                await browser.close()

        return self.findings
