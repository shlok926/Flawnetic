# Design Document

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Design Document |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Related Docs** | `01-PRD.md`, `02-TRD.md`, `05-ARCHITECTURE.md` |
| **Last Updated** | 24 June 2026 |

---

## 1. Purpose
This document defines the **UX/UI design decisions**, key **user flows**, **component structure**, and **design system** for the platform's web dashboard. It also captures major **design decisions** made during architecture and product scoping — with rationale.

---

## 2. Design Principles
| Principle | Meaning in this product |
|---|---|
| **Zero friction start** | From landing page to first scan running: ≤ 3 clicks. No signup required for a limited free trial run |
| **Evidence-first UI** | Every finding leads immediately to screenshot + logs — no hunting for proof |
| **Progressive disclosure** | Executive summary upfront; technical detail available on drill-down. Non-technical users should not be overwhelmed |
| **Honest reporting** | Never overstate coverage. Automated-tool limitations are clearly stated in report and dashboard, not buried |
| **Mobile-readable dashboard** | While the tool tests websites, the person reviewing results may be on a phone while with a client |

---

## 3. User Flows

### 3.1 Primary Flow — New Scan (First-Time User)
```
[Landing Page]
    → Enter URL + tick "I own / am authorized to test this site"
    → (Optional) Configure: max pages, modules, browsers
    → Click "Start Scan"
    → [Live Progress Screen]
         Crawl progress bar: pages discovered
         Per-module status indicators (Functional ✓ / Security running… / Accessibility queued)
         Real-time finding counter ticking up as bugs are discovered
    → [Scan Complete]
         Summary card: X pages, Y bugs, severity donut chart
         "View Report" + "Download PDF" buttons
    → [Report View] (see Section 5)
```

### 3.2 Returning User — Compare Runs
```
[Dashboard — Project History]
    → Select project → see all past scan runs with date, bug count, trend line
    → Click "Compare" between two runs
    → [Diff View]: new findings (🔴), fixed (✅), unchanged (🟡)
    → Export comparison PDF
```

### 3.3 Developer / CI User (Phase 3)
```
CLI: sitesentinel scan --url https://example.com --fail-on critical
    → Returns exit code 1 if critical findings found
    → Uploads report artifact to CI pipeline
    → Slack/Jira notification sent
```

---

## 4. Screen Designs (Wireframe Descriptions)

### 4.1 Landing / Home Page
- Hero: large URL input bar, CTA button "Scan this site"
- Subtext: what modules run, what the report looks like
- Sample report screenshot (social proof)
- "No signup required for your first scan" trust badge

### 4.2 Scan Configuration Screen
```
┌─────────────────────────────────────────────────────────┐
│  Target URL:  [ https://example.com          ] [Scan ▶] │
├─────────────────────────────────────────────────────────┤
│  Test Modules:                                           │
│  ☑ Functional   ☑ Security   ☑ Accessibility            │
│  ☑ Cross-Browser/Device   ☑ Usability & Performance     │
├─────────────────────────────────────────────────────────┤
│  Browsers:  ☑ Chrome   ☑ Firefox   ☑ Safari (WebKit)   │
│  Devices:   ☑ Desktop  ☑ Mobile (iPhone 14 emulation)  │
├─────────────────────────────────────────────────────────┤
│  Advanced:  Max Pages [50▾]   Max Depth [4▾]            │
├─────────────────────────────────────────────────────────┤
│  ☑ I own or have written authorization to test this URL │
│                                       [Start Scan ▶]   │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Live Progress Screen
```
┌─────────────────────────────────────────────────────────┐
│  Scanning: https://example.com              [Cancel]    │
│  ──────────────────────────────────── 34 / 50 pages    │
│                                                          │
│  Functional       ██████████░░░░░░  Running (18 done)  │
│  Security         ██████████████░░  Running            │
│  Accessibility    ████████████████  Done ✓             │
│  Cross-Browser    ░░░░░░░░░░░░░░░░  Queued             │
│  Usability        ░░░░░░░░░░░░░░░░  Queued             │
│                                                          │
│  Findings so far: 🔴 2 Critical  🟠 4 High  🟡 3 Medium │
│                                                          │
│  Latest finding:  "Remarks field accepts SQL strings"   │
│  (live feed ↓)                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.4 Dashboard — Project List
- Card per project: name, URL, last scan date, last scan bug count with severity pills, "New Scan" button
- Trend sparkline (bugs over last N scans)

