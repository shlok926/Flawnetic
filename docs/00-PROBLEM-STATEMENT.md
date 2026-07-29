# Problem Statement (PS)

| Document Control | |
|---|---|
| **Project** | Flawnetic *(name pending finalization)* |
| **Document Type** | Problem Statement |
| **Version** | 1.0 |
| **Status** | Draft |
| **Author** | Shlok Thorat (MatrixX) |
| **Last Updated** | 24 June 2026 |

---

## 1. Background
Modern websites must function correctly, stay secure, remain accessible to all users, and render consistently across browsers and devices before they can be considered "production ready." Today, validating all of this requires a QA team to operate **five or more separate tools** — one for functional automation, one for security scanning, one for accessibility, one for visual/cross-browser checks, and one for bug tracking/reporting — each with its own setup, license, and learning curve.

## 2. Problem Definition
Small teams, freelance QA engineers, agencies, and students do not have the budget, time, or headcount to run a full enterprise QA stack (e.g., Burp Suite + BrowserStack + Applitools + ACCELQ, collectively $10,000–$80,000+/year) before shipping or handing over a website. As a result:
- Websites ship with undiscovered functional bugs, security gaps, accessibility violations, and cross-browser inconsistencies
- QA engineers spend disproportionate time manually writing bug reports instead of finding bugs
- Clients/stakeholders receive inconsistent, non-standardized bug documentation (or none at all)

## 3. Current Alternatives & Their Limitations
| Alternative | Limitation |
|---|---|
| Manual QA testing | Slow, inconsistent coverage, depends on tester experience, no automatic evidence capture |
| testRigor / Katalon / mabl | Require authored test scenarios (even in plain English); not a zero-input full-site crawl; enterprise pricing |
| OWASP ZAP / Burp Suite | Security-only; no awareness of functional, accessibility, or visual issues |
| axe DevTools / Lighthouse | Accessibility/performance-only; standalone, not part of a unified report |
| BrowserStack / LambdaTest | Pure infrastructure (browsers/devices); no test intelligence of its own |
| Manual bug report writing (Word/Excel/Jira) | Time-consuming, inconsistent formatting, evidence attached manually |

**No existing solution autonomously tests an entire website across all major QA dimensions from a single URL input and outputs one consolidated, evidence-backed, professional report.**

## 4. Impact of the Problem
- Businesses launch with avoidable bugs that damage user trust and conversion
- Security vulnerabilities (e.g., missing input validation, exposed misconfigurations) go undetected pre-launch
- Accessibility non-compliance creates legal exposure (ADA/EAA) and excludes users with disabilities
- QA professionals (including students building portfolios) lack an affordable, comprehensive way to demonstrate full-spectrum testing skill

## 5. Proposed Solution (Summary)
A tool that takes a single website URL, autonomously crawls every page and interactive element, tests it across **functional, security, accessibility, cross-browser/device, and usability/performance** dimensions with zero manual scripting, and generates a **professional, enterprise-grade bug report** (with embedded screenshots and evidence) — at a fraction of the cost and setup time of assembling the equivalent enterprise toolchain.

Full detail in `01-PRD.md`.

## 6. Goals
- G1: Eliminate the need to manually write test scenarios for baseline site coverage
- G2: Unify functional, security, accessibility, visual, and usability testing into one pass
- G3: Auto-generate client-ready bug reports with embedded evidence
- G4: Make full-spectrum QA accessible to individuals/small teams, not just enterprises

## 7. Non-Goals (explicitly out of scope for this problem statement)
- Replacing certified/manual penetration testing for compliance audits (PCI-DSS, SOC 2)
- Native mobile app (iOS/Android) testing — mobile **web** is in scope, native apps are not
- Load/stress/performance-under-traffic testing
- Game testing

## 8. Stakeholders
| Stakeholder | Interest |
|---|---|
| Freelance QA engineers / SDETs | Faster, cheaper way to deliver professional audits |
| Startup founders / small dev teams | Pre-launch confidence without hiring a QA team |
| Digital agencies | Client-deliverable reports as part of website handover |
| QA/Cybersecurity students | Real, demonstrable, professional-grade project for portfolio |
| End users of tested websites (indirect) | Better functioning, safer, more accessible websites |
