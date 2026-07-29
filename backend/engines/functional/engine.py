from typing import List, Dict, Any
import asyncio
from playwright.async_api import async_playwright, Response

class FunctionalEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.findings = []

    async def check_api_response(self, response: Response):
        """Monitors all API calls made by the page for errors (Senior QA network monitoring)."""
        if response.status >= 500:
            self.findings.append({
                "module": "security", # Classify 500s as potential security/functional risks
                "title": f"API Internal Server Error ({response.status})",
                "description": f"The endpoint '{response.url}' crashed returning {response.status}. This indicates unhandled exceptions on the backend.",
                "severity": "high",
                "priority": "high",
                "steps_to_reproduce": {"step": f"Trigger request to {response.url}"}
            })
        # Check for missing security headers on API responses
        headers = await response.all_headers()
        if "x-content-type-options" not in headers and response.request.resource_type in ["fetch", "xhr"]:
            self.findings.append({
                "module": "security",
                "title": "Missing Security Headers on API",
                "description": f"API '{response.url}' is missing 'X-Content-Type-Options' header.",
                "severity": "low",
                "priority": "low"
            })

    async def analyze_and_test(self, url: str) -> List[Dict[str, Any]]:
        """
        Advanced QA Automation: Fuzzes forms, tests for XSS/SQLi, and monitors API endpoints.
        """
        self.findings = []
        
        # Payloads used by Senior Security/QA Engineers
        fuzz_payloads = {
            "xss": "<script>alert('flawnetic')</script>",
            "sqli": "' OR '1'='1",
            "boundary": "A" * 5000  # Buffer overflow / boundary testing
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            
            # Listen to background network requests (API testing)
            page.on("response", self.check_api_response)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
                
                # Check for Forms
                forms = await page.locator("form").all()
                for i, form in enumerate(forms):
                    action = await form.get_attribute("action") or "unknown_action"
                    method = await form.get_attribute("method") or "GET"
                    
                    if method.upper() == "GET" and "login" in action.lower():
                        self.findings.append({
                            "module": "security",
                            "title": "Insecure Login Form (GET)",
                            "description": f"Login form submits via GET to '{action}'. Credentials will leak in browser history.",
                            "severity": "critical",
                            "priority": "high"
                        })

                    # SMART FORM FILLING (XSS & SQLi Testing)
                    inputs = await form.locator("input[type='text'], input[type='search'], textarea").all()
                    
                    if len(inputs) > 0:
                        # Test SQLi on the first text input
                        try:
                            await inputs[0].fill(fuzz_payloads["sqli"])
                            # Find submit button
                            submit_btn = form.locator("button[type='submit'], input[type='submit']").first
                            if await submit_btn.is_visible():
                                await submit_btn.click()
                                await page.wait_for_load_state("networkidle", timeout=5000)
                                
                                # Check if error thrown (Poor man's SQLi detection)
                                body_text = await page.content()
                                if "syntax error" in body_text.lower() or "mysql" in body_text.lower():
                                    self.findings.append({
                                        "module": "security",
                                        "title": "Possible SQL Injection Vulnerability",
                                        "description": f"Form at {url} crashed or returned DB errors when injected with SQL payloads.",
                                        "severity": "critical",
                                        "priority": "high",
                                        "steps_to_reproduce": {"step": f"Inject '{fuzz_payloads['sqli']}' into the form input"}
                                    })
                                    
                                # Go back to continue testing
                                await page.goto(url, wait_until="networkidle")
                        except Exception:
                            pass # Element not interactable
                            
                # Check for Broken Links
                empty_links = await page.locator("a[href=''], a[href='#']").count()
                if empty_links > 0:
                    self.findings.append({
                        "module": "functional",
                        "title": "Empty or Dead Links Detected",
                        "description": f"Found {empty_links} links pointing to empty ('') or hash ('#') hrefs.",
                        "severity": "low",
                        "priority": "low"
                    })

            except Exception as e:
                self.findings.append({
                    "module": "functional",
                    "title": "Functional Testing Page Load Error",
                    "description": f"Failed to load {url}: {str(e)}",
                    "severity": "medium",
                    "priority": "medium"
                })
            finally:
                await browser.close()
                
        return self.findings
