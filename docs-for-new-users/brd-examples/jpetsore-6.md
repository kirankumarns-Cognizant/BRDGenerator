# Business Requirements Document

## 1. Title Block

| Attribute | Value |
|---|---|
| Component | jpetsore-6 |
| Repository | jpetstore-6 |
| Domain | eCommerce Pet Store |
| Framework | Stripes + Spring + MyBatis |
| Run ID | 20260615-a3f7 |
| Date | 2026-06-15 |
| BRD Status | LOCKED |
| Overall Confidence | 86% |
| Version | 1.0 |
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
- [14. Appendix — Artifact Catalog](#14-appendix--artifact-catalog)

## 3. Executive Summary

JPetStore is a server-rendered web storefront that enables users to browse pet categories, search products, manage cart items, register/sign in, and place orders. The primary interaction surface is Stripes action endpoints routed via .action URL patterns and backed by Spring services and MyBatis mapper SQL.

Journey extraction confirms six core user journeys with strong behavioral evidence from integration tests, especially checkout, cart management, profile update, and order history. The implementation uses session-based authentication markers and action-level checks for order access rather than centralized web security middleware.

The BRD is locked at 86% confidence because functional flows are clear and test-backed. Main blockers are security/compliance hardening around credential/payment data handling and inventory race-condition protection during stock decrement.

## 4. Scope

### In Scope

| # | Capability |
|---|---|
| 1 | Catalog browsing across category, product, and item levels |
| 2 | Keyword search over products |
| 3 | Account registration, sign-on, sign-off, profile edit |
| 4 | Cart add/update/remove and subtotal recomputation |
| 5 | Checkout with optional shipping override and confirmation |
| 6 | Order persistence and order history/detail retrieval |

### Out of Scope

| Capability | Reason |
|---|---|
| External payment gateway integration | Current implementation stores card fields directly in order model/schema |
| Multi-tenant identity federation | No IdP integration found |
| Multi-region deployment strategy | Runtime is demo-oriented with embedded DB setup |

### Deferred

| Capability | Reason |
|---|---|
| Expanded localization beyond english/japanese | Current account options expose two languages |
| Full audit event trail for account/order lifecycle | Not implemented in current handlers/services |

## 5. Stakeholders and Actors

| Actor | Type | Responsibilities |
|---|---|---|
| Shopper (guest) | External user | Browse catalog, search products, view item details |
| Shopper (authenticated) | External user | Manage account, cart, checkout, view orders |
| Customer Support | Internal user | Investigate order/account issues using DB/application logs |
| Security/Compliance | Governance | Ensure credential/payment handling and access controls |
| Operations | Platform | Deploy WAR, manage runtime and data availability |

Authorization warning: No global HTTP auth middleware was found in [src/main/webapp/WEB-INF/web.xml](src/main/webapp/WEB-INF/web.xml#L62). Access control relies on session checks in action beans such as [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L126).

## 6. System Dependencies

### Regulatory Flags Summary

| Flag | Evidence | Impact |
|---|---|---|
| PII in account/order tables | [src/main/resources/database/jpetstore-hsqldb-schema.sql](src/main/resources/database/jpetstore-hsqldb-schema.sql#L35) | Privacy controls and retention obligations |
| Payment card attribute stored in order table | [src/main/resources/database/jpetstore-hsqldb-schema.sql](src/main/resources/database/jpetstore-hsqldb-schema.sql#L89) | Potential PCI scope expansion |

### Servlet Container

- Type: Runtime platform
- Protocol: HTTP
- Direction: Inbound
- has_fallback: No
- has_circuit_breaker: No
- is_spof: Yes
- Migration notes: Move toward managed runtime with health checks and autoscaling.

### Stripes MVC

- Type: Web framework
- Protocol: In-process
- Direction: Internal
- has_fallback: No
- has_circuit_breaker: No
- is_spof: No
- Migration notes: Consider migration path to Spring MVC for ecosystem and security middleware support.

### Spring + MyBatis + HSQLDB

- Type: Service/data layer
- Protocol: JDBC + SQL
- Direction: Outbound to DB
- has_fallback: No
- has_circuit_breaker: No
- is_spof: Yes
- Migration notes: Embedded datasource configured in [src/main/webapp/WEB-INF/applicationContext.xml](src/main/webapp/WEB-INF/applicationContext.xml#L31) should be replaced for production.

## 7. User Journeys

### Journey Map Summary

| ID | Name | Actor | Source | Classification | Confidence |
|---|---|---|---|---|---|
| J01 | Browse catalog and item details | Guest | code+it | CLEAN_MAP | 0.95 |
| J02 | Search products by keyword | Guest/Auth user | code+it | CLEAN_MAP | 0.91 |
| J03 | Register and sign in | New user | code+it | CLEAN_MAP | 0.92 |
| J04 | Manage cart | Shopper | code+it+unit | CLEAN_MAP | 0.93 |
| J05 | Checkout and place order | Auth shopper | code+it+unit | CLEAN_MAP | 0.94 |
| J06 | View order history/detail | Auth shopper | code+it | CLEAN_MAP | 0.89 |

### Flow Diagrams (ASCII)

Order lifecycle:

START -> Cart Ready -> Checkout Requested -> Shipping Override? -> Confirm Order -> Submit -> Order Persisted -> View Order

State transitions:
- Checkout Requested -> Shipping Override when shippingAddressRequired = true
- Checkout Requested -> Confirm Order when shippingAddressRequired = false
- Confirm Order -> Submit when confirmed = true

Session/account lifecycle:

Guest -> Sign In Attempt -> Authenticated Session -> Account/Profile Edit -> Sign Out -> Guest

Evidence references:
- [src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java](src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java#L71)
- [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L145)

## 8. Business Rules

### Validation Rules

| Rule ID | Rule | Evidence |
|---|---|---|
| R-VAL-01 | Username/password required for signon/new/edit account | [src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java#L76) |
| R-VAL-02 | Empty keyword search returns error | [src/main/java/org/mybatis/jpetstore/web/actions/CatalogActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/CatalogActionBean.java#L191) |
| R-VAL-03 | Null/blank cart item id rejected | [src/main/java/org/mybatis/jpetstore/web/actions/CartActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/CartActionBean.java#L70) |

### Constraints

| Rule ID | Rule | Evidence |
|---|---|---|
| R-CON-01 | Allowed credit card types: Visa/MasterCard/American Express | [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L60) |
| R-CON-02 | Account language options limited to english/japanese | [src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java#L57) |

### Authorization Rules

| Rule ID | Rule | Evidence |
|---|---|---|
| R-AUTH-01 | Checkout requires authenticated account | [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L126) |
| R-AUTH-02 | View order allowed only for owner username | [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L179) |

### Workflow Rules

| Rule ID | Rule | Evidence |
|---|---|---|
| R-WF-01 | Shipping form is optional branch in checkout | [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L145) |
| R-WF-02 | Confirmation gate before order insertion | [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L148) |

### Calculation Rules

| Rule ID | Rule | Evidence |
|---|---|---|
| R-CALC-01 | Cart subtotal = sum(listPrice * qty) | [src/main/java/org/mybatis/jpetstore/domain/Cart.java](src/main/java/org/mybatis/jpetstore/domain/Cart.java#L110) |
| R-CALC-02 | Inventory decremented by line-item quantity on order insert | [src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml](src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml#L78) |

## 9. Gap Analysis

### Classification Summary

| Class | Count |
|---|---|
| CLEAN_MAP | 8 |
| TRANSFORM | 3 |
| MISSING | 4 |
| DEFERRED | 2 |
| BLOCKING | 2 |

#### 🔴 CRITICAL — G-BLK-01 Credentials and payment data hardening

Severity: CRITICAL  
Effort: M  
Affected journeys/rules: J03, J05, R-AUTH-01  
Recommendation: Hash passwords, remove plain credential persistence, and adopt payment tokenization.

Evidence:
- [src/main/resources/database/jpetstore-hsqldb-schema.sql](src/main/resources/database/jpetstore-hsqldb-schema.sql#L30)
- [src/main/resources/database/jpetstore-hsqldb-schema.sql](src/main/resources/database/jpetstore-hsqldb-schema.sql#L89)

#### 🟠 HIGH — G-BLK-02 Inventory oversell risk under concurrency

Severity: HIGH  
Effort: M  
Affected journeys/rules: J05, R-CALC-02  
Recommendation: Add conditional update checks and lock strategy to prevent stock below zero.

Evidence:
- [src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml](src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml#L78)
- [src/main/java/org/mybatis/jpetstore/service/OrderService.java](src/main/java/org/mybatis/jpetstore/service/OrderService.java#L58)

Non-blocking gaps:

| ID | Class | Detail |
|---|---|---|
| G-NB-01 | MISSING | No explicit CSRF mitigation evidence |
| G-NB-02 | MISSING | No audit log trail for profile/order changes |
| G-NB-03 | TRANSFORM | Centralize auth policy instead of action-level checks |
| G-NB-04 | DEFERRED | Limited language options for globalization |

## 10. Acceptance Criteria

### Catalog and Discovery

| AC | Scenario | Type | Coverage |
|---|---|---|---|
| AC-J01-01 | Browse category/product/item details | ✅ positive | COVERED |
| AC-J02-01 | Empty keyword search returns error | ❌ negative | COVERED |

### Account and Authentication

| AC | Scenario | Type | Coverage |
|---|---|---|---|
| AC-J03-01 | Register then sign in successfully | ✅ positive | COVERED |
| AC-J05-01 | Checkout attempt without signon blocked | ❌ negative | PARTIAL |

### Cart and Checkout

| AC | Scenario | Type | Coverage |
|---|---|---|---|
| AC-J04-01 | Cart add/update/remove recalculates totals | ✅ positive | COVERED |
| AC-J05-02 | Shipping override branch before confirmation | 📐 boundary | COVERED |
| AC-RISK-01 | Concurrent order submit does not oversell stock | 📐 boundary | **GAP** |

### Orders

| AC | Scenario | Type | Coverage |
|---|---|---|---|
| AC-J06-01 | User cannot view another user order | ❌ negative | PARTIAL |

Primary behavior evidence in [src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java](src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java#L71).

## 11. Risk Register

### Severity Summary

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 1 |
| 🟠 HIGH | 2 |
| 🟡 MEDIUM | 2 |
| 🟢 LOW | 1 |

#### 🔴 RK-01 Plain credential and payment data handling

> Category: security_compliance  
> Likelihood: HIGH  
> Impact: HIGH  
> Score: 9  
> Mitigation: Hash passwords with adaptive algorithm and externalize payment tokenization.  
> Owner: Security Lead

#### 🟠 RK-02 Inventory decrement race/oversell

> Category: inventory_integrity  
> Likelihood: MEDIUM  
> Impact: HIGH  
> Score: 8  
> Mitigation: Introduce stock floor checks and transactional lock strategy.  
> Owner: Backend Lead

#### 🟠 RK-03 Distributed authorization logic

> Category: authorization  
> Likelihood: MEDIUM  
> Impact: MEDIUM  
> Score: 7  
> Mitigation: Centralize authorization policy and enforce consistently.  
> Owner: Architecture

#### 🟡 RK-04 Embedded database availability

> Category: availability  
> Likelihood: LOW  
> Impact: HIGH  
> Score: 6  
> Mitigation: Replace embedded datasource with managed persistent DB.  
> Owner: Platform

#### 🟡 RK-05 Missing auditability

> Category: auditability  
> Likelihood: MEDIUM  
> Impact: MEDIUM  
> Score: 5  
> Mitigation: Introduce immutable account/order audit events.  
> Owner: Compliance

#### 🟢 RK-06 Partial negative-flow test coverage

> Category: testing  
> Likelihood: MEDIUM  
> Impact: LOW  
> Score: 3  
> Mitigation: Add negative authorization and concurrency tests.  
> Owner: QA Lead

## 12. Open Items

| ID | Question | Owner |
|---|---|---|
| OI-01 | Target production identity provider and password policy? | Product Security |
| OI-02 | Should oversell be blocked with strict inventory floor? | Domain Owner |
| OI-03 | Keep payment fields in scope or externalize to PSP tokenization? | Architecture |

## 13. Assumptions

| ID | Statement | Basis | risk_if_wrong | Owner |
|---|---|---|---|---|
| A-01 | Session-level auth is acceptable for current demo scope | Action-bean checks exist | Security gaps in production | Security Lead |
| A-02 | Embedded HSQLDB is non-production only | datasource config scripts | Data loss/outage risk | Platform |
| A-03 | Existing integration test represents critical business path | ScreenTransitionIT covers full order flow | Uncovered regressions | QA Lead |

## 14. Appendix — Artifact Catalog

| Artifact | Type | Relevance | Notes |
|---|---|---|---|
| [src/main/webapp/index.html](src/main/webapp/index.html#L29) | Entry page | High | Store entry link to Catalog.action |
| [src/main/webapp/WEB-INF/web.xml](src/main/webapp/WEB-INF/web.xml#L62) | Routing config | High | .action dispatcher mapping |
| [src/main/webapp/WEB-INF/applicationContext.xml](src/main/webapp/WEB-INF/applicationContext.xml#L31) | Spring config | High | Embedded datasource + mapper scan |
| [src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/AccountActionBean.java#L126) | Action handler | High | Signon/new account/profile flows |
| [src/main/java/org/mybatis/jpetstore/web/actions/CatalogActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/CatalogActionBean.java#L191) | Action handler | High | Search validation + catalog navigation |
| [src/main/java/org/mybatis/jpetstore/web/actions/CartActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/CartActionBean.java#L70) | Action handler | High | Cart validation and quantity update |
| [src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java](src/main/java/org/mybatis/jpetstore/web/actions/OrderActionBean.java#L145) | Action handler | High | Checkout branching and ownership checks |
| [src/main/java/org/mybatis/jpetstore/service/OrderService.java](src/main/java/org/mybatis/jpetstore/service/OrderService.java#L58) | Service | High | Inventory/order persistence path |
| [src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml](src/main/resources/org/mybatis/jpetstore/mapper/ItemMapper.xml#L78) | SQL mapper | High | Inventory decrement statement |
| [src/main/resources/database/jpetstore-hsqldb-schema.sql](src/main/resources/database/jpetstore-hsqldb-schema.sql#L30) | DB schema | High | Signon/password and order card fields |
| [src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java](src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java#L71) | Integration test | High | End-to-end behavioral evidence |
| [src/test/java/org/mybatis/jpetstore/domain/CartTest.java](src/test/java/org/mybatis/jpetstore/domain/CartTest.java#L34) | Unit test | Medium | Cart totals/quantities behavior |
| [src/test/java/org/mybatis/jpetstore/service/OrderServiceTest.java](src/test/java/org/mybatis/jpetstore/service/OrderServiceTest.java#L143) | Unit test | Medium | Inventory update call verification |

*Document generated by BRD Pipeline — Run ID: 20260615-a3f7 | Confidence: 86% (HIGH) | BRD Locked: ✅ YES | Generated: 2026-06-15*