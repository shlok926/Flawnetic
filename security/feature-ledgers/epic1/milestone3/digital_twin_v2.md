# FLAWNETIC
# FEATURE SECURITY & THREAT RECORD (FSTR)
## Feature: Enterprise Digital Twin Domain
**Epic:** 1 | **Milestone:** 3 | **Version:** 2.0 (Enterprise Refinement)

---

## 1. ASSETS
1. **Runtime Digital Twin Graph:** Operational representation for AI/Testing execution.
2. **Knowledge Twin Graph:** Semantic business logic inferences.
3. **TwinChangeSets:** Classified vulnerability drift diffs.
4. **Twin Projection Read Models:** Cached Neo4j graph data.

## 2. TRUST BOUNDARIES
- **Event Bus Boundary:** Only authenticated producers (State/Evidence Contexts) can emit `Twin` lifecycle events.
- **TQL Boundary:** AI Agents cannot execute raw Cypher queries. They must use the Abstract Twin Query Language (TQL), which is strictly parsed and parameterized to prevent injection.
- **Tenant Isolation Boundary:** Graph queries must carry a cryptographically verified `TenantId`.

## 3. ENTERPRISE THREAT MODEL (RED TEAM REVIEW)

| ID | Threat | Root Cause | Impact | Likelihood | Mitigation & Residual Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T1** | **Graph Traversal DoS** | Maliciously crafted unbounded graph query causing 100% CPU on Neo4j. | HIGH | Medium | **Control:** TQL Enforcer limits maximum traversal depth (e.g., Depth=5) and timeout (50ms). *Residual Risk:* Sub-optimal queries may still cause latency spikes. |
| **T2** | **Cypher/TQL Injection** | AI Agent hallucinates a malicious query payload. | CRITICAL | Low | **Control:** TQL operates via the Specification Pattern. Queries are built programmatically via ASTs, eliminating string concatenation. |
| **T3** | **Cross-Tenant Graph Leakage** | Missing partition key in a read query. | CRITICAL | Low | **Control:** Repository layer auto-injects `TenantId` prefixes into every physical query. Devs cannot manually omit it. |
| **T4** | **Rollback Privilege Escalation** | Low-privilege user initiates rollback to vulnerable twin. | HIGH | Low | **Control:** Strict RBAC (`Twin_Admin`). Rollbacks emit `TwinRollbackInitiated` audit events for alerting. |
| **T5** | **Race Condition (Exploiting Eventual Consistency)** | Testing engine reads stale projection right after evidence ingestion. | MEDIUM | High | **Control:** API Gateway issues a `RevisionToken`. Clients demanding strict consistency pass this token; query blocks until projection reaches that revision. |
| **T6** | **Twin Component Poisoning via Vector DB** | Injecting semantically misleading components to confuse AI similarity searches. | HIGH | Medium | **Control:** Vector Indexing only occurs *after* the `Certified` boundary is crossed and Lineage is cryptographically verified. |

## 4. SECURITY CONTROLS & ABUSE CASES
- **Control 1: Tenant-Based Partitioning:** Physical or logical sharding in the DB ensures a compromised tenant graph cannot traverse into another tenant's nodes.
- **Control 2: Zero-Trust AI (Read-Only):** AI is physically isolated from the write-repositories (`ICommandDigitalTwinRepository`).
- **Abuse Case:** Attacker replays historical `EvidenceVerified` events to duplicate Twin Nodes.
- *Blocked by:* Event Sourcing Idempotency. Consumers track processed Event IDs; duplicates are silently discarded.

## 5. SECURITY TESTS & MONITORING
- **Tests Required:** 
  1. `test_tql_prevents_unbounded_traversal` (Property test).
  2. `test_tenant_isolation_graph_query` (Contract test).
  3. `test_read_after_write_consistency_token` (Integration test).
- **Monitoring Alerts:**
  - Alert if `TQL_Timeout_Rate` > 1% (Indicates DoS attempt or graph corruption).
  - Alert if `Stale_Twin_Reads` > 100/hr (Indicates projection rebuilding failure).

## 6. VERSION HISTORY
- **v1.0** (2026-08-04): Initial Architecture Security Review.
- **v2.0** (2026-08-04): ARB Enterprise Refinements (TQL Injection, Graph DoS, Race Conditions, Vector Poisoning).
