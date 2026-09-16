# Business Requirements Document

## Title Block

| Attribute | Value |
|---|---|
| Component | spring-petclinic |
| Domain | Veterinary clinic management |
| Framework | Spring Boot 4.0.3, Spring MVC, Thymeleaf, Spring Data JPA |
| Run ID | 20260615-spc-01 |
| Date | 2026-06-15 |
| BRD Status | LOCKED |
| Overall Confidence | 84% |
| Version | 1.0 |
| Prepared By | GitHub Copilot BRD Pipeline |

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Scope](#scope)
3. [Stakeholders and Actors](#stakeholders-and-actors)
4. [System Dependencies](#system-dependencies)
5. [User Journeys](#user-journeys)
6. [Business Rules](#business-rules)
7. [Gap Analysis](#gap-analysis)
8. [Acceptance Criteria](#acceptance-criteria)
9. [Risk Register](#risk-register)
10. [Open Items](#open-items)
11. [Assumptions](#assumptions)
12. [Appendix - Artifact Catalog](#appendix---artifact-catalog)

## Executive Summary

Spring Petclinic is a server-rendered veterinary clinic management application that allows staff to register and search owners, maintain pets under an owner, record pet visits, and browse a directory of veterinarians. The application is built as a single Spring Boot deployable with Thymeleaf views, a JPA persistence layer, validation rules in both annotations and controller logic, and optional runtime profiles for H2, MySQL, and PostgreSQL.

The recovered BRD is locked because the core user flows are well-supported by code, templates, schema, message bundles, and a meaningful test suite that covers controllers, persistence behavior, validation, portability, and localization discipline. Confidence is not higher than 84% because the repository is explicitly a sample application, which means several enterprise behaviors are absent by design and business intent beyond the demo scope is not fully specified.

The dominant finding is that the application models record-keeping workflows rather than a production-hardened clinic platform. Owner, pet, and visit management are concrete and test-backed. In contrast, authentication, authorization, PII governance, auditability, and full appointment scheduling semantics are not implemented and should be treated as blocking gaps if this component is used as the baseline for a real product or migration effort.

## Scope

### In Scope

| # | Capability | Description |
|---|---|---|
| 1 | Owner search | Search owners by last-name prefix, including broad search when last name is blank. |
| 2 | Owner registration | Create owners with validated address, city, and 10-digit telephone. |
| 3 | Owner maintenance | View and update owner details with route-to-form id consistency checks. |
| 4 | Pet maintenance | Add and update pets under an owner with duplicate-name and birth-date validation. |
| 5 | Visit recording | Create dated visit records with required description and history display. |
| 6 | Veterinarian directory | Render veterinarian lists in HTML and JSON. |
| 7 | Localization support | Resolve UI messages through locale-aware message bundles and lang parameter switching. |
| 8 | Multi-database profiles | Support H2 by default with MySQL and PostgreSQL profile-specific runtime options. |

### Out of Scope

| Capability | Reason |
|---|---|
| Billing and payments | No code, schema, or tests indicate charging, invoicing, or settlement workflows. |
| Staff scheduling and clinician assignment | Visits have date and description only, with no provider or time-slot model. |
| Identity and access management | No authentication or authorization subsystem exists. |
| Deletion or archival lifecycle | No owner, pet, or visit delete/archive routes or behaviors were found. |
| Notifications and reminders | No messaging, email, SMS, or eventing integrations were found. |

### Deferred

| Capability | Reason |
|---|---|
| Production actuator hardening | Current configuration intentionally exposes all endpoints for development/testing. |
| Demo error-route removal | The crash route is demonstrative and should be removed or shielded outside demos. |
| PII governance controls | Owner contact data exists without masking, retention, or audit implementation. |

## Stakeholders and Actors

| Actor | Type | Responsibilities |
|---|---|---|
| Clinic staff | Primary user | Search owners, register/update owners, add/update pets, record visits. |
| Pet owner | Informational actor | Subject of owner, pet, and visit records; no self-service capability is implemented. |
| Veterinarian | Informational actor | Appears in the directory and specialty catalog; no interactive workflow is implemented. |
| System administrator | Operational actor | Chooses runtime profile, database connectivity, and environment controls. |
| Developer/tester | Supporting actor | Uses integration profiles, Docker-backed tests, and the demo error path. |

Authorization warning: no HTTP authentication or role-based authorization was found. Current endpoints should be treated as effectively open until access control is introduced.

## System Dependencies

### Regulatory Flags Summary

| Flag | Status | Notes |
|---|---|---|
| PII present | Yes | Owner address and telephone are stored and rendered. |
| Authentication required for production | Yes | Not implemented in current codebase. |
| Audit logging required for production | Likely | Not implemented, but owner contact updates and visit history imply traceability needs. |
| Healthcare compliance logic | No explicit evidence | No insurance, treatment, prescription, or payment compliance rules were found. |

### Spring Boot MVC Runtime

| Attribute | Value |
|---|---|
| Type | Framework/runtime |
| Protocol | In-process MVC over HTTP |
| Direction | Inbound |
| has_fallback | No |
| has_circuit_breaker | No |
| is_spof | Yes |
| Migration notes | Business logic is controller-centric. Service/API separation would simplify modernization. |

### H2 Database

| Attribute | Value |
|---|---|
| Type | Database |
| Protocol | JDBC |
| Direction | Outbound |
| has_fallback | No |
| has_circuit_breaker | No |
| is_spof | Yes |
| Migration notes | Default startup database seeded from SQL scripts. Useful for demos and local validation, not enough for enterprise tenancy or governance. |

### MySQL Profile

| Attribute | Value |
|---|---|
| Type | Database |
| Protocol | JDBC |
| Direction | Outbound |
| has_fallback | No |
| has_circuit_breaker | No |
| is_spof | Yes |
| Migration notes | Supported via profile and Testcontainers coverage. Configuration is property-driven and should be externalized securely. |

### PostgreSQL Profile

| Attribute | Value |
|---|---|
| Type | Database |
| Protocol | JDBC |
| Direction | Outbound |
| has_fallback | No |
| has_circuit_breaker | No |
| is_spof | Yes |
| Migration notes | Supported via profile and Docker Compose-backed integration flow. Keep schema parity across all DB variants. |

### JCache/Caffeine for Vet Cache

| Attribute | Value |
|---|---|
| Type | Cache |
| Protocol | JCache API |
| Direction | Internal |
| has_fallback | Yes |
| has_circuit_breaker | No |
| is_spof | No |
| Migration notes | Only veterinarian lookups are cached. Missing cache hurts performance, not functional correctness. |

### Message Bundles and Locale Switching

| Attribute | Value |
|---|---|
| Type | Localization |
| Protocol | Properties file lookup with lang query parameter |
| Direction | Internal |
| has_fallback | Yes |
| has_circuit_breaker | No |
| is_spof | No |
| Migration notes | Locale is session-backed. Translation parity is enforced by tests and should remain a quality gate. |

### Actuator Endpoints

| Attribute | Value |
|---|---|
| Type | Operational interface |
| Protocol | HTTP |
| Direction | Inbound |
| has_fallback | No |
| has_circuit_breaker | No |
| is_spof | No |
| Migration notes | Currently wide open in properties for development/testing. Production rollout requires restriction and access control. |

## User Journeys

### Journey Map Summary

| ID | Name | Actor | Source | Classification | Confidence |
|---|---|---|---|---|---|
| J1 | Open clinic home page | Pet owner or clinic staff | WelcomeController + welcome view | CLEAN_MAP | 0.95 |
| J2 | Search owners by last name prefix | Clinic staff | OwnerController + owner tests | CLEAN_MAP | 0.95 |
| J3 | Register a new owner | Clinic staff | OwnerController + owner tests | CLEAN_MAP | 0.93 |
| J4 | Update an owner record | Clinic staff | OwnerController + owner tests | CLEAN_MAP | 0.92 |
| J5 | View owner details including pets and visits | Clinic staff | OwnerController + ownerDetails view | CLEAN_MAP | 0.94 |
| J6 | Add a pet to an owner | Clinic staff | PetController + validator/tests | CLEAN_MAP | 0.95 |
| J7 | Edit pet details | Clinic staff | PetController + service tests | CLEAN_MAP | 0.91 |
| J8 | Book a visit for a pet | Clinic staff | VisitController + visit tests | CLEAN_MAP | 0.93 |
| J9 | Browse veterinarian directory in HTML | Pet owner or clinic staff | VetController HTML route | CLEAN_MAP | 0.90 |
| J10 | Fetch veterinarian directory in JSON | Browser or API consumer | VetController JSON route | TRANSFORM | 0.86 |
| J11 | Trigger demo error page | Developer or tester | CrashController | DEFERRED | 0.89 |

### Flow Diagram - Owner and Pet Lifecycle

```text
[Start]
   |
   v
[Find Owners] --blank/partial last name--> [Owner Results]
   |                                         | 0 results -> [Search Error]
   |                                         | 1 result  -> [Owner Detail]
   |                                         | many      -> [Paginated List]
   v
[Add Owner] --valid--> [Owner Detail]
   |
   +--invalid required fields--> [Owner Form Errors]

[Owner Detail]
   |
   +--> [Edit Owner] --valid--> [Owner Detail]
   |         |
   |         +--id mismatch/invalid--> [Edit Error]
   |
   +--> [Add Pet] --valid--> [Owner Detail]
             |
             +--duplicate name / blank name / missing type / future date--> [Pet Form Errors]
```

### Flow Diagram - Visit Lifecycle

```text
[Owner Detail]
   |
   v
[Select Pet]
   |
   v
[New Visit Form]
   |
   +--owner/pet mismatch--> [Request Rejected]
   |
   +--blank description--> [Visit Form Errors]
   |
   +--valid description--> [Visit Saved with Current Date Default]
                              |
                              v
                         [Owner Detail with Visit History]
```

## Business Rules

### Validation Rules

| ID | Rule |
|---|---|
| BR-VAL-01 | Owner address is required. |
| BR-VAL-02 | Owner city is required. |
| BR-VAL-03 | Owner telephone is required and must be exactly 10 digits. |
| BR-VAL-04 | Pet name is required. |
| BR-VAL-05 | New pets must have a type. |
| BR-VAL-06 | Pet birth date is required. |
| BR-VAL-07 | Pet birth date cannot be in the future. |
| BR-VAL-08 | Visit description is required. |

### Constraints

| ID | Rule |
|---|---|
| BR-CON-01 | Form binding must not set owner, pet, or nested ids directly. |
| BR-CON-02 | Pet names must be unique per owner, matched case-insensitively. |
| BR-CON-03 | A visit can only be added to a pet owned by the owner in context. |
| BR-CON-04 | Owner update route ownerId must match the submitted owner identity. |

### Authorization Rules

| ID | Rule |
|---|---|
| BR-AUTH-01 | No authorization rule is implemented today; all current access control must be added externally or in future code. |

### Workflow Rules

| ID | Rule |
|---|---|
| BR-WF-01 | Blank owner search broadens search instead of failing validation. |
| BR-WF-02 | Owner search is prefix-based on last name and paginated with page size 5. |
| BR-WF-03 | Exactly one owner search result redirects directly to details. |
| BR-WF-04 | Visit records default their date to the current day. |
| BR-WF-05 | Vet HTML pages are paginated, while JSON returns the full list wrapper. |

### Calculations

| ID | Rule |
|---|---|
| BR-CALC-01 | Pagination size for owner and veterinarian list views is fixed at 5. |

## Gap Analysis

### Classification Summary

| Classification | Count |
|---|---|
| CLEAN_MAP | 8 |
| TRANSFORM | 3 |
| MISSING | 5 |
| DEFERRED | 3 |
| BLOCKING | 4 |

#### 🔴 CRITICAL - G-BL-01 No authentication or authorization

Severity: 🔴 CRITICAL  
Effort: Medium  
Affected journeys: J2, J3, J4, J5, J6, J7, J8, J9, J10, J11  
Recommendation: Introduce staff authentication, role-based access, and public/private route partitioning before production use.

#### 🟠 HIGH - G-BL-02 Public PII exposure without governance

Severity: 🟠 HIGH  
Effort: Medium  
Affected journeys: J3, J4, J5  
Recommendation: Define data classification, redaction, retention, and auditing requirements for owner contact data.

#### 🟠 HIGH - G-BL-03 Visit workflow lacks scheduling controls

Severity: 🟠 HIGH  
Effort: High  
Affected journeys: J8  
Recommendation: Define appointment semantics and implement clinician/time-slot, duration, and overlap rules before treating visits as appointments.

#### 🟠 HIGH - G-BL-04 Unsafe default operational exposure

Severity: 🟠 HIGH  
Effort: Low  
Affected journeys: J1, J11  
Recommendation: Restrict actuator exposure and remove or shield demo-only endpoints in non-development environments.

### Non-Blocking Gaps

| ID | Classification | Detail |
|---|---|---|
| G-TR-01 | TRANSFORM | The JSON vet endpoint is unversioned and unmanaged as a formal API. |
| G-TR-02 | TRANSFORM | Business behavior is controller-centric and tightly coupled to Thymeleaf views. |
| G-TR-03 | TRANSFORM | Seed-data bootstrap is demo-oriented rather than operationally governed. |
| G-MI-01 | MISSING | No delete/archive lifecycle exists for owners, pets, or visits. |
| G-MI-02 | MISSING | No scheduling conflict, provider assignment, or capacity logic exists. |
| G-MI-03 | MISSING | No audit trail for owner, pet, or visit changes exists. |
| G-MI-04 | MISSING | No PII minimization, masking, or retention controls exist. |
| G-MI-05 | MISSING | No public/staff capability boundary exists. |
| G-DE-01 | DEFERRED | The crash route is a demo convenience rather than business capability. |
| G-DE-02 | DEFERRED | Actuator exposure must be environment-specific. |
| G-DE-03 | DEFERRED | Front-end modernization is optional and separate from core requirement recovery. |

## Acceptance Criteria

### Owner Management

| ID | Scenario | Type | Coverage |
|---|---|---|---|
| AC-OWN-01 | Create owner with valid mandatory fields | ✅ positive | COVERED |
| AC-OWN-02 | Reject owner creation when address or telephone is missing | ❌ negative | COVERED |
| AC-OWN-03 | Return all owners when search last name is blank | 📐 boundary | COVERED |
| AC-OWN-04 | Redirect directly to details when exactly one owner matches search | ✅ positive | COVERED |
| AC-OWN-05 | Reject owner update when route ownerId does not match the submitted owner id | ❌ negative | COVERED |

### Pet Management

| ID | Scenario | Type | Coverage |
|---|---|---|---|
| AC-PET-01 | Create pet with unique name, type, and valid birth date | ✅ positive | COVERED |
| AC-PET-02 | Reject duplicate pet names under the same owner | ❌ negative | COVERED |
| AC-PET-03 | Reject future birth dates for pets | ❌ negative | COVERED |
| AC-PET-04 | Reject blank pet name or missing type for new pet creation | ❌ negative | COVERED |

### Visit Management

| ID | Scenario | Type | Coverage |
|---|---|---|---|
| AC-VIS-01 | Create a visit with description for an existing owner-pet pair | ✅ positive | COVERED |
| AC-VIS-02 | Reject visit submission when description is blank | ❌ negative | COVERED |
| AC-VIS-03 | Prevent booking if the pet does not belong to the owner in context | ❌ negative | PARTIAL |
| AC-VIS-04 | Prevent conflicting appointments for the same clinician and time slot | 📐 boundary | **GAP** |

### Vet Directory

| ID | Scenario | Type | Coverage |
|---|---|---|---|
| AC-VET-01 | Render veterinarian list as HTML with pagination | ✅ positive | COVERED |
| AC-VET-02 | Return veterinarian list as JSON under vetList | ✅ positive | COVERED |

### Platform and Localization

| ID | Scenario | Type | Coverage |
|---|---|---|---|
| AC-PLT-01 | Support language switching with a lang query parameter and message bundles | ✅ positive | PARTIAL |
| AC-PLT-02 | Run core integration flows against H2, MySQL, and PostgreSQL profiles | ✅ positive | COVERED |

## Risk Register

### Severity Summary

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 1 |
| 🟠 HIGH | 3 |
| 🟡 MEDIUM | 1 |
| 🟢 LOW | 1 |

#### R-01 - Unauthenticated access to operational and clinical data

> Category: security  
> Likelihood: High  
> Impact: High  
> Score: 25  
> Severity: 🔴 CRITICAL  
> Mitigation: Introduce authentication, authorization, and route segmentation.  
> Owner: Product and platform engineering

#### R-02 - PII leakage through owner detail views

> Category: privacy  
> Likelihood: Medium  
> Impact: High  
> Score: 20  
> Severity: 🟠 HIGH  
> Mitigation: Classify owner data, add masking rules, audit access, and define retention policy.  
> Owner: Security and compliance

#### R-03 - Visit workflow misused as real appointment scheduler

> Category: business  
> Likelihood: High  
> Impact: Medium  
> Score: 20  
> Severity: 🟠 HIGH  
> Mitigation: Clarify appointment domain model and implement clinician/time-slot constraints.  
> Owner: Product management

#### R-04 - Overexposed actuator endpoints

> Category: operations  
> Likelihood: Medium  
> Impact: Medium  
> Score: 15  
> Severity: 🟠 HIGH  
> Mitigation: Restrict actuator exposure by environment and add endpoint authentication.  
> Owner: Platform engineering

#### R-05 - Database portability drift across profiles

> Category: integration  
> Likelihood: Medium  
> Impact: Medium  
> Score: 12  
> Severity: 🟡 MEDIUM  
> Mitigation: Keep schema scripts aligned and retain cross-profile integration coverage.  
> Owner: Backend engineering

#### R-06 - Localization regression from hard-coded UI strings

> Category: quality  
> Likelihood: Low  
> Impact: Medium  
> Score: 6  
> Severity: 🟢 LOW  
> Mitigation: Keep i18n sync tests as a release gate for UI changes.  
> Owner: Frontend engineering

## Open Items

| ID | Question | Owner |
|---|---|---|
| OI-01 | Should owner, pet, and visit workflows be staff-only, or is any public self-service intended? | Product owner |
| OI-02 | Should visits evolve into scheduled appointments with clinician assignment and time slots? | Product owner |
| OI-03 | What retention, masking, and audit obligations apply to owner contact information? | Security/compliance |
| OI-04 | Are delete/archive behaviors required for owners, pets, and visit records? | Business analyst |

## Assumptions

| ID | Statement | Basis | Risk If Wrong | Owner |
|---|---|---|---|---|
| A-01 | Clinic staff are the primary data-entry users. | All CRUD flows are staff-oriented and server-rendered. | Public UX and access control requirements may be materially different. | Business analyst |
| A-02 | The veterinarian JSON endpoint is a convenience feed, not a public contract. | Only one JSON route exists and it is unversioned. | Consumers may already depend on a stable API shape and availability. | Integration owner |
| A-03 | Open actuator exposure and the crash route are development defaults, not product requirements. | Properties and crash controller wording explicitly target demo/testing behavior. | Operational risk and scope may be understated. | Platform owner |
| A-04 | Visit records represent lightweight clinical events, not calendared appointments. | The model stores date and description only, with no provider or time. | Scheduling requirements would be under-modeled. | Product owner |

## Appendix - Artifact Catalog

| Artifact | Type | Relevance | Notes |
|---|---|---|---|
| src/main/java/org/springframework/samples/petclinic/PetClinicApplication.java | Application entry point | High | Bootstraps runtime. |
| src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java | Controller | High | Owner search, create, update, detail journeys. |
| src/main/java/org/springframework/samples/petclinic/owner/PetController.java | Controller | High | Pet create/update journeys and validation. |
| src/main/java/org/springframework/samples/petclinic/owner/VisitController.java | Controller | High | Visit creation flow. |
| src/main/java/org/springframework/samples/petclinic/vet/VetController.java | Controller | High | Vet HTML and JSON routes. |
| src/main/java/org/springframework/samples/petclinic/system/WelcomeController.java | Controller | Medium | Home page route. |
| src/main/java/org/springframework/samples/petclinic/system/CrashController.java | Controller | Medium | Demo-only error route. |
| src/main/java/org/springframework/samples/petclinic/owner/Owner.java | Domain entity | High | Owner fields, PII, pet aggregation. |
| src/main/java/org/springframework/samples/petclinic/owner/Pet.java | Domain entity | High | Pet birth date, type, and visits. |
| src/main/java/org/springframework/samples/petclinic/owner/Visit.java | Domain entity | High | Visit defaults and required description. |
| src/main/java/org/springframework/samples/petclinic/owner/PetValidator.java | Validation | High | Required pet fields. |
| src/main/java/org/springframework/samples/petclinic/owner/OwnerRepository.java | Repository | High | Prefix search and owner retrieval. |
| src/main/java/org/springframework/samples/petclinic/vet/VetRepository.java | Repository | High | Cached vet lookup. |
| src/main/java/org/springframework/samples/petclinic/system/WebConfiguration.java | Configuration | High | Session locale and lang parameter switching. |
| src/main/java/org/springframework/samples/petclinic/system/CacheConfiguration.java | Configuration | Medium | JCache configuration for vets. |
| src/main/resources/application.properties | Configuration | High | H2 default profile, open actuator exposure. |
| src/main/resources/application-mysql.properties | Configuration | High | MySQL profile details. |
| src/main/resources/application-postgres.properties | Configuration | High | PostgreSQL profile details. |
| src/main/resources/db/h2/schema.sql | Schema | High | Canonical domain schema. |
| src/main/resources/db/h2/data.sql | Seed data | High | Demonstrates representative domain data. |
| src/main/resources/messages/messages.properties | Localization | High | Validation and UI messages. |
| src/main/resources/templates/owners/findOwners.html | View | Medium | Search UX and error rendering. |
| src/main/resources/templates/owners/ownerDetails.html | View | High | Owner detail, pet list, visit history, action links. |
| src/main/resources/templates/pets/createOrUpdateVisitForm.html | View | High | Visit form and history display. |
| src/test/java/org/springframework/samples/petclinic/owner/OwnerControllerTests.java | Test | High | Owner journey behavior evidence. |
| src/test/java/org/springframework/samples/petclinic/owner/PetControllerTests.java | Test | High | Pet validation and editing evidence. |
| src/test/java/org/springframework/samples/petclinic/owner/VisitControllerTests.java | Test | High | Visit flow evidence. |
| src/test/java/org/springframework/samples/petclinic/owner/PetValidatorTests.java | Test | High | Rule validation evidence. |
| src/test/java/org/springframework/samples/petclinic/service/ClinicServiceTests.java | Test | High | Persistence and multi-entity behavior evidence. |
| src/test/java/org/springframework/samples/petclinic/PetClinicIntegrationTests.java | Test | High | End-to-end H2 evidence. |
| src/test/java/org/springframework/samples/petclinic/MySqlIntegrationTests.java | Test | Medium | MySQL portability evidence. |
| src/test/java/org/springframework/samples/petclinic/PostgresIntegrationTests.java | Test | Medium | PostgreSQL portability evidence. |
| src/test/java/org/springframework/samples/petclinic/system/I18nPropertiesSyncTest.java | Test | Medium | Localization quality gate. |

*Document generated by BRD Pipeline - Run ID: 20260615-spc-01 | Confidence: 84% (HIGH) | BRD Locked: ✅ YES | Generated: 2026-06-15*