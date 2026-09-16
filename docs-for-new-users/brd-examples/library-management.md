# Business Requirements Document (BRD)

## 1. Title Block

| Attribute | Value |
|---|---|
| Component | library-management |
| Domain | Library Operations |
| Framework | Java 8, NetBeans Ant, Apache Derby |
| Run ID | 20260615-a7c2 |
| Date | 2026-06-15 |
| BRD Status | LOCKED |
| Overall Confidence | 74% |
| Version | 1.0 |
| Prepared By | brd-orchestrator |

## 2. Table of Contents

1. [Executive Summary](#3-executive-summary)
2. [Scope](#4-scope)
3. [Stakeholders and Actors](#5-stakeholders-and-actors)
4. [System Dependencies](#6-system-dependencies)
5. [User Journeys](#7-user-journeys)
6. [Business Rules](#8-business-rules)
7. [Gap Analysis](#9-gap-analysis)
8. [Acceptance Criteria](#10-acceptance-criteria)
9. [Risk Register](#11-risk-register)
10. [Open Items](#12-open-items)
11. [Assumptions](#13-assumptions)
12. [Appendix - Artifact Catalog](#14-appendix---artifact-catalog)

## 3. Executive Summary

The library-management component is a Java console application that supports core library workflows: authentication, catalog search, hold placement, issue/return/renew operations, borrower and staff management, and historical reporting. Runtime behavior is orchestrated from the main menu in [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L265), while persistence is coordinated through Derby in [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L598).

The BRD is LOCKED at 74% confidence based on code and documentation triangulation, with one major limitation: no automated tests were found in the component even though a test source root is configured in [library-management/library-management/Project/nbproject/project.properties](library-management/library-management/Project/nbproject/project.properties#L78). This lowers behavioral certainty for boundary paths (queue expiry, persistence failure, and fine settlement corner cases).

Top findings are security and reliability focused. The component uses static credentials and an admin password gate ([library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L318), [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L603)), and writes state back with a full delete-and-reinsert strategy ([library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L961)). These are high-priority modernization targets.

## 4. Scope

### In Scope

| # | Capability |
|---|---|
| 1 | Role-based login and portal routing for Borrower, Clerk, Librarian |
| 2 | Catalog search by title, subject, author |
| 3 | Hold request queueing and precedence checks |
| 4 | Issue, return, and renew workflows |
| 5 | Fine calculation and payment state handling |
| 6 | Admin menu functions: add clerk/librarian, view history, view inventory |
| 7 | Startup load from Derby and shutdown persistence back to Derby |

### Out of Scope

| Capability | Reason |
|---|---|
| Web or REST API | System is implemented as console-only in current baseline |
| External identity provider integration | No IAM abstraction exists in current design |
| Multi-branch tenancy support | Data model and runtime assume single library instance |
| Notification channels (email/SMS) | No messaging integration in current implementation |

### Deferred

| Capability | Reason |
|---|---|
| Search relevance and fuzzy matching | Exact-match behavior currently hardcoded |
| Operational audit trail | No existing event model; requires data model extensions |

## 5. Stakeholders and Actors

| Actor | Type | Responsibilities |
|---|---|---|
| Borrower | End user | Search books, place holds, view profile and fine state |
| Clerk | Operational staff | Checkout/check-in/renew, manage borrower details |
| Librarian | Supervisory staff | All clerk capabilities plus catalog administration |
| Administrator | Privileged operator | Add clerks/librarian, view issued-book history and inventory |
| Operations/DBA | Technical stakeholder | Derby availability, backup/recovery, runtime configuration |

Authorization warning: HTTP auth does not exist because the system is console-based; authorization is menu-level and password-based, including a fixed administrative password gate.

## 6. System Dependencies

### Regulatory Flags Summary

| Flag | Evidence | Impact |
|---|---|---|
| PII_STORAGE | [library-management/library-management/Database Schema.txt](library-management/library-management/Database%20Schema.txt#L2) | Name, address, phone, password fields require data protection controls |
| SECRETS_IN_CODE | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L602) | Credentials hardcoded in source increase secret exposure risk |

### Apache Derby Network Server

| Field | Value |
|---|---|
| Type | Database |
| Protocol | JDBC |
| Direction | Outbound |
| Has Fallback | No |
| Has Circuit Breaker | No |
| Is SPOF | Yes |
| Evidence | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L602) |
| Migration Notes | Externalize connection configuration and use transactional persistence strategy |

### derbyclient-10.2.2.0.jar

| Field | Value |
|---|---|
| Type | Runtime library |
| Protocol | JDBC driver |
| Direction | Runtime classpath |
| Has Fallback | No |
| Has Circuit Breaker | N/A |
| Is SPOF | No |
| Evidence | [library-management/library-management/Project/nbproject/project.properties](library-management/library-management/Project/nbproject/project.properties#L32) |
| Migration Notes | Validate compatibility when upgrading JDK/build stack |

### NetBeans Ant Tooling

| Field | Value |
|---|---|
| Type | Build dependency |
| Protocol | Ant XML |
| Direction | Build-time |
| Has Fallback | Yes (portable to Maven/Gradle) |
| Has Circuit Breaker | N/A |
| Is SPOF | No |
| Evidence | [library-management/library-management/Project/build.xml](library-management/library-management/Project/build.xml#L1) |
| Migration Notes | Consider migration to CI-friendly modern build tool |

## 7. User Journeys

### Journey Map Summary

| ID | Name | Actor | Source | Classification | Confidence |
|---|---|---|---|---|---|
| J-01 | Authenticate user into role portal | Borrower/Clerk/Librarian | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L515) | CLEAN_MAP | 0.93 |
| J-02 | Search books by title/subject/author | Borrower/Clerk/Librarian | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L252) | CLEAN_MAP | 0.90 |
| J-03 | Place hold request | Borrower/Staff proxy | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L168) | CLEAN_MAP | 0.92 |
| J-04 | Issue book with hold priority | Clerk/Librarian | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L212) | CLEAN_MAP | 0.95 |
| J-05 | Return book and settle fine | Clerk/Librarian | [library-management/library-management/Project/src/LMS/Loan.java](library-management/library-management/Project/src/LMS/Loan.java#L118) | CLEAN_MAP | 0.92 |
| J-06 | Renew borrowed book | Clerk/Librarian | [library-management/library-management/Project/src/LMS/Loan.java](library-management/library-management/Project/src/LMS/Loan.java#L149) | TRANSFORM | 0.85 |
| J-07 | Admin staff management/reporting | Administrator | [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L308) | TRANSFORM | 0.88 |
| J-08 | Persist state on exit | System | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L961) | TRANSFORM | 0.86 |

### Flow Diagrams (ASCII)

Employee lifecycle (mapped to borrower/staff lifecycle in this component):

```text
[Admin Password Gate]
        |
        v
[Create Clerk/Librarian] ---> [Stored in PERSON + STAFF + ROLE tables]
        |
        +--> [Login via ID/PASSWORD] ---> [Role Portal]
```

Leave lifecycle (mapped to loan lifecycle in this component):

```text
[Search Book] -> [Issue Attempt] -> (Issued?) --yes--> [Offer Hold]
                              | no
                              v
                    (Hold Queue Exists?) --yes--> [Only Earliest Requester Allowed]
                              | no
                              v
                          [Loan Created]
                              |
                              v
                           [Return]
                              |
                              v
                     [Fine Computed + Payment State]
```

## 8. Business Rules

### Validation Rules

| Rule ID | Rule | Evidence |
|---|---|---|
| R-VAL-01 | Menu choice must be numeric and within configured bounds | [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L19) |

### Constraints

| Rule ID | Rule | Evidence |
|---|---|---|
| R-CON-01 | System allows only one librarian singleton per library | [library-management/library-management/Project/src/LMS/Librarian.java](library-management/library-management/Project/src/LMS/Librarian.java#L31) |

### Authorization

| Rule ID | Rule | Evidence |
|---|---|---|
| R-AUTH-01 | Administrative portal uses fixed password "lib" | [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L318) |
| R-AUTH-02 | Role login is ID/password match against in-memory entities | [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java#L515) |

### Workflow

| Rule ID | Rule | Evidence |
|---|---|---|
| R-WF-01 | Borrower cannot hold a book already borrowed by themselves | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L174) |
| R-WF-02 | Duplicate hold requests by same borrower are rejected | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L186) |
| R-WF-03 | Hold queue priority enforces earliest requester first | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L260) |
| R-WF-04 | Expired hold requests are removed during issue processing | [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java#L224) |

### Calculations

| Rule ID | Rule | Evidence |
|---|---|---|
| R-CALC-01 | Fine = overdue days after deadline x per-day fine | [library-management/library-management/Project/src/LMS/Loan.java](library-management/library-management/Project/src/LMS/Loan.java#L93) |
| R-CFG-01 | Default policy fine=20/day, hold_expiry=7, return_deadline=5 | [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java#L274) |

## 9. Gap Analysis

| Classification | Count |
|---|---|
| CLEAN_MAP | 5 |
| TRANSFORM | 3 |
| MISSING | 3 |
| DEFERRED | 2 |
| BLOCKING | 2 |

#### 🔴 CRITICAL - G-BLK-01 Weak authentication and secret exposure

Severity: CRITICAL  
Effort: Medium  
Affected Journeys: J-01, J-07  
Affected Rules: R-AUTH-01, R-AUTH-02  
Recommendation: Replace fixed/shared credentials with per-user hashed authentication and environment-based secret management.

#### 🟠 HIGH - G-BLK-02 No automated regression tests

Severity: HIGH  
Effort: Medium  
Affected Journeys: J-01, J-04, J-05, J-08  
Affected Rules: R-WF-03, R-CALC-01  
Recommendation: Add unit/integration tests for login, hold ordering, fine boundary behavior, and DB persistence.

Non-blocking gaps:

| Gap ID | Classification | Severity | Description |
|---|---|---|---|
| G-TR-01 | TRANSFORM | 🟡 MEDIUM | Exact-match case-sensitive search only |
| G-TR-02 | TRANSFORM | 🟡 MEDIUM | Renewal lacks max-renewal policy/eligibility checks |
| G-MS-01 | MISSING | 🟠 HIGH | No lockout/throttling for failed logins |
| G-MS-02 | MISSING | 🟡 MEDIUM | No admin action audit trail |
| G-MS-03 | MISSING | 🟠 HIGH | No transaction wrapper for full-table rewrite |
| G-DF-01 | DEFERRED | 🟢 LOW | Console-only interface |
| G-DF-02 | DEFERRED | 🟢 LOW | Single-library assumption |

## 10. Acceptance Criteria

### Authentication

| ID | Indicator | Scenario | Type | Coverage |
|---|---|---|---|---|
| AC-01 | ✅ | Valid role login routes user to correct portal | positive | PARTIAL |
| AC-02 | ❌ | Invalid credentials are rejected | negative | PARTIAL |

### Search and Holds

| ID | Indicator | Scenario | Type | Coverage |
|---|---|---|---|---|
| AC-03 | ✅ | Title search returns exact matched catalog rows | positive | PARTIAL |
| AC-04 | ❌ | Duplicate hold request by same borrower is blocked | negative | PARTIAL |
| AC-05 | 📐 | Non-earliest requester cannot bypass hold queue | boundary | PARTIAL |
| AC-06 | 📐 | Expired holds are removed during issue path | boundary | **GAP** |

### Circulation and Administration

| ID | Indicator | Scenario | Type | Coverage |
|---|---|---|---|---|
| AC-07 | ✅ | Overdue return generates fine prompt | positive | PARTIAL |
| AC-08 | ✅ | Renewal updates issued date | positive | PARTIAL |
| AC-09 | ❌ | Second librarian creation is denied | negative | PARTIAL |
| AC-10 | ✅ | State is persisted to DB on exit | positive | **GAP** |

## 11. Risk Register

Summary counts:

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 1 |
| 🟠 HIGH | 3 |
| 🟡 MEDIUM | 3 |
| 🟢 LOW | 1 |

#### RK-01 - Hardcoded secrets and static admin password

> Category: security  
> Likelihood: High  
> Impact: Very High  
> Score: 0.86  
> Mitigation: Remove embedded credentials, add secure secret injection and per-user admin authorization.  
> Owner: Security

#### RK-02 - PII and password storage in plain fields

> Category: compliance  
> Likelihood: High  
> Impact: High  
> Score: 0.70  
> Mitigation: Hash passwords, apply data minimization and encryption where needed, define retention controls.  
> Owner: Data Protection

#### RK-03 - Persistence rewrite can lose data on failure

> Category: reliability  
> Likelihood: Medium  
> Impact: High  
> Score: 0.60  
> Mitigation: Add transaction boundaries and/or migrate to incremental upsert persistence.  
> Owner: Engineering

#### RK-04 - No automated test coverage

> Category: delivery_quality  
> Likelihood: Very High  
> Impact: Medium  
> Score: 0.63  
> Mitigation: Implement regression tests for high-risk journeys.  
> Owner: QA

#### RK-05 - Shared static hold request state

> Category: functional_correctness  
> Likelihood: Medium  
> Impact: Medium  
> Score: 0.42  
> Mitigation: Make hold request queues book-scoped and non-static.  
> Owner: Engineering

#### RK-06 - Exact match search limits discoverability

> Category: usability  
> Likelihood: Medium  
> Impact: Medium  
> Score: 0.34  
> Mitigation: Add case-insensitive and partial-match search behavior.  
> Owner: Product

#### RK-07 - No brute-force throttling

> Category: security  
> Likelihood: Medium  
> Impact: Medium  
> Score: 0.36  
> Mitigation: Add lockout/rate-limiting policy for repeated failures.  
> Owner: Security

#### RK-08 - Single Derby endpoint dependency

> Category: dependency  
> Likelihood: Medium  
> Impact: Low  
> Score: 0.18  
> Mitigation: Add backup/restore and disaster recovery procedures.  
> Owner: Operations

## 12. Open Items

| ID | Question | Owner |
|---|---|---|
| OI-01 | Should administrator become a first-class persisted role instead of shared password gate? | Product + Security |
| OI-02 | What credential policy (hashing algorithm, reset flow, complexity) is required? | Security |
| OI-03 | Should hold queues be per-book only, given static queue implementation? | Engineering |
| OI-04 | What RPO/RTO is required for exit-time persistence failures? | Operations |

## 13. Assumptions

| ID | Statement | Basis | Risk If Wrong | Owner |
|---|---|---|---|---|
| A-01 | Single-library runtime is acceptable | Singleton patterns and menu model | Multi-branch rollout will require partitioning and policy redesign | Product |
| A-02 | Console trust model is acceptable for users | Local interactive execution pattern | Security baseline insufficient for remote/hosted deployment | Security |

## 14. Appendix - Artifact Catalog

| Artifact | Type | Relevance | Notes |
|---|---|---|---|
| [library-management/library-management/README.md](library-management/library-management/README.md) | Documentation | 0.88 | Actors/use-cases and setup instructions |
| [library-management/library-management/Database Schema.txt](library-management/library-management/Database%20Schema.txt) | DB schema | 0.94 | Person/book/loan/hold relational model |
| [library-management/library-management/Project/nbproject/project.properties](library-management/library-management/Project/nbproject/project.properties) | Build config | 0.95 | Java 8, main class, test source config |
| [library-management/library-management/Project/src/LMS/Main.java](library-management/library-management/Project/src/LMS/Main.java) | Entry/menu orchestration | 0.97 | Role workflows and admin gate |
| [library-management/library-management/Project/src/LMS/Library.java](library-management/library-management/Project/src/LMS/Library.java) | Domain/persistence service | 0.99 | Login, create entities, DB load/save |
| [library-management/library-management/Project/src/LMS/Book.java](library-management/library-management/Project/src/LMS/Book.java) | Domain entity | 0.98 | Hold and issue logic |
| [library-management/library-management/Project/src/LMS/Loan.java](library-management/library-management/Project/src/LMS/Loan.java) | Domain entity | 0.96 | Fine and renewal logic |
| [library-management/library-management/Project/src/LMS/HoldRequestOperations.java](library-management/library-management/Project/src/LMS/HoldRequestOperations.java) | Utility/domain | 0.90 | Shared hold queue behavior |

*Document generated by BRD Pipeline - Run ID: 20260615-a7c2 | Confidence: 74% (MEDIUM-HIGH) | BRD Locked: ✅ YES | Generated: 2026-06-15*
