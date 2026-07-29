# Tech Stack Document

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Tech Stack |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `02-TRD.md`, `05-ARCHITECTURE.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Stack Overview (Quick Reference)

| Layer | Technology |
|---|---|
| Browser Automation | Playwright (Python bindings) |
| AI / LLM Brain | Claude API (claude-sonnet-4-6) |
| Security Scanning | OWASP ZAP (Docker, REST API) |
| Accessibility | axe-core via axe-playwright |
| Performance / SEO | Lighthouse CI (Node) |
| Visual Regression | pixelmatch (Node) |
| Backend API | Python + FastAPI |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic (migrations) |
| Object Storage | AWS S3 / MinIO (self-host option) |
| PDF Report | HTML templates → Puppeteer (headless Chrome) |
| Report Charts | Chart.js (server-side render) |
| Frontend Dashboard | React 18 + Tailwind CSS |
| Frontend State | Zustand (lightweight, no Redux boilerplate) |
| Real-time Progress | Server-Sent Events (SSE) |
| Containerization | Docker + Docker Compose |
| Python package mgmt | pip + requirements.txt (uv for speed) |

---

## 2. Layer-by-Layer Detail

### 2.1 Browser Automation — Playwright (Python)
**Why Playwright:**
- Single API for Chromium, Firefox, and WebKit — covers all 3 major rendering engines
- Built-in mobile viewport emulation (iPhone, Pixel presets)
- Native async support (asyncio) — critical for running multiple browser contexts concurrently
- Built-in network interception (needed to capture HAR files)
- `playwright.Tracing` produces a complete trace/video of each test run (evidence)
- `axe-playwright` integrates axe-core natively
- Active maintenance by Microsoft; far superior to Selenium for modern SPAs

**Why not Selenium:**
- Lacks native async, built-in tracing, and cross-browser setup requires more configuration
- No native mobile emulation without Appium

**Key packages:**
```
playwright==1.45+
axe-playwright==0.1.x
```

---

### 2.2 AI / LLM — Claude API (Anthropic)
**Used for:**
1. **Crawler Planner-Actor-Validator loop** — "given this DOM state and what we've explored, what's the next highest-value action?"
2. **Test data generation** — generate varied, realistic negative test inputs per field type
3. **Finding deduplication** — "are these 5 similar-looking findings the same root cause?"
4. **Bug narrative writing** — structured JSON output: title, steps, expected, actual, root-cause-hint
5. **Executive summary** — 1-paragraph plain-English scan overview for non-technical stakeholders

**Model:** `claude-sonnet-4-6` (cost-efficient + strong structured output)

**Why Claude specifically:**
- Consistent structured JSON output from complex prompts (critical for the `Finding` schema)
- Strong reasoning for the crawler Planner step — better than GPT-4o on nuanced DOM-state decisions in benchmarks we've reviewed
- Anthropic's API terms allow commercial SaaS use without the restrictive output-ownership ambiguity of some other providers

**Cost control:**
- Crawler LLM calls capped by `max_pages` config
- All AI calls use `max_tokens: 1000` for report narrative, `max_tokens: 300` for triage classifications
- Batch deduplication (send all raw findings in one call) rather than one call per finding

---

### 2.3 Security Scanning — OWASP ZAP (Docker)
**Why ZAP:**
- Free, open-source, Apache License 2.0 — no license cost even for commercial product
- REST API (Automation Framework) — fully scriptable, no GUI interaction needed
- Passive scan runs alongside the crawl with zero additional overhead
- Active scan covers OWASP Top 10 classes: injection, broken auth indicators, security misconfiguration, sensitive data exposure, etc.
- Industry-recognized tool — findings attributed to "powered by OWASP ZAP" carry credibility

**Deployment:** Docker container (`softwaresecurityproject/zap2docker-stable`) in the Compose stack, accessed via `http://zap:8080`

**Why not Burp Suite:**
- Burp Pro = $449+/year per seat license — not viable for an open/affordable product
- Burp's REST API is also available but ZAP's is more permissive for SaaS embedding

---

### 2.4 Accessibility — axe-core via axe-playwright
**Why axe-core:**
- Industry-standard WCAG engine; used under the hood by testRigor, Katalon, Deque's commercial products
- MIT license, free
- Returns structured violations with: WCAG criterion, element selector, impact level (critical/serious/moderate/minor), and fix suggestions
- `axe-playwright` integrates it as a single function call per page within existing Playwright sessions — zero extra browser overhead

---

### 2.5 Performance / SEO — Lighthouse CI
**Why Lighthouse:**
- Google-maintained, free, industry-standard score
- Produces: Performance score, SEO score, Best Practices score, Accessibility score (complements axe-core)
- CI-friendly (CLI: `lhci autorun`)
- Runs in the same Docker environment via `@lhci/cli` Node package

---

### 2.6 Visual Regression — pixelmatch
**Why pixelmatch:**
- Lightweight (zero license cost), open-source
- Pixel-level diff with configurable tolerance threshold
- Outputs a diff PNG highlighting changed regions — embeddable in the report as evidence
- Good enough for MVP visual diffing without Applitools ($$$)

**Upgrade path:** Applitools Eyes can be swapped in later as a premium visual-regression tier without changing the rest of the pipeline — it outputs the same type of diff result

---

### 2.7 Backend API — Python + FastAPI
**Why FastAPI:**
- Native async (asyncio) — important for orchestrating long-running scans without blocking
- Auto-generates OpenAPI docs (useful for Phase 3 CLI/CI integration)
- Pydantic models for request/response validation double as the data schema for `Finding` objects
- Fast to build with, strong typing

**Why Python over Node.js:**
- Playwright has first-class Python support
- Celery (our task queue) is Python-native
- Claude Python SDK is more mature than the JS SDK for complex structured-output use cases

---

### 2.8 Task Queue — Celery + Redis
**Why a task queue:**
A scan takes 5–15 minutes. This cannot live in a synchronous HTTP request. The worker process must be decoupled from the API process.

**Why Celery + Redis:**
- Celery is the de facto Python async task runner; mature, well-documented
- Redis as the broker is lightweight and fast (vs. RabbitMQ which is heavier for this scale)
- Celery supports task chaining: `crawl → functional_engine → security_engine → report_gen` as a pipeline
- Celery Flower (optional) gives a web UI to monitor running tasks during dev

---

### 2.9 Database — PostgreSQL
**Why Postgres:**
- Strong relational structure for the Runs → Pages → Findings → Evidence hierarchy
- JSONB columns for `config`, `summary`, and `Finding.steps_to_reproduce` (flexible without sacrificing queryability)
- Battle-tested for SaaS; horizontal read scaling via read replicas when needed
- Alembic (SQLAlchemy ORM) handles schema migrations cleanly

---

### 2.10 Object Storage — AWS S3 / MinIO
**Why object storage (not Postgres) for evidence:**
Screenshots, DOM snapshots, HAR files, and video traces are binary, large (100KB–5MB each), and high-volume. Storing them in Postgres BLOBs would balloon the DB size and slow queries. S3-compatible object storage is the right tool.

**MinIO** for local/self-hosted deployments (drop-in S3 API), AWS S3 for production cloud. The app uses the `boto3` client — switching between them is one env-var change.

---

### 2.11 PDF Report Generation — Puppeteer (Node)
**Why HTML → PDF via Puppeteer (headless Chrome):**
- Full CSS control over the report design (colors, fonts, layout, branded header/footer)
- Chart.js charts render pixel-perfectly in the browser before PDF capture
- Screenshots embed naturally in HTML `<img>` tags
- Puppeteer is the most reliable HTML→PDF tool with complex CSS (WeasyPrint struggles with modern CSS Grid/Flexbox)

**Why not a PDF library (ReportLab, fpdf2):**
- Low-level PDF libraries require constructing the layout programmatically in code — slow to iterate on design, hard to maintain
- We want designers to be able to change the report template in HTML/CSS without touching Python

---

### 2.12 Frontend — React 18 + Tailwind CSS
**Why React:**
- Component model maps naturally to the dashboard's reusable pieces (SeverityBadge, FindingCard, ProgressBar, ScanHistoryTable)
- Live progress via SSE is cleanly handled in React's `useEffect` + state
- Large ecosystem of compatible charting and UI libraries

**Why Tailwind:**
- Utility-first = rapid iteration; no context-switching between CSS files and components
- Design tokens (colors, spacing) defined once in `tailwind.config.js` — easy to apply the design system

**State management:** Zustand (lightweight) — no Redux boilerplate needed for this scale

**Real-time:** Server-Sent Events (SSE) from FastAPI → React's `EventSource` API for live progress; simpler than WebSockets since progress is unidirectional (server → client only)

---

## 3. Full Dependency List (MVP)

### Python (Backend + Workers)
```
fastapi
uvicorn[standard]
celery
redis
sqlalchemy
alembic
psycopg2-binary
playwright
axe-playwright
anthropic
boto3
pydantic
python-multipart
python-jose[cryptography]       # JWT auth
passlib[bcrypt]                  # password hashing
```

### Node (Report rendering + Lighthouse)
```
puppeteer
chart.js
@lhci/cli
pixelmatch
pngjs
```

### Infrastructure (Docker Compose services)
```
postgres:16
redis:7-alpine
softwaresecurityproject/zap2docker-stable
minio/minio                     # local S3-compatible storage
node:20-slim                    # for Puppeteer + Lighthouse
```

---

## 4. Alternatives Considered (not chosen for MVP)

| Option | Reason not chosen |
|---|---|
| Selenium instead of Playwright | Weaker SPA support, no native tracing, more setup per browser |
| Burp Suite instead of ZAP | Paid license, not viable for open/affordable SaaS |
| Applitools instead of pixelmatch | Cost; pixelmatch sufficient for MVP |
| Django instead of FastAPI | Sync-first design; async patterns are bolted on; heavier for an API-only backend |
| Next.js instead of React | No need for SSR here; adds complexity without benefit for a dashboard SPA |
| RabbitMQ instead of Redis | Heavier operational overhead for this scale; Redis is sufficient as a Celery broker |
