# SiteSentinel AI
### Autonomous End-to-End Website Testing & Enterprise Bug Reporting Platform

> **Working name:** SiteSentinel AI — rename freely once you finalize branding.

## What is this?
SiteSentinel AI is a tool that takes **only a website URL** and autonomously:
1. Crawls the entire site (every page, button, form, link)
2. Tests it from every angle — **functional, security, accessibility, cross-browser/device, usability, visual**
3. Captures evidence (screenshots, DOM snapshots, console/network logs) for every bug found
4. Auto-generates a **professional, enterprise-grade Bug Report (PDF)** with severity/priority, steps to reproduce, and embedded screenshots — with zero manual scripting.

## Why this exists (the gap)
Today's market splits this work across many disconnected tools:
- Functional/visual/accessibility AI testing → testRigor, mabl, Katalon
- Security scanning (DAST) → OWASP ZAP, Burp Suite
- Accessibility → axe DevTools, Lighthouse
- Cross-browser/device → BrowserStack, LambdaTest
- Bug reporting → Marker.io, BugHerd, manual Jira tickets

No single affordable tool **autonomously crawls a full site with zero scripting** AND **unifies all 4 testing dimensions** AND **outputs a client-ready evidence-backed PDF report** in one pass. That's the product gap SiteSentinel AI fills.

See full competitive breakdown in [`08-COMPETITIVE-ANALYSIS-USP.md`](./08-COMPETITIVE-ANALYSIS-USP.md).

## Document Index

| Doc | Purpose |
|---|---|
| [`01-PRD.md`](./01-PRD.md) | Product Requirements — goals, users, use cases, features, success metrics |
| [`02-ARCHITECTURE.md`](./02-ARCHITECTURE.md) | System design, modules, data flow, how everything connects |
| [`03-TECH-STACK.md`](./03-TECH-STACK.md) | Exact technologies, libraries, and why each was chosen |
| [`04-DATABASE-SCHEMA.md`](./04-DATABASE-SCHEMA.md) | Tables, relationships, sample data model |
| [`05-API-SPEC.md`](./05-API-SPEC.md) | REST API endpoints for the platform |
| [`06-BUG-REPORT-TEMPLATE.md`](./06-BUG-REPORT-TEMPLATE.md) | The exact structure the AI fills to generate the final PDF report |
| [`07-ROADMAP.md`](./07-ROADMAP.md) | Phased build plan — MVP → Phase 2 → Phase 3, with timelines |
| [`08-COMPETITIVE-ANALYSIS-USP.md`](./08-COMPETITIVE-ANALYSIS-USP.md) | Existing tools, their gaps, and our USP |

## Suggested order to read/build
`PRD → ARCHITECTURE → TECH-STACK → DATABASE-SCHEMA → API-SPEC → BUG-REPORT-TEMPLATE → ROADMAP`. Use `COMPETITIVE-ANALYSIS-USP` for pitching/resume/investor-style framing.

## Quick start (once code begins)
```bash
git clone <your-repo>
cd sitesentinel-ai
docker-compose up -d        # spins up ZAP, Postgres, Redis
pip install -r requirements.txt --break-system-packages
playwright install
python run.py --url https://example.com
```
(Full setup details will live in the repo's own README once code starts — this doc set is the **pre-code blueprint**.)
