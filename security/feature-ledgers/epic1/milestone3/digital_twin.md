# FLAWNETIC
# FEATURE SECURITY & THREAT RECORD (FSTR)
## Feature: Enterprise Digital Twin Domain
**Epic:** 1 | **Milestone:** 3 | **Version:** 1.0

---

## 1. ASSETS
1. **Digital Twin Graph:** The canonical repository of target application intelligence.
2. **Twin Versions:** Point-in-time snapshots of application architecture.
3. **ChangeSets:** The diff logic highlighting vulnerability drift.
4. **Certification Scores:** Confidence/Freshness metrics used for AI reasoning.

## 2. TRUST BOUNDARIES
- **Event Bus Boundary:** The Twin Domain consumes events exclusively from the authenticated Kafka Event Bus (State Context and Evidence Context).
- **Read/Query Boundary:** AI Agents and Testing Engines access the Twin strictly through Read-Only APIs (`ITwinProjectionRepository`).
- **Administrative Boundary:** Rollback and archiving require `Twin_Admin` JWT claims.

## 3. THREAT MODEL

| ID | Threat | Root Cause | Impact | Likelihood | Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T1** | **Twin Poisoning** | Malicious injection of unverified states/evidence bypassing the pipeline. | CRITICAL | Low | Domain explicitly requires cryptographically verified `EvidenceVerified` and `StateActivated` events. Direct database inserts are rejected. |
| **T2** | **Version Tampering** | Retroactively altering a certified Twin snapshot to hide a vulnerability. | HIGH | Low | TwinVersions transition to an immutable `Certified` state. Append-only logic enforced at repository layer. |
| **T3** | **Rollback Abuse** | Forcing the testing engine to run against a stale, vulnerable Twin version. | HIGH | Medium | Rollback generates a new distinct version (`v3 = clone of v1`), and requires `Twin_Admin` RBAC. |
| **T4** | **Cross-Tenant Leakage** | Shared Graph DB edges bridging Tenant A and Tenant B. | CRITICAL | High | Strict `TenantId` prefixing on all graph nodes, edges, and search indexes (RLS pattern). |
| **T5** | **Stale Twin Exploitation**| Stale/outdated logic leads to false-positive AI reports. | MEDIUM | High | Certification engine continuously degrades the `Freshness` score. Queries return a `StaleWarning` if freshness < 0.5. |
| **T6** | **Denial of Service (DoS)**| Massive ChangeSet calculation causing worker OOM (Memory Exhaustion). | HIGH | Medium | Change Detection Engine streams diff processing and caps max graph comparison depth. |

## 4. SECURITY CONTROLS & ABUSE CASES
- **Control 1: Immutable Pointers:** `Twin v(n)` shares pointers with `Twin v(n-1)`. Modification attempts on a shared component result in an Optimistic Locking failure.
- **Control 2: Zero-Trust AI:** AI models querying the Digital Twin operate with read-only scoped tokens.
- **Abuse Case:** Attacker attempts to flood the Digital Twin with fake components. *Blocked by:* Event Bus authentication and State Context's rate-limiting circuit breakers.

## 5. ACCEPTED RISKS
- **Risk 1:** Temporary desynchronization (Eventual Consistency) between the actual target app and the Digital Twin representation. Accepted as a natural consequence of the Discovery crawl latency.

## 6. SECURITY TESTS & MONITORING
- **Tests Required:** 
  1. `test_twin_poisoning_rejection` (Simulate forged events).
  2. `test_cross_tenant_graph_isolation` (Verify Tenant A cannot query Tenant B's components).
  3. `test_rollback_rbac_enforcement`.
- **Monitoring Alerts:**
  - Alert if `Twin_Drift` > 30% in a single day.
  - Alert if `Failed_Event_Consumptions` > 10/min (Indicates poisoning attempts or schema drift).

## 7. VERSION HISTORY
- **v1.0** (2026-08-04): Initial Architecture Security Review (Epic 1, Milestone 3, Stage 1).
