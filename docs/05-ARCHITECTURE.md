# Architecture Document

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Architecture Document |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `02-TRD.md`, `04-TECH-STACK.md`, `06-SECURITY.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Architectural Goals
- **Modularity:** Each test engine (functional, security, accessibility, visual, usability) is independently replaceable without touching the others
- **Scalability:** Scan workers scale horizontally; API layer is stateless
- **Resilience:** A failed test engine (e.g., ZAP timeout) marks that module as "skipped" in the report — it does not fail the entire scan
- **Evidence-first:** Every finding is immutably linked to its evidence at write time — no post-hoc evidence association
- **Cost-bounded LLM use:** Claude API is called at defined, bounded points only — not in a free-running loop without limits

---

## 2. System Context Diagram
```
┌───────────────────────────────────────────────────────────────┐
│                        EXTERNAL ACTORS                        │
│                                                               │
│  [User / Browser]     [CI/CD Pipeline]     [Target Website]  │
│       │                     │                     │           │
└───────┼─────────────────────┼─────────────────────┼───────────┘
        │  HTTPS (REST/SSE)   │  CLI / REST          │  HTTP(S)
        ▼                     ▼                      │
┌───────────────────────────────────────┐             │
│        Flawnetic PLATFORM        │  ───────────┘
│  ┌─────────┐  ┌────────┐  ┌────────┐ │  (Playwright, ZAP probe outbound)
│  │Dashboard│  │API     │  │Workers │ │
│  │(React)  │  │(FastAPI│  │(Celery)│ │
│  └─────────┘  └────────┘  └────────┘ │
│  ┌──────────────────────────────────┐ │
│  │ Postgres | Redis | MinIO/S3      │ │
│  └──────────────────────────────────┘ │
└───────────────────────────────────────┘
        │  External API calls outbound
        ▼
┌─────────────────────────────────────────────┐
│  EXTERNAL SERVICES                           │
│  Claude API (Anthropic) | ZAP (in Docker)   │
│  Lighthouse CI (in Docker)                   │
└─────────────────────────────────────────────┘
```

---

## 3. Full Component Architecture (L2 Decomposition)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (React + Tailwind) — served via Nginx                             │
│  Pages: Landing | Scan Config | Live Progress | Dashboard | Report View     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ REST + SSE
┌────────────────────────────────────▼────────────────────────────────────────┐
│  API LAYER (FastAPI — stateless, async)                                     │
│  Routers: /auth  /projects  /scans  /findings  /reports  /export           │
│  Middleware: JWT auth, request logging, rate limiting                       │
│  Pushes scan jobs → Redis queue on POST /scans                              │
└──────────────┬────────────────────────────────────┬─────────────────────────┘
               │ SQL reads/writes                   │ Job enqueue
┌──────────────▼──────────────┐    ┌────────────────▼────────────────────────┐
│  PostgreSQL                  │    │  Redis (Celery broker + result backend) │
│  Tables: users, projects,    │    └────────────────┬────────────────────────┘
│  scan_runs, pages,           │                     │ Job dequeue
│  findings, evidence, reports │    ┌────────────────▼────────────────────────┐
└─────────────────────────────┘    │  WORKER LAYER (Celery workers)           │
                                    │                                           │
              ┌─────────────────────┼────────────────────────────────────┐     │
              │                                                            │     │
              ▼                     ▼                    ▼                ▼     │
┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌────────────┐│
│ CRAWLER /         │  │ FUNCTIONAL       │  │ SECURITY       │  │ACCESSIBILITY││
│ EXPLORER AGENT    │  │ ENGINE           │  │ ENGINE         │  │ENGINE      ││
│                   │  │                  │  │                │  │            ││
│ Playwright        │  │ Playwright       │  │ ZAP REST API   │  │axe-core    ││
│ + Claude API      │  │ + Claude API     │  │ (Docker svc)   │  │axe-playwright││
│ (Planner-Actor    │  │ (test-data gen)  │  │                │  │            ││
│ -Validator loop)  │  │                  │  │                │  │            ││
│                   │  │                  │  │                │  │            ││
│ Outputs:          │  │ Outputs:         │  │ Outputs:       │  │ Outputs:   ││
│ Site Graph (JSON) │  │ Finding[]        │  │ Finding[]      │  │ Finding[]  ││
└────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘  └─────┬──────┘│
         │                     │                     │                  │      │
         ▼                     ▼                     ▼                  ▼      │
┌─────────────────────────────────────────────────────────────────────────────┐│
│  VISUAL/CROSS-BROWSER ENGINE    │    USABILITY/PERFORMANCE ENGINE           ││
│  Playwright multi-context       │    Lighthouse CI + broken-link sweep      ││
│  + pixelmatch diff              │    + console-error capture                ││
│  Outputs: Finding[]             │    Outputs: Finding[]                     ││
└────────────────────┬────────────┘    └────────────────┬────────────────────┘│
                     │                                   │                     │
                     ▼                                   ▼                     │
         ┌─────────────────────────────────────────────────────────┐          │
         │  EVIDENCE CAPTURE LAYER                                  │          │
         │  On every Finding emitted:                               │          │
         │  → Screenshot (Playwright page.screenshot)               │          │
         │  → DOM snapshot (page.content())                         │          │
         │  → Console log (page.on('console'))                      │          │
         │  → Network HAR (Playwright HAR recording)                │          │
         │  → Upload all to MinIO/S3                                │          │
         │  → Write evidence rows to DB                             │          │
         └──────────────────────────────┬──────────────────────────┘          │
                                        │                                      │
                                        ▼                                      │
         ┌─────────────────────────────────────────────────────────┐          │
         │  AI TRIAGE ENGINE (Claude API)                           │          │
         │  Input: all Finding[] for this scan_run                  │          │
         │  → Deduplicate similar findings                          │          │
         │  → Classify severity + priority per rubric               │          │
         │  → Write human-readable title/steps/expected/actual      │          │
         │  → Root-cause hint where pattern is recognizable         │          │
         │  Output: enriched Finding[] saved to DB                  │          │
         └──────────────────────────────┬──────────────────────────┘          │
                                        │                                      │
                                        ▼                                      │
         ┌─────────────────────────────────────────────────────────┐          │
         │  REPORT GENERATOR                                         │          │
         │  HTML template + Jinja2 → rendered HTML (with charts,    │          │
         │  embedded screenshots, structured finding blocks)         │          │
         │  → Puppeteer (headless Chrome) → PDF                     │          │
         │  → Upload PDF to MinIO/S3                                │          │
         │  → Write reports row to DB                               │          │
         │  → Update scan_run.status = "done"                       │          │
         └─────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Flow for a Complete Scan

### Step 1 — Scan Kickoff
```
User POST /scans
  → API validates input, writes scan_run (status=queued) to Postgres
  → Pushes job ID to Redis queue
  → Returns { run_id, status: "queued" } to client
  → Client opens SSE connection to /scans/{run_id}/live
```

### Step 2 — Crawl Phase (Worker picks up job)
```
Worker: run_crawler(run_id, base_url, config)
  → Playwright Chromium context launched
  → BFS/DFS traversal from root URL
  → Per page:
      - record page (url, title, http_status) → DB pages table
      - extract interactive elements → part of Site Graph JSON
      - take baseline screenshot → MinIO
      - run axe-core immediately (while page is loaded) → Accessibility findings
      - emit SSE event: { page_url, pages_found: N }
  → Claude API consulted when navigation ambiguity detected (SPA routes, dynamic menus)
  → Site Graph (JSON) stored in scan_run.site_graph
```

### Step 3 — Parallel Test Execution
```
After crawl complete, fan out in parallel (Celery group):
  ├── functional_engine(scan_run_id, site_graph)
  ├── security_engine(scan_run_id, site_graph)       [if module enabled]
  ├── visual_engine(scan_run_id, site_graph)          [if module enabled]
  └── usability_engine(scan_run_id, site_graph)       [if module enabled]
  (accessibility already done per-page during crawl)

Each engine:
  → Produces Finding[] objects
  → Evidence Capture triggered per finding → MinIO upload → evidence rows to DB
  → Emits SSE events with running finding count
```

### Step 4 — AI Triage
```
After all engines complete:
  → Fetch all Finding[] for this scan_run from DB
  → Single Claude API call (batch prompt): dedupe + classify + narrate
  → Update findings rows in DB with enriched content
  → Update scan_run.summary (severity_counts, total_pages, total_findings)
```

### Step 5 — Report Generation
```
  → Jinja2 template rendered with enriched findings + charts
  → Chart.js charts rendered server-side (Node child process)
  → Puppeteer generates PDF
  → PDF uploaded to MinIO → URL saved to reports table
  → scan_run.status = "done"
  → Final SSE event sent to client: { status: "done", report_url }
```

---

## 5. Database Schema (Key Tables)
```
users
  id (uuid PK), email, password_hash, name, role, created_at

projects
  id (uuid PK), user_id (FK), name, base_url, created_at

scan_runs
  id (uuid PK), project_id (FK), status (enum), started_at, finished_at,
  config (jsonb), summary (jsonb), site_graph (jsonb)

pages
  id (uuid PK), scan_run_id (FK), url, title, http_status, screenshot_url

findings
  id (uuid PK), scan_run_id (FK), page_id (FK, nullable),
  module (enum: functional|security|accessibility|visual|usability),
  title, description, steps_to_reproduce (jsonb), expected_result, actual_result,
  severity (enum), priority (enum), root_cause_hint, occurrence_count, detected_at

evidence
  id (uuid PK), finding_id (FK),
  type (enum: screenshot|dom_snapshot|console_log|network_har|video_trace),
  storage_url, created_at

reports
  id (uuid PK), scan_run_id (FK), pdf_url, generated_at
```

---

## 6. Deployment Architecture (MVP vs Production)

### MVP — Docker Compose (single machine)
```
┌─────────────────────────────────────────────┐
│  docker-compose.yml                          │
│                                              │
│  services:                                   │
│    frontend    (Nginx + React build)         │
│    api         (FastAPI, uvicorn)            │
│    worker      (Celery, playwright, zap)     │
│    zap         (OWASP ZAP daemon)            │
│    postgres    (Postgres 16)                 │
│    redis       (Redis 7)                     │
│    minio       (S3-compatible local storage) │
│    node        (Puppeteer + Lighthouse)      │
└─────────────────────────────────────────────┘
```

### Production — Cloud
```
┌─────────────────────────────────────────────────────┐
│  Nginx reverse proxy (SSL termination)               │
│  → React SPA (CDN/static hosting)                   │
│  → FastAPI (1–N instances, load balanced)            │
│  → Celery workers (auto-scaled, N replicas)          │
│     each worker has: Playwright + ZAP sidecar        │
│                                                       │
│  Managed services:                                   │
│  → PostgreSQL (managed DB — Supabase/RDS/Neon)      │
│  → Redis (managed — Upstash/ElastiCache)             │
│  → AWS S3 (evidence + PDF storage)                   │
└─────────────────────────────────────────────────────┘
```

---

## 7. Concurrency Model
- Each scan runs in its own Celery task chain
- Multiple scans can run concurrently, limited only by available worker replicas and ZAP instance count
- Within a single scan, functional/security/visual/usability engines run as a Celery `group` (parallel)
- Playwright contexts are isolated per scan (no state leakage between scans)

---

## 8. Failure Handling

| Failure Scenario | Behavior |
|---|---|
| Crawler hits a page with 404/5xx | Record the status in pages table; continue crawl |
| ZAP scan times out | Mark security module as "skipped — timed out"; report notes this |
| Claude API call fails | Retry up to 2 times; if still failing, use templated fallback text for that finding |
| Evidence upload to MinIO fails | Log error, mark evidence as "upload_failed", finding still saved |
| Worker crashes mid-scan | Redis Celery retry: scan resumes from last checkpoint (page-level idempotency via URL dedup) |
| Report generation fails | scan_run.status = "report_failed"; user shown link to raw findings JSON as fallback |

---

## 9. Normalized `Finding` Object (Cross-Module Contract)
```json
{
  "id": "uuid",
  "scan_run_id": "uuid",
  "page_id": "uuid | null",
  "module": "functional | security | accessibility | visual | usability",
  "title": "string",
  "description": "string",
  "steps_to_reproduce": ["string"],
  "expected_result": "string",
  "actual_result": "string",
  "severity": "critical | high | medium | low",
  "priority": "high | medium | low",
  "root_cause_hint": "string | null",
  "occurrence_count": 1,
  "evidence": {
    "screenshot_url": "string",
    "dom_snapshot_url": "string",
    "console_log_url": "string",
    "network_har_url": "string"
  },
  "detected_at": "ISO8601 timestamp"
}
```
Every test engine writes findings in this exact shape. This contract is what makes the unified report possible — the report generator only ever consumes `Finding[]` regardless of which module produced them.
