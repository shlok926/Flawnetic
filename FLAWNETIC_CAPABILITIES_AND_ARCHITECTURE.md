# FLAWNETIC — Autonomous Web QA & Vulnerability Audit Platform
## End-to-End Capabilities, Multi-Engine Architecture & Hybrid Testing Guide

---

## 1. Overview of Flawnetic Platform

**Flawnetic** is an **Autonomous, AI-Powered End-to-End Web QA & Vulnerability Audit Platform**. It replaces slow manual QA and fragmented security testing by executing a fully automated 5-stage testing pipeline against any target web application.

---

## 2. 5-Stage Automated Testing Pipeline

### Stage 1: Autonomous Crawling (Playwright Engine)
- **Deep DOM & Route Discovery**: Crawls target URLs, follows links, extracts forms, inputs, buttons, and interactive controls.
- **Sitemap Graph Construction**: Builds a full `SiteGraph` tree representing the complete page hierarchy and discovered elements.
- **Unlinked Endpoint Testing**: Integrates high-value seed URL discovery (`/login`, `/register`, `/admin`, etc.) to test unlinked routes.

### Stage 2: Multi-Engine Audit Execution (5 Core Engines)
1. **Functional QA & Fuzzing Engine**:
   - Tests input forms, textareas, and controls against **SQL Injection** (`' OR '1'='1' --`), **Cross-Site Scripting (XSS)** (`<script>window.__flawnetic_xss__=1</script>`), and empty validation bypasses.
   - Monitors network API responses for **HTTP 500/502 Backend Server Crashes**.
   - Identifies empty, hash, or dead anchor links (`a[href='']`, `a[href='#']`).
2. **Security Engine (OWASP DAST & Headers)**:
   - Audits missing HTTP security headers (**Content-Security-Policy**, **HSTS**, **X-Frame-Options**, **X-Content-Type-Options**).
   - Conducts DAST active and passive scanning using OWASP ZAP for CORS, SSL/TLS, and runtime security flaws.
3. **Accessibility Engine (axe-core & WCAG 2.1)**:
   - Audits WCAG 2.1 compliance (missing form labels, missing image `alt` attributes, unreadable color contrast, invalid ARIA roles).
4. **Usability Engine**:
   - Validates viewport responsiveness, touch target sizes, and text readability across viewport dimensions.
5. **Visual Rendering Engine**:
   - Renders multi-browser screenshots (Chromium, Firefox, WebKit) across desktop, tablet, and mobile breakpoints to detect layout overflow glitches.

### Stage 3: AI Triage & Bug Analysis Engine
- **Deduplication**: Groups duplicate findings across pages into unique bug IDs (`FL-001`, `FL-002`).
- **Severity & Risk Rating**: Assigns normalized severity levels (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and calculates an overall normalized Risk Score (0.0 – 10.0).
- **AI Root Cause & Fix Generation**: Leverages Anthropic Claude AI to generate root cause analysis, expected vs. actual behavior, and code remediation patches.

### Stage 4: Enterprise PDF Report Generation
- **Executive Cover & Risk Gauge**: Dark slate header banner, metadata block, and normalized risk rating card.
- **Severity Matrix & Status Table**: 4-card severity summary and 5-engine audit status breakdown.
- **Detailed Finding Cards**: Individual pages per finding with numbered reproduction steps, styled payload code boxes, expected/actual results, and AI code patches.
- **MinIO/S3 Storage**: Uploads PDF reports to cloud storage and returns browser-accessible presigned download URLs.

### Stage 5: Real-Time Dashboard UI (React 18)
- **WebSocket Streaming**: Streams live crawl progress, page counts, discovered elements, and real-time vulnerability notifications to the React dashboard.

---

## 3. Comprehensive Finding Coverage (Frontend & Backend)

### External / Frontend (UI) Findings
- **Usability & UX Deficiencies**: Unclickable touch targets, missing button labels, improper font contrast.
- **Accessibility Glitches**: Unlabeled inputs, missing image alt text, broken ARIA accessibility trees.
- **Layout & Visual Glitches**: Viewport overflow (horizontal scrolling on mobile), broken images, dead links (`href="#"` / `href=""`).
- **Uncaught JS Errors**: Browser console JavaScript exceptions and unhandled promise rejections.

### Internal / Backend (API & Data) Findings
- **Unhandled Server Errors**: HTTP 500 Internal Server Error, 502 Bad Gateway, and 504 Gateway Timeout responses during UI interaction.
- **Missing Security Configurations**: Unset or weak CSP, CORS wildcard origins (`Access-Control-Allow-Origin: *`), missing HSTS.
- **Data Validation & Error Leaks**: Database syntax error leaks (MySQL, Oracle, PostgreSQL, SQLite, OLEDB) and authentication bypasses via SQLi.

---

## 4. Authenticated & Partner Portal Testing

Flawnetic supports authenticated scanning for protected portals (e.g. `/partner-portal`, `/dashboard`, `/settings`):

1. **Storage State / Cookie Auth**: Automatically logs into authentication forms and saves session cookies or JWT access tokens.
2. **Authenticated Route Crawling**: Reuses the saved authentication state across Playwright browser contexts to audit protected internal pages.
3. **Authorization & Best Practices**:
   - **Authorized Targets Only**: Automated scanners must strictly be executed against authorized staging, development, or localhost environments.
   - **Production Credential Guard**: Production credentials and third-party portals require explicit owner consent prior to automated fuzzing.

---

## 5. Hybrid Testing (SAST + DAST) & Code Repository Access

When Live Application Auditing (**DAST**) is combined with Source Code Access (**SAST**), testing accuracy increases significantly:

### 1. Static Application Security Testing (SAST - Source Code Scanner)
- **Hardcoded Secrets Detection**: Detects committed API keys, database credentials, and JWT secrets (`GitLeaks`, `TruffleHog`).
- **Software Composition Analysis (SCA)**: Identifies vulnerable third-party dependencies and CVEs in `requirements.txt` or `package.json` (`Bandit`, `Semgrep`, `Snyk`).
- **Insecure Code Patterns**: Flags raw SQL query concatenation, unsafe `eval()`, and weak cryptographic algorithms directly in source code.

### 2. Dynamic Application Security Testing (DAST - Flawnetic Live Scanner)
- **Runtime Execution**: Verifies whether vulnerabilities are actually exploitable in the deployed environment.
- **Real User Experience**: Identifies visual regressions, broken business logic, and UI accessibility failures.

### Comparison: DAST-Only vs. Hybrid SAST+DAST

| Audit Feature | DAST Only (URL) | Hybrid (URL + Code Repo) |
| :--- | :---: | :---: |
| **Runtime Errors & Live Exploits** | ✅ Yes | ✅ Yes |
| **Visual Regressions & WCAG** | ✅ Yes | ✅ Yes |
| **Exact Source Code File & Line Number** | ❌ No (URL only) | ✅ Yes (`backend/api/routers/auth.py#L42`) |
| **Ready-to-Merge Code Patch (Git Diff)** | ⚠️ Generic Advice | ✅ Precise Repository Code Patch |
| **Hardcoded Secrets & Dependency CVEs** | ❌ No | ✅ Yes |

---

## 6. Summary & Recommendations

- **Immediate Utility**: Flawnetic automates complete E2E testing, vulnerability detection, and enterprise PDF report generation via single API / CLI execution.
- **Future Architecture Roadmap**: Expanding Flawnetic to incorporate a SAST Engine (`Semgrep` / `Bandit` runner) will enable fully automated **Hybrid Security & QA Auditing** with exact line-level Git diff patches.
