# FLAWNETIC
# EPIC 1 — MILESTONE 3 — STAGE 1
## ENTERPRISE DIGITAL TWIN DOMAIN (v2.0)
### Status: ARCHITECTURE SPECIFICATION (FINAL)
### Review ID: EPIC1-M3-STAGE1-ARB-REFINEMENT

---

## 1. RUNTIME DIGITAL TWIN VS KNOWLEDGE TWIN
The architecture splits the Twin into two explicit Read Models (CQRS Projections) to prevent scaling limits at 100M+ nodes:
- **Runtime Twin (Operational Graph):** Highly volatile. Tracks current layouts, raw components, and transition triggers. Optimized for sub-50ms AI navigation and testing execution.
- **Knowledge Twin (Semantic Graph):** Highly stable. Tracks AI-inferred business logic ("This is a Checkout Flow", "This endpoint processes PCI data"). Rebuilt asynchronously from Runtime Twin diffs.

## 2. PROJECTION LAYER ARCHITECTURE & GRAPH PARTITIONING
To survive 100M+ entities across thousands of tenants:
- **Projection Versioning:** Projections (`ITwinProjectionRepository`) are versioned. If the projection schema changes, a parallel Projection V2 is built from the immutable Event Log without downtime.
- **Graph Partitioning:** Multi-tenant graph DBs (Neo4j) suffer from query amplification. The architecture enforces strict **Tenant-Based Graph Partitioning**. A tenant's graph is physically isolated or sharded, guaranteeing zero cross-tenant query leakage and O(1) tenant localization.

## 3. COMPLETE TWIN IDENTITY MODEL & COMPONENT LINEAGE
- `TwinId`: UUID.
- `TwinVersionId`: Semantic (e.g., `v1.4.2`).
- `NodeId`: Cryptographic hash derived from Evidence's `LogicalEvidenceId`.
- **Lineage:** Every `TwinComponent` tracks `origin_evidence_id` and `mutated_by_transition_id`. A node cannot exist if its evidence lineage is broken.

## 4. CONFIDENCE & FRESHNESS DECOMPOSITION
- **Confidence Matrix:** 
  - `StructuralConfidence` (Hash matches).
  - `EvidenceConfidence` (Evidence signatures valid).
  - `SemanticConfidence` (AI inference probability).
- **Freshness Matrix:**
  - `TemporalFreshness` (Days since last scan).
  - `VelocityDrift` (Expected change vs actual). If a target deploys daily, freshness decays to 0.0 in 24 hours.

## 5. DIGITAL TWIN HEALTH MODEL & VALIDATION PIPELINE
- **Health Indicators:** `OrphanedNodeRatio`, `UnverifiedEvidenceRatio`, `GraphCycleCount`, `ReplaySuccessRate`.
- **Validation Pipeline:** Before a `TwinVersion` becomes `Certified`, it must pass: Graph Integrity Check -> Lineage Verification Check -> Policy Check -> Certification Engine.

## 6. CHANGE CLASSIFICATION ENGINE
`TwinChangeSet` now classifies changes into actionable severity tiers:
- `MINOR`: CSS changes, static text updates.
- `MAJOR`: New DOM nodes, new API endpoints, removed components.
- **`CRITICAL`:** Authentication flow changed, Authorization boundaries moved, forms requesting new PII fields.

## 7. ABSTRACT TWIN QUERY LANGUAGE (TQL)
To decouple downstream AI and Testing Engines from Cypher/Gremlin, we introduce an **Abstract Twin Query Language (TQL)** via the Specification Pattern.
*Example:* `TQL.find(Components).where(Semantic == "Login").within(Version == "latest")`.
This allows swapping Neo4j for Amazon Neptune or ArangoDB transparently.

## 8. EXPANDED DOMAIN EVENT CATALOG
- `TwinProjectionRebuilding`: Saga initiation for rebuilding read models.
- `TwinChangeClassified`: Emitted by Change Engine when a `CRITICAL` diff is detected.
- `TwinHealthDegraded`: Emitted when Freshness drops below threshold.

## 9. OBSERVABILITY & PERFORMANCE BUDGETS
- **Budgets (100M Node Scale):** 
  - Max Graph Traversal (Depth 5): < 20ms.
  - TQL to Cypher translation: < 2ms.
  - Twin Projection Update: < 500ms (Eventual Consistency limit).
- **Observability:** Distributed tracing (OpenTelemetry) traces the path from `EvidenceVerified` event to `TwinNodeInserted` event.

---

## 10. ARB SECOND REVIEW & ENTERPRISE MATURITY (INDEPENDENT REVIEW)

**Critique 1: What breaks at 100 million entities?**
- *Issue:* A single Kafka partition for `TwinUpdated` events will bottleneck.
- *Fix:* Topic partitioning must be strictly keyed by `TenantId` to guarantee order per tenant while scaling horizontally across partitions.

**Critique 2: What blocks future evolution?**
- *Issue:* Tying the Twin directly to specific ML model outputs.
- *Fix:* Enforced the **AI Governance** rule. AI only produces `AIProposalEvents`. The Twin domain remains deterministic. Semantic nodes are separated into the Knowledge Twin.

**Critique 3: Can eventual consistency become exploitable?**
- *Issue:* An attacker submits evidence, then immediately queries the Twin before the projection updates, causing a race condition in security tests.
- *Fix:* The API Gateway provides a `RevisionToken`. Queries can optionally supply this token to demand `Read-After-Write` consistency, forcing the read query to wait for the projection to catch up.

## 11. INDEPENDENTLY DISCOVERED MISSING FEATURES
- **Semantic Indexing (Vector DB):** Alongside the Graph DB, `TwinComponents` should be simultaneously indexed into a Vector Database (Milvus/Qdrant) to allow AI agents to perform semantic similarity searches (e.g., "Find all components that look like a payment gateway").
- **Snapshot Compaction:** Retaining every single version forever is too costly. Added `Snapshot Compaction`: Every 30 versions, a Full Snapshot is saved, and intermediate `TwinChangeSets` are archived to cold storage, keeping the operational graph lightweight.

## 12. FINAL CERTIFICATION DECISION
🟢 **FULLY APPROVED.**
The architecture successfully leverages CQRS, Event Sourcing, Domain-Driven Design, and Graph Partitioning. It is resilient, decoupled, AI-safe, and capable of operating at massive enterprise scale. 
**Decision:** Freeze the Digital Twin v2.0 Architecture. All future modifications must occur via Architectural Decision Records (ADRs).
