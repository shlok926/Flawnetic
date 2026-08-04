# FLAWNETIC ENTERPRISE PLATFORM
# FROZEN ARCHITECTURE INDEX

This document is the **Single Source of Truth** for the Flawnetic Enterprise Platform's frozen architectural boundaries. 

**IMPORTANT DIRECTIVE:**
If a subsystem is listed here as `FROZEN`, its Architecture, Domain Models, and Core Infrastructure Contracts are **IMMUTABLE**. Any future engineering changes to these subsystems MUST be proposed, reviewed, and approved via an Architecture Decision Record (ADR) before implementation.

---

## 1. Discovery Foundation
- **Version:** v1.0
- **Status:** 🟢 FROZEN
- **Review ID:** EPIC1-M1-CERT-001
- **Freeze Date:** (Milestone 1 Completion)
- **Dependencies:** None
- **Future Changes:** ADR only
- **Location:** `architecture/frozen/discovery/`
- **Description:** Stateless, memory-safe web discovery plugins, recursive DOM parsing, footprint generation, and async execution engines.

---

## 2. Application State Machine
- **Version:** v3.0
- **Status:** 🟢 FROZEN
- **Review ID:** EPIC1-M2-STAGE1-ARB
- **Freeze Date:** (Milestone 2 Stage 1 Completion)
- **Dependencies:** Discovery Foundation
- **Future Changes:** ADR only
- **Location:** `architecture/frozen/state_machine/`
- **Description:** Pure DDD implementation, bounded contexts, canonical hashing, memory safety, and stateless application mapping.

---

## 3. Evidence Graph
- **Version:** v3.0
- **Status:** 🟢 FROZEN
- **Review ID:** EPIC1-M2-STAGE3-ARB-003
- **Freeze Date:** (Milestone 2 Stage 3 Completion)
- **Dependencies:** State Machine
- **Future Changes:** ADR only
- **Location:** `architecture/frozen/evidence_graph/`
- **Description:** Cryptographically signed, immutable chain of custody for discovery artifacts. Strict CQRS repository contracts decoupling storage from logic.

---

## 4. Digital Twin
- **Version:** v2.0
- **Status:** 🟢 FROZEN
- **Review ID:** EPIC1-M3-STAGE3.2.2-ARB
- **Freeze Date:** 2026-08-04
- **Dependencies:** Evidence Graph, State Machine
- **Future Changes:** ADR only
- **Location:** `architecture/frozen/digital_twin/`
- **Description:** Highly scalable read-models (Knowledge/Runtime Twins). Features read-after-write LRU cache, distributed Replay Cursors, Bulk Ingestion, and cryptographic Snapshot Integrity.

---

## CURRENT WORKING SUBSYSTEM
**Next Subsystem in Pipeline:** 
EPIC 1 | MILESTONE 3 | STAGE 4 — **Knowledge Graph Domain Architecture**
(Status: Planning)
