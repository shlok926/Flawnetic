# FLAWNETIC
# ENGINEERING DECISION RECORD (EDR) STANDARD

## Purpose
While **Architectural Decision Records (ADRs)** capture macro-level system architecture decisions (e.g., "Use CQRS for Digital Twin", "Adopt Event Sourcing"), the **Engineering Decision Record (EDR)** captures micro-level implementation and library choices. 

EDRs ensure that future engineers understand the "Why" behind specific technical tools, patterns, and language features, reducing endless debates over technical debt or alternative libraries.

---

## EDR Template

### EDR-[ID]: [Short, Descriptive Title]
**Date:** YYYY-MM-DD
**Author:** [Name/Team]
**Status:** [Proposed | Accepted | Rejected | Deprecated | Superseded by EDR-XXX]

### 1. Context & Problem Statement
*Describe the specific engineering problem. (e.g., "We need to parse massive HTML DOMs quickly without running into Python recursion limits.")*

### 2. Decision Drivers
*What constraints are driving this decision? (e.g., Performance, Community Support, Security, Licensing)*
- Driver 1
- Driver 2

### 3. Considered Options
*What alternatives did we evaluate?*
- Option A (e.g., BeautifulSoup4 + lxml)
- Option B (e.g., Selectolax)
- Option C (e.g., html5lib)

### 4. Decision Outcome
*What did we choose and why?*
**Chosen Option:** [Option Name]
**Reasoning:** *Explain why this option was chosen over the others based on the Decision Drivers.*

### 5. Consequences
*What are the tradeoffs of this decision?*
- **Positive:** (e.g., 10x faster parsing, uses C-extensions).
- **Negative:** (e.g., Requires compiling native binaries on Alpine Linux during CI).
- **Risk:** (e.g., Library is maintained by a single open-source developer).

### 6. Validation / Proof
*Link to benchmarks, POCs, or GitHub issues that validate this decision.*

---

## EDR Examples vs ADR Examples

| Decision | Type | Example |
| :--- | :--- | :--- |
| **Separating Reads from Writes** | **ADR** | ADR-005: Adopt CQRS for Evidence Graph. |
| **Choosing the SQL Driver** | **EDR** | EDR-012: Use `asyncpg` instead of `psycopg2` for async PostgreSQL performance. |
| **Choosing a Hashing Algorithm** | **EDR** | EDR-015: Use `SHA-256` instead of `MD5` for Evidence Identity to prevent collision attacks. |
| **Pydantic Immutability** | **EDR** | EDR-018: Use `ConfigDict(frozen=True)` for all Domain Entities instead of `dataclasses`. |
| **Browser Automation Engine** | **EDR** | EDR-021: Use `Playwright` over `Selenium` or `Puppeteer` for bi-directional network interception. |
