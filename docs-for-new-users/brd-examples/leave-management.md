# Business Requirements Document: leave-management

## 1. Title Block

| Field | Value |
|---|---|
| Component | leave-management |
| Domain | Leave and Attendance Management |
| Framework | Spring Boot 2.7.18 (Java 11, Maven) |
| Run ID | 20260615-0915-a7c2 |
| Date | 2026-06-15 |
| BRD Status | LOCKED |
| Overall Confidence | 84% |
| Version | 1.1 |
| Prepared By | BRD Pipeline Orchestrator |

## 2. Table of Contents

- [3. Executive Summary](#3-executive-summary)
- [4. Scope](#4-scope)
- [5. Stakeholders and Actors](#5-stakeholders-and-actors)
- [6. System Dependencies](#6-system-dependencies)
- [7. User Journeys](#7-user-journeys)
- [8. Business Rules](#8-business-rules)
- [9. Gap Analysis](#9-gap-analysis)
- [10. Acceptance Criteria](#10-acceptance-criteria)
- [11. Risk Register](#11-risk-register)
- [12. Open Items](#12-open-items)
- [13. Assumptions](#13-assumptions)
- [14. Appendix - Artifact Catalog](#14-appendix---artifact-catalog)

## 3. Executive Summary

The leave-management component implements employee leave submission, managerial decisioning, leave balance governance, and notification/escalation support in a legacy Spring Boot service. Core workflows are clearly represented across controller-service-repository boundaries, with strong policy intent in submission and approval code paths. Primary journey evidence is in [leave-management/src/main/java/com/vz/leave/controller/LeaveRequestController.java](leave-management/src/main/java/com/vz/leave/controller/LeaveRequestController.java#L27), [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L55), [leave-management/src/main/java/com/vz/leave/controller/ApprovalController.java](leave-management/src/main/java/com/vz/leave/controller/ApprovalController.java#L25), and [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L49).

This BRD is LOCKED at 84% confidence because discovery, journey extraction, rule extraction, and risk analysis converge with limited contradiction. GitNexus symbol context confirms key execution links for submit and approve flows, while repository-level queries and code comments reinforce policy boundaries and known implementation gaps.

Top findings are concentrated in authorization enforcement, escalation completeness, balance integrity under concurrency, and test coverage. Business requirements are stable enough for planning and modernization, but several blocking controls must be addressed before production-grade compliance and security posture can be claimed.

## 4. Scope

### In Scope

| # | Capability |
|---|---|
| 1 | Submit leave requests with validation, overlap, balance, and department checks |
| 2 | Approve/reject pending leave requests and record decisions |
| 3 | Cancel eligible leave requests with conditional balance restoration |
| 4 | Register employees and initialize policy-driven leave balances |
| 5 | Execute comp-off accrual and year-end carry-forward logic |
| 6 | Perform notification attempts and stale-request escalation checks |

### Out of Scope

| Capability | Reason |
|---|---|
| Payroll or finance posting | Separate domain and no integration implementation |
| Holiday calendar integration | Not implemented in business-day logic |
| Identity provider internals | Upstream concern outside component boundary |
| UI/mobile workflows | Service-only repository scope |

### Deferred

| Capability | Reason |
|---|---|
| Multi-level approval for long leaves | Requires model and workflow redesign |
| Managed escalation ticketing and SLA tracking | No current state model or integration channel |

## 5. Stakeholders and Actors

| Actor | Type | Responsibilities |
|---|---|---|
| Employee | Business user | Submit leave, cancel requests, receive outcomes |
| Direct Manager | Business approver | Approve/reject requests and provide rationale |
| HR Operations | Policy owner | Define leave policy and exception handling |
| Compliance | Governance | Enforce retention, auditability, and authorization controls |
| Platform/DevOps | Technical owner | Operate runtime, mail integration, and configuration hygiene |
| Scheduler | System actor | Run monthly balance audit and scheduled checks |
| External SSO Gateway | External dependency | Provides upstream identity context for users |

Authorization warning: no in-service HTTP auth middleware is implemented for mutating routes. Sensitive operations rely on caller-supplied IDs and warning logs rather than mandatory policy enforcement ([leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java](leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java#L17), [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L60)).

## 6. System Dependencies

### Regulatory Flags Summary

| Flag | Status | Notes |
|---|---|---|
| Authorization control | ❌ Missing | Approval manager check is soft warning, not hard block |
| Audit trail retention | ❌ Missing | No immutable audit trail for decision lifecycle |
| Data integrity protection | ❌ Partial | Balance deduction lacks explicit race-condition guard |
| Test governance | ❌ Missing | Only context-load test present |
| PII policy coverage | ❌ Partial | Reason/emergency contact stored without retention/masking policy |

### Spring Boot Web

- Type: framework
- Protocol: HTTP
- Direction: inbound
- has_fallback: false
- has_circuit_breaker: false
- is_spof: false
- Migration notes: add Spring Security and endpoint validation policies

### Spring Data JPA / Hibernate

- Type: persistence
- Protocol: JDBC
- Direction: outbound
- has_fallback: false
- has_circuit_breaker: false
- is_spof: true
- Migration notes: add locking and stronger DB constraints for policy invariants

### H2 Database

- Type: database
- Protocol: JDBC
- Direction: outbound
- has_fallback: false
- has_circuit_breaker: false
- is_spof: true
- Migration notes: replace in-memory assumptions with managed production datastore

### SMTP Mail Integration

- Type: integration
- Protocol: SMTP
- Direction: outbound
- has_fallback: false
- has_circuit_breaker: false
- is_spof: true
- Migration notes: enforce TLS/auth, asynchronous delivery, retries, and fallback channels ([leave-management/src/main/resources/application.properties](leave-management/src/main/resources/application.properties#L23), [leave-management/src/main/java/com/vz/leave/service/NotificationService.java](leave-management/src/main/java/com/vz/leave/service/NotificationService.java#L42))

### Spring Scheduling

- Type: platform
- Protocol: in-process
- Direction: internal
- has_fallback: false
- has_circuit_breaker: false
- is_spof: false
- Migration notes: add observability and actionable response for audit anomalies ([leave-management/src/main/java/com/vz/leave/service/LeaveAccrualService.java](leave-management/src/main/java/com/vz/leave/service/LeaveAccrualService.java#L73))

### External Identity Provider / SSO Gateway

- Type: security
- Protocol: SSO
- Direction: inbound
- has_fallback: false
- has_circuit_breaker: false
- is_spof: true
- Migration notes: maintain upstream identity but enforce authorization server-side in this service

## 7. User Journeys

### Journey Map Summary

| ID | Name | Actor | Source | Classification | Confidence |
|---|---|---|---|---|---|
| J001 | Submit Leave Request | Employee | LeaveRequestController + LeaveRequestService | PRIMARY | 0.95 |
| J002 | Approve or Reject Leave | Manager | ApprovalController + ApprovalService | PRIMARY | 0.92 |
| J003 | Cancel Leave Request | Employee/Operations | LeaveRequestController + LeaveRequestService | SECONDARY | 0.86 |
| J004 | Register Employee and Initialize Balances | HR/Admin | EmployeeController + EmployeeService | SECONDARY | 0.88 |
| J005 | Maintain Leave Balances | System | LeaveBalanceService + LeaveAccrualService | BACKEND | 0.90 |
| J006 | Notify Stakeholders and Escalate Stale Requests | System | NotificationService + ApprovalService | BACKEND | 0.76 |

### Flow Diagrams

Employee lifecycle:

```text
[Create Employee]
      |
      v
[ACTIVE + Department Assigned]
      |
      +--> [Initialize Leave Balances]
      |
      +--> [Submit Leave Requests]
      |
      v
[DEACTIVATE]
```

Leave lifecycle:

```text
[SUBMIT]
   |
   v
[PENDING] ----> [REJECTED]
   |  \
   |   \--> [CANCELLED]
   v
[APPROVED] ----> [CANCELLED]
   |
   +--> [DEDUCT BALANCE]

[PENDING > 3 DAYS]
   |
   v
[ESCALATION LOG ENTRY]
   |
   +--> no durable ESCALATED state currently
```

## 8. Business Rules

### Validation Rules

| Rule ID | Description | Evidence |
|---|---|---|
| VAL001 | Employee must be active to submit leave | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L63) |
| VAL002 | Start date must be before or equal to end date | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L74) |
| VAL003 | Rejection requires non-empty comment | [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L114) |
| VAL004 | Emergency contact required when businessDays > 5 | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L133) |

### Constraint Rules

| Rule ID | Description | Evidence |
|---|---|---|
| CONST001 | No overlapping PENDING/APPROVED leave per employee | [leave-management/src/main/java/com/vz/leave/repository/LeaveRequestRepository.java](leave-management/src/main/java/com/vz/leave/repository/LeaveRequestRepository.java#L31) |
| CONST002 | Requested days must not exceed available balance | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L99) |
| CONST003 | Department max concurrent leave threshold enforced | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L107) |
| CONST004 | Department blackout window blocks submission | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L117) |
| CONST005 | COMP_OFF accrual capped at 12 days/year | [leave-management/src/main/java/com/vz/leave/service/LeaveAccrualService.java](leave-management/src/main/java/com/vz/leave/service/LeaveAccrualService.java#L52) |
| CONST006 | Probation employees cannot take annual leave | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L68) |
| CONST007 | Annual leave requires at least 3 days notice | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L123) |

### Authorization Rules

| Rule ID | Description | Evidence |
|---|---|---|
| AUTH001 | Only direct manager should approve leave | [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L60) |
| AUTH002 | Self-approval must be rejected | [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L55) |
| AUTH003 | Mutating routes require authenticated role checks | [leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java](leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java#L17) |

### Workflow Rules

| Rule ID | Description | Evidence |
|---|---|---|
| WF001 | Core status machine: PENDING -> APPROVED/REJECTED/CANCELLED | [leave-management/src/main/java/com/vz/leave/model/LeaveStatus.java](leave-management/src/main/java/com/vz/leave/model/LeaveStatus.java#L9) |
| WF002 | Cancelling APPROVED leave restores deducted balance | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L211) |
| WF003 | Pending requests over 3 days should escalate | [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L145) |
| WF004 | Leaves >15 days flagged for director approval | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L138) |

### Calculation Rules

| Rule ID | Description | Evidence |
|---|---|---|
| CALC001 | Available = total + carriedForward - used | [leave-management/src/main/java/com/vz/leave/model/LeaveBalance.java](leave-management/src/main/java/com/vz/leave/model/LeaveBalance.java#L28) |
| CALC002 | Business days exclude weekends only | [leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java](leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java#L55) |
| CALC003 | Half-day requests deduct 0.5 | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L97) |
| CALC004 | New joiner annual entitlement is prorated and rounded to 0.5 | [leave-management/src/main/java/com/vz/leave/service/EmployeeService.java](leave-management/src/main/java/com/vz/leave/service/EmployeeService.java#L63) |
| CALC005 | Year-end annual carry-forward capped at 5 | [leave-management/src/main/java/com/vz/leave/service/LeaveBalanceService.java](leave-management/src/main/java/com/vz/leave/service/LeaveBalanceService.java#L57) |

## 9. Gap Analysis

| Classification | Count |
|---|---|
| CLEAN_MAP | 5 |
| TRANSFORM | 4 |
| MISSING | 3 |
| DEFERRED | 2 |
| BLOCKING | 5 |

#### 🔴 CRITICAL - GAP-B01: Missing hard authorization enforcement on approval path

- Severity: CRITICAL
- Effort: M
- Affected: J002, AUTH001, AUTH003
- Evidence: [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L60), [leave-management/src/main/java/com/vz/leave/controller/ApprovalController.java](leave-management/src/main/java/com/vz/leave/controller/ApprovalController.java#L25)
- Recommendation: enforce direct-manager authorization as hard failure with authenticated principal binding.

#### 🔴 CRITICAL - GAP-B02: No endpoint-level auth on employee administration

- Severity: CRITICAL
- Effort: M
- Affected: J004, AUTH003
- Evidence: [leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java](leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java#L17)
- Recommendation: require role-based authorization and auditable action identity.

#### 🟠 HIGH - GAP-B03: Escalation workflow is log-only and lacks state

- Severity: HIGH
- Effort: M
- Affected: J006, WF003
- Evidence: [leave-management/src/main/java/com/vz/leave/service/ApprovalService.java](leave-management/src/main/java/com/vz/leave/service/ApprovalService.java#L145), [leave-management/src/main/java/com/vz/leave/model/LeaveStatus.java](leave-management/src/main/java/com/vz/leave/model/LeaveStatus.java#L9)
- Recommendation: add ESCALATED state, de-duplication, and integration-based escalation action.

#### 🟠 HIGH - GAP-B04: Balance deduction lacks concurrency safety

- Severity: HIGH
- Effort: M
- Affected: J001, J005, CONST002
- Evidence: [leave-management/src/main/java/com/vz/leave/service/LeaveBalanceService.java](leave-management/src/main/java/com/vz/leave/service/LeaveBalanceService.java#L41)
- Recommendation: enforce atomic updates and non-negative invariant checks.

#### 🟠 HIGH - GAP-B05: Automated behavior tests are largely missing

- Severity: HIGH
- Effort: L
- Affected: J001, J002, J003, J005, J006
- Evidence: [leave-management/src/test/java/com/vz/leave/LeaveManagementApplicationTests.java](leave-management/src/test/java/com/vz/leave/LeaveManagementApplicationTests.java#L7)
- Recommendation: add unit/integration regression suite covering policy and workflow negatives.

### Non-Blocking Gaps

| ID | Classification | Description | Evidence |
|---|---|---|---|
| GAP-N01 | TRANSFORM | MM-dd string comparison can mis-handle year boundary blackout windows | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L170) |
| GAP-N02 | TRANSFORM | Public holidays excluded from business-day calculations | [leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java](leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java#L55) |
| GAP-N03 | MISSING | Leave list endpoint returns all rows with no pagination | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L229) |
| GAP-N04 | DEFERRED | Long-leave dual approval not implemented | [leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java](leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java#L138) |
| GAP-N05 | DEFERRED | Holiday calendar integration absent | [leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java](leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java#L55) |

## 10. Acceptance Criteria

### Leave Submission

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J001-01 | ✅ Positive | Active employee with balance submits valid annual leave and request becomes PENDING | PARTIAL |
| AC-J001-02 | ❌ Negative | Probation employee cannot submit annual leave | **GAP** |
| AC-J001-03 | 📐 Boundary | Annual leave with less than 3-day notice is blocked | **GAP** |
| AC-J001-04 | ❌ Negative | Leave >5 business days without emergency contact is blocked | **GAP** |

### Approval and Rejection

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J002-01 | ✅ Positive | Direct manager approves pending request and balance is deducted | PARTIAL |
| AC-J002-02 | ❌ Negative | Non-manager cannot approve request | **GAP** |
| AC-J002-03 | ❌ Negative | Reject without reason is blocked | **GAP** |

### Cancellation

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J003-01 | ✅ Positive | Cancel APPROVED request restores balance | PARTIAL |
| AC-J003-02 | ❌ Negative | Cancel REJECTED/CANCELLED request is blocked | **GAP** |

### Employee Onboarding

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J004-01 | ✅ Positive | Employee creation initializes all leave buckets | PARTIAL |
| AC-J004-02 | 📐 Boundary | Annual proration rounds to nearest 0.5 day | **GAP** |

### Balance and Accrual

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J005-01 | 📐 Boundary | COMP_OFF accrual over 12 days is rejected | **GAP** |
| AC-J005-02 | 📐 Boundary | Year-end carry-forward caps annual balance at 5 | **GAP** |

### Notifications and Escalation

| ID | Indicator | Scenario | Coverage |
|---|---|---|---|
| AC-J006-01 | ❌ Negative | Notification failure does not lose business event | **GAP** |
| AC-J006-02 | ✅ Positive | Pending >3 days enters durable escalation workflow | **GAP** |

## 11. Risk Register

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 2 |
| 🟠 HIGH | 3 |
| 🟡 MEDIUM | 2 |
| 🟢 LOW | 1 |

#### R-01 - Unauthorized approval or admin mutation (🔴 CRITICAL)

> Category: Security  
> Likelihood: HIGH  
> Impact: HIGH  
> Score: 9  
> Mitigation: enforce principal-based authorization and role checks for all mutating endpoints.  
> Owner: Security and API Team

#### R-02 - Policy bypass for long-leave and manager validation (🔴 CRITICAL)

> Category: Compliance  
> Likelihood: MEDIUM  
> Impact: HIGH  
> Score: 8  
> Mitigation: convert warning-only controls into hard enforcement and multi-step approval where policy requires.  
> Owner: HR Policy and Engineering

#### R-03 - Data integrity under concurrent approvals (🟠 HIGH)

> Category: Reliability  
> Likelihood: MEDIUM  
> Impact: HIGH  
> Score: 7  
> Mitigation: add locking strategy and atomic non-negative checks.  
> Owner: Platform Team

#### R-04 - Notification and escalation loss (🟠 HIGH)

> Category: Integration  
> Likelihood: HIGH  
> Impact: MEDIUM  
> Score: 7  
> Mitigation: move to async outbox/queue with retries, fallback, and stateful escalation.  
> Owner: Operations

#### R-05 - Insecure SMTP configuration (🟠 HIGH)

> Category: Security  
> Likelihood: MEDIUM  
> Impact: MEDIUM  
> Score: 6  
> Mitigation: require SMTP auth, TLS, secret-store driven credentials, and environment overrides.  
> Owner: DevOps

#### R-06 - No decision audit trail (🟡 MEDIUM)

> Category: Compliance  
> Likelihood: MEDIUM  
> Impact: MEDIUM  
> Score: 5  
> Mitigation: persist immutable actor/action timeline with retention policy.  
> Owner: Compliance

#### R-07 - Minimal regression safety from weak tests (🟡 MEDIUM)

> Category: Delivery  
> Likelihood: HIGH  
> Impact: MEDIUM  
> Score: 6  
> Mitigation: implement journey-level unit and API integration tests with CI quality gate.  
> Owner: Engineering Manager

#### R-08 - Calendar edge-case inaccuracies (🟢 LOW)

> Category: Business Logic  
> Likelihood: MEDIUM  
> Impact: LOW  
> Score: 3  
> Mitigation: use policy-driven date ranges and holiday service integration.  
> Owner: Product and Engineering

## 12. Open Items

| ID | Question | Owner |
|---|---|---|
| OI-01 | What trust boundary guarantees caller identity and role claims before reaching this service? | Security Architect |
| OI-02 | Is director-level approval mandatory block for >15-day leave or post-fact review? | HR Policy Owner |
| OI-03 | What retention and masking policy applies to leave reason and emergency contact PII? | Compliance |
| OI-04 | Which escalation target system is authoritative (ticketing, mail, workflow engine)? | Operations |
| OI-05 | What test coverage and release gate threshold is mandatory for this component? | Engineering Manager |

## 13. Assumptions

| ID | Statement | Basis | Risk if Wrong | Owner |
|---|---|---|---|---|
| A-01 | Upstream SSO provides authenticated user identity | Application class notes and architecture comments | Unauthorized requests may reach mutating endpoints | Security Architect |
| A-02 | H2 behavior approximates production DB semantics for current policy logic | Local config and seeded SQL usage | Production race/constraint behavior diverges | Platform Team |
| A-03 | HR policy accepts current leave-type allocations and carry-forward rules | Service-level hardcoded constants | Policy non-compliance and entitlement disputes | HR Operations |
| A-04 | Email is currently acceptable as primary notification channel | NotificationService implementation | Missed approvals if SMTP unavailable | Operations |

## 14. Appendix - Artifact Catalog

| Artifact | Type | Relevance | Notes |
|---|---|---|---|
| leave-management/pom.xml | Build config | High | Framework/runtime dependencies and versions |
| leave-management/src/main/java/com/vz/leave/LeaveManagementApplication.java | Entry point | High | Application bootstrap and scheduling enablement |
| leave-management/src/main/java/com/vz/leave/controller/LeaveRequestController.java | Controller | High | Leave submit/read/cancel APIs |
| leave-management/src/main/java/com/vz/leave/controller/ApprovalController.java | Controller | High | Approve/reject/escalate APIs |
| leave-management/src/main/java/com/vz/leave/controller/EmployeeController.java | Controller | High | Employee lifecycle and balances API |
| leave-management/src/main/java/com/vz/leave/controller/DepartmentController.java | Controller | Medium | Department CRUD and blackout parameters |
| leave-management/src/main/java/com/vz/leave/service/LeaveRequestService.java | Service | Critical | Core submission/cancellation policy engine |
| leave-management/src/main/java/com/vz/leave/service/ApprovalService.java | Service | Critical | Approval authorization and escalation logic |
| leave-management/src/main/java/com/vz/leave/service/LeaveBalanceService.java | Service | Critical | Balance updates and carry-forward process |
| leave-management/src/main/java/com/vz/leave/service/LeaveAccrualService.java | Service | High | Comp-off accrual and monthly audit |
| leave-management/src/main/java/com/vz/leave/service/EmployeeService.java | Service | High | Employee creation and balance initialization |
| leave-management/src/main/java/com/vz/leave/service/NotificationService.java | Service | High | SMTP notifications and failure behavior |
| leave-management/src/main/java/com/vz/leave/repository/LeaveRequestRepository.java | Repository | High | Overlap/concurrency/stale queries |
| leave-management/src/main/java/com/vz/leave/model/LeaveRequest.java | Model | High | Status, business-day calculation, timestamps |
| leave-management/src/main/java/com/vz/leave/model/LeaveBalance.java | Model | High | Balance availability formula |
| leave-management/src/main/java/com/vz/leave/model/Employee.java | Model | High | Probation logic and manager relationship |
| leave-management/src/main/java/com/vz/leave/model/LeaveStatus.java | Enum | High | Workflow state machine |
| leave-management/src/main/java/com/vz/leave/model/LeaveType.java | Enum | Medium | Leave policy buckets |
| leave-management/src/main/resources/application.properties | Runtime config | High | SMTP/database/security posture |
| leave-management/src/main/resources/data.sql | Seed data | Medium | Sample org structure and edge-case hints |
| leave-management/src/test/java/com/vz/leave/LeaveManagementApplicationTests.java | Test | Critical | Indicates test coverage gap |
| KB/leave-management/leave-management/discovery.json | Pipeline artifact | High | Discovery and scope output |
| KB/leave-management/leave-management/journey-map.json | Pipeline artifact | High | Journey extraction output |
| KB/leave-management/leave-management/business-rules.json | Pipeline artifact | High | Rule extraction output |
| KB/leave-management/leave-management/gap-analysis.json | Pipeline artifact | High | Gap classification output |
| KB/leave-management/leave-management/brd-final.json | Pipeline artifact | High | BRD lock/confidence synthesis |
| KB/leave-management/leave-management/acceptance-criteria.json | Pipeline artifact | High | AC generation output |
| KB/leave-management/leave-management/acceptance-criteria.feature | Pipeline artifact | High | Gherkin scenarios |
| KB/leave-management/leave-management/risk-register.json | Pipeline artifact | High | Risk mapping output |
| KB/leave-management/leave-management/dependency-register.json | Pipeline artifact | High | Dependency and compliance mapping |

*Document generated by BRD Pipeline - Run ID: 20260615-0915-a7c2 | Confidence: 84% (HIGH) | BRD Locked: YES | Generated: 2026-06-15*
