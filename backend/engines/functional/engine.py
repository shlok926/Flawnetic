from typing import List, Dict, Any, Optional
import asyncio
import logging
from playwright.async_api import async_playwright, Response

logger = logging.getLogger(__name__)

class FunctionalEngine:
    """
    Enterprise Functional & Fuzzing QA Engine for Flawnetic.
    Tests web forms, inputs, controls for SQLi, XSS, broken validation, and network errors.
    """
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.findings: List[Dict[str, Any]] = []

    async def check_api_response(self, response: Response):
        """Monitors all API calls made by the page for errors (Senior QA network monitoring)."""
        if response.status >= 500:
            self.findings.append({
                "module": "functional",
                "title": f"API Internal Server Error ({response.status})",
                "description": f"The endpoint '{response.url}' returned HTTP status {response.status}. Indicates unhandled backend exceptions.",
                "severity": "high",
                "priority": "high",
                "steps_to_reproduce": {"step": f"Trigger request to {response.url}"}
            })

    async def _submit_form(self, page, input_element):
        """
        Try multiple form submission strategies:
        1. Click submit button inside closest form
        2. Click any visible submit button on page
        3. Press Enter key on input element
        """
        try:
            # Strategy 1: submit button in form
            form_handle = await input_element.evaluate_handle("el => el.closest('form')")
            if form_handle:
                form = form_handle.as_element()
                if form:
                    submit_btn = await form.query_selector("input[type='submit'], button[type='submit'], button:not([type]), input[type='image']")
                    if submit_btn and await submit_btn.is_visible():
                        await submit_btn.click()
                        await page.wait_for_timeout(1500)
                        return

            # Strategy 2: any submit button on page
            submit_btn = await page.query_selector("input[type='submit'], button[type='submit']")
            if submit_btn and await submit_btn.is_visible():
                await submit_btn.click()
                await page.wait_for_timeout(1500)
                return

            # Strategy 3: Enter key
            await input_element.press("Enter")
            await page.wait_for_timeout(1500)

        except Exception as e:
            logger.warning(f"Form submission strategy warning: {e}")

    async def analyze_and_test(self, url: str) -> List[Dict[str, Any]]:
        """
        Functional & Fuzzing QA Engine: Tests forms, inputs, and controls for XSS, SQLi, and errors.
        """
        self.findings = []
        print(f"[FUNCTIONAL] Starting analysis on URL: {url}")

        fuzz_payloads = {
            "sqli": "' OR '1'='1' --",
            "xss": "<script>window.__flawnetic_xss__=1</script>",
            "boundary": "A" * 2000
        }

        INPUT_SELECTORS = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='search']",
            "input[type='tel']",
            "input[type='url']",
            "input[type='number']",
            "input:not([type])",
            "textarea",
            "input[type='hidden']"
        ]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            page.on("response", self.check_api_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)

                # Extract forms
                forms = await page.locator("form").all()

                # Extract all testable inputs
                all_inputs = []
                for selector in INPUT_SELECTORS:
                    found = await page.locator(selector).all()
                    all_inputs.extend(found)

                # Filter visible / actionable inputs
                actionable_inputs = []
                for inp in all_inputs:
                    try:
                        # Allow hidden fields if explicitly present, otherwise check visibility
                        is_vis = await inp.is_visible()
                        is_dis = await inp.is_disabled()
                        if is_vis and not is_dis:
                            actionable_inputs.append(inp)
                    except Exception:
                        pass

                total_elements = len(actionable_inputs) + len(forms)
                print(f"[FUNCTIONAL] Found {total_elements} elements to test")

                # Test 1: Insecure Login Form Check (GET method for sensitive forms)
                for i, form in enumerate(forms):
                    action = await form.get_attribute("action") or ""
                    method = await form.get_attribute("method") or "GET"
                    if method.upper() == "GET" and ("login" in action.lower() or "auth" in action.lower()):
                        print(f"[FUNCTIONAL] TC-001 on Form[{i}]: FAILED - Insecure GET Login Form detected")
                        self.findings.append({
                            "module": "functional",
                            "title": "Insecure Login Form (GET)",
                            "description": f"Form submits credentials via GET method to '{action}'. Sensitive parameters leak in HTTP referrer headers and browser logs.",
                            "severity": "critical",
                            "priority": "high",
                            "steps_to_reproduce": {"step": f"Submit login form at {url}"}
                        })

                # Test 2: Input Fuzzing (SQLi, XSS, Validation)
                for i, inp in enumerate(actionable_inputs):
                    label = (await inp.get_attribute("aria-label") or await inp.get_attribute("placeholder") or await inp.get_attribute("name") or await inp.get_attribute("id") or f"Input[{i}]").strip()
                    test_id = f"00{i+2}"

                    # 2A. Test SQL Injection
                    try:
                        url_before = page.url
                        
                        # Fill target input
                        await inp.fill(fuzz_payloads["sqli"])
                        
                        # If inside a form, also fill sibling text/password inputs with SQLi payload
                        try:
                            form_handle = await inp.evaluate_handle("el => el.closest('form')")
                            if form_handle:
                                form = form_handle.as_element()
                                if form:
                                    siblings = await form.query_selector_all("input[type='text'], input[type='password'], input:not([type])")
                                    for sib in siblings:
                                        try:
                                            if await sib.is_visible() and not await sib.is_disabled():
                                                val = await sib.input_value()
                                                if not val:
                                                    await sib.fill(fuzz_payloads["sqli"], timeout=2000)
                                        except Exception:
                                            pass
                        except Exception:
                            pass

                        await self._submit_form(page, inp)
                        await page.wait_for_load_state("networkidle", timeout=4000)
                        
                        url_after = page.url
                        content = (await page.content()).lower()

                        sql_error_patterns = [
                            "sql syntax", "mysql_fetch", "ora-0", "pg_query",
                            "sqlite_", "unclosed quotation", "syntax error",
                            "microsoft ole db", "odbc drivers", "jdbc",
                            "you have an error in your sql", "warning: mysql", "invalid query"
                        ]

                        # Auth Bypass Detection via URL Change
                        is_login_page = any(lp in url_before.lower() for lp in ["login", "signin", "auth"])
                        is_authenticated_page = any(ap in url_after.lower() for ap in ["main.jsp", "dashboard", "account", "admin"]) and not any(ep in url_after.lower() for ep in ["login_error", "failed", "error"])

                        if is_login_page and is_authenticated_page:
                            print(f"[FUNCTIONAL] TC-sqli on {label}: FAILED - Auth bypass via SQLi (CRITICAL)")
                            self.findings.append({
                                "module": "functional",
                                "title": "SQL Injection Authentication Bypass",
                                "description": f"Input field '{label}' on {url} allowed complete authentication bypass when injected with SQL payload '{fuzz_payloads['sqli']}'. Redirected to {url_after}.",
                                "severity": "critical",
                                "priority": "high",
                                "steps_to_reproduce": {
                                    "step_1": f"Navigate to {url}",
                                    "step_2": f"Inject '{fuzz_payloads['sqli']}' into '{label}' field",
                                    "step_3": "Click Sign In / Submit",
                                    "step_4": f"Observe authentication bypass and redirect to {url_after}"
                                },
                                "expected_result": "Error message shown or login denied.",
                                "actual_result": f"Form accepts SQL payload and grants access to {url_after}"
                            })

                        elif any(p in content for p in sql_error_patterns):
                            print(f"[FUNCTIONAL] TC-sqli on {label}: FAILED - Database syntax error leaked (CRITICAL)")
                            self.findings.append({
                                "module": "functional",
                                "title": "Possible SQL Injection Vulnerability",
                                "description": f"Input field '{label}' on {url} triggered database syntax errors when injected with SQL payload '{fuzz_payloads['sqli']}'.",
                                "severity": "critical",
                                "priority": "high",
                                "steps_to_reproduce": {"step": f"Inject '{fuzz_payloads['sqli']}' into '{label}' field and submit."},
                                "expected_result": "Sanitized input processing.",
                                "actual_result": "Raw database error returned to user."
                            })
                        else:
                            print(f"[FUNCTIONAL] TC-sqli on {label}: PASSED")

                    except Exception as err:
                        logger.warning(f"SQLi test error on {label}: {err}")
                    finally:
                        await page.goto(url, wait_until="networkidle", timeout=10000)

                    # 2B. Test Cross-Site Scripting (XSS)
                    try:
                        # Re-locate input safely after page reload
                        all_curr_inputs = []
                        for sel in INPUT_SELECTORS:
                            found = await page.locator(sel).all()
                            all_curr_inputs.extend(found)
                        if i < len(all_curr_inputs):
                            target_inp = all_curr_inputs[i]
                            is_vis = False
                            try:
                                is_vis = await target_inp.is_visible()
                            except Exception:
                                is_vis = False

                            if is_vis:
                                await target_inp.fill(fuzz_payloads["xss"])
                                await self._submit_form(page, target_inp)
                                await page.wait_for_load_state("networkidle", timeout=4000)

                                xss_executed = await page.evaluate("() => window.__flawnetic_xss__ === 1")
                                raw_content = await page.content()

                            if xss_executed:
                                print(f"[FUNCTIONAL] TC-xss on {label}: FAILED - Stored/Reflected XSS executed (CRITICAL)")
                                self.findings.append({
                                    "module": "functional",
                                    "title": "Cross-Site Scripting (XSS) Execution",
                                    "description": f"Input field '{label}' on {url} executed injected JavaScript payload '{fuzz_payloads['xss']}'.",
                                    "severity": "critical",
                                    "priority": "high",
                                    "steps_to_reproduce": {"step": f"Inject '{fuzz_payloads['xss']}' into '{label}' field and submit."}
                                })
                            elif "<script>window.__flawnetic_xss__=1</script>" in raw_content:
                                print(f"[FUNCTIONAL] TC-xss on {label}: FAILED - Reflected XSS tag present (HIGH)")
                                self.findings.append({
                                    "module": "functional",
                                    "title": "Reflected Cross-Site Scripting (XSS)",
                                    "description": f"Input field '{label}' on {url} reflected unescaped HTML script tags in the DOM response.",
                                    "severity": "high",
                                    "priority": "high",
                                    "steps_to_reproduce": {"step": f"Inject '{fuzz_payloads['xss']}' into '{label}' field and submit."}
                                })
                    except Exception as err:
                        logger.warning(f"XSS test error on {label}: {err}")
                    finally:
                        await page.goto(url, wait_until="networkidle", timeout=10000)

                # Test 3: Dead / Empty Link Detection
                empty_links = await page.locator("a[href=''], a[href='#']").count()
                if empty_links > 0:
                    print(f"[FUNCTIONAL] TC-999 on DeadLinks: FAILED - Found {empty_links} dead links")
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
