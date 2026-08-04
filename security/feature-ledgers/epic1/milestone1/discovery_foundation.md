# FLAWNETIC
# FEATURE SECURITY & THREAT RECORD (FSTR)
**Feature:** Epic 1 - Discovery Foundation (Fingerprinting & Link Discovery)
**Location:** security/feature-ledgers/epic1/milestone1/discovery_foundation.md

---

## 1. Feature Overview
**Purpose:** Provides an event-driven, plugin-based enterprise discovery platform to map target applications without executing untrusted client-side code prematurely.
**Business Value:** Safely generates the Application Graph & Digital Twin, reducing CI/CD crawl times via incremental discovery.
**Architecture Summary:** Includes the `ApplicationFingerprintEngine`, `LinkDiscoveryPlugin`, `DiscoverySession`, and an abstract `EventBus`.
**ADR References:** ADR-001 (Graph Modeling), ADR-005 (Discovery Sessions), ADR-006 (Evidence Graph).
**Dependencies:** `BeautifulSoup`, `lxml`, `pydantic`.

---

## 2. Security Ownership
**Security Owner:** Discovery Platform Team
**Review Required By:** Security Architecture Board
**Next Review:** Epic 1 Milestone 2

---

## 3. Security Requirements
1. Only `http`/`https` schemas are allowed in discovery.
2. Maximum DOM parsing size is strictly 5MB.
3. All Plugin outputs must be frozen, immutable entities.
4. No untrusted JavaScript execution during static fingerprinting.
5. No external resource loading (images, scripts) during static discovery.
6. Plugins must not maintain mutable global or instance state.
7. Knowledge Contracts are mandatory for event publishing.

---

## 4. Assumptions & Out of Scope
**Assumptions:**
- `BeautifulSoup` behaves correctly.
- `lxml` is patched and not vulnerable to existing CVEs.
- The Python runtime is trusted.
- The Discovery Worker operates in network isolation.
- OS permissions are configured correctly (non-root container).

**Out of Scope:**
- Browser exploitation / V8 vulnerabilities.
- Kernel-level exploits.
- Supply chain compromise of third-party libraries.
- OS sandbox escape.

---

## 5. Assets Protected & Trust Boundaries
**Assets:**
- Discovery Session State
- Knowledge Graph / Digital Twin
- Plugin Contracts (Entities)
- Worker Node Memory/CPU

**Trust Boundaries:**
- Target Website (Untrusted) <-> Plugin (Parsing Boundary)
- Plugin (Sanitization Boundary) <-> Event Bus (Trusted Internal)

---

## 6. Attack Surface
- **Inputs:** HTTP Headers (`Server`, `X-Powered-By`), Raw HTML (`html_content`), Raw URLs (`href` attributes).
- **Outputs:** Emitted JSON events (`TechnologyFingerprintEntity`, `LinkEntity`).

---

## 7. Threat Model (STRIDE)
| Threat | Description | Likelihood | Impact | Risk | Affected Assets |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | Target spoofs `X-Powered-By: React` or `<div id="__next">` to deceive the AI engine. | High | Low | Low | Digital Twin |
| **Tampering (XSS)** | Target embeds `<a href="javascript:alert(1)">`. | High | Critical | Critical | Worker Node / Later execution stages |
| **Denial of Service** | Target serves a 50MB HTML file to cause OOM in BeautifulSoup. | Medium | High | High | Worker Node Memory |
| **Denial of Service** | Target serves 50,000 duplicated SEO tracking links (`?utm_source=...`) to cause cyclic loops. | High | High | High | Worker Node CPU / DB Storage |

---

## 8. Future Threats (Horizon Tracking)
- Service Worker Manipulation
- WebAssembly extraction and static analysis
- Dynamic hydration masking true application state
- Advanced anti-bot defenses
- AI-generated dynamic DOM structures designed to poison the crawler

---

## 9. Abuse Cases
### Link Bombing (Resource Exhaustion)
- **Goal:** Crash the crawler worker.
- **Technique:** Serve an infinite sequence of nested `<div>` or thousands of unique URLs on a single page.
- **Expected Outcome:** OOM Exception in the python process.
- **Mitigation:** Implemented a strict `MAX_DOM_BYTES = 5MB` truncation in both `ApplicationFingerprintEngine` and `LinkDiscoveryPlugin`.

### XSS Injection via URI
- **Goal:** Execute arbitrary code when Flawnetic later renders the link in a headless browser.
- **Technique:** Anchor tags with `javascript:` or `data:` payloads.
- **Mitigation:** Strict `DANGEROUS_SCHEMAS` deny-list in `LinkDiscoveryPlugin.normalize()`.

---

## 10. Security Controls
- **Resource Limits:** Hard truncation of HTML content at 5MB.
- **Output Validation:** Pydantic `ConfigDict(frozen=True)` ensures strictly typed, immutable outputs.
- **Isolation:** Stateless plugin architecture prevents cross-page data contamination.
- **URL Normalization:** Strips tracking query parameters to enforce deduplication.

---

## 11. Security Decision Log (Residual Risks)
**Accepted Risk ID:** SR-001
**Description:** DOM larger than 5MB may lose valid links located at the bottom of the document.
**Reason:** Must protect worker stability and prevent OOM attacks (Billion Laughs).
**Alternatives Considered:** Streaming HTML parser.
**Rejected Because:** Implementation complexity outweighed the rare benefit of 5MB+ valid documents.
**Review Frequency:** Annually.
**Owner:** Discovery Platform Team.

---

## 12. Attack Simulation Matrix (Validation)
| Threat | Simulation | Expected Result | Result Status |
| :--- | :--- | :--- | :--- |
| DOM Bomb / Memory Exhaust | Provide 50MB HTML string | Truncated safely at 5MB | ✅ Passed |
| Duplicate Storm | Pass 5,000 URLs varying only by `utm_source` | De-duplicated to 1 URL | ✅ Passed |
| Dangerous URI Scheme | Pass `<a href="javascript:alert(1)">` | Dropped entirely | ✅ Passed |
| Spoofed Framework | Supply fake React DOM ID markers | Detected, but low confidence score assigned | ✅ Passed |
| Malformed HTML | Supply `<<<<>` broken tags | Graceful fallback, no parser crash | ✅ Passed |

---

## 13. Monitoring & Incident Response
**Indicators of Compromise (IoCs):**
1. High `DOM truncation count`.
2. `Duplicate rate > 90%`.
3. Frequent `PluginFailed` events emitted on the Event Bus.

**Incident Response:**
1. Isolate the `DiscoverySession` and pause the crawl.
2. Review the truncated DOM evidence.
3. Automatically ban the domain/tenant from automated scheduling.

---

## 14. Security Metrics
- **Threats Identified:** 4
- **Threats Mitigated:** 4
- **Accepted Risks:** 1 (SR-001)
- **Security Test Pass Rate:** 100%

---

## 15. Security Regression History
- **v1.0** (2026-08-04) - Initial creation for Epic 1 Discovery Foundation (Fingerprinting & Link Plugins). DOM limits and schema filters applied.
