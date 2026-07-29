# 02 — System Architecture

## 1. High-Level Flow

```
User Input (URL)
      │
      ▼
┌─────────────────────────────┐
│ 1. CRAWLER / EXPLORER AGENT │  Playwright + Claude API (Planner-Actor-Validator loop)
│    Discovers: pages, forms, │
│    buttons, links, inputs   │
└──────────────┬───────────────┘
               │  produces: Site Graph (JSON) — every page + every interactive element
               ▼
   ┌───────────┼────────────┬───────────────┬──────────────┐
   ▼           ▼            ▼               ▼              ▼
FUNCTIONAL   SECURITY    ACCESSIBILITY   VISUAL/CROSS-   USABILITY/
ENGINE       ENGINE      ENGINE          DEVICE ENGINE   PERFORMANCE
(Playwright  (OWASP ZAP  (axe-core on    (Playwright     (Lighthouse,
+ Claude     API, async  every page,     multi-context:  broken-link
test-data    scan        WCAG 2.1 AA)    Chromium/        checker,
generation)  alongside                   Firefox/WebKit  console-error
                                          + mobile         capture)
                                          viewports +
                                          pixelmatch diff)
   │           │            │               │              │
   └───────────┴────────────┴───────────────┴──────────────┘
               │  every module emits a normalized Finding object
               ▼
┌─────────────────────────────┐
│ 2. EVIDENCE CAPTURE LAYER    │  On every Finding: screenshot, DOM snapshot,
│                              │  console log, network HAR, Playwright trace
└──────────────┬───────────────┘
               ▼
┌─────────────────────────────┐
│ 3. AI TRIAGE & REPORT ENGINE │  Claude API:
│                              │  - classify severity/priority
│                              │  - dedupe similar findings
│                              │  - write human-readable bug narrative
│                              │  - suggest likely root cause
└──────────────┬───────────────┘
               ▼
┌─────────────────────────────┐
│ 4. REPORT GENERATOR          │  HTML → PDF (Puppeteer/WeasyPrint)
│                              │  + Chart.js (severity dist., pass/fail %)
│                              │  + executive summary
└──────────────┬───────────────┘
               ▼
┌─────────────────────────────┐
│ 5. DASHBOARD (React)         │  Live run progress, history, trends,
│                              │  RTM auto-mapped to test cases
└───────────────────────────────┘
```

## 2. Module Responsibilities

### Crawler / Explorer Agent
- Input: a root URL
- Uses Playwright to load pages, extract DOM tree
- Uses Claude API in a **Planner → Actor → Validator** loop (same pattern Skyvern popularized) to decide: "what hasn't been explored yet, what's the next most valuable action"
- Builds a **Site Graph**: nodes = pages, edges = navigation actions, leaves = interactive elements (button, input, dropdown, link) with metadata (selector, label, inferred type)
- Stops based on configurable limits (max pages, max depth, time budget) to control LLM cost

### Functional Engine
- For every form/input discovered, generates test data:
  - Positive case (valid input)
  - Negative cases: empty, max-length overflow, special characters only, numeric-only into text fields, SQL/XSS-pattern strings (for input-validation testing, NOT for actual exploitation)
- Executes via Playwright, compares expected vs actual DOM state / error messages
- Emits a `Finding` per failed assertion

### Security Engine
- Runs OWASP ZAP in daemon mode (Docker container), driven via its REST API
- Passive scan during crawl (header checks, cookie flags, mixed content, exposed source maps)
- Active scan post-crawl on discovered endpoints (XSS, SQLi, etc. — OWASP Top 10)
- Findings imported from ZAP's report format, normalized into our `Finding` schema

### Accessibility Engine
- Injects `axe-core` via `axe-playwright` on every discovered page
- Captures WCAG 2.1 AA violations with element selector + impact level

### Visual / Cross-Device Engine
- Re-runs key flows across Chromium, Firefox, WebKit contexts
- Mobile viewport emulation (e.g., iPhone 14, Pixel 7 presets)
- Screenshot diffing (pixelmatch) against the previous run's baseline for visual regressions

### Usability / Performance Engine
- Lighthouse CI run per page (performance, SEO, best practices scores)
- Broken-link checker (HTTP status sweep across all discovered URLs)
- Console error/warning capture during every page load

### Evidence Capture Layer
- Triggered automatically whenever any engine emits a `Finding`
- Captures: full-page screenshot, DOM snapshot (HTML), browser console log, network HAR, Playwright trace file
- Stores artifacts in object storage (S3-compatible), references saved in DB

### AI Triage & Report Engine
- Takes raw `Finding` list → groups duplicates (e.g., same bug across 5 pages → 1 entry with "occurs on N pages")
- Classifies severity (Critical/High/Medium/Low) and priority using a rubric prompt
- Writes the bug title, steps-to-reproduce, expected-vs-actual in plain English
- Adds a root-cause hint where pattern is recognizable (e.g., "missing server-side validation")

### Report Generator
- Populates the template defined in `06-BUG-REPORT-TEMPLATE.md`
- Renders HTML → PDF, embeds screenshots, adds charts (severity distribution, pass/fail ratio, pages tested)
- Adds executive summary paragraph (AI-generated, human-tone)

### Dashboard
- React + Tailwind SPA
- Shows: live run progress, historical runs, trend lines (bugs over time), drill-down per finding, RTM view mapping test cases to requirements/pages

## 3. Data Flow Object: `Finding` (normalized schema)
```json
{
  "id": "uuid",
  "run_id": "uuid",
  "module": "functional | security | accessibility | visual | usability",
  "page_url": "string",
  "element_selector": "string | null",
  "title": "string",
  "description": "string",
  "steps_to_reproduce": ["string"],
  "expected_result": "string",
  "actual_result": "string",
  "severity": "critical | high | medium | low",
  "priority": "high | medium | low",
  "evidence": {
    "screenshot_url": "string",
    "dom_snapshot_url": "string",
    "console_log_url": "string",
    "network_har_url": "string"
  },
  "detected_at": "timestamp"
}
```
This single schema is what every engine outputs into — it's what makes the unified report possible.

## 4. Deployment Topology (MVP)
- Single Docker Compose stack: `app` (FastAPI backend) + `worker` (Celery, runs Playwright) + `zap` (OWASP ZAP daemon) + `postgres` + `redis` (queue) + `frontend` (React, served via Nginx)
- Object storage: local volume for MVP → swap to S3-compatible bucket for production
