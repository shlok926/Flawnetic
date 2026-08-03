# FLAWNETIC ENGINEERING PRINCIPLES
**Document ID:** `PRINCIPLES-FLAWNETIC-2026-001`  
**Version:** 1.0  
**Status:** LEVEL 3 GOVERNANCE DOCUMENT  
**Classification:** ENFORCEABLE ENGINEERING STANDARDS  
**Precedence Level:** Level 3 (Overrides Level 4–6 Documents; Aligns with `MANIFESTO.md`, `GOVERNANCE_INDEX.md` & `ENGINEERING_PLAYBOOK.md`)  
**Approval Authority:** Principal Engineers, Staff Architects & Security Architect

---

## EXECUTIVE QUANTITATIVE THRESHOLDS (NON-NEGOTIABLE)

```text
┌──────────────────────────────────────┬────────────────────────────────────────┐
│ Metric / Threshold                   │ Mandatory Value                        │
├──────────────────────────────────────┼────────────────────────────────────────┤
│ Minimum Test Coverage                │ ≥ 90.0% Line Coverage (pytest-cov)     │
│ Maximum Function Length              │ ≤ 40 Lines (excluding docstrings)      │
│ Maximum File Length                  │ ≤ 400 Lines (excluding tests/imports)  │
│ Maximum Cyclomatic Complexity        │ ≤ 10 per Function (Ruff C901)          │
│ Maximum Code Nesting Depth           │ ≤ 3 Levels                             │
│ Maximum Module Import Coupling       │ Zero Circular Dependencies             │
│ Default API Response Timeout         │ ≤ 5.0 Seconds                          │
│ Default Celery Task Hard Timeout     │ ≤ 600.0 Seconds (10 minutes)           │
│ Maximum Unhandled Exceptions         │ 0 (All errors caught & logged)         │
│ Linters & Static Analysis            │ 0 Ruff / Black / MyPy Errors           │
└──────────────────────────────────────┴────────────────────────────────────────┘
```

---

## 1. REPOSITORY STANDARDS

### Rule REP-01: Local AI Workspace Isolation
- **Why**: Keeps local AI knowledge context separate from production application builds and public git repositories.
- **Required Implementation**: `.ai/` directory must be explicitly listed in `.gitignore`. No commits, PRs, or release artifacts may include `.ai/` files.
- **Good Example**: `grep -q "^\.ai/" .gitignore`
- **Bad Example**: `git add .ai/`
- **Automated Enforcement**: `.gitignore` check job in `.github/workflows/ci.yml`.
- **Exception Policy**: None.

---

## 2. ARCHITECTURE STANDARDS

### Rule ARC-01: Applied Single Responsibility & Per-Module Isolation
- **Why**: Prevents cascade failures across scanning engines and maintains modular testability.
- **Required Implementation**: Engine modules (`functional`, `security`, `accessibility`, `triage`) must be isolated. Engine tasks in `tasks.py` must run inside per-module `try/except` blocks.
- **Good Example**:
  ```python
  results = _run_module_safely("security", lambda: asyncio.run(security_engine.run(url)))
  ```
- **Bad Example**:
  ```python
  # Running all engines in one unhandled loop where 1 crash breaks everything
  results = run_all_engines_together(url)
  ```
- **Automated Enforcement**: Pytest module isolation test suite.
- **Related Manifesto Section**: Section 5 (Architecture Principles).

---

## 3. CODING STANDARDS

### Rule COD-01: Explicit Domain Naming (No Single-Letter Abbreviations)
- **Why**: Single-letter or ambiguous variables degrade readability and maintainability.
- **Required Implementation**: Variable names must explicitly state their domain object.
- **Good Example**: `discovered_urls: list[str]`, `steps_to_reproduce: list[dict]`
- **Bad Example**: `u: list`, `s: list`, `r: dict`
- **Automated Enforcement**: `ruff check` (N802, N803 rules).
- **Related Manifesto Section**: Section 3 (Engineering Philosophy).

---

## 4. API STANDARDS

### Rule API-01: Strict Pydantic Request & Response Schemas
- **Why**: Prevents malformed payloads, injection vectors, and unauthorized field exposure.
- **Required Implementation**: All FastAPI routes must define explicit Pydantic `response_model` classes.
- **Good Example**:
  ```python
  @router.post("/scans", response_model=ScanRunStatusResponse)
  def create_scan(scan: ScanCreateRequest): ...
  ```
- **Bad Example**:
  ```python
  @router.post("/scans")
  def create_scan(raw_data: dict): return raw_data
  ```
- **Automated Enforcement**: `mypy --strict` and FastAPI schema validation.

---

## 5. SECURITY STANDARDS

### Rule SEC-01: Environment-Restricted CORS Policy
- **Why**: Wildcard origins (`*`) with credentials expose authenticated API users to cross-domain attacks.
- **Required Implementation**: Parse allowed origins array strictly from `settings.frontend_url`.
- **Good Example**:
  ```python
  origins = [o.strip() for o in settings.frontend_url.split(",") if o.strip()]
  app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True)
  ```
- **Bad Example**:
  ```python
  app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
  ```
- **Automated Enforcement**: Pytest security router test (`test_cors_policy`).
- **Related Manifesto Section**: Section 6 (Security Philosophy).

### Rule SEC-02: Endpoint Rate Limiting
- **Why**: Prevents brute-force credential attempts and Denial of Service (DoS).
- **Required Implementation**: Apply `slowapi` rate limits on auth (5 req/min) and scan endpoints (10 req/min).

---

## 6. AI ENGINEERING STANDARDS

### Rule AIE-01: Input DOM Sanitization & PII Redaction
- **Why**: Prevents indirect prompt injection attacks from malicious target websites and guards user privacy.
- **Required Implementation**: Strip raw HTML/script tags from web content before feeding it to LLM prompts, and redact credentials/PII.
- **Good Example**:
  ```python
  clean_dom = sanitize_text(raw_html[:2000])
  ```
- **Bad Example**:
  ```python
  prompt = f"Analyze this DOM: {raw_page_content}"
  ```
- **Automated Enforcement**: Pytest AI analyzer mock tests.
- **Related Manifesto Section**: Section 7 (AI Principles).

### Rule AIE-02: Structural JSON Output Validation with Fallback
- **Why**: Guarantees AI outputs adhere to system data models without crashing on format hallucinations.
- **Required Implementation**: Parse LLM responses using `json.loads()` inside `try/except` and fall back to template text on failure.

---

## 7. DATABASE STANDARDS

### Rule DB-01: Explicit Foreign Key Indexes & Migration Scripts
- **Why**: Unindexed foreign keys cause N+1 query performance degradation on large tables.
- **Required Implementation**: All foreign key columns (`scan_run_id`, `project_id`, `page_id`) must have explicit DB indexes defined in Alembic migrations.

---

## 8. FRONTEND STANDARDS

### Rule FE-01: React 18 SPA Component Isolation & Accessible Standards
- **Why**: Keeps UI responsive, maintainable, and WCAG compliant.
- **Required Implementation**: Separate presentation UI components (`FindingsExplorer.jsx`, `ScanTracker.jsx`) from state modals.

---

## 9. BACKEND STANDARDS

### Rule BE-01: Presigned MinIO Cloud Storage Hostname Resolution
- **Why**: Docker internal endpoints (`minio:9000`) fail DNS resolution when opened in external browsers.
- **Required Implementation**: Replace internal endpoint strings with `settings.s3_public_url` (`http://localhost:9000`).

---

## 10. TESTING STANDARDS

### Rule TST-01: Mandatory $\ge 90.0\%$ Line Coverage Threshold
- **Why**: Guarantees code quality, safety during refactoring, and regression prevention.
- **Required Implementation**: Run `pytest --cov=backend --cov-fail-under=90` in CI/CD pipeline.
- **Related Manifesto Section**: Section 8 (Testing Philosophy).

---

## 11. PERFORMANCE STANDARDS

### Rule PER-01: Async Playwright & Connection Pooling
- **Why**: Blocking I/O loops starve worker threads.
- **Required Implementation**: Use `async`/`await` for browser automation and `httpx.AsyncClient` pooling.

---

## 12. OBSERVABILITY & LOGGING STANDARDS

### Rule OBS-01: Contextual JSON Logging with Exception Traces
- **Why**: Enables 2 AM production incident debugging without guessing.
- **Required Implementation**: Log errors using standard `logging` module with `exc_info=True` and contextual keys.
- **Good Example**:
  ```python
  logger.error(f"Scan execution failed for {scan_run_id}: {e}", exc_info=True)
  ```
- **Bad Example**:
  ```python
  except Exception: print("Error happened")
  ```

---

## 13. ERROR HANDLING STANDARDS

### Rule ERR-01: Zero Unhandled Exception Swallowing
- **Why**: Silent error swallowing masks underlying contract breaks and corrupts DB states.
- **Required Implementation**: Always catch specific exceptions, log traces, and update DB task status to `failed`.

---

## 14. DOCKER & CONTAINER STANDARDS

### Rule DOC-01: Multi-Profile Service Isolation
- **Why**: Keeps lightweight local dev scans fast while supporting heavy security engines.
- **Required Implementation**: Heavy security tools (OWASP ZAP) must be isolated under `profiles: ["security"]` in `docker-compose.yml`.

---

## 15. CI/CD STANDARDS

### Rule CICD-01: Automated Pipeline Fail-Fast Policy
- **Why**: Prevents broken or unformatted code from reaching `main`.
- **Required Implementation**: `.github/workflows/ci.yml` must execute `ruff check`, `black --check`, `mypy`, `pytest` (90% gate), and `docker compose build`.

---

## 16. QUALITY GATES & COMPLIANCE

```text
┌──────────────────────────────────────┬────────────────────────────────────────┐
│ Quality Gate                         │ Verification Tool                      │
├──────────────────────────────────────┼────────────────────────────────────────┤
│ 1. Code Formatting                   │ black --check backend/                 │
│ 2. Linter & Style                    │ ruff check backend/                    │
│ 3. Static Type Analysis              │ mypy backend/                          │
│ 4. Unit & Integration Tests          │ pytest backend/tests/                  │
│ 5. Test Coverage Gate                │ pytest --cov=backend --cov-fail-under=90│
│ 6. Container Build                   │ docker compose build                   │
└──────────────────────────────────────┴────────────────────────────────────────┘
```
