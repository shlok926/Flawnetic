# Security Document

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Security Document |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `02-TRD.md`, `05-ARCHITECTURE.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Purpose
This document covers **two distinct security concerns**:

**Part A — Security of the platform itself:** how Flawnetic protects its own users, data, and infrastructure.

**Part B — Security testing methodology:** exactly how the platform tests target websites for security vulnerabilities, what it detects, and what its limitations are.

---

# PART A — Platform Security (The Tool Itself)

## A.1 Authentication & Authorization
| Control | Implementation |
|---|---|
| User authentication | JWT (JSON Web Tokens), signed with `HS256`, `python-jose` library |
| Password storage | `bcrypt` hashing via `passlib` — never stored in plaintext |
| Token expiry | Access token: 60 minutes; refresh token: 7 days |
| Authorization model | Resource-based ownership — users can only access their own projects, scans, findings, reports. Enforced at API layer (every DB query filtered by `user_id`) |
| Admin access | Role enum (`admin` / `member`) in users table; admin-only endpoints gated by role check middleware |

## A.2 Secret Management
| Control | Implementation |
|---|---|
| API keys (Claude, AWS) | Injected via environment variables — never hardcoded |
| Source control | `.env` files in `.gitignore`; secrets never committed |
| Production | Secrets manager (AWS Secrets Manager / Doppler) — env vars injected at container runtime |
| ZAP API key | Generated per-deployment, not default, stored in env vars |

## A.3 Input Validation & Injection Prevention
| Control | Implementation |
|---|---|
| API input validation | Pydantic models enforce type, length, and format on all request bodies |
| URL validation | `url` field validated against a strict SSRF-prevention allowlist: must be `http://` or `https://` with a resolvable public host; private/loopback IPs (`10.x`, `192.168.x`, `localhost`, `169.254.x`) explicitly rejected |
| Database queries | SQLAlchemy ORM with parameterized queries throughout — no raw SQL string concatenation |
| Report HTML rendering | Jinja2 with `autoescape=True` — all dynamic content HTML-escaped before insertion into report templates |

## A.4 SSRF (Server-Side Request Forgery) Prevention
**This is the most critical platform-specific security risk.** The platform's core function is to make HTTP requests to a user-specified URL. Without controls, an attacker could point the scanner at internal services (`http://169.254.169.254/latest/meta-data/` on AWS EC2, `http://postgres:5432/`, etc.).

**Mitigations:**
- URL validation rejects private IP ranges, loopback addresses, and link-local addresses before any request is made
- DNS resolution check: resolve the submitted URL's hostname and validate the resulting IP is not in a private range (before Playwright/ZAP receives the URL)
- ZAP is configured in a sandboxed Docker network that has no route to internal services; it can only reach the external internet
- Playwright browser contexts are also sandboxed — no access to the host network outside of the Docker bridge

## A.5 Scan Scope Enforcement
- Users must explicitly tick an authorization checkbox ("I own or have written authorization to test this URL") before security scans are triggered — this is a legal requirement for responsible use
- URL submitted must match the project's registered `base_url` — no ad-hoc cross-domain scanning without creating a new project
- Crawl is restricted to the same origin (no crawling to external third-party domains linked from the target)

## A.6 Data Security
| Control | Implementation |
|---|---|
| Data in transit | All API communication over HTTPS (TLS 1.2+); MinIO/S3 access via HTTPS; ZAP API only accessible within the internal Docker network |
| Data at rest | PostgreSQL encrypted at rest (managed DB with encryption enabled); S3 bucket with SSE-S3 encryption |
| Evidence isolation | Evidence artifacts stored under `/{scan_run_id}/{finding_id}/` key prefix — no cross-user path traversal possible without authenticated access |
| Evidence retention | Default 30-day retention; user-deletable on demand |
| PDF reports | Stored in same S3 bucket with the same encryption; served via pre-signed time-limited URLs (15-min expiry) — not public-permanent links |

## A.7 Rate Limiting & Abuse Prevention
- API rate limiting (e.g., 100 req/min per IP) via FastAPI middleware + Redis token bucket
- Concurrent scan limit per user (e.g., 2 active scans at a time in free tier)
- `max_pages` / `max_depth` limits on every scan to prevent runaway resource consumption
- ZAP active-scan thread limits configured to prevent the platform from DOSing small target sites

## A.8 Dependency Security
- Dependabot or equivalent alerts for known CVEs in Python/Node packages
- Docker base images pinned to specific digest (not just `:latest`) in production
- ZAP Docker image updated monthly to incorporate latest scan rules

## A.9 Logging & Monitoring
- All API requests logged (method, path, user_id, status, response time) — no request bodies logged (to avoid capturing sensitive test data)
- Worker scan events logged per step
- Alerts on: repeated auth failures, unexpected 5xx spikes, ZAP container health failures
- No PII (email, name) included in application logs — only user_id (UUID)

---

# PART B — Security Testing Methodology (What We Test On Target Sites)

## B.1 Testing Approach Overview
The security engine uses **OWASP ZAP** (Open-source DAST — Dynamic Application Security Testing) as its core detection engine, driven via ZAP's REST API. DAST means we test the **running application from the outside** — no access to source code required.

All security testing is:
- **Passive first, Active second** — passive scan runs alongside crawling (low risk, no modified requests); active scan runs after crawl completion (sends crafted payloads to test endpoints)
- **Non-destructive** — ZAP is configured in safe mode; payloads are designed to detect vulnerabilities, not exploit them or modify data
- **Evidence-backed** — every security finding includes the request/response pair as proof

## B.2 OWASP Top 10 Coverage Matrix

