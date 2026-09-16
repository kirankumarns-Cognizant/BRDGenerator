# Business Requirements Document
## employee-simulator

| Field | Value |
|-------|-------|
| **Component** | employee-simulator |
| **Domain** | HR Management |
| **Framework** | Spring Boot 3.4.1 / Java 25 |
| **Run ID** | 20260615-brd1 |
| **Date** | 2026-06-15 |
| **BRD Status** | ✅ LOCKED |
| **Confidence** | 86% (HIGH) |
| **Version** | 1.0 |
| **Prepared By** | BRD Pipeline — brd-orchestrator |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope](#2-scope)
3. [Stakeholders and Actors](#3-stakeholders-and-actors)
4. [System Dependencies](#4-system-dependencies)
5. [User Journeys](#5-user-journeys)
6. [Business Rules](#6-business-rules)
7. [Gap Analysis](#7-gap-analysis)
8. [Acceptance Criteria](#8-acceptance-criteria)
9. [Risk Register](#9-risk-register)
10. [Open Items](#10-open-items)
11. [Assumptions](#11-assumptions)
12. [Appendix — Artifact Catalog](#12-appendix--artifact-catalog)

---

## 1. Executive Summary

The **employee-simulator** is a Spring Boot 3.4.1 REST API that simulates an HR management back-end. It provides two primary capability areas: **Employee Lifecycle Management** — covering hire, update, role promotion, termination, reinstatement, payroll calculation, and email generation; and **Leave Management Workflow** — covering leave application, manager approval/rejection, and employee self-service cancellation with automatic balance tracking. The system also exposes an MCP (Model Context Protocol) server over Spring AI to allow AI agents to query Elasticsearch-backed operational logs.

The BRD is **LOCKED** at **86% confidence**. The codebase is well-structured, with consistent service-layer business rules and solid integration test coverage across 25 `@DataJpaTest` tests. Evidence weight is HIGH across all functional areas. The two primary agents (EmployeeService, LeaveService) are clearly separated and their business rules are fully traceable from entity → service → test.

**Two BLOCKING gaps require immediate attention before production use:** (a) the application has no HTTP authentication layer — role-based controls can be bypassed by passing arbitrary `requesterId` values in request bodies; and (b) Elasticsearch credentials are hardcoded in a committed `application.properties` file. Three additional HIGH-severity findings — an incorrect cross-year leave duration calculation, unprotected terminate/reinstate endpoints, and an exposed H2 database console — must be resolved in the next sprint. All other gaps are medium/low priority deferred items (DB migration, OpenAPI docs, audit trail).

---

## 2. Scope

### 2.1 In Scope

| # | Capability |
|---|-----------|
| 1 | Employee CRUD (create, read, update, delete) |
| 2 | Employee role hierarchy management (STAFF → MANAGER → ADMIN promotion) |
| 3 | Employee lifecycle state management (ACTIVE ↔ TERMINATED) |
| 4 | Progressive three-bracket payroll tax calculation |
| 5 | Email address generation from employee name and department |
| 6 | Leave request submission (ANNUAL, SICK, UNPAID, MATERNITY, PATERNITY) |
| 7 | Leave request approval workflow (PENDING → APPROVED / REJECTED) |
| 8 | Leave request cancellation with 2-day notice rule for APPROVED leave |
| 9 | Leave balance tracking (ANNUAL cap 20d, SICK cap 10d; UNPAID/MATERNITY/PATERNITY uncapped) |
| 10 | XSS input validation on employee name and department fields |
| 11 | E2E request ID propagation via `X-E2E-Request-Id` / `X-Request-Id` headers (MDC correlation) |
| 12 | MCP server: Elasticsearch log retrieval tools (by E2E ID, free text, recent, error) |

### 2.2 Out of Scope

| Item | Reason |
|------|--------|
| HTTP authentication / authorization | No Spring Security; no JWT/session management — BLOCKING gap |
| Employee self-service portal (UI) | No front-end layer in repository |
| Payroll disbursement / payment integration | No payment provider dependency |
| Leave accrual / year-end balance reset | No scheduling or accrual logic found |
| Employee onboarding workflow beyond record creation | No onboarding domain logic |
| Performance review / appraisal | Not implemented |
| Multi-tenant / multi-company support | Single-tenant by design |
| Kafka / RabbitMQ / Redis messaging | No such dependencies in pom.xml |

### 2.3 Deferred

| Item | Reason |
|------|--------|
| H2 → production-grade database (PostgreSQL/MySQL) | Dev/demo only; migration not scoped |
| Spring Security / JWT integration | Identified as BLOCKING gap (G-001) |
| ON_LEAVE status lifecycle | Enum defined but never applied — open item OI-001 |
| Swagger / OpenAPI documentation | No springdoc dependency |
| Elasticsearch client migration to Java 8.x | Deprecated client in use (G-012) |
| JPA Audit trail (createdBy, modifiedBy) | Not implemented (G-014) |

---

## 3. Stakeholders and Actors

| Actor | Type | Responsibilities |
|-------|------|-----------------|
| **STAFF** | System Actor (internal) | Apply for leave; cancel own leave; view own leave history |
| **MANAGER** | System Actor (internal) | Approve / reject leave requests; promote employees; view pending leave queue |
| **ADMIN** | System Actor (internal) | All MANAGER capabilities; maximum role ceiling |
| **HR_ADMIN** | Conceptual Actor (maps to ADMIN role) | Hire, terminate, reinstate, update employees; run payroll; generate emails |
| **AI_AGENT** | System Actor (external) | Invoke MCP log retrieval tools via Spring AI MCP server |
| **Dev / Platform Team** | Human Stakeholder | Deployment, security hardening, DB migration |
| **Product Owner** | Human Stakeholder | Leave policy decisions, ON_LEAVE lifecycle, feature roadmap |

> ⚠️ **Authorization Warning:** Role enforcement is **service-layer only**. There is no HTTP-level authentication. Any caller knowing a valid employee ID can claim any role by passing `requesterId` in the request body. This is a CRITICAL security gap (G-001, RISK-001).

### Regulatory Flags Summary

| Flag | Fields / Rules | Risk |
|------|---------------|------|
| **PII** | Employee name, email address (generated), hire date | Data exposure risk if H2 console or API is accessible |
| **Financial** | Salary (stored), annual tax, monthly net (computed) | Salary exposed in API responses to any caller |
| **Authorization** | Service-layer RBAC only — no HTTP security | Full privilege escalation possible |
| **Security** | XSS prevention on name/department; hardcoded Elastic password | Password must be rotated immediately |

---

## 4. System Dependencies

### DEP-001 — H2 Database

| Attribute | Value |
|-----------|-------|
| **Type** | Embedded relational database |
| **Protocol** | JDBC |
| **Direction** | Downstream (synchronous) |
| **Has Fallback** | No |
| **Has Circuit Breaker** | No |
| **Is SPOF** | Yes |

Stores `Employee` and `LeaveRequest` entities. File path `./data/testdb` is relative. Not suitable for production use — is a single point of failure with no high-availability capability.

**Migration note:** Move to PostgreSQL/MySQL with Flyway schema versioning before any non-demo deployment.

### DEP-002 — Elasticsearch (filebeat-* index)

| Attribute | Value |
|-----------|-------|
| **Type** | External log search engine |
| **Protocol** | HTTPS REST (elasticsearch-rest-high-level-client 7.17.10) |
| **Direction** | Downstream (synchronous) |
| **Has Fallback** | ✅ Yes — local `./logs/application.log` file |
| **Has Circuit Breaker** | No |
| **Is SPOF** | No (fallback exists) |

Provides structured log retrieval for MCP tools. Client library is **deprecated and incompatible with Elasticsearch 8+**. SSL CA cert path is hardcoded to a local Windows path (`C:/elastic/...`).

**Migration note:** Migrate to `co.elastic.clients:elasticsearch-java` 8.x. Externalize cert path.

### DEP-003 — Spring AI MCP Server

| Attribute | Value |
|-----------|-------|
| **Type** | Inbound AI tool protocol server |
| **Protocol** | HTTP / MCP (Model Context Protocol) |
| **Direction** | Upstream (inbound) |
| **Has Fallback** | No |
| **Has Circuit Breaker** | No |
| **Is SPOF** | No |

Exposes five Elasticsearch log tools (`getLogsByE2EId`, `searchLogs`, `getRecentLogs`, `getErrorLogs`, `getLogLevelSummary`) to AI agents via Spring AI 1.0.0.

---

## 5. User Journeys

### 5.1 Journey Map Summary

| ID | Journey Name | Actor | Source | Classification | Confidence |
|----|-------------|-------|--------|---------------|-----------|
| J-EMP-001 | Hire Employee | HR_ADMIN | code+test | happy_path | HIGH |
| J-EMP-002 | Retrieve Employee by ID | ANY | code | happy_path | HIGH |
| J-EMP-003 | List All Employees | ANY | code | happy_path | HIGH |
| J-EMP-004 | Filter Employees by Department | ANY | code | happy_path | HIGH |
| J-EMP-005 | List Active Employees | ANY | code | happy_path | HIGH |
| J-EMP-006 | Update Employee | HR_ADMIN | code | happy_path | HIGH |
| J-EMP-007 | Delete Employee | HR_ADMIN | code+test | happy_path | HIGH |
| J-EMP-008 | Promote Employee | MANAGER/ADMIN | code+test | happy_path | HIGH |
| J-EMP-009 | Terminate Employee | HR_ADMIN | code+test | happy_path | HIGH |
| J-EMP-010 | Reinstate Terminated Employee | HR_ADMIN | code+test | happy_path | HIGH |
| J-EMP-011 | Calculate Payroll | HR_ADMIN | code+test | happy_path | HIGH |
| J-EMP-012 | Generate Employee Email | HR_ADMIN | code+test | happy_path | HIGH |
| J-LEAVE-001 | Apply for Leave | EMPLOYEE | code+test | happy_path | HIGH |
| J-LEAVE-002 | Approve Leave Request | MANAGER/ADMIN | code+test | happy_path | HIGH |
| J-LEAVE-003 | Reject Leave Request | MANAGER/ADMIN | code+test | happy_path | HIGH |
| J-LEAVE-004 | Cancel Pending Leave | EMPLOYEE (owner) | code+test | happy_path | HIGH |
| J-LEAVE-005 | Cancel Approved Leave (with notice) | EMPLOYEE (owner) | code+test | happy_path | HIGH |
| J-LEAVE-006 | View My Leave Requests | EMPLOYEE | code | happy_path | HIGH |
| J-LEAVE-007 | View Pending Leave Queue | MANAGER/ADMIN | code | happy_path | HIGH |
| J-LOG-001 | Retrieve Logs by E2E ID (MCP) | AI_AGENT | code | happy_path | MEDIUM |

### 5.2 State Machine Diagrams

#### Employee Lifecycle State Machine

```
                    ┌─────────────────────┐
                    │                     │
  [hire/create] --> │       ACTIVE        │ <-- [reinstate]
                    │                     │
                    └─────────┬───────────┘
                              │ [terminate]
                              │ (blocks if has direct reports)
                              ▼
                    ┌─────────────────────┐
                    │    TERMINATED       │
                    │ (payroll blocked,   │
                    │  leave blocked)     │
                    └─────────────────────┘

  ON_LEAVE: defined in enum but NEVER applied (Gap G-003)

  Role Hierarchy:
  STAFF --> MANAGER --> ADMIN  (one step at a time, by MANAGER/ADMIN requester)
                            ↑
                       CEILING: cannot promote beyond ADMIN
```

#### Leave Request State Machine

```
                    ┌─────────────────────┐
  [apply]     ----> │      PENDING        │
                    └──────┬──────┬───────┘
                           │      │
              [approve]    │      │  [reject]
              (MGMT only)  │      │  (MGMT only)
                           │      │
                    ┌──────▼──┐  ┌▼────────┐
                    │APPROVED │  │REJECTED │ ← terminal
                    └────┬────┘  └─────────┘
                         │
              [cancel]   │    (owner only,
              + refund    │     start ≥ 2 days away)
                         ▼
                    ┌──────────┐
                    │CANCELLED │ ← terminal
                    └──────────┘

  From PENDING: cancel is also possible (owner only, no notice required)
```

---

## 6. Business Rules

### 6.1 Validation Rules

| ID | Rule | Source | Confidence |
|----|------|--------|-----------|
| R-VAL-001 | Employee **name** must not contain HTML tags (XSS prevention) | XssValidator.java | HIGH |
| R-VAL-002 | Employee **department** must not contain HTML tags (XSS prevention) | XssValidator.java | HIGH |
| R-VAL-003 | Leave **start date** and **end date** must both be provided (not null) | LeaveService.java | HIGH |
| R-VAL-004 | Leave **start date** must not be after end date | LeaveService.java | HIGH |
| R-VAL-005 | No overlapping PENDING or APPROVED leave for the same employee | LeaveService.java / LeaveRepository | HIGH |

### 6.2 Constraints

| ID | Rule | Source | Confidence |
|----|------|--------|-----------|
| R-LEAVE-001 | **Annual leave** default balance: 20 days. Cannot apply if balance < requested days | Employee.java / LeaveService | HIGH |
| R-LEAVE-002 | **Sick leave** default balance: 10 days. Cannot apply if balance < requested days | Employee.java / LeaveService | HIGH |
| R-LEAVE-003 | **UNPAID, MATERNITY, PATERNITY** leave types have no balance cap | LeaveType.java / LeaveService | HIGH |
| R-LIFE-003 | **ADMIN** is the role ceiling — cannot be promoted further | EmployeeService.java | HIGH |
| R-LIFE-004 | **TERMINATED** employees cannot have payroll calculated or leave submitted | EmployeeService / LeaveService | HIGH |
| R-CON-001 | Manager with **active direct reports** cannot be deleted or terminated | EmployeeService.java / EmployeeRepository | HIGH |

### 6.3 Authorization Rules

| ID | Rule | Source | Confidence |
|----|------|--------|-----------|
| R-AUTH-001 | **Promotion** requires MANAGER or ADMIN role (`requesterId`). STAFF → AUTHORIZATION_VIOLATION | EmployeeService.java | HIGH |
| R-AUTH-002 | **Leave approval/rejection** requires MANAGER or ADMIN role. STAFF → AUTHORIZATION_VIOLATION | LeaveService.java | HIGH |
| R-AUTH-003 | **Leave cancellation** is owner-only. Different employee → AUTHORIZATION_VIOLATION | LeaveService.java | HIGH |

### 6.4 Workflow Rules

| ID | Rule | Source | Confidence |
|----|------|--------|-----------|
| R-LIFE-001 | New employee defaults: `role=STAFF`, `status=ACTIVE`, `annualLeaveBalance=20`, `sickLeaveBalance=10` | Employee.java | HIGH |
| R-LIFE-002 | Only **ACTIVE** employees can be promoted | EmployeeService.java | HIGH |
| R-LIFE-005 | Only **TERMINATED** employees can be reinstated | EmployeeService.java | HIGH |
| R-LEAVE-004 | **Approval** deducts balance (ANNUAL or SICK); other types trigger no deduction | LeaveService.java | HIGH |
| R-LEAVE-005 | **Rejection** does NOT modify any leave balance | LeaveService.java | HIGH |
| R-LEAVE-006 | Only **PENDING** requests can be approved | LeaveService.java | HIGH |
| R-LEAVE-007 | Only **PENDING** requests can be rejected | LeaveService.java | HIGH |
| R-LEAVE-008 | **REJECTED** and **CANCELLED** are terminal states — no further transitions | LeaveService.java | HIGH |
| R-LEAVE-009 | **APPROVED** leave cancellation requires ≥ 2 calendar days notice before start date | LeaveService.java | HIGH |
| R-LEAVE-010 | **APPROVED** leave cancellation refunds the previously deducted balance | LeaveService.java | HIGH |
| R-LOG-001 | All HTTP requests receive an E2E request ID (new UUID or from `X-E2E-Request-Id` header) propagated via MDC | RequestIdFilter.java | HIGH |

### 6.5 Calculation Rules

| ID | Rule | Source | Confidence |
|----|------|--------|-----------|
| R-CALC-001 | Payroll Tax Bracket 1: $0–$50,000 → **0% tax** | EmployeeService.java | HIGH |
| R-CALC-002 | Payroll Tax Bracket 2: $50,001–$100,000 → **20%** on the portion above $50k | EmployeeService.java | HIGH |
| R-CALC-003 | Payroll Tax Bracket 3: $100,001+ → **30%** on portion above $100k (plus fixed $10k mid-bracket tax). `monthlyNet = (gross − tax) / 12` | EmployeeService.java | HIGH |
| R-CALC-004 | Email formula: `firstName.lastName@department.company.com` (spaces in dept → dashes; single-word name: firstName = lastName) | EmployeeService.java | HIGH |

---

## 7. Gap Analysis

### 7.1 Classification Summary

| Classification | Count | Description |
|---------------|-------|-------------|
| CLEAN_MAP | 18 | Fully implemented with test evidence |
| TRANSFORM | 3 | Implemented but needs change (auth, salary validation) |
| MISSING | 4 | Required but not yet implemented |
| DEFERRED | 5 | Out of current scope; planned for future |
| **BLOCKING** | **2** | **Must fix before production use** |

### 7.2 Blocking Gaps

#### 🔴 G-001 — No HTTP Authentication Layer

**Severity:** CRITICAL | **Effort:** HIGH

The application has no Spring Security or HTTP-level authentication. Role-based checks exist only at the service layer via `requesterId` parameters. Any caller can claim any role by supplying any employee ID.

**Affected journeys:** J-EMP-008, J-LEAVE-002, J-LEAVE-003, J-LEAVE-004, J-LEAVE-005
**Affected rules:** R-AUTH-001, R-AUTH-002, R-AUTH-003

**Recommendation:** Add Spring Security with JWT. Map authenticated principal to `Employee.id`. Replace `requesterId` body parameter with `SecurityContextHolder`.

#### 🔴 G-002 — Elasticsearch Credentials Committed in Plaintext

**Severity:** CRITICAL | **Effort:** LOW

`application.properties` contains `elastic.password=zc17rW*9pTuGQMunVa-K` hardcoded. This is a direct credential exposure vulnerability.

**Recommendation:** Rotate credential immediately. Add `application.properties` to `.gitignore`. Use environment variables or Azure Key Vault.

### 7.3 Non-Blocking Gaps

| ID | Title | Severity | Effort | Classification |
|----|-------|----------|--------|---------------|
| G-003 | ON_LEAVE Status Never Applied | 🟡 MEDIUM | MEDIUM | MISSING |
| G-004 | Cross-Year Leave Calculation Defect | 🟠 HIGH | LOW | MISSING |
| G-005 | H2 Console Exposed | 🟠 HIGH | LOW | MISSING |
| G-006 | No Leave Balance Accrual | 🟡 MEDIUM | HIGH | MISSING |
| G-007 | No Salary Field Validation | 🟡 MEDIUM | LOW | TRANSFORM |
| G-008 | Terminate Endpoint Has No Auth Check | 🟠 HIGH | LOW | TRANSFORM |
| G-009 | Reinstate Endpoint Has No Auth Check | 🟠 HIGH | LOW | TRANSFORM |
| G-010 | No Production Database | 🟡 MEDIUM | HIGH | DEFERRED |
| G-011 | No OpenAPI Documentation | 🟢 LOW | LOW | DEFERRED |
| G-012 | Deprecated Elasticsearch Client | 🟡 MEDIUM | MEDIUM | DEFERRED |
| G-013 | Orphaned Leave Records on Employee Delete | 🟢 LOW | MEDIUM | DEFERRED |
| G-014 | No JPA Audit Trail | 🟡 MEDIUM | MEDIUM | DEFERRED |

---

## 8. Acceptance Criteria

### 8.1 Employee Lifecycle

| ID | Scenario | Type | Coverage |
|----|----------|------|---------|
| AC-001 | Hire employee — happy path | ✅ positive | COVERED |
| AC-002 | Hire — XSS in name rejected | ❌ negative | COVERED |
| AC-003 | Delete manager with direct reports | ❌ negative | COVERED |
| AC-004 | Promote STAFF → MANAGER by MANAGER | ✅ positive | COVERED |
| AC-005 | Promotion by STAFF rejected | ❌ negative | COVERED |
| AC-006 | Promote ADMIN — ceiling constraint | 📐 boundary | COVERED |
| AC-007 | Terminate ACTIVE employee | ✅ positive | COVERED |
| AC-008 | Terminate already-TERMINATED | ❌ negative | COVERED |
| AC-009 | Reinstate TERMINATED employee | ✅ positive | COVERED |
| AC-010 | Reinstate ACTIVE employee fails | ❌ negative | COVERED |

### 8.2 Payroll

| ID | Scenario | Type | Coverage |
|----|----------|------|---------|
| AC-011 | $80k salary — mid bracket tax | ✅ positive | COVERED |
| AC-012 | $120k salary — top bracket tax | ✅ positive | COVERED |
| AC-013 | $50k salary — tax-free threshold | 📐 boundary | COVERED |
| AC-014 | TERMINATED employee payroll blocked | ❌ negative | COVERED |
| AC-015 | No salary configured — blocked | ❌ negative | COVERED |

### 8.3 Email Generation

| ID | Scenario | Type | Coverage |
|----|----------|------|---------|
| AC-016 | Two-word name | ✅ positive | COVERED |
| AC-017 | Single-word name (ADO #2832 fix) | 📐 boundary | COVERED |

### 8.4 Leave Management

| ID | Scenario | Type | Coverage |
|----|----------|------|---------|
| AC-018 | Apply ANNUAL leave — happy path | ✅ positive | COVERED |
| AC-019 | Insufficient annual balance rejected | ❌ negative | COVERED |
| AC-020 | TERMINATED employee blocked | ❌ negative | COVERED |
| AC-021 | Overlapping date range rejected | ❌ negative | COVERED |
| AC-022 | Invalid date range (start > end) | ❌ negative | COVERED |
| AC-023 | Approve leave — balance deducted | ✅ positive | COVERED |
| AC-024 | STAFF approver blocked | ❌ negative | COVERED |
| AC-025 | Reject leave — balance unchanged | ✅ positive | COVERED |
| AC-026 | Cancel PENDING leave — no notice needed | ✅ positive | COVERED |
| AC-027 | Cancel another employee's leave blocked | ❌ negative | COVERED |
| AC-028 | Cancel APPROVED leave — balance refunded | ✅ positive | COVERED |
| AC-029 | Cancel APPROVED with < 2 days notice rejected | ❌ negative | **GAP** |
| AC-030 | Cross-year leave — correct day count | 📐 boundary | **GAP** |
| AC-031 | MATERNITY leave — no balance check | ✅ positive | COVERED |

### 8.5 Log Retrieval (MCP)

| ID | Scenario | Type | Coverage |
|----|----------|------|---------|
| AC-032 | Retrieve logs by E2E ID via MCP tool | ✅ positive | PARTIAL |

---

## 9. Risk Register

### 9.1 Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH | 5 |
| 🟡 MEDIUM | 3 |
| 🟢 LOW | 2 |

### 9.2 Risk Detail

#### 🔴 RISK-001 — No HTTP Authentication — Full Privilege Escalation

> **Category:** Security | **Likelihood:** HIGH | **Impact:** CRITICAL
> 
> No Spring Security or token-based authentication. Any caller can self-promote to ADMIN, approve their own leave, or terminate any employee by passing an arbitrary `requesterId`.
> 
> **Mitigation:** Add Spring Security with JWT; derive identity from `SecurityContext`.
> **Owner:** Security / Platform Team | **Timeline:** Immediate

#### 🔴 RISK-002 — Elasticsearch Credentials Committed in Repository

> **Category:** Security | **Likelihood:** HIGH | **Impact:** CRITICAL
> 
> `application.properties` contains `elastic.password=zc17rW*9pTuGQMunVa-K`. Direct credential exposure if repository is accessed by unauthorized parties.
> 
> **Mitigation:** Rotate password immediately. Move to environment variables / Key Vault. Add `application.properties` to `.gitignore`.
> **Owner:** Security Team | **Timeline:** Immediate — today

#### 🟠 RISK-003 — Terminate and Reinstate Endpoints Have No Authorization Gate

> **Category:** Security | **Likelihood:** HIGH | **Impact:** HIGH
> 
> `POST /employees/{id}/terminate` and `POST /employees/{id}/reinstate` have no role check. Any caller can terminate or reinstate any employee.
> 
> **Mitigation:** Add `requesterId` parameter and MANAGER/ADMIN check.
> **Owner:** Dev Team | **Timeline:** Sprint +1

#### 🟠 RISK-004 — Cross-Year Leave Duration Calculation Defect

> **Category:** Data Integrity | **Likelihood:** MEDIUM | **Impact:** HIGH
> 
> `getDayOfYear()` subtraction produces negative/incorrect day counts for cross-year leave dates. Causes wrong balance deductions.
> 
> **Mitigation:** Replace with `ChronoUnit.DAYS.between(startDate, endDate) + 1`.
> **Owner:** Dev Team | **Timeline:** Sprint +1

#### 🟠 RISK-005 — H2 Console Exposed

> **Category:** Security | **Likelihood:** MEDIUM | **Impact:** HIGH
> 
> `spring.h2.console.enabled=true` in application.properties. If deployed beyond local dev, `/h2-console` exposes full SQL access to all HR data.
> 
> **Mitigation:** Disable in non-dev Spring profiles.
> **Owner:** DevOps | **Timeline:** Before staging deployment

#### 🟠 RISK-006 — PII Stored Without Encryption or Access Control

> **Category:** Compliance | **Likelihood:** MEDIUM | **Impact:** HIGH
> 
> Employee name, salary, hire date stored unencrypted. Salary returned in full API responses to any caller.
> 
> **Mitigation:** Encrypt sensitive columns. Apply role-based field masking in API responses.
> **Owner:** Security / Legal | **Timeline:** Pre-production

#### 🟠 RISK-007 — H2 Database Not Suitable for Production

> **Category:** Operational | **Likelihood:** HIGH | **Impact:** HIGH
> 
> H2 is single-process, non-clusterable, and unsuitable for production HR data persistence.
> 
> **Mitigation:** Migrate to PostgreSQL/MySQL with Flyway.
> **Owner:** Infrastructure | **Timeline:** Pre-production

#### 🟡 RISK-008 — Deprecated Elasticsearch REST High Level Client

> **Category:** Technical Debt | **Likelihood:** HIGH | **Impact:** MEDIUM
> 
> `elasticsearch-rest-high-level-client 7.17.10` is deprecated and incompatible with ES 8+.
> 
> **Mitigation:** Migrate to `co.elastic.clients:elasticsearch-java` 8.x.
> **Owner:** Dev Team | **Timeline:** Sprint +2

#### 🟡 RISK-009 — No Leave Balance Accrual or Year-End Reset

> **Category:** Functional | **Likelihood:** HIGH | **Impact:** MEDIUM
> 
> Leave balances are static defaults that never reset. All employees will eventually exhaust balances with no automatic replenishment.
> 
> **Mitigation:** Define leave year policy; implement `@Scheduled` annual reset.
> **Owner:** Product Owner / Dev Team | **Timeline:** Sprint +2

#### 🟡 RISK-010 — No Audit Trail for Employee/Leave Changes

> **Category:** Compliance | **Likelihood:** HIGH | **Impact:** MEDIUM
> 
> No record of who changed employee records or leave requests beyond request ID in logs.
> 
> **Mitigation:** Enable Spring Data JPA Auditing.
> **Owner:** Dev Team | **Timeline:** Sprint +2

#### 🟢 RISK-011 — Orphaned Leave Requests on Employee Delete

> **Category:** Data Integrity | **Likelihood:** MEDIUM | **Impact:** LOW
> 
> Deleting an employee leaves orphaned `LeaveRequest` records with no owning employee.
> 
> **Mitigation:** Cascade-cancel open requests on delete, or implement soft-delete.
> **Owner:** Dev Team | **Timeline:** Sprint +3

#### 🟢 RISK-012 — No Salary Field Validation

> **Category:** Data Integrity | **Likelihood:** MEDIUM | **Impact:** LOW
> 
> Negative/zero salary accepted at creation. Only blocked at payroll time.
> 
> **Mitigation:** Add `@Positive` or `@Min(0)` to `Employee.salary`.
> **Owner:** Dev Team | **Timeline:** Sprint +1

---

## 10. Open Items

| ID | Question | Owner |
|----|----------|-------|
| OI-001 | Should `ON_LEAVE` employee status be fully implemented (set on leave approval, cleared on return), or removed from the enum? | Product Owner |
| OI-002 | What is the intended leave year policy — calendar year or hire-date anniversary? Should unused balance roll over? | HR Policy / Product Owner |
| OI-003 | Should `DELETE /employees/{id}` be soft-delete (retain record, mark deleted) or hard delete? What happens to open leave requests? | Product Owner / Data Architect |
| OI-004 | What currency and tax jurisdiction are the payroll tax brackets modelled after? Are the brackets configurable or are they fixed? | Finance / Product Owner |

---

## 11. Assumptions

| ID | Statement | Basis | Risk If Wrong | Owner |
|----|-----------|-------|--------------|-------|
| A-001 | Role-based authorization is enforced at the service layer only; there is no HTTP security filter | No Spring Security in pom.xml; no `SecurityConfig` class; all checks are manual if/throw | Any caller knowing a valid endpoint can bypass role checks | Security / Platform Team |
| A-002 | H2 file-based database is the runtime store for dev/demo environments only | `spring.datasource.url=jdbc:h2:file` in application.properties; no production override found | Data loss on restart in shared environments | DevOps / Infrastructure |
| A-003 | Leave day calculation uses `getDayOfYear()` subtraction which is year-boundary-unsafe | Code: `endDate.getDayOfYear() - startDate.getDayOfYear() + 1` | Cross-year leaves will compute incorrect balances | Dev Team |
| A-004 | Elasticsearch credentials are stored in plaintext in committed application.properties | `elastic.password=zc17rW*9pTuGQMunVa-K` present in version-controlled file | Credential exposure if repository is shared | Security Team |
| A-005 | `ON_LEAVE` status is an incomplete feature — defined in enum but never applied by any service | No service sets `EmployeeStatus.ON_LEAVE`; no test exercises it | Incomplete employee lifecycle representation | Product Owner |

---

## 12. Appendix — Artifact Catalog

| Path | Type | Relevance | Notes |
|------|------|-----------|-------|
| employee-simulator/pom.xml | build | HIGH | Spring Boot 3.4.1, Java 25, Spring AI 1.0.0, H2 2.2.224, ES client 7.17.10 |
| employee-simulator/src/main/java/org/example/App.java | source_code | LOW | Main `@SpringBootApplication` entry point |
| employee-simulator/src/main/java/org/example/controller/EmployeeController.java | source_code | HIGH | 13 endpoints covering full employee lifecycle |
| employee-simulator/src/main/java/org/example/controller/LeaveController.java | source_code | HIGH | 6 endpoints covering full leave request workflow |
| employee-simulator/src/main/java/org/example/controller/HealthController.java | source_code | LOW | Health check endpoint |
| employee-simulator/src/main/java/org/example/controller/McpController.java | source_code | MEDIUM | MCP server endpoint configuration |
| employee-simulator/src/main/java/org/example/service/EmployeeService.java | source_code | HIGH | Core business logic: CRUD, promote, terminate, reinstate, payroll, email |
| employee-simulator/src/main/java/org/example/service/LeaveService.java | source_code | HIGH | Leave workflow with authorization and balance rules |
| employee-simulator/src/main/java/org/example/entity/Employee.java | source_code | HIGH | Aggregate root with role/status enums, salary, managerId, leave balances |
| employee-simulator/src/main/java/org/example/entity/LeaveRequest.java | source_code | HIGH | Leave entity with workflow state machine in Javadoc |
| employee-simulator/src/main/java/org/example/entity/enums/EmployeeRole.java | source_code | HIGH | STAFF < MANAGER < ADMIN hierarchy |
| employee-simulator/src/main/java/org/example/entity/enums/EmployeeStatus.java | source_code | HIGH | ACTIVE, ON_LEAVE (unused), TERMINATED |
| employee-simulator/src/main/java/org/example/entity/enums/LeaveStatus.java | source_code | HIGH | PENDING → APPROVED/REJECTED/CANCELLED state machine |
| employee-simulator/src/main/java/org/example/entity/enums/LeaveType.java | source_code | HIGH | ANNUAL, SICK (capped), UNPAID, MATERNITY, PATERNITY (uncapped) |
| employee-simulator/src/main/java/org/example/dto/PayrollResult.java | source_code | MEDIUM | Immutable record: id, name, annualGross, annualTax, monthlyNet |
| employee-simulator/src/main/java/org/example/elastic/ElasticSearchService.java | source_code | MEDIUM | ES log retrieval with local file fallback |
| employee-simulator/src/main/java/org/example/mcp/ElasticMcpTools.java | source_code | MEDIUM | Spring AI `@Tool` methods for MCP server |
| employee-simulator/src/main/java/org/example/config/RequestIdFilter.java | source_code | MEDIUM | E2E request ID propagation via MDC |
| employee-simulator/src/main/java/org/example/util/XssValidator.java | source_code | LOW | Regex-based HTML tag detection |
| employee-simulator/src/main/java/org/example/exception/GlobalExceptionHandler.java | source_code | LOW | Global `@RestControllerAdvice` |
| employee-simulator/src/main/resources/application.properties | config | HIGH | H2 datasource, logging, ES connection (WARNING: hardcoded password) |
| employee-simulator/src/main/resources/application.properties.example | config | HIGH | Template without real credentials |
| employee-simulator/src/main/resources/logback-spring.xml | config | MEDIUM | Logstash JSON encoder; requestId in MDC |
| employee-simulator/src/test/java/org/example/service/EmployeeServiceTest.java | test | HIGH | 15 integration tests: lifecycle, payroll, email |
| employee-simulator/src/test/java/org/example/service/LeaveServiceTest.java | test | HIGH | 10 integration tests: leave workflow, auth, validation |

---

*Document generated by BRD Pipeline — Run ID: 20260615-brd1 | Confidence: 86% (HIGH) | BRD Locked: ✅ YES | Generated: 2026-06-15*
