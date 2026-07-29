# Technical Requirements Document (TRD)

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Technical Requirements Document |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `01-PRD.md`, `04-TECH-STACK.md`, `05-ARCHITECTURE.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Purpose
Translate the product requirements (`01-PRD.md`) into concrete technical requirements that engineering can build against.

## 2. System Overview
The system is composed of five logical layers: **Crawler/Explorer**, **Test Engines** (functional, security, accessibility, visual, usability), **Evidence Capture**, **AI Triage & Report Generation**, and **Dashboard/API**. See `05-ARCHITECTURE.md` for the full diagram.

## 3. Technical Requirements by Module

### 3.1 Crawler / Explorer Agent
| ID | Requirement |
|---|---|
| TR-1.1 | Must support Chromium, Firefox, and WebKit rendering engines via a single automation API (Playwright) |
| TR-1.2 | Must build a Site Graph: nodes = pages, edges = navigation actions, leaves = interactive elements with metadata (selector, label, type) |
| TR-1.3 | Must support configurable crawl limits: `max_pages`, `max_depth`, `time_budget_minutes` |
| TR-1.4 | Must deduplicate URLs (query-param normalization, trailing slash handling) to avoid re-crawling the same page |
| TR-1.5 | Must use an LLM-driven decision loop (Planner → Actor → Validator) to prioritize unexplored, high-value paths when DOM-based discovery is ambiguous (e.g., SPA routes) |

### 3.2 Functional Test Engine
| ID | Requirement |
|---|---|
| TR-2.1 | Must generate test data per detected input type: text, email, number, date, dropdown, checkbox, file upload |
| TR-2.2 | Must execute negative cases: empty input, max-length overflow, special-characters-only, numeric-only into text fields, leading/trailing whitespace |
| TR-2.3 | Must compare actual DOM/error-message state against expected state per assertion |
| TR-2.4 | Must emit a normalized `Finding` object (schema in `05-ARCHITECTURE.md`) for every failed assertion |

### 3.3 Security Test Engine
| ID | Requirement |
|---|---|
| TR-3.1 | Must integrate with OWASP ZAP via its REST API in a containerized (Docker) deployment |
| TR-3.2 | Must run a passive scan during crawl (headers, cookie flags, mixed content, exposed source maps) |
| TR-3.3 | Must run an active scan post-crawl against discovered endpoints (OWASP Top 10 classes: injection, broken auth indicators, security misconfiguration, etc.) |
| TR-3.4 | Must require an explicit "I am authorized to test this site" confirmation flag before any active scan is triggered |
| TR-3.5 | Must use only non-destructive, safe-mode payloads — no scan configuration that could corrupt or delete target-site data |

### 3.4 Accessibility Test Engine
| ID | Requirement |
|---|---|
| TR-4.1 | Must inject `axe-core` (via `axe-playwright`) on every discovered page |
| TR-4.2 | Must capture WCAG 2.1 Level AA violations with element selector and impact level (critical/serious/moderate/minor) |

### 3.5 Visual / Cross-Browser Engine
| ID | Requirement |
|---|---|
| TR-5.1 | Must re-execute key flows across at least 2 browser engines + 1 mobile viewport emulation per scan |
| TR-5.2 | Must perform pixel-level screenshot diffing against the prior run's baseline (pixelmatch or equivalent) |
| TR-5.3 | Must support a configurable diff-tolerance threshold to avoid false positives from anti-aliasing/minor rendering noise |

### 3.6 Usability / Performance Engine
| ID | Requirement |
|---|---|
| TR-6.1 | Must run a Lighthouse audit (performance, SEO, best practices) per page |
| TR-6.2 | Must sweep all discovered URLs for non-2xx/3xx HTTP status (broken link detection) |
| TR-6.3 | Must capture browser console errors/warnings during each page load |

### 3.7 Evidence Capture
| ID | Requirement |
|---|---|
| TR-7.1 | Must automatically capture, on every `Finding`: full-page screenshot, DOM snapshot (HTML), console log, network HAR |
| TR-7.2 | Evidence artifacts must be stored in object storage (S3-compatible) with a reference URL persisted in the `evidence` table |
| TR-7.3 | Evidence storage access must be via signed/temporary URLs, not public-permanent links |

### 3.8 AI Triage & Report Generation
| ID | Requirement |
|---|---|
| TR-8.1 | Must deduplicate findings that recur across multiple pages into a single entry with an occurrence count |
| TR-8.2 | Must classify severity (Critical/High/Medium/Low) and priority (High/Medium/Low) per a defined rubric (see `06-SECURITY.md` for severity rubric used on security findings specifically) |
| TR-8.3 | Must generate human-readable title, steps-to-reproduce, and expected-vs-actual text per finding via LLM call with structured (JSON) output |
| TR-8.4 | Must render the final report from HTML templates to PDF, embedding screenshots and Chart.js-rendered charts |

### 3.9 Dashboard / API
| ID | Requirement |
|---|---|
| TR-9.1 | Must expose a REST API per `06-API-SPEC.md`-equivalent contract for all scan lifecycle operations |
| TR-9.2 | Must provide a live progress stream (WebSocket or Server-Sent Events) during an active scan |
| TR-9.3 | Dashboard must support filtering findings by module, severity, and page |

## 4. Non-Functional / Cross-Cutting Technical Requirements
| ID | Requirement |
|---|---|
| TR-NF-1 | All long-running operations (crawl, scan, report generation) must execute asynchronously via a job queue, never blocking the API request thread |
| TR-NF-2 | System must support horizontal scaling of worker processes independent of the API layer |
| TR-NF-3 | All LLM calls must have a request timeout and a retry policy (max 2 retries) to avoid stuck scans |
| TR-NF-4 | All secrets (API keys, ZAP credentials) must be injected via environment variables / secrets manager — never hardcoded or committed to source control |
| TR-NF-5 | Database schema must support adding new finding "modules" without a breaking migration (use an enum + JSONB metadata pattern) |

## 5. Interface Requirements
- **Inbound:** REST API (JSON over HTTPS), WebSocket/SSE for live progress
- **Outbound (Phase 3):** Jira REST API, Trello REST API, Slack Webhooks, GitHub Actions artifact upload

## 6. Data Requirements
See `04-DATABASE-SCHEMA.md`-equivalent content in `05-ARCHITECTURE.md` (Finding schema) for the canonical data model. Key data retention rule: evidence artifacts retained 30 days by default, configurable per project.

## 7. Environment Requirements
| Environment | Purpose |
|---|---|
| **Local/Dev** | Docker Compose: app, worker, ZAP, Postgres, Redis — single-machine |
| **Staging** | Mirrors production topology at smaller scale, used for testing against real demo targets (OWASP Juice Shop, SauceDemo) |
| **Production** | Containerized deployment (e.g., on a VPS/cloud provider) with object storage (S3/MinIO), managed Postgres, managed Redis |

## 8. Third-Party Dependencies
| Dependency | Risk if unavailable |
|---|---|
| Claude API (Anthropic) | AI triage/report-writing degrades to templated text; crawler falls back to pure DOM-based heuristics |
| OWASP ZAP | Security module disabled for that scan; report flags security section as "skipped" |
| Lighthouse CI | Performance/SEO section skipped |

## 9. Technical Acceptance Criteria (maps to PRD Release Criteria)
- Crawler discovers ≥ 95% of internal pages on a standard-navigation test site
- End-to-end scan → report pipeline completes without manual intervention
- No destructive action is ever taken against a target site during any test module
