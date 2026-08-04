# FLAWNETIC
# ARCHITECTURE FITNESS SPECIFICATION (AFS)
## Review ID: AFS-002 (Enterprise Refinement)
**Status:** ACTIVE

This specification defines the automated gates, invariants, and metrics required to permanently protect the frozen Enterprise Architecture from regressions, technical debt, and domain bleed.

Any commit violating these invariants MUST fail CI/CD based on the defined Rule Criticality Matrix. Exceptions require an approved Architectural Decision Record (ADR) and must be logged in the Architectural Debt Register.

---

## RULE CRITICALITY MATRIX
| Level | Enforcement Policy | Merge Policy |
| :--- | :--- | :--- |
| **BLOCKER** | Halts CI immediately. Cannot be bypassed. | Merge Impossible |
| **CRITICAL** | Fails CI. Requires ARB override. | Release Blocked |
| **HIGH** | Emits warnings. Requires ADR to merge. | Warning until next release |
| **MEDIUM** | Emits warnings. Logged in Debt Register. | Permitted (creates Debt) |
| **LOW** | Informational metric tracking. | Permitted |

## CI QUALITY LEVELS
To optimize velocity, AFS checks execute in tiered pipelines:
1. **Fast Checks (Pre-commit):** AST boundary parsing (`pytest-archon`), Immutability checks, Plugin validation.
2. **Standard Checks (PR Level):** Unit tests, Repository Contract Tests, FSTR Validation.
3. **Deep Architecture Scan (Nightly):** Dependency tree analysis, Performance Benchmarking, Memory Leak profiling.

---

## ARCHITECTURE INVARIANT REGISTRY

### AFS-INV-001: Strict Layer Isolation (Hexagonal Architecture)
- **Owner:** Architecture Team | **Severity:** BLOCKER
- **Rule:** `domain` packages cannot import `infrastructure`, `presentation`, or external web frameworks.
- **Verification:** `pytest-archon` automated AST analysis.

### AFS-INV-002: Cross-Aggregate Referencing
- **Owner:** Architecture Team | **Severity:** BLOCKER
- **Rule:** Aggregates cannot hold direct object references to other Aggregates (e.g., `DigitalTwin` cannot hold an instance of `ImmutableEvidence`, only `EvidenceId`).
- **Verification:** AST typing parser.

### AFS-INV-003: CQRS Read/Write Isolation
- **Owner:** Architecture Team | **Severity:** CRITICAL
- **Rule:** The `Query` layer must never import or invoke `ICommandRepository`.
- **Verification:** AST static analysis.

### AFS-INV-004: Zero-Trust AI Governance
- **Owner:** Security/AI Team | **Severity:** BLOCKER
- **Rule:** AI services are restricted to `Read-Only` credentials and can only emit `AIProposalEvents`. AI cannot mutate Domain state directly.
- **Verification:** JWT Scope validation at API Gateway; RBAC static analysis.

### AFS-INV-005: Event Bus Contract Compatibility
- **Owner:** Platform Team | **Severity:** CRITICAL
- **Rule:** Domain events must only make additive, backward-compatible schema changes. Ordering, Idempotency, and Exactly-Once Replay semantics must be maintained.
- **Verification:** Pydantic JSON Schema diff validation.

### AFS-INV-006: Stateless Plugin Compliance
- **Owner:** Platform Team | **Severity:** CRITICAL
- **Rule:** Every Discovery Plugin MUST be perfectly stateless, declare capabilities/permissions, and return canonical Domain Entities.
- **Verification:** Plugin Contract Test Suite.

### AFS-INV-007: Mandatory Tenant Isolation
- **Owner:** Security Team | **Severity:** BLOCKER
- **Rule:** Every Graph/DB read query MUST explicitly pass `tenant_id`.
- **Verification:** SAST tools (Bandit/Semgrep) preventing omitted `tenant_id` kwargs in Repository interfaces.

### AFS-INV-008: Immutable Entity Constraint
- **Owner:** Architecture Team | **Severity:** CRITICAL
- **Rule:** All Domain Entities and Value Objects MUST enforce immutability (`ConfigDict(frozen=True)`).
- **Verification:** Python Reflection/AST checking base classes.

---

## ARCHITECTURAL DEBT REGISTER
Violations of `MEDIUM` severity, or ARB-approved overrides for `HIGH/CRITICAL` rules, are not silently ignored. They are registered in the codebase:
- `architecture/debt/ADR_PENDING.md`
- `architecture/debt/KNOWN_EXCEPTIONS.md`

## RUNTIME DRIFT DETECTION
Static checks alone cannot guarantee architecture. EBPF or APM tracing (OpenTelemetry) will trigger Alerts if:
- *Service A bypasses the repository layer and executes SQL directly.*
- *Event stream ordering invariants are violated at runtime.*

## RULE EVOLUTION POLICY
AFS invariants evolve over time. Changes are managed via states:
- `PROPOSED`: In testing phase (emits warnings).
- `ACTIVE`: Fully enforced in CI.
- `DEPRECATED`: Replaced by a new invariant.
- `REMOVED`: No longer enforced.

## CERTIFICATION TRACEABILITY
To make Release Certification auditable, every Certification Report MUST explicitly trace its lineage:
`Certification -> [AFS-INV-00X] -> [ADR-00X] -> [FSTR-00X] -> [PERF-00X]`
