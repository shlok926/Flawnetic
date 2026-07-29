# Product Requirements Document (PRD)

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Product Requirements Document |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `00-PROBLEM-STATEMENT.md`, `02-TRD.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Objective
Define **what** the product must do for its users — independent of *how* it is technically built (that is covered in the TRD and Architecture docs).

## 2. Product Summary
Flawnetic is an autonomous website QA platform. A user submits a URL; the system crawls the site, executes functional, security, accessibility, cross-browser/device, and usability tests against it with no manual scripting, and produces a single professional bug report with embedded evidence.

## 3. User Personas
| Persona | Goal |
|---|---|
| **Freelance QA/SDET (Priya)** | Run a complete audit for a client in under an hour, deliver a polished report |
| **Startup Founder (Raj)** | Sanity-check the site before launch without hiring QA |
| **Agency QA Lead (Meera)** | Standardize bug reporting across multiple client projects |
| **Student/Portfolio builder (you)** | Produce a real, demonstrable, professional QA artifact |
| **Enterprise QA Engineer (Phase 3)** | Add an automated pre-release gate in CI/CD |

## 4. User Stories
- As a user, I can submit a URL and receive a crawled sitemap without writing any code
- As a user, I can choose which test modules to run (functional/security/accessibility/visual/usability) per scan
- As a user, I can see live progress while a scan runs
- As a user, every bug found includes a screenshot and clear reproduction steps
- As a user, I receive one downloadable PDF report with an executive summary, charts, and detailed findings
- As a user, I can re-run a scan later and see what changed since the previous run
- As an agency user, I can label the report with my own branding (Phase 3)
- As an enterprise user, I can trigger a scan from CI/CD and fail the build on critical findings (Phase 3)

## 5. Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | System shall accept a root URL and crawl internal links up to a configurable depth/page limit | Must |
| FR-2 | System shall identify all interactive elements per page (buttons, forms, inputs, links, dropdowns) | Must |
| FR-3 | System shall generate positive and negative test data for each input field (empty, overflow, special characters, numeric-only, etc.) | Must |
| FR-4 | System shall execute a security scan (OWASP Top 10 coverage) against discovered pages/endpoints | Must |
| FR-5 | System shall run WCAG 2.1 AA accessibility checks on every discovered page | Should |
| FR-6 | System shall execute the same test flows across multiple browsers and at least one mobile viewport | Should |
| FR-7 | System shall capture a screenshot, DOM snapshot, console log, and network log for every failure | Must |
| FR-8 | System shall classify each finding's severity and priority | Must |
| FR-9 | System shall generate a human-readable bug description (title, steps, expected/actual) per finding | Must |
| FR-10 | System shall export a single PDF report containing an executive summary, metrics charts, and detailed findings | Must |
| FR-11 | System shall allow the user to filter/view findings by module, severity, and page before export | Should |
| FR-12 | System shall require explicit user confirmation of authorization to test the target URL before running security scans | Must |

## 6. Non-Functional Requirements
| ID | Requirement |
|---|---|
| NFR-1 | A scan of a 50-page site should complete and produce a report within 15 minutes (MVP target) |
| NFR-2 | The platform must not perform any destructive action against the target site (read-only/safe-payload testing only) |
| NFR-3 | Evidence artifacts (screenshots, logs) must be retained for at least 30 days and deletable on request |
| NFR-4 | The system must scale horizontally to run multiple scans concurrently (queue-based worker design) |
| NFR-5 | All security findings must include supporting evidence — no "claimed" vulnerability without a reproducible request/response or screenshot |
| NFR-6 | Report PDF must render correctly when opened in standard PDF viewers (no broken layout, embedded fonts) |

## 7. Assumptions
- MVP targets unauthenticated, publicly accessible pages (login-gated flows are Phase 3)
- The user submitting a scan owns or has explicit permission to test the target site
- Initial usage is single-tenant per scan (no real-time collaboration in MVP)

## 8. Constraints
- LLM (Claude API) usage must be cost-bounded per scan via max page/depth limits
- Security scanning depends on OWASP ZAP's detection capabilities and inherits its known limitations (cannot validate business-logic flaws)
- Accessibility automation covers an estimated 20–40% of real-world WCAG issues (industry-wide limitation of automated tools) — must be disclosed in every report

## 9. Success Metrics
| Metric | Target |
|---|---|
| Time to first report (50-page site) | < 15 minutes |
| Bug coverage vs. manual QA baseline | ≥ 80% (benchmarked against OWASP Juice Shop) |
| Security false-positive rate | < 15% |
| Report usable as-is for client delivery | Yes, with no manual rework |

## 10. Release Criteria (MVP)
- Crawler reliably discovers ≥ 95% of internal pages on a test site with standard navigation
- Functional engine produces at least one valid finding on a known-buggy demo app
- Report PDF generates without manual intervention end-to-end

## 11. Out of Scope (MVP and near-term)
- Native mobile app testing
- Load/stress testing
- Manual exploratory session recording
- Authenticated/multi-step login flows (until Phase 3)