| OWASP 2021 Category | Detection Approach | Coverage Level |
|---|---|---|
| **A01 — Broken Access Control** | ZAP active scan: forced browsing, insecure direct object references (IDOR indicators) | Partial — automated IDOR detection is limited; forced browsing covers common paths |
| **A02 — Cryptographic Failures** | Passive scan: HTTPS enforcement, mixed content, insecure cookies (no `Secure` flag), weak cipher negotiation, sensitive data in URLs | Good |
| **A03 — Injection (SQLi, XSS, etc.)** | Active scan: crafted payloads in all discovered input parameters (GET/POST) | Good for reflected XSS, basic SQLi; stored XSS harder without state |
| **A04 — Insecure Design** | Not automatically detectable — flagged in report disclaimer as requiring manual review | None (inherent DAST limitation) |
| **A05 — Security Misconfiguration** | Passive scan: missing security headers (CSP, X-Frame-Options, HSTS, X-Content-Type-Options, Referrer-Policy), directory listing, exposed stack traces, verbose error messages | Excellent |
| **A06 — Vulnerable & Outdated Components** | Passive scan: version disclosure in headers, known vulnerable libraries via JS detection | Partial |
| **A07 — Identification & Authentication Failures** | Passive scan: insecure login forms (HTTP vs HTTPS), no CSRF tokens, missing `HttpOnly`/`Secure` on session cookies, weak `SameSite` | Good for indicators; cannot test password policy without auth |
| **A08 — Software & Data Integrity Failures** | Passive: missing Subresource Integrity (SRI) on CDN scripts | Partial |
| **A09 — Security Logging & Monitoring Failures** | Not automatically testable from outside | None (inherent DAST limitation) |
| **A10 — Server-Side Request Forgery (SSRF)** | Active scan: SSRF payloads on URL parameters | Basic coverage; advanced SSRF is hard to detect externally |

## B.3 Security Check Categories (Detailed)

### B.3.1 HTTP Security Headers (Passive — every page)
| Header | What missing it means |
|---|---|
| `Content-Security-Policy` | XSS mitigation absent |
| `Strict-Transport-Security` (HSTS) | HTTPS not enforced; downgrade attacks possible |
| `X-Frame-Options` | Clickjacking possible |
| `X-Content-Type-Options: nosniff` | MIME-type sniffing attacks possible |
| `Referrer-Policy` | Sensitive URLs may leak in Referer header |
| `Permissions-Policy` | Browser features not restricted |

### B.3.2 Cookie Security (Passive)
- Missing `HttpOnly` flag → cookie accessible to JavaScript (XSS escalation)
- Missing `Secure` flag → cookie sent over HTTP
- Missing `SameSite` attribute → CSRF risk

### B.3.3 Cross-Site Scripting (XSS) (Active)
- Reflected XSS: ZAP injects payloads (`<script>alert(1)</script>`, event handler variants) into all URL parameters and POST body fields; checks if payload appears unescaped in the response
- DOM-based XSS: Playwright observes execution of injected event handlers during page render

### B.3.4 SQL Injection (Active)
- Classic SQLi patterns (`' OR '1'='1`, `1; DROP TABLE--`) injected into form fields and URL parameters
- Error-based detection: looks for database error messages in response
- Boolean-based detection: response difference analysis

### B.3.5 Sensitive Information Exposure (Passive + Active)
- Stack traces / debug information in responses
- Sensitive data in URL query strings (session tokens, passwords)
- Exposed `.git` directory, `/.env`, `/config.json`, `/phpinfo.php` (common misconfiguration paths)
- Source map files (`.js.map`) exposed in production — reveals obfuscated source code

### B.3.6 CSRF (Passive)
- Checks for CSRF token presence in forms (hidden input with anti-CSRF token)
- Checks `SameSite` cookie attribute

## B.4 Severity Classification Rubric (Security Findings)

| Severity | Criteria (Security-specific) |
|---|---|
| **Critical** | Remote code execution possible; direct data exfiltration; authentication bypass; persistent XSS on high-traffic pages |
| **High** | Reflected XSS confirmed; SQL injection confirmed (even read-only); HSTS missing on login pages; session cookie without `HttpOnly` + `Secure` |
| **Medium** | Missing security headers (CSP, X-Frame-Options); CSRF token absent; mixed content; verbose error messages |
| **Low** | `SameSite` attribute not set; Referrer-Policy missing; non-sensitive version disclosure |

## B.5 Limitations & Disclaimers (Mandatory — included in every report)
1. **This is automated DAST, not a manual penetration test.** Automated tools cannot detect business-logic vulnerabilities (e.g., broken pricing, unauthorized privilege escalation requiring account knowledge).
2. **OWASP ZAP active scanning may produce false positives** (findings that appear to be vulnerabilities but are not exploitable in context). Every High/Critical finding should be manually verified before remediation or disclosure.
3. **Authenticated flows are not tested in MVP** — vulnerabilities that only appear after login (e.g., IDOR on user-specific resources) are not covered.
4. **This report does not constitute a security audit for compliance purposes** (PCI-DSS, SOC 2, ISO 27001, etc.). A certified penetration test by a qualified professional is required for those.
5. **Coverage note:** Approximately 30–50% of real-world OWASP Top 10 vulnerabilities are detectable via automated DAST; the rest require manual review, source code access, or business-context knowledge.

## B.6 Responsible Use Policy
- Users must confirm authorization to test before any active security scan is triggered
- The platform logs all active scan targets with timestamp and user_id for audit purposes
- Any user found scanning targets they do not own or have permission to test will have their account suspended
- The platform never stores target-site response bodies beyond what is needed as evidence for confirmed findings; raw request/response pairs are retained for evidence purposes only and subject to the same 30-day retention policy as other evidence
