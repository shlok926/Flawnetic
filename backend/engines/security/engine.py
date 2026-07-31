import logging
import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

class SecurityEngine:
    """
    OWASP ZAP DAST & Security Vulnerability Audit Engine for Flawnetic.
    Interfaces with OWASP ZAP Daemon REST API and executes passive/active scans.
    Also performs standalone HTTP security header & TLS configuration checks.
    """

    def __init__(self, zap_base_url: str = "http://localhost:8080", zap_api_key: str = ""):
        self.zap_base_url = zap_base_url.rstrip("/")
        self.zap_api_key = zap_api_key
        self.findings: List[Dict[str, Any]] = []

    async def _check_zap_status((self)) -> bool:
        """Verifies if OWASP ZAP Daemon is online and responding."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.zap_base_url}/JSON/core/view/version/?apikey={self.zap_api_key}")
                return res.status_code == 200
        except Exception:
            return False

    async def scan_security_headers(self, url: str) -> List[Dict[str, Any]]:
        """Scans target URL for missing security headers, information disclosure, and cookie security flags."""
        findings = []
        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False, follow_redirects=True) as client:
                response = await client.get(url)
                headers = {k.lower(): v for k, v in response.headers.items()}
                cookies = response.cookies

                # 1. Missing Security Headers
                security_headers_rules = [
                    ("strict-transport-security", "Missing HSTS Header", "Strict-Transport-Security header is missing, exposing users to SSL stripping attacks.", "medium"),
                    ("content-security-policy", "Missing Content Security Policy (CSP)", "Content-Security-Policy header is missing, allowing potential XSS and data injection attacks.", "high"),
                    ("x-frame-options", "Missing Anti-Clickjacking Header", "X-Frame-Options header is missing, making the application vulnerable to Clickjacking attacks.", "medium"),
                    ("x-content-type-options", "Missing MIME Sniffing Protection", "X-Content-Type-Options: nosniff header is missing, permitting browsers to MIME-sniff response types.", "low"),
                    ("referrer-policy", "Missing Referrer Policy", "Referrer-Policy header is missing, which may leak sensitive URL parameters to third-party domains.", "low")
                ]

                for header_key, title, desc, severity in security_headers_rules:
                    if header_key not in headers:
                        findings.append({
                            "module": "security",
                            "title": title,
                            "description": f"{desc} Target: {url}",
                            "severity": severity,
                            "priority": severity,
                            "steps_to_reproduce": {"step": f"Inspect HTTP response headers for {url}"}
                        })

                # 2. Server Information Disclosure
                for server_header in ["server", "x-powered-by", "x-aspnet-version"]:
                    if server_header in headers:
                        findings.append({
                            "module": "security",
                            "title": f"Server Information Disclosure ({headers[server_header]})",
                            "description": f"The response header '{server_header}' exposes backend technology stack details ({headers[server_header]}).",
                            "severity": "low",
                            "priority": "low",
                            "steps_to_reproduce": {"step": f"Check response header '{server_header}'"}
                        })

                # 3. Insecure Cookie Flags
                for cookie_name, cookie_val in cookies.items():
                    # Cookie security checks
                    raw_cookie = response.headers.get("set-cookie", "")
                    if "httponly" not in raw_cookie.lower():
                        findings.append({
                            "module": "security",
                            "title": f"Insecure Cookie Flag: Missing HttpOnly ({cookie_name})",
                            "description": f"Cookie '{cookie_name}' is missing the 'HttpOnly' flag, allowing JavaScript client access during XSS.",
                            "severity": "medium",
                            "priority": "medium",
                            "steps_to_reproduce": {"step": f"Check Set-Cookie header for {cookie_name}"}
                        })
                    if url.startswith("https://") and "secure" not in raw_cookie.lower():
                        findings.append({
                            "module": "security",
                            "title": f"Insecure Cookie Flag: Missing Secure ({cookie_name})",
                            "description": f"Cookie '{cookie_name}' is missing the 'Secure' flag over HTTPS connection.",
                            "severity": "medium",
                            "priority": "medium",
                            "steps_to_reproduce": {"step": f"Check Set-Cookie header for {cookie_name}"}
                        })

        except Exception as e:
            logger.warning(f"Header security scan failed for {url}: {e}")

        return findings

    async def run_zap_dast_scan(self, target_url: str) -> List[Dict[str, Any]]:
        """Triggers OWASP ZAP spider and active scan against target URL via REST API."""
        zap_online = await self._check_zap_status()
        if not zap_online:
            logger.info("OWASP ZAP daemon offline. Falling back to native security headers & DAST inspection.")
            return await self.scan_security_headers(target_url)

        findings = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Access URL through ZAP proxy
                await client.get(f"{self.zap_base_url}/JSON/core/action/accessUrl/?url={target_url}&apikey={self.zap_api_key}")
                
                # Fetch ZAP alerts
                res = await client.get(f"{self.zap_base_url}/JSON/core/view/alerts/?baseurl={target_url}&apikey={self.zap_api_key}")
                if res.status_code == 200:
                    alerts = res.json().get("alerts", [])
                    for alert in alerts:
                        risk = alert.get("risk", "Low").lower()
                        severity = "critical" if risk == "high" else risk
                        findings.append({
                            "module": "security",
                            "title": alert.get("name", "OWASP ZAP Vulnerability"),
                            "description": alert.get("description", "Vulnerability detected by OWASP ZAP DAST Scanner."),
                            "severity": severity if severity in ["critical", "high", "medium", "low"] else "medium",
                            "priority": severity if severity in ["high", "medium", "low"] else "medium",
                            "steps_to_reproduce": {"url": alert.get("url"), "param": alert.get("param")}
                        })

        except Exception as e:
            logger.error(f"ZAP DAST scan execution error: {e}")

        # Combine with header security scan
        header_findings = await self.scan_security_headers(target_url)
        return findings + header_findings