### 4.5 Finding Detail View
```
┌─────────────────────────────────────────────────────────┐
│  [🔴 Critical]  SS-014 — Checkout form accepts XSS     │
│  Module: Security | Page: /checkout                     │
├──────────────────────┬──────────────────────────────────┤
│  Steps to Reproduce: │  SCREENSHOT                      │
│  1. Navigate to /    │  [embedded image]                │
│     checkout         │                                  │
│  2. Enter            │                                  │
│     <script>alert(1) │  [View DOM Snapshot]             │
│     </script> in     │  [Download Console Log]          │
│     Name field       │  [Download Network HAR]          │
│  3. Click Place Order│                                  │
│                      │                                  │
│  Expected: Error msg │                                  │
│  Actual: Script runs │                                  │
├──────────────────────┴──────────────────────────────────┤
│  Root Cause Hint (AI): Missing server-side input        │
│  sanitization; no Content-Security-Policy header        │
│  Recommendation: Sanitize all user inputs server-side;  │
│  implement strict CSP                                    │
└─────────────────────────────────────────────────────────┘
```

### 4.6 Report View (in-browser, before PDF download)
- Page 1–2: Executive Summary + Metrics Charts (donut, bar, pass/fail %)
- Page 3+: Findings (sorted Critical → Low), one block per finding, screenshot embedded
- Appendices: Security (OWASP mapping), Accessibility (WCAG criterion), Cross-browser matrix, Performance table
- Last page: Sitemap of all pages tested + disclaimer

---

## 5. Design System

### Colors
| Role | Value | Usage |
|---|---|---|
| Primary | `#6366F1` (Indigo) | Buttons, active states, links |
| Danger/Critical | `#EF4444` | Critical severity badge |
| Warning/High | `#F97316` | High severity badge |
| Caution/Medium | `#EAB308` | Medium severity badge |
| Info/Low | `#3B82F6` | Low severity badge |
| Success | `#22C55E` | Passed tests, resolved findings |
| Background | `#0F172A` | Dark mode (primary) |
| Surface | `#1E293B` | Cards, panels |
| Text Primary | `#F1F5F9` | Headings |
| Text Secondary | `#94A3B8` | Metadata, labels |

### Typography
| Level | Font | Weight | Size |
|---|---|---|---|
| H1 | Inter | 700 | 32px |
| H2 | Inter | 600 | 24px |
| H3 | Inter | 600 | 18px |
| Body | Inter | 400 | 14px |
| Code/selector | JetBrains Mono | 400 | 13px |

### Component Library
- Built with React + Tailwind CSS utility classes
- Severity badge: `<SeverityBadge level="critical|high|medium|low" />`
- Finding card: collapsible, includes evidence thumbnails
- Progress bar: per-module with status enum (queued/running/done/failed)
- Chart: Chart.js donut + bar, rendered server-side for PDF embedding

---

## 6. Key Design Decisions (with Rationale)

| Decision | Options Considered | Chosen | Rationale |
|---|---|---|---|
| Dark vs light dashboard | Light / Dark | **Dark** | QA/dev audience; bug evidence screenshots (often white-background sites) pop better on dark background |
| Report format | PDF only / HTML only / Both | **HTML (interactive) + PDF (export)** | HTML allows click-to-zoom screenshots, collapsible details; PDF for client email attachment |
| AI writes bug text or human-readable template | Template strings / LLM generation | **LLM for narrative, deterministic for data** | Data fields (selector, URL, severity) are deterministic; human-readable title/steps/root-cause are where LLM adds real value |
| Single-page app vs multi-page | SPA (React) / MPA | **SPA** | Live scan progress needs real-time state updates; SPA handles WebSocket/SSE naturally |
| Scan trigger UX | Wizard / Single screen | **Single screen with progressive reveal** | Reducing friction is a core principle; wizard adds steps |
