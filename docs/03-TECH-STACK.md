# 03 — Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Browser automation** | Playwright (Python) | Single API for Chromium, Firefox, WebKit; built-in mobile viewport emulation, network interception, tracing — covers crawling + functional + visual + cross-browser in one library |
| **AI / LLM** | Claude API (Anthropic) | Used for: crawler decision-making (Planner-Actor-Validator), test-data generation, severity classification, bug-narrative writing. Strong structured-output (JSON) reliability needed for the `Finding` schema |
| **Security scanning** | OWASP ZAP (Docker, REST API) | Free, open-source, mature OWASP Top 10 coverage, scriptable via Automation Framework — avoids reinventing a DAST engine |
| **Accessibility** | axe-core via `axe-playwright` | Industry-standard WCAG engine; same engine used under the hood by testRigor and most accessibility tools |
| **Performance/SEO** | Lighthouse CI | Google-maintained, free, gives performance + SEO + best-practices scores per page |
| **Visual regression** | pixelmatch (Node) or `resemble.js` | Lightweight, open-source pixel-diffing — avoids Applitools licensing cost for MVP; can upgrade later |
| **Backend API** | Python + FastAPI | Async-friendly (important for orchestrating long-running scans), good typing/validation via Pydantic, easy OpenAPI docs generation |
| **Task queue / orchestration** | Celery + Redis | Scans are long-running and parallelizable (security scan + accessibility scan can run concurrently) — needs a real job queue, not request/response |
| **Database** | PostgreSQL | Relational structure fits Runs → Pages → Findings → Evidence well; JSONB columns for flexible `Finding` metadata |
| **Object storage** | S3-compatible (AWS S3 / MinIO for self-host) | Screenshots, DOM snapshots, HAR files, videos — large binary artifacts don't belong in Postgres |
| **Report rendering** | HTML templates → Puppeteer (or WeasyPrint for pure-Python) for PDF | Lets us design the report visually in HTML/CSS (full control over branding) then export to a portable PDF |
| **Charts in report** | Chart.js (rendered server-side via headless browser) | Severity distribution, pass/fail %, trend lines |
| **Frontend dashboard** | React + Tailwind CSS | Fast to build, component-driven, matches the dashboard needs (live progress, history, drill-down) |
| **CI/CD integration (Phase 3)** | GitHub Actions + a published CLI (`pip install sitesentinel-cli`) | Lets engineering teams run scans pre-merge without touching the dashboard |
| **Containerization** | Docker + Docker Compose | ZAP, Postgres, Redis, app, worker all need isolated, reproducible environments |

## Why not just use one big AI agent (e.g., raw Skyvern/Browser-Use) for everything?
Pure vision/LLM-driven agents (Skyvern, Browser-Use) are excellent at **navigating unfamiliar sites** but:
- Expensive per-step (every action = an LLM call)
- Not deterministic — bad for compliance-grade security findings, where false positives/negatives must be minimized
- No built-in security/accessibility detection logic

**Our approach:** use Playwright (deterministic, cheap) for the actual test execution and evidence capture, and reserve the LLM for the parts that genuinely need judgment — deciding what to explore next, writing human-readable bug text, and classifying severity. This keeps cost predictable and findings auditable.

## Alternatives considered (and why not, for now)
| Option | Reason not chosen for MVP |
|---|---|
| Selenium instead of Playwright | Playwright has better modern SPA support, native tracing, and a cleaner async API |
| Burp Suite instead of ZAP | Burp Pro requires a paid license ($449+/year); ZAP is free and CI-friendly out of the box |
| Applitools instead of pixelmatch | Applitools is excellent but adds real cost; pixelmatch is "good enough" for MVP visual diffing |
| Building a custom DAST engine | Reinventing OWASP ZAP's decade of vulnerability-pattern research is not a good use of time |
| Node.js instead of Python for backend | Either works; Python chosen for stronger data/AI tooling ecosystem (pandas, easy Claude SDK usage) — swap is low-risk if your team prefers Node |
