# FLAWNETIC
# EPIC 1 — MILESTONE 2 — STAGE 3
## ENTERPRISE EVIDENCE GRAPH ARCHITECTURE (v2.0)
### Status: ARCHITECTURE SPECIFICATION (FINAL REFINEMENT)
### Review ID: EPIC1-M2-STAGE3-ARB-002

---

## 1. EVIDENCE PROVENANCE & CHAIN OF CUSTODY (Refinement 1)
Evidence cannot be anonymous. The `EvidenceMetadata` Value Object is expanded to include a complete **Provenance Chain**:
- `CollectionMethod`: (e.g., Playwright network intercept, DOM snapshot).
- `PluginVersion`, `SessionVersion`, `WorkerId`, `TenantId`, `CorrelationId`.
- `ParentEvidenceId`: Points to previous evidence if this artifact was derived.
- `CaptureTimestamp`, `CollectionConfidence`, `IntegrityStatus`.

## 2. CRYPTOGRAPHIC INTEGRITY MODEL (Refinement 2)
To ensure verifiable trust, `ContentHash` is expanded to a `CryptographicSignature` Value Object:
- `ContentHash` (SHA-256).
- `ContentSignature` (RSA/ECDSA signature of the hash).
- `SignatureAlgorithm`.
- `VerificationStatus` (Valid, Invalid, Tampered).
*This guarantees that exported evidence can be independently cryptographically verified by auditors.*

## 3. EVIDENCE VERSION GRAPH (Refinement 3)
Evidence nodes evolve via explicit relationships to support historical replay:
- `Original`: The raw baseline capture.
- `Supersedes`: Replaces previous flawed evidence.
- `DerivedFrom`: Processed evidence (e.g., a normalized DOM derived from a raw DOM).
- `MergedInto` / `SplitFrom`: For composite evidence artifacts.

## 4. EVIDENCE CLASSIFICATION (Refinement 4)
All Evidence must declare a `SensitivityClassification` to prepare for strict enterprise compliance:
- `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `SECRET`.

## 5. RETENTION POLICY & LIFECYCLE STATE MACHINE (Refinement 5 & 9)
Evidence nodes follow a strict, tenant-configurable lifecycle:
- **States:** `Collected -> Verified -> Referenced -> Archived -> Expired -> Deleted`.
- **Retention Tiers:** `Hot` (Redis/Memory), `Warm` (S3 Standard), `Cold` (S3 Glacier), `Archived`, `Destroyed`.

## 6. EVIDENCE LINEAGE (Refinement 6)
**The Golden Rule:** Every downstream object (State, Transition, Digital Twin Node, Knowledge Graph Entity, AI Finding) MUST contain an `EvidenceId` pointer. No inferred object may exist without cryptographic lineage back to raw evidence.

## 7. CQRS: EVIDENCE QUERY API (Refinement 8)
Read and Write paths are explicitly decoupled:
- **Write Repository (`ICommandEvidenceRepository`):** Optimized for atomic appends and integrity validation (Postgres).
- **Read / Search Repository (`IQueryEvidenceRepository`):** Optimized for Graph traversal and text search (Elasticsearch / OpenSearch).

## 8. EVIDENCE VALIDATION PIPELINE (Refinement 10)
Raw payloads must pass strict validation *before* reaching Immutable Storage:
`Schema Validation -> Size Validation -> Integrity Validation -> Malware Validation (Future) -> Policy Validation -> Classification -> Storage`.

## 9. REPOSITORY CONTRACT GUARANTEES (Refinement 7)
All repository adapters must guarantee:
- Idempotent writes (via ContentHash).
- Immutable updates (Appends only).
- Atomic creation (Metadata + Storage pointer).
- Hash uniqueness, Correlation isolation, Tenant isolation.

## 10. OBSERVABILITY & PERFORMANCE BUDGETS (Refinement 12 & 13)
- **Metrics:** `EvidenceCreatedPerSec`, `StorageLatency`, `ValidationFailures`, `HashVerificationFailures`.
- **Budgets:** 
  - Max hash generation latency: < 5ms.
  - Max immutable write latency (S3): < 200ms.
  - Max metadata persistence latency: < 50ms.
  - Max replay/retrieval latency: < 500ms.

## 11. EXPANDED THREAT MODEL (Refinement 11)
| Threat | Mitigation |
| :--- | :--- |
| **Replay Attacks** | `CorrelationId` and `WorkerId` validation prevents external event injection. |
| **Cross-Tenant Leakage** | Repository queries mandate `TenantId` partitioning (Row Level Security). |
| **Hash Substitution** | Cryptographic Signatures (RSA/ECDSA) prevent unauthorized hash replacement. |
| **Storage Corruption** | Validation Pipeline recalculates hash upon every retrieval (Read-Repair). |
| **Object Deletion** | IAM policies enforce `WORM` (Write Once Read Many) on S3 buckets. |
| **Partial Upload** | Atomic operations ensure metadata is only written if S3 upload succeeds. |
| **Unauthorized Replay** | Replay engine requires signed JWT with `Replay_Read` scope. |
| **Metadata Forgery** | Metadata is cryptographically signed along with the content hash. |

## 12. FUTURE COMPATIBILITY & ADVERSARIAL ENGINEERING (Refinement 14 & 15)
The architecture inherently supports downstream AI reasoning, Replay Engines, and Certification Engines because it acts purely as an append-only, cryptographically signed ledger.
**Adversarial Protocol Enforced:** Every implementation step in the Evidence Graph will be subjected to the `Implement -> Attack -> Patch -> Certify` loop before merging.

---
**FINAL VERDICT:** 🟢 **ARCHITECTURE CERTIFIED FOR STAGE 3 IMPLEMENTATION REFINEMENT.**
