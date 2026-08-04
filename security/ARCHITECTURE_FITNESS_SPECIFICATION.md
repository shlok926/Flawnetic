# FLAWNETIC
# ARCHITECTURE FITNESS SPECIFICATION (AFS)
## Review ID: AFS-001
**Status:** ACTIVE

This specification defines the automated gates, invariants, and metrics required to permanently protect the frozen Enterprise Architecture from regressions, technical debt, and domain bleed.

Any commit violating these invariants MUST fail CI/CD. Exceptions require an approved Architectural Decision Record (ADR).

---

## 1. LAYER DEPENDENCY RULES (HEXAGONAL ARCHITECTURE)
- **Why:** Protects business logic from framework and infrastructure changes.
- **Verification:** `pytest-archon` automated AST analysis.
- **Rule:** `domain` packages cannot import `infrastructure`, `presentation`, or external web frameworks.
- **CI Enforcement:** Hard Fail on PR.
- **Severity:** CRITICAL. No exceptions allowed.

## 2. DDD & AGGREGATE RULES
- **Why:** Prevents monolithic data coupling and distributed deadlocks.
- **Verification:** AST parsing enforcing that cross-aggregate references use IDs (e.g., `EvidenceId`), never object references.
- **Rule:** A Bounded Context (e.g., `DigitalTwin`) cannot directly read/write tables of another Bounded Context (e.g., `State`).
- **Runtime Enforcement:** Database schema separated by schemas/microservices.
- **Severity:** CRITICAL.

## 3. EVENT CONTRACT RULES
- **Why:** Ensures Eventual Consistency pipelines don't break due to missing payloads.
- **Verification:** Pydantic JSON Schema validation against an established Schema Registry.
- **Rule:** Domain events must only make additive, backward-compatible schema changes. Breaking changes require a major version bump and dual-writing.
- **CI Enforcement:** Fail if PR modifies existing Pydantic Event Models without `version` bump.
- **Severity:** HIGH.

## 4. CQRS RULES
- **Why:** Read performance must not degrade Write availability.
- **Verification:** AST static analysis checking interface implementation.
- **Rule:** The `Query` layer must never import or invoke `ICommandRepository`.
- **Runtime Enforcement:** Read replicas use read-only database connections.
- **Severity:** HIGH.

## 5. AI GOVERNANCE RULES
- **Why:** Prevents AI from hallucinating direct database mutations.
- **Verification:** RBAC scopes and static analysis.
- **Rule:** AI services are strictly provisioned with `Read-Only` credentials and can only emit `AIProposalEvents`.
- **Runtime Enforcement:** Reject API writes lacking `Human_Verified` or `Admin` JWT claims.
- **Severity:** CRITICAL.

## 6. REPOSITORY RULES
- **Why:** Storage providers must remain interchangeable.
- **Verification:** `pytest-archon`.
- **Rule:** `domain` services can only inject `IRepository` interfaces. Direct imports of `SQLAlchemy` or `boto3` inside domain are blocked.
- **Severity:** HIGH.

## 7. ADR COMPLIANCE RULES
- **Why:** Prevents silent architectural drift.
- **Verification:** Git Hook / CI Job.
- **Rule:** If a PR modifies any file in `domain/aggregates` or alters the `ARCHITECTURE_FITNESS_SPECIFICATION.md`, it requires a referenced `ADR-XXX` in the PR description.
- **Severity:** MEDIUM (Requires manual PR block override).

## 8. SECURITY RULES
- **Why:** Prevents cross-tenant data leaks and tampering.
- **Verification:** SAST tools (Bandit/Semgrep) and Unit Tests.
- **Rule:** Every Graph/DB read query MUST include `tenant_id`. Every payload saved MUST be hashed.
- **Runtime Enforcement:** Row-Level Security (RLS) active on all PostgreSQL databases.
- **Severity:** CRITICAL.

## 9. PERFORMANCE BUDGETS
- **Why:** Ensures the twin can scale to 100M+ nodes.
- **Verification:** Benchmark CI pipeline (`pytest-benchmark`).
- **Rule:** Domain Logic processing time < 50ms per state.
- **CI Enforcement:** Fail if performance degrades by > 10% vs `main` branch baseline.
- **Severity:** HIGH.

## 10. ARCHITECTURE METRICS (OBSERVABILITY)
- **Why:** Detects architectural decay over time.
- **Metrics Tracked:** `Cyclomatic Complexity`, `Coupling Index`, `Orphaned Evidence Count`, `Unprocessed Event Queue Size`.
- **Runtime Enforcement:** Prometheous/Grafana alerts trigger if thresholds exceeded.

## 11. AUTOMATED FITNESS TESTS (CI/CD GATES)
Every PR triggers the **Fitness Pipeline**:
1. **Static Architecture Analysis (`pytest-archon`)**: Verifies boundaries.
2. **Immutability Check**: Asserts all Aggregate models have `frozen=True`.
3. **Repository Contract Tests**: Runs the same test suite against `InMemoryRepo` and `PostgresRepo` to ensure identical behavior.
4. **Performance Gate**: Executes benchmark regression testing.
5. **Security Gate**: Bandit/Semgrep check for manual Cypher/SQL queries bypassing the TQL AST.

## EXCEPTION POLICY
Only the Architecture Review Board (ARB) can approve an ADR that intentionally violates an AFS rule. If approved, the AFS rule must be explicitly updated to reflect the new Enterprise baseline.
