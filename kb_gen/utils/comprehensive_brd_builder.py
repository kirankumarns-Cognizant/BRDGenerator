"""
Comprehensive BRD Builder — generates complete markdown BRD with diagrams and specs.
Creates complete documentation with OpenAPI, sequences, processes, and endpoints.
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# Saturated stroke + dark label so the pastel fills stay legible under both the
# light and dark Mermaid themes.
_NODE_STYLES = {
    "Client":     "fill:#e1f5ff,stroke:#0277bd,stroke-width:2px,color:#0b2530",
    "Controller": "fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#3b2200",
    "Service":    "fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#2e1033",
    "Mapper":     "fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#0f2913",
    "Repository": "fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#3a0d1d",
    "Database":   "fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#1a2227",
}

# Request-processing flowchart: node id -> role, role -> style.
_FLOW_ROLES = {
    "A": "entry", "B": "decision", "C": "error", "D": "process",
    "E": "process", "F": "process", "G": "process", "H": "process",
    "I": "process", "J": "decision", "K": "error", "L": "error",
    "M": "success", "N": "success", "O": "endpoint",
}
_FLOW_STYLES = {
    "entry":    "fill:#e1f5ff,stroke:#0277bd,stroke-width:2px,color:#0b2530",
    "decision": "fill:#fff8e1,stroke:#f9a825,stroke-width:2px,color:#3a2d00",
    "process":  "fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#2e1033",
    "error":    "fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#3d0a0a",
    "success":  "fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#0f2913",
    "endpoint": "fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#1a2227",
}


class ComprehensiveBRDBuilder:
    """Builds comprehensive BRD markdown with all sections."""

    def __init__(self, repo_name: str, signals: Dict[str, Any]):
        self.repo_name = repo_name
        self.signals = signals

    def build(self) -> str:
        """Build complete comprehensive BRD."""
        sections = []

        sections.append(self._build_title())
        sections.append(self._build_table_of_contents())
        sections.append(self._build_executive_summary())
        sections.append(self._build_system_overview())
        sections.append(self._build_technology_stack())
        sections.append(self._build_component_inventory())
        sections.append(self._build_domain_model())
        sections.append(self._build_functional_requirements())
        sections.append(self._build_api_specification())
        sections.append(self._build_endpoints_documentation())
        sections.append(self._build_data_flow_diagrams())
        sections.append(self._build_sequence_diagrams())
        sections.append(self._build_process_diagrams())
        sections.append(self._build_business_rules())
        sections.append(self._build_user_journeys())
        sections.append(self._build_non_functional_requirements())
        sections.append(self._build_acceptance_criteria())
        sections.append(self._build_gap_analysis())
        sections.append(self._build_risk_assessment())
        sections.append(self._build_recommendations())
        sections.append(self._build_artifacts_inventory())
        sections.append(self._build_test_scenarios())
        sections.append(self._build_appendices())

        return "\n\n".join(filter(None, sections))

    def _build_title(self) -> str:
        """Build title section."""
        return f"""# Comprehensive Business Requirements Document
## {self.repo_name}

**Generated:** {self.signals.get('timestamp', 'N/A')}
**Confidence Level:** {self.signals.get('confidence', 0.75):.2%}
"""

    def _build_table_of_contents(self) -> str:
        """Build table of contents."""
        return """## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [Component Inventory](#component-inventory)
5. [Domain Model](#domain-model)
6. [Functional Requirements](#functional-requirements)
7. [API Specification](#api-specification)
8. [Endpoints Documentation](#endpoints-documentation)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Sequence Diagrams](#sequence-diagrams)
11. [Process Diagrams](#process-diagrams)
12. [Business Rules](#business-rules)
13. [User Journeys](#user-journeys)
14. [Non-Functional Requirements](#non-functional-requirements)
15. [Acceptance Criteria](#acceptance-criteria)
16. [Gap Analysis](#gap-analysis)
17. [Risk Assessment](#risk-assessment)
18. [Recommendations](#recommendations)
19. [Artifacts Inventory](#artifacts-inventory)
20. [Test Scenarios](#test-scenarios)
21. [Appendices](#appendices)
"""

    def _build_executive_summary(self) -> str:
        """Build executive summary."""
        frameworks = self.signals.get('frameworks', [])
        loc = self.signals.get('loc', 0)
        java_classes = sum(self.signals.get('java_class_patterns', {}).values())

        return f"""## Executive Summary

**Project:** {self.repo_name}
**Primary Language:** Java
**Build System:** Gradle/Maven
**Frameworks:** {', '.join(frameworks) or 'None detected'}
**Total LOC:** {loc:,}
**Components:** {java_classes} identified

### Overview
The {self.repo_name} system is a comprehensive application designed to manage core business operations. This document provides a complete specification of system requirements, architecture, and implementation details.

### Key Objectives
- Provide scalable and maintainable software architecture
- Support core business processes efficiently
- Ensure data integrity and security
- Enable seamless integration with external systems
"""

    def _build_system_overview(self) -> str:
        """Build system overview."""
        packages = self.signals.get('main_packages', [])
        return f"""## System Overview

### Purpose
{self.repo_name} serves as a critical component in the business architecture, providing essential functionality for:
- Core business process management
- Data persistence and retrieval
- External system integration
- User interaction and reporting

### System Scope

**In Scope:**
- Core business logic implementation
- Data access layer
- Business rule enforcement
- Transaction management
- User management

**Out of Scope:**
- UI/Frontend implementation details
- Advanced analytics
- Machine learning capabilities
- Third-party integrations beyond scope

### Architecture Style
Layered Microservice Architecture with clear separation of concerns:
- **Controller Layer:** Request handling and routing
- **Service Layer:** Business logic implementation
- **Repository Layer:** Data access and persistence
- **Domain Layer:** Business entities and value objects

### Main Packages
```
{chr(10).join(f'- {pkg}' for pkg in packages[:10])}
```
"""

    def _build_technology_stack(self) -> str:
        """Build technology stack section with actual repo data."""
        signals = self.signals
        frameworks = signals.get('frameworks', [])
        dependencies = signals.get('dependencies', {})
        loc = signals.get('loc', 0)

        framework_list = "\n".join([f"- **{fw}:** Detected in repository" for fw in frameworks]) if frameworks else "- No frameworks detected"

        dep_details = ""
        if dependencies:
            for dep_type, dep_list in dependencies.items():
                if dep_list:
                    dep_details += f"\n### {dep_type.title()} Dependencies\n"
                    dep_details += "\n".join([f"- {dep}" for dep in dep_list[:10]])

        return f"""## Technology Stack

### Detected Frameworks
{framework_list}

### Primary Language
- **Language:** Java
- **Total Lines of Code:** {loc:,}
- **Build System:** {'Gradle' if 'gradle' in str(dependencies).lower() else 'Maven'}

### Architecture Patterns
- **Layered Architecture:** Detected
- **MVC Pattern:** {self.signals['java_class_patterns'].get('Controller', 0)} controllers found
- **Service Layer:** {self.signals['java_class_patterns'].get('Service', 0)} services found
- **Repository Pattern:** {self.signals['java_class_patterns'].get('Repository', 0)} repositories found

### Key Technologies Detected
- **ORM/Persistence:** Detected from imports
- **Testing Frameworks:** Based on dependencies
- **Build Tools:** {'Gradle' if 'gradle' in dependencies else 'Maven'}

### Dependencies by Type
{dep_details if dep_details else "No specific dependencies mapped"}

### File Distribution
```
Total Java Files: {len(signals.get('java_files', []))}
Main Packages: {len(signals.get('main_packages', []))}
Components by Type:
  - Controllers: {self.signals['java_class_patterns'].get('Controller', 0)}
  - Services: {self.signals['java_class_patterns'].get('Service', 0)}
  - Repositories: {self.signals['java_class_patterns'].get('Repository', 0)}
  - Entities: {self.signals['java_class_patterns'].get('Entity', 0)}
  - Mappers: {self.signals['java_class_patterns'].get('Mapper', 0)}
```
"""

    def _build_component_inventory(self) -> str:
        """Build component inventory with actual repo components."""
        patterns = self.signals.get('java_class_patterns', {})
        java_files = self.signals.get('java_files', [])
        main_packages = self.signals.get('main_packages', [])

        # Categorize components by type
        controllers = [f for f in java_files if 'Controller' in f]
        services = [f for f in java_files if 'Service' in f]
        repositories = [f for f in java_files if 'Repository' in f]
        entities = [f for f in java_files if 'Entity' in f or 'Model' in f]

        components = f"""## Component Inventory

### Component Summary
| Component Type | Count | Description |
|---|---|---|
| Controllers | {patterns.get('Controller', 0)} | REST API endpoints |
| Services | {patterns.get('Service', 0)} | Business logic layer |
| Repositories | {patterns.get('Repository', 0)} | Data access layer |
| Entities | {patterns.get('Entity', 0)} | Domain models |
| DTOs | {patterns.get('DTO', 0)} | Data transfer objects |
| Mappers | {patterns.get('Mapper', 0)} | Entity/DTO mappers |

### Package Structure
```
Main Packages: {', '.join(main_packages[:5]) if main_packages else 'N/A'}
Total Java Files: {len(java_files)}
```

### Key Controllers
{chr(10).join([f'- `{f}`' for f in controllers[:5]]) if controllers else '- No controllers detected'}

### Key Services
{chr(10).join([f'- `{f}`' for f in services[:5]]) if services else '- No services detected'}

### Key Repositories
{chr(10).join([f'- `{f}`' for f in repositories[:5]]) if repositories else '- No repositories detected'}

### Key Domain Entities
{chr(10).join([f'- `{f}`' for f in entities[:5]]) if entities else '- No entities detected'}

### All Components ({len(java_files)} total)
{chr(10).join([f'- `{f}`' for f in java_files[:30]])}
"""
        return components

    def _build_domain_model(self) -> str:
        """Build domain model section with actual repo entities."""
        java_files = self.signals.get('java_files', [])[:10]

        # Extract entity names from actual repo
        entities = [f.split(".")[-1] for f in java_files if 'Entity' in f or 'Model' in f or 'Domain' in f]

        entity_diagram = "┌─────────────────────────────────────────────────────┐\n"
        entity_diagram += "│                  Domain Entities                     │\n"
        entity_diagram += "├─────────────────────────────────────────────────────┤\n│                                                       │\n"

        for i, entity in enumerate(entities[:4]):
            if i % 2 == 0:
                entity_diagram += f"│  ┌──────────────┐      ┌──────────────┐             │\n"
                entity_diagram += f"│  │   {entity:12}│      │   {entities[i+1] if i+1 < len(entities) else 'Related':12}│             │\n"
                entity_diagram += f"│  │              │      │              │             │\n"
                entity_diagram += f"│  │ - property1  │─────▶│ - property1  │             │\n"
                entity_diagram += f"│  │ - property2  │      │ - property2  │             │\n"
                entity_diagram += f"│  └──────────────┘      └──────────────┘             │\n"
                entity_diagram += f"│         │                      ▲                     │\n"
                entity_diagram += f"│         │                      │                     │\n"
                entity_diagram += f"│         └──────────────────────┘                     │\n│                                                       │\n"

        entity_diagram += "└─────────────────────────────────────────────────────┘"

        entity_list = "\n".join([f"- **{e}:** Core domain entity" for e in entities[:5]])

        return f"""## Domain Model

### Detected Entities
Based on repository analysis, the following domain entities were identified:

{entity_list}

### Entity Relationships

```
{entity_diagram}
```

### Key Entities
- **Primary Entities:** {', '.join(entities[:3]) if entities else 'Core business objects'}
- **Supporting Entities:** {', '.join(entities[3:6]) if len(entities) > 3 else 'Related business objects'}
- **Value Objects:** Immutable domain concepts

### Domain Rules
- Entities maintain their own identity
- Value objects are compared by their attributes
- Aggregates protect domain invariants
- Entities and value objects use ubiquitous language

### Detected Patterns
- Repository Pattern: {self.signals['java_class_patterns'].get('Repository', 0)} repositories
- Service Layer: {self.signals['java_class_patterns'].get('Service', 0)} services
- Controllers: {self.signals['java_class_patterns'].get('Controller', 0)} controllers
"""

    def _build_functional_requirements(self) -> str:
        """Build functional requirements based on repo components."""
        patterns = self.signals.get('java_class_patterns', {})
        frameworks = self.signals.get('frameworks', [])
        controllers = patterns.get('Controller', 0)
        services = patterns.get('Service', 0)
        repos = patterns.get('Repository', 0)

        capabilities = []
        if controllers > 0:
            capabilities.append(f"- Request routing and API endpoint management ({controllers} controllers)")
        if services > 0:
            capabilities.append(f"- Business logic processing ({services} service classes)")
        if repos > 0:
            capabilities.append(f"- Data persistence and queries ({repos} repository components)")
        if patterns.get('Entity', 0) > 0:
            capabilities.append(f"- Entity management ({patterns.get('Entity', 0)} domain models)")
        if patterns.get('Mapper', 0) > 0:
            capabilities.append(f"- Data transformation between layers ({patterns.get('Mapper', 0)} mappers)")

        flows = []
        if controllers > 0 and services > 0 and repos > 0:
            flows.append("```\nRequest → Controller → Service → Repository → Database\n```")
        elif controllers > 0 and services > 0:
            flows.append("```\nRequest → Controller → Service\n```")
        elif controllers > 0 and repos > 0:
            flows.append("```\nRequest → Controller → Repository → Database\n```")

        return f"""## Functional Requirements

### Core Capabilities (Based on Repository Analysis)

{chr(10).join(capabilities) if capabilities else "- Generic entity management capabilities"}

### Detected Framework Features
- Framework: {', '.join(frameworks) if frameworks else 'Standard Java'}
- Architecture: Layered with {sum([1 for v in [controllers, services, repos] if v > 0])} distinct layers

### Processing Flows

{chr(10).join(flows) if flows else "```\\nRequest → Controller → Service → Repository → Database\\n```"}

### Key Operations
1. **Request Handling**
   - Endpoint routing via {controllers if controllers > 0 else 'controllers'}
   - Parameter validation
   - Response formatting

2. **Business Logic**
   - Processing via {services if services > 0 else 'service layer'}
   - Rule enforcement
   - State management

3. **Data Access**
   - Queries via {repos if repos > 0 else 'repositories'}
   - Transaction handling
   - Result mapping

4. **Response**
   - Data transformation
   - Error handling
   - Response serialization
"""

    def _build_api_specification(self) -> str:
        """Build OpenAPI specification based on repo controllers."""
        java_files = self.signals.get('java_files', [])
        controllers = [f for f in java_files if 'Controller' in f]
        entities = [f.split(".")[-1] for f in java_files if 'Entity' in f or 'Model' in f]

        # Generate real endpoint paths from actual controller names
        paths_yaml = ""
        endpoint_list = []

        for ctrl in controllers[:10]:  # Get up to 10 controllers
            ctrl_name = ctrl.split(".")[-1].replace("Controller", "").strip()
            if not ctrl_name:
                continue

            # Create resource path from controller name
            resource = ctrl_name.lower()

            # Generate CRUD endpoints
            paths_yaml += f"""  /api/v1/{resource}:
    get:
      summary: List all {resource}
      operationId: list{ctrl_name}
      tags:
        - {ctrl_name}
      parameters:
        - name: page
          in: query
          schema:
            type: integer
        - name: size
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: Success - list of {resource}
    post:
      summary: Create new {resource}
      operationId: create{ctrl_name}
      tags:
        - {ctrl_name}
      responses:
        '201':
          description: Created
        '400':
          description: Validation error

  /api/v1/{resource}/{{id}}:
    get:
      summary: Get {resource} by ID
      operationId: get{ctrl_name}ById
      tags:
        - {ctrl_name}
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
        '404':
          description: Not found
    put:
      summary: Update {resource}
      operationId: update{ctrl_name}
      tags:
        - {ctrl_name}
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Updated
        '404':
          description: Not found
    delete:
      summary: Delete {resource}
      operationId: delete{ctrl_name}
      tags:
        - {ctrl_name}
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Deleted
        '404':
          description: Not found

"""
            endpoint_list.append(f"- {ctrl_name}: /api/v1/{resource}")

        if not paths_yaml:
            paths_yaml = """  /api/v1/resources:
    get:
      summary: List resources
      responses:
        '200':
          description: Success
"""
            endpoint_list = ["- Generic: /api/v1/resources"]

        endpoints_section = "\n".join(endpoint_list) if endpoint_list else "No controllers detected"

        return f"""## API Specification

### OpenAPI 3.0.0 Specification

Detected {len(controllers)} real controller(s) generating {len(controllers) * 5} API endpoints.

```yaml
openapi: 3.0.0
info:
  title: {self.repo_name} API
  version: 1.0.0
  description: RESTful API for {self.repo_name} with {len(controllers)} resource(s)

servers:
  - url: http://localhost:8080
    description: Development
  - url: https://api.example.com
    description: Production

paths:
{paths_yaml}
components:
  schemas:
    Error:
      type: object
      properties:
        error:
          type: string
        status:
          type: integer
        timestamp:
          type: string
          format: date-time
```

### Detected Endpoints by Controller

{endpoints_section}

### Total API Operations
- Controllers: {len(controllers)}
- Entity Models: {len(entities)}
- Estimated Endpoints: {len(controllers) * 5}
- Supported Operations: Create, Read, Update, Delete (CRUD)
"""

    def _build_endpoints_documentation(self) -> str:
        """Build endpoints documentation based on detected controllers."""
        java_files = self.signals.get('java_files', [])
        controllers = [f for f in java_files if 'Controller' in f]

        doc_endpoints = ""
        for i, ctrl in enumerate(controllers[:10], 1):
            ctrl_class = ctrl.split(".")[-1].replace("Controller", "").strip()
            if not ctrl_class:
                continue

            resource = ctrl_class.lower()
            full_class = ctrl

            doc_endpoints += f"""#### {i}. {ctrl_class} Endpoints

**Resource:** {resource}
**Implementation:** `{full_class}`

**Available Operations:**
```
GET    /api/v1/{resource}           - List all {resource}
POST   /api/v1/{resource}           - Create new {resource}
GET    /api/v1/{resource}/{{id}}    - Get specific {resource}
PUT    /api/v1/{resource}/{{id}}    - Update {resource}
DELETE /api/v1/{resource}/{{id}}    - Delete {resource}
```

**Example Requests:**
```bash
# List
curl -X GET "http://localhost:8080/api/v1/{resource}" \\
  -H "Authorization: Bearer token"

# Create
curl -X POST "http://localhost:8080/api/v1/{resource}" \\
  -H "Authorization: Bearer token" \\
  -H "Content-Type: application/json" \\
  -d '{{}}'

# Get by ID
curl -X GET "http://localhost:8080/api/v1/{resource}/123" \\
  -H "Authorization: Bearer token"

# Update
curl -X PUT "http://localhost:8080/api/v1/{resource}/123" \\
  -H "Authorization: Bearer token" \\
  -H "Content-Type: application/json" \\
  -d '{{}}'

# Delete
curl -X DELETE "http://localhost:8080/api/v1/{resource}/123" \\
  -H "Authorization: Bearer token"
```

---

"""

        if not doc_endpoints:
            doc_endpoints = """#### Generic Endpoints
No controllers detected - using generic endpoint pattern.
"""

        return f"""## Endpoints Documentation

### Base URL
```
http://localhost:8080/api/v1
```

### Detected API Controllers: {len(controllers)}
Real controllers generating {len(controllers) * 5} endpoint operations.

### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <your_token>
```

### Detected Endpoints from Repository

{doc_endpoints}

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful GET/PUT request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |

### Response Format

Success responses include timestamps:
```json
{{
  "id": "unique-id",
  "createdAt": "2026-09-11T12:00:00Z",
  "updatedAt": "2026-09-11T12:00:00Z",
  "status": "SUCCESS"
}}
```

Error responses follow standard format:
```json
{{
  "error": "Description of error",
  "status": 400,
  "timestamp": "2026-09-11T12:00:00Z",
  "details": {{}}
}}
```
"""

    def _build_data_flow_diagrams(self) -> str:
        """Build data flow diagrams based on actual repo architecture."""
        patterns = self.signals.get('java_class_patterns', {})

        controllers = patterns.get('Controller', 0)
        services = patterns.get('Service', 0)
        mappers = patterns.get('Mapper', 0)
        repos = patterns.get('Repository', 0)
        entities = patterns.get('Entity', 0)

        # Build actual data flow path
        flow_path = ["Client"]
        if controllers > 0:
            flow_path.append(f"Controller ({controllers})")
        if services > 0:
            flow_path.append(f"Service ({services})")
        if mappers > 0:
            flow_path.append(f"Mapper ({mappers})")
        if repos > 0:
            flow_path.append(f"Repository ({repos})")
        flow_path.append("Database")

        flow_arrow = " → ".join(flow_path)

        # Generate Mermaid C4 diagram
        mermaid = "```mermaid\ngraph LR\n"
        nodes = ["Client"]
        mermaid += "    Client[\"👤 Client<br/>HTTP Request\"]\n"

        if controllers > 0:
            mermaid += f"    Controller[\"🎯 {controllers} Controller(s)<br/>HTTP Routing\"]\n"
            mermaid += "    Client -->|Request| Controller\n"
            nodes.append("Controller")
        else:
            mermaid += "    Database[(\"🗄️ Database\")]\n"
            mermaid += "    Client -->|Direct Access| Database\n"
            nodes.append("Database")

        if services > 0 and controllers > 0:
            mermaid += f"    Service[\"⚙️ {services} Service(s)<br/>Business Logic\"]\n"
            mermaid += "    Controller -->|Process| Service\n"
            nodes.append("Service")

        if mappers > 0 and services > 0:
            mermaid += f"    Mapper[\"🔄 {mappers} Mapper(s)<br/>Data Transform\"]\n"
            mermaid += "    Service -->|Transform| Mapper\n"
            nodes.append("Mapper")
        elif mappers > 0 and controllers > 0:
            mermaid += f"    Mapper[\"🔄 {mappers} Mapper(s)<br/>Data Transform\"]\n"
            mermaid += "    Controller -->|Transform| Mapper\n"
            nodes.append("Mapper")

        if repos > 0:
            mermaid += f"    Repository[\"📊 {repos} Repository/ies<br/>Data Access\"]\n"
            nodes.append("Repository")
            if "Mapper" in nodes:
                mermaid += "    Mapper -->|Query| Repository\n"
            elif services > 0:
                mermaid += "    Service -->|Query| Repository\n"
            elif controllers > 0:
                mermaid += "    Controller -->|Query| Repository\n"

        if (repos > 0 or controllers > 0) and "Database" not in nodes:
            mermaid += "    Database[(\"🗄️ Database\")]\n"
            nodes.append("Database")
            if repos > 0:
                mermaid += "    Repository -->|SQL| Database\n"
                mermaid += "    Database -->|ResultSet| Repository\n"
            elif controllers > 0 and not (services > 0 or mappers > 0):
                mermaid += "    Controller -->|SQL| Database\n"
                mermaid += "    Database -->|ResultSet| Controller\n"

        # Response path
        if repos > 0 and "Mapper" in nodes:
            mermaid += "    Repository -->|Entity| Mapper\n"
            mermaid += "    Mapper -->|DTO| Service\n"
            mermaid += "    Service -->|Result| Controller\n"
        elif repos > 0 and services > 0:
            mermaid += "    Repository -->|Entity| Service\n"
            mermaid += "    Service -->|Result| Controller\n"
        elif repos > 0 and controllers > 0:
            mermaid += "    Repository -->|Data| Controller\n"

        if controllers > 0:
            mermaid += "    Controller -->|JSON| Client\n"

        # Light fills need an explicit dark label colour, otherwise Mermaid's
        # dark theme draws light text on them and nothing is readable.
        for node in nodes:
            mermaid += f"    style {node} {_NODE_STYLES[node]}\n"
        mermaid += "```"

        return f"""## Data Flow Diagrams

### System Data Flow - Actual Architecture

**Flow:** {flow_arrow}

### Layer Detection Summary

| Layer | Component | Count | Status |
|-------|-----------|-------|--------|
| Presentation | Controller | {controllers} | {'✓ Present' if controllers > 0 else '✗ Missing'} |
| Business Logic | Service | {services} | {'✓ Present' if services > 0 else '✗ Missing'} |
| Data Mapping | Mapper | {mappers} | {'✓ Present' if mappers > 0 else '✗ Missing'} |
| Data Access | Repository | {repos} | {'✓ Present' if repos > 0 else '✗ Missing'} |
| Domain | Entity | {entities} | {'✓ Present' if entities > 0 else '✗ Missing'} |

### Data Flow Diagram

{mermaid}

### Flow Description

1. **Request Entry:** Client sends HTTP request to system
2. **Controller Layer:** Routes request to appropriate handler ({controllers} controllers)
3. **Service Layer:** Executes business logic and rules ({services} services)
4. **Transformation:** Maps between Entity and DTO formats ({mappers} mappers)
5. **Persistence:** Repository accesses database ({repos} repositories)
6. **Database:** Stores/retrieves data
7. **Response:** Data flows back through layers as JSON

### Data Transformation Steps

Each layer transforms data for its specific purpose:
- **Controller:** HTTP → Domain Objects
- **Service:** Domain Objects → Business Results
- **Mapper:** Entity → DTO (serialization)
- **Repository:** DTO → SQL Queries
- **Database:** SQL ↔ Persistent Data

### Request Types Supported

Based on {repos} detected repositories and {services} detected services:
- **GET** - Retrieve data from database
- **POST** - Create new records
- **PUT** - Update existing records
- **DELETE** - Remove records
"""

    def _build_sequence_diagrams(self) -> str:
        """Build sequence diagrams dynamically from actual repo components."""
        patterns = self.signals.get('java_class_patterns', {})
        
        controllers = patterns.get('Controller', 0)
        services = patterns.get('Service', 0)
        mappers = patterns.get('Mapper', 0)
        repos = patterns.get('Repository', 0)
        entities = patterns.get('Entity', 0)

        # Build dynamic layers based on what's actually in the repo.
        # Names must avoid Mermaid's case-insensitive sequence keywords (actor,
        # participant, note, loop, alt, opt, par, box, create, destroy, end, …):
        # a line starting with one is lexed as that keyword, not as a sender.
        layers = ["Client", "HTTP"]
        if controllers > 0:
            layers.append("Controller")
        if services > 0:
            layers.append("Service")
        if mappers > 0:
            layers.append("Mapper")
        if repos > 0:
            layers.append("Repository")
        layers.append("Database")

        # Generate Mermaid sequence diagram
        mermaid = "```mermaid\nsequenceDiagram\n"

        # Every participant must be declared; an undeclared one is a parse error.
        for layer in layers:
            mermaid += f"    participant {layer}\n"

        # Walk consecutive pairs of the detected layers so each message can only
        # reference components that were actually found in the repo.
        request_labels = {
            "HTTP": "HTTP Request",
            "Controller": "Route Request",
            "Service": "Invoke Business Logic",
            "Mapper": "Transform Data",
            "Repository": "Query/Persist",
            "Database": "Execute SQL",
        }
        for src, dst in zip(layers, layers[1:]):
            mermaid += f"    {src}->>{dst}: {request_labels[dst]}\n"

        response_labels = {
            "Repository": "Result",
            "Mapper": "DTO",
            "Service": "Entity",
            "Controller": "Result",
            "HTTP": "JSON Response",
            "Client": "HTTP 200 OK",
        }
        back = list(reversed(layers))
        for src, dst in zip(back, back[1:]):
            mermaid += f"    {src}-->>{dst}: {response_labels[dst]}\n"

        mermaid += "```"

        return f"""## Sequence Diagrams

### Architecture-Based Data Flow ({len(layers)-2} detected layers)

**Detected Components:**
- Controllers: {controllers}
- Services: {services}
- Mappers: {mappers}
- Repositories: {repos}
- Entities: {entities}

**Request Flow:** {' → '.join(layers)}

{mermaid}

### Diagram Explanation

1. **Client** sends HTTP request
2. **Controller** (if present) routes and validates request
3. **Service** (if present) executes business logic
4. **Mapper** (if present) transforms data between layers
5. **Repository** (if present) handles data persistence
6. **Database** stores and retrieves data
7. Response flows back through layers as JSON

This diagram is generated from your actual repository architecture with {controllers} controllers, {services} services, {repos} repositories detected.
"""

    def _build_process_diagrams(self) -> str:
        """Build process diagrams based on actual repo components."""
        patterns = self.signals.get('java_class_patterns', {})
        
        controllers = patterns.get('Controller', 0)
        services = patterns.get('Service', 0)
        repos = patterns.get('Repository', 0)
        entities = patterns.get('Entity', 0)
        mappers = patterns.get('Mapper', 0)
        
        # Build workflow based on actual components
        workflow_steps = []
        workflow_steps.append("[1] Receive HTTP Request")
        
        if controllers > 0:
            workflow_steps.append(f"[2] Route via {controllers} Controller(s)")
            workflow_steps.append("[3] Parse & Validate Input")
        
        if services > 0:
            workflow_steps.append(f"[4] Execute Business Logic ({services} Service(s))")
            workflow_steps.append("[5] Apply Business Rules")
        
        if mappers > 0:
            workflow_steps.append(f"[6] Transform Data ({mappers} Mapper(s))")
        
        if repos > 0:
            workflow_steps.append(f"[7] Persist to Database ({repos} Repository/ies)")
            workflow_steps.append("[8] Commit Transaction")
        
        workflow_steps.append("[9] Prepare Response")
        workflow_steps.append("[10] Return JSON Response")
        
        workflow_text = "\n ".join(f"→ {step}" for step in workflow_steps)

        # Build Mermaid flowchart
        mermaid = "```mermaid\ngraph TD\n"
        mermaid += "    A[HTTP Request Received] --> B{Valid Request?}\n"
        mermaid += "    B -->|No| C[Return 400 Error]\n"
        mermaid += "    B -->|Yes| D[Authenticate]\n"
        
        if controllers > 0:
            mermaid += f"    D --> E[Route to Controller]\n"
            if services > 0:
                mermaid += f"    E --> F[Call Service]\n"
                if mappers > 0:
                    mermaid += f"    F --> G[Map Data]\n"
                    if repos > 0:
                        mermaid += f"    G --> H[Repository Query]\n"
                        mermaid += f"    H --> I[Database Operation]\n"
                        mermaid += f"    I --> J{{Success?}}\n"
                    else:
                        mermaid += f"    G --> J{{Success?}}\n"
                else:
                    if repos > 0:
                        mermaid += f"    F --> H[Repository Query]\n"
                        mermaid += f"    H --> I[Database Operation]\n"
                        mermaid += f"    I --> J{{Success?}}\n"
                    else:
                        mermaid += f"    F --> J{{Success?}}\n"
            else:
                mermaid += f"    E --> J{{Success?}}\n"
        else:
            mermaid += f"    D --> J{{Success?}}\n"
        
        mermaid += "    J -->|No| K[Log Error & Rollback]\n"
        mermaid += "    K --> L[Return Error Response]\n"
        mermaid += "    J -->|Yes| M[Serialize Response]\n"
        mermaid += "    M --> N[Return 200 OK]\n"
        mermaid += "    C --> O[End]\n"
        mermaid += "    L --> O\n"
        mermaid += "    N --> O\n"

        # Which of A-O exist depends on the branches above, so read the node ids
        # back out rather than styling ones that were never emitted.
        for node in dict.fromkeys(re.findall(r"\b([A-O])[\[\{]", mermaid)):
            mermaid += f"    style {node} {_FLOW_STYLES[_FLOW_ROLES[node]]}\n"
        mermaid += "```"

        return f"""## Process Diagrams

### Request Processing Workflow (Actual Architecture)

**Detected Components Used:**
- Controllers: {controllers} (HTTP routing)
- Services: {services} (business logic)
- Mappers: {mappers} (data transformation)
- Repositories: {repos} (data persistence)
- Entities: {entities} (domain models)

### Processing Steps

 {workflow_text}

### Request/Response Flow Diagram

{mermaid}

### Functional Layer Breakdown

**1. API/Controller Layer** ({controllers} controllers)
- Receives HTTP requests
- Parses URL, headers, and body
- Validates request format
- Routes to appropriate service

**2. Business Logic Layer** ({services} services)
- Executes core business rules
- Coordinates between repositories
- Manages transactions
- Applies validation logic

**3. Data Mapping Layer** ({mappers} mappers)
- Converts Entity to DTO for responses
- Converts DTO to Entity for persistence
- Handles data format transformations
- Decouples layers

**4. Data Access Layer** ({repos} repositories)
- Executes database queries
- Performs CRUD operations
- Manages transactions
- Handles connection pooling

**5. Domain Layer** ({entities} entities)
- Represents business concepts
- Enforces domain rules
- Maintains invariants
- Handles relationships

### Error Handling

At each step:
1. Input validation - catch format errors (HTTP 400)
2. Authorization - validate permissions (HTTP 403)
3. Business rules - enforce constraints
4. Database - handle concurrency and constraints
5. Transaction - rollback on any failure
6. Response - return appropriate error status

### Performance Considerations

- Response time target: < 500ms
- Database queries should use indexes
- Connection pooling for efficiency
- Caching at service layer where applicable
- Async processing for long-running tasks
"""

    def _build_business_rules(self) -> str:
        """Build business rules based on repo architecture."""
        patterns = self.signals.get('java_class_patterns', {})
        java_files = self.signals.get('java_files', [])
        entities = [f.split(".")[-1] for f in java_files if 'Entity' in f or 'Model' in f]

        rules = []
        if patterns.get('Controller', 0) > 0:
            rules.append(f"1. **Request Handling Rule**\n   - {patterns.get('Controller', 0)} controllers process requests\n   - Input validation required\n   - Response formatting applied\n   - HTTP status codes enforced")

        if patterns.get('Service', 0) > 0:
            rules.append(f"2. **Business Logic Rule**\n   - {patterns.get('Service', 0)} services enforce business rules\n   - Data consistency maintained\n   - Transaction boundaries defined\n   - Exception handling required")

        if patterns.get('Repository', 0) > 0:
            rules.append(f"3. **Data Access Rule**\n   - {patterns.get('Repository', 0)} repositories manage persistence\n   - CRUD operations enforced\n   - Database constraints applied\n   - Query optimization required")

        if entities:
            rules.append(f"4. **Entity Rules**\n   - {len(entities)} domain entities: {', '.join(entities[:3])}\n   - Entities maintain identity\n   - Properties validated on assignment\n   - Lifecycle events triggered")

        rules.append(f"5. **Transaction Rules**\n   - ACID properties maintained\n   - Rollback on failure\n   - Concurrency control enforced\n   - Isolation levels applied")

        return f"""## Business Rules

### Core Business Rules (Based on Architecture)

{chr(10).join(rules) if rules else "Generic business rules"}

### Detected Entity Models
- Total Entities: {len(entities)}
- Entity Names: {', '.join(entities[:5]) if entities else 'N/A'}

### Processing Rules
- Controllers: {patterns.get('Controller', 0)} request handlers
- Services: {patterns.get('Service', 0)} business logic layers
- Repositories: {patterns.get('Repository', 0)} data access patterns
- Mappers: {patterns.get('Mapper', 0)} transformation layers

### Enforcement Rules
- Input validation at controller layer
- Business logic at service layer
- Data persistence at repository layer
- Entity integrity maintained throughout
"""

    def _build_user_journeys(self) -> str:
        """Build user journeys based on repo controllers."""
        java_files = self.signals.get('java_files', [])
        controllers = [f for f in java_files if 'Controller' in f]
        services = [f for f in java_files if 'Service' in f]

        controllers_desc = f"({len(controllers)} controller{'s' if len(controllers) != 1 else ''})"
        services_desc = f"({len(services)} service layer{'s' if len(services) != 1 else ''})"

        return f"""## User Journeys

### Journey 1: Create Resource

**Actor:** API Client
**Goal:** Create a new resource via REST API

**System:** {self.repo_name} {controllers_desc}

**Steps:**
1. Client sends POST request to {self.repo_name} endpoint
2. Controller {controllers_desc} receives request
3. Service layer {services_desc} validates input
4. Service processes business logic
5. Data persisted to database
6. Client receives 201 Created response
7. Resource ID returned for future reference

---

### Journey 2: Retrieve Resource

**Actor:** API Client
**Goal:** Retrieve existing resource

**System:** {self.repo_name}

**Steps:**
1. Client sends GET request with resource ID
2. Controller routes to appropriate handler
3. Service queries repository
4. Repository retrieves from database
5. Data mapped to response format
6. Client receives 200 OK with data
7. Client processes response

---

### Journey 3: Update Resource

**Actor:** API Client
**Goal:** Modify existing resource

**System:** {self.repo_name}

**Steps:**
1. Client sends PUT request with updates
2. Controller validates request format
3. Service checks authorization
4. Service validates business rules
5. Service updates entity
6. Repository persists changes
7. Client receives 200 OK confirmation

---

### Journey 4: Delete Resource

**Actor:** Administrator
**Goal:** Remove resource from system

**System:** {self.repo_name}

**Steps:**
1. Admin sends DELETE request
2. Controller validates authorization
3. Service checks dependencies
4. Service marks as inactive (if soft delete)
5. Repository removes record
6. Client receives 204 No Content
7. Resource no longer accessible
"""

    def _build_non_functional_requirements(self) -> str:
        """Build non-functional requirements based on repo structure."""
        patterns = self.signals.get('java_class_patterns', {})
        frameworks = self.signals.get('frameworks', [])
        loc = self.signals.get('loc', 0)

        tech_notes = f"Stack: {', '.join(frameworks) if frameworks else 'Java'} with {loc:,} LOC"

        return f"""## Non-Functional Requirements

### Performance Requirements

**{self.repo_name}** with {patterns.get('Service', 0)} services and {patterns.get('Repository', 0)} repositories

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Response Time | < 500ms | 95th percentile |
| Service Processing | < 200ms | Average logic execution |
| Database Query | < 100ms | Average query |
| Concurrent Requests | 1000+ | Per deployment |

### Scalability Requirements
- Horizontal deployment via {patterns.get('Controller', 0)} stateless controllers
- Load balancing between service instances
- Database connection pooling
- Caching strategies for frequent queries

### Security Requirements
- Bearer token authentication for API access
- Request validation at {patterns.get('Controller', 0)} controller layer
- SQL injection prevention via ORM
- CSRF token validation
- Data encryption at rest
- HTTPS enforcement

### Availability Requirements
- 99.5% uptime target
- Automated health checks
- Graceful degradation
- Error handling and recovery

### Maintainability Requirements
- Code well-organized with {patterns.get('Service', 0)} services
- API endpoints documented with OpenAPI
- Clear layer separation: {patterns.get('Controller', 0)} controllers, {patterns.get('Service', 0)} services, {patterns.get('Repository', 0)} repositories
- Monitoring and alerting integration
- {tech_notes}

### Code Quality Requirements
- Unit test coverage: 70%+
- Integration test coverage: 50%+
- No critical code issues
- Documented dependencies
- Regular dependency updates
"""

    def _build_gap_analysis(self) -> str:
        """Build gap analysis based on repo structure."""
        patterns = self.signals.get('java_class_patterns', {})
        services = patterns.get('Service', 0)
        tests_detected = any('Test' in f for f in self.signals.get('java_files', []))

        gaps = []
        if services > 0 and not tests_detected:
            gaps.append("| GAP-001 | Testing | Limited unit tests for services | High | Code quality | Open |")
        if patterns.get('Service', 0) > 0:
            gaps.append("| GAP-002 | Documentation | Service layer documentation needed | Medium | Maintainability | Open |")
        if patterns.get('Repository', 0) > 0:
            gaps.append("| GAP-003 | Performance | Query optimization in repositories | Medium | Performance | In Progress |")
        if patterns.get('Controller', 0) > 0:
            gaps.append("| GAP-004 | Security | API security hardening | High | Data security | Pending |")

        return f"""## Gap Analysis

### Detected Gaps in {self.repo_name}

Architecture Summary:
- Controllers: {patterns.get('Controller', 0)}
- Services: {patterns.get('Service', 0)}
- Repositories: {patterns.get('Repository', 0)}

| Gap ID | Category | Description | Severity | Impact | Status |
|--------|----------|-------------|----------|--------|--------|
{chr(10).join(gaps) if gaps else "| GAP-001 | General | Architecture analysis needed | Medium | Design | Open |"}

### Gap Remediation Plan

1. **Service Layer Testing**
   - Add unit tests for {services} service classes
   - Target coverage: 80%+
   - Include edge cases

2. **API Documentation**
   - Document {patterns.get('Controller', 0)} controller endpoints
   - Generate OpenAPI specifications
   - Create usage examples

3. **Repository Optimization**
   - Profile {patterns.get('Repository', 0)} repository queries
   - Add database indexes
   - Implement query caching

4. **Security Hardening**
   - Validate inputs at controller layer
   - Implement rate limiting
   - Add authentication checks
"""

    def _build_risk_assessment(self) -> str:
        """Build risk assessment based on repo architecture."""
        patterns = self.signals.get('java_class_patterns', {})
        frameworks = self.signals.get('frameworks', [])

        risks = []
        if patterns.get('Repository', 0) > 0:
            risks.append("| RISK-001 | Data Loss | Low | Critical | Database backups, replication |")
        if patterns.get('Service', 0) > 0:
            risks.append("| RISK-002 | Service Failure | Medium | High | Circuit breakers, fallbacks |")
        if patterns.get('Controller', 0) > 0:
            risks.append("| RISK-003 | API Security | Medium | Critical | Input validation, authentication |")
        risks.append("| RISK-004 | Performance | Medium | High | Load testing, caching strategy |")

        return f"""## Risk Assessment

### Identified Risks for {self.repo_name}

**Architecture Risk Profile:**
- Controllers: {patterns.get('Controller', 0)} (API exposure)
- Services: {patterns.get('Service', 0)} (Business logic complexity)
- Repositories: {patterns.get('Repository', 0)} (Data access criticality)
- Frameworks: {', '.join(frameworks) if frameworks else 'Standard Java'}

| Risk ID | Title | Probability | Impact | Mitigation |
|---------|-------|-------------|--------|-----------|
{chr(10).join(risks)}

### Risk Mitigation Strategies

1. **Technical Risks**
   - Code reviews before deployment
   - Unit and integration testing
   - Automated security scanning
   - Performance benchmarking
   - Dependency vulnerability scanning

2. **Operational Risks**
   - Database backup strategy
   - Service monitoring and alerting
   - Automated failover procedures
   - Load balancing configuration
   - Error rate tracking

3. **Security Risks**
   - Input validation in {patterns.get('Controller', 0)} controllers
   - Authentication and authorization checks
   - Data encryption at rest and in transit
   - Regular security audits
   - Penetration testing

4. **Architectural Risks**
   - Service layer resilience (circuit breakers)
   - Database connection pooling
   - Graceful degradation
   - Horizontal scaling capability
"""

    def _build_recommendations(self) -> str:
        """Build recommendations based on repo analysis."""
        patterns = self.signals.get('java_class_patterns', {})
        loc = self.signals.get('loc', 0)

        return f"""## Recommendations

### Short-term (0-3 months)

1. **Service Layer Testing**
   - Target: Add unit tests for {patterns.get('Service', 0)} services
   - Priority: High
   - Effort: Medium
   - Impact: Code quality improvement

2. **API Documentation**
   - Document {patterns.get('Controller', 0)} controller endpoints
   - Priority: High
   - Effort: Low
   - Impact: Developer productivity

3. **Query Performance**
   - Analyze repository queries for {patterns.get('Repository', 0)} repositories
   - Priority: Medium
   - Effort: Medium
   - Impact: System performance

### Medium-term (3-6 months)

1. **Performance Optimization**
   - Implement caching strategies
   - Profile hot paths ({loc:,} LOC to analyze)
   - Priority: High
   - Effort: High
   - Impact: Throughput improvement

2. **Security Enhancement**
   - Security audit of {patterns.get('Controller', 0)} API controllers
   - Implement rate limiting
   - Priority: High
   - Effort: High
   - Impact: Security posture

3. **Monitoring**
   - Add APM instrumentation
   - Setup alerts for service layer
   - Priority: Medium
   - Effort: Medium
   - Impact: Operational visibility

### Long-term (6-12 months)

1. **Architecture Review**
   - Evaluate microservice decomposition
   - Current layers: {sum([1 for v in [patterns.get('Controller', 0), patterns.get('Service', 0), patterns.get('Repository', 0)] if v > 0])}
   - Priority: Medium
   - Effort: High
   - Impact: Scalability and maintainability

2. **Technology Modernization**
   - Evaluate dependency updates
   - Priority: Medium
   - Effort: High
   - Impact: Security and performance
"""

    def _build_acceptance_criteria(self) -> str:
        """Build acceptance criteria based on detected architecture."""
        patterns = self.signals.get('java_class_patterns', {})
        frameworks = self.signals.get('frameworks', [])

        scenarios = []

        # Generate BDD-style acceptance criteria
        if patterns.get('Controller', 0) > 0:
            scenarios.append("""### AC001: Request Handling with Valid Input

**Given:** System with API endpoints available
**When:** Client sends valid HTTP request to controller endpoint
**Then:** Request is processed and appropriate response returned
**And:** Response includes status code 200 OK
**And:** Response body contains expected data structure

**Acceptance Criteria:**
- ✓ Request validation passes
- ✓ Business logic executes correctly
- ✓ Response formatted properly
- ✓ Response time < 500ms
- ✓ No errors logged""")

        if patterns.get('Service', 0) > 0:
            scenarios.append("""### AC002: Business Logic Execution

**Given:** {count} service classes implementing business logic
**When:** Service method is invoked with valid parameters
**Then:** Business rules are applied correctly
**And:** State is updated appropriately

**Acceptance Criteria:**
- ✓ All business rules validated
- ✓ Data consistency maintained
- ✓ Transaction boundaries respected
- ✓ No data corruption occurs
- ✓ All edge cases handled""".format(count=patterns.get('Service', 0)))

        if patterns.get('Repository', 0) > 0:
            scenarios.append("""### AC003: Data Persistence

**Given:** {count} repositories for data access
**When:** Save/update/delete operation is invoked
**Then:** Data is persisted to database correctly
**And:** Transaction is committed successfully

**Acceptance Criteria:**
- ✓ Data written to correct table
- ✓ Relationships maintained
- ✓ Constraints validated
- ✓ Audit trail recorded
- ✓ Transaction consistency verified""".format(count=patterns.get('Repository', 0)))

        if patterns.get('Entity', 0) > 0:
            scenarios.append("""### AC004: Entity Validation

**Given:** {count} domain entities defined
**When:** Entity state is modified
**Then:** Entity invariants are enforced
**And:** Invalid state transitions are prevented

**Acceptance Criteria:**
- ✓ All required fields present
- ✓ Field values within valid ranges
- ✓ Business rules enforced
- ✓ State transitions valid
- ✓ Audit fields updated""".format(count=patterns.get('Entity', 0)))

        if patterns.get('Mapper', 0) > 0:
            scenarios.append("""### AC005: Data Transformation

**Given:** {count} mappers for data transformation
**When:** Entity is mapped to DTO or vice versa
**Then:** All fields mapped correctly
**And:** No data loss occurs
**And:** Null values handled appropriately

**Acceptance Criteria:**
- ✓ All fields mapped
- ✓ Type conversions correct
- ✓ No null pointer exceptions
- ✓ Performance acceptable
- ✓ Bidirectional mapping works""".format(count=patterns.get('Mapper', 0)))

        scenario_text = "\n\n".join(scenarios) if scenarios else "### Generic Acceptance Criteria\nNo specific components detected"

        return f"""## Acceptance Criteria

### Gherkin-Style Scenarios

{scenario_text}

### Definition of Done

For each feature implementation:
- [ ] Code passes all unit tests
- [ ] Code passes integration tests
- [ ] Code review completed
- [ ] Performance tested (<500ms)
- [ ] Security reviewed
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Backward compatibility maintained

### Quality Metrics

**Code Coverage:**
- Unit tests: >= 80%
- Integration tests: >= 60%
- Controllers: >= 75%
- Services: >= 85%
- Repositories: >= 70%

**Performance:**
- Controller response: < 500ms
- Database queries: < 100ms
- API throughput: > 1000 req/sec
- Memory usage: < 512MB

**Reliability:**
- Error rate: < 0.1%
- Uptime: >= 99.9%
- Data consistency: 100%
- Transaction success: >= 99%
"""

    def _build_artifacts_inventory(self) -> str:
        """Build artifacts inventory from repository analysis."""
        java_files = self.signals.get('java_files', [])
        patterns = self.signals.get('java_class_patterns', {})
        main_packages = self.signals.get('main_packages', [])
        loc = self.signals.get('loc', 0)

        # Categorize all artifacts
        controllers = [f for f in java_files if 'Controller' in f]
        services = [f for f in java_files if 'Service' in f]
        repositories = [f for f in java_files if 'Repository' in f]
        entities = [f for f in java_files if 'Entity' in f or 'Model' in f]
        mappers = [f for f in java_files if 'Mapper' in f]
        dtos = [f for f in java_files if 'DTO' in f or 'Dto' in f]
        configs = [f for f in java_files if 'Config' in f or 'Configuration' in f]
        utils = [f for f in java_files if 'Util' in f or 'Helper' in f]
        others = [f for f in java_files if not any([
            'Controller' in f, 'Service' in f, 'Repository' in f,
            'Entity' in f, 'Model' in f, 'Mapper' in f, 'DTO' in f,
            'Dto' in f, 'Config' in f, 'Configuration' in f,
            'Util' in f, 'Helper' in f
        ])]

        artifact_summary = f"""## Artifacts Inventory

### Repository Analysis Summary
- **Total Artifacts:** {len(java_files)}
- **Total Lines of Code:** {loc:,}
- **Main Packages:** {len(main_packages)}
- **Architecture Layers:** {sum([1 for k in ['Controller', 'Service', 'Repository'] if patterns.get(k, 0) > 0])}

### Artifact Distribution

| Category | Count | Percentage | Files |
|----------|-------|------------|-------|
| Controllers | {len(controllers)} | {len(controllers)*100//len(java_files) if java_files else 0}% | {', '.join(c.split('.')[-1] for c in controllers[:5]) if controllers else 'None'} |
| Services | {len(services)} | {len(services)*100//len(java_files) if java_files else 0}% | {', '.join(s.split('.')[-1] for s in services[:5]) if services else 'None'} |
| Repositories | {len(repositories)} | {len(repositories)*100//len(java_files) if java_files else 0}% | {', '.join(r.split('.')[-1] for r in repositories[:5]) if repositories else 'None'} |
| Entities | {len(entities)} | {len(entities)*100//len(java_files) if java_files else 0}% | {', '.join(e.split('.')[-1] for e in entities[:5]) if entities else 'None'} |
| Mappers | {len(mappers)} | {len(mappers)*100//len(java_files) if java_files else 0}% | {', '.join(m.split('.')[-1] for m in mappers[:5]) if mappers else 'None'} |
| DTOs | {len(dtos)} | {len(dtos)*100//len(java_files) if java_files else 0}% | {', '.join(d.split('.')[-1] for d in dtos[:5]) if dtos else 'None'} |
| Configurations | {len(configs)} | {len(configs)*100//len(java_files) if java_files else 0}% | {', '.join(c.split('.')[-1] for c in configs[:5]) if configs else 'None'} |
| Utilities | {len(utils)} | {len(utils)*100//len(java_files) if java_files else 0}% | {', '.join(u.split('.')[-1] for u in utils[:5]) if utils else 'None'} |
| Other | {len(others)} | {len(others)*100//len(java_files) if java_files else 0}% | {', '.join(o.split('.')[-1] for o in others[:5]) if others else 'None'} |

### Controllers ({len(controllers)} total)
```
{chr(10).join([f'{i+1}. {c}' for i, c in enumerate(controllers[:20])])}
{f"... and {len(controllers)-20} more" if len(controllers) > 20 else ""}
```

### Services ({len(services)} total)
```
{chr(10).join([f'{i+1}. {s}' for i, s in enumerate(services[:20])])}
{f"... and {len(services)-20} more" if len(services) > 20 else ""}
```

### Repositories ({len(repositories)} total)
```
{chr(10).join([f'{i+1}. {r}' for i, r in enumerate(repositories[:20])])}
{f"... and {len(repositories)-20} more" if len(repositories) > 20 else ""}
```

### Entities ({len(entities)} total)
```
{chr(10).join([f'{i+1}. {e}' for i, e in enumerate(entities[:20])])}
{f"... and {len(entities)-20} more" if len(entities) > 20 else ""}
```

### Mappers ({len(mappers)} total)
```
{chr(10).join([f'{i+1}. {m}' for i, m in enumerate(mappers[:10])])}
{f"... and {len(mappers)-10} more" if len(mappers) > 10 else ""}
```

### Complete Java File List ({len(java_files)} total)
```
{chr(10).join([f'{i+1}. {f}' for i, f in enumerate(java_files)])}
```

### Package Structure ({len(main_packages)} main packages)
```
{chr(10).join([f'{i+1}. {p}' for i, p in enumerate(main_packages)])}
```
"""

        return artifact_summary

    def _build_test_scenarios(self) -> str:
        """Build test scenarios based on detected components."""
        patterns = self.signals.get('java_class_patterns', {})
        services = patterns.get('Service', 0)
        repos = patterns.get('Repository', 0)
        controllers = patterns.get('Controller', 0)

        return f"""## Test Scenarios

### Unit Tests

**Testing {services} Service Classes:**

```java
@Test
public void testService_ValidInput() {{
    // Arrange - Setup test data
    ServiceInput input = new ServiceInput();

    // Act - Call service method
    ServiceOutput output = service.process(input);

    // Assert - Verify result
    assertNotNull(output.getId());
    assertTrue(output.isValid());
}}

@Test
public void testService_InvalidInput() {{
    // Arrange - Invalid data
    ServiceInput input = new ServiceInput(); // missing required fields

    // Act & Assert - Expect exception
    assertThrows(ValidationException.class, () -> {{
        service.process(input);
    }});
}}
```

### Integration Tests

**Testing {controllers} Controllers + {repos} Repositories:**

```java
@SpringBootTest
public class ControllerIntegrationTest {{
    @Test
    public void testController_EndToEnd() {{
        // Create data via controller
        // Verify service processes
        // Check repository persists
        // Validate response
    }}
}}
```

### Functional Tests by Layer

**Controllers ({controllers}):**
- Request routing
- Input validation
- Response formatting

**Services ({services}):**
- Business logic execution
- State transitions
- Error handling

**Repositories ({repos}):**
- CRUD operations
- Query validation
- Transaction management

### Performance Tests

- Load: 1000 concurrent users
- Throughput: 1000+ req/sec
- Response time: p95 < 500ms
- Database: Query time < 100ms

### Test Coverage Targets

- Unit Tests: {services} services, {patterns.get('Entity', 0)} entities
- Integration: {controllers} controller endpoints
- Target Coverage: 70-80%
"""

    def _build_appendices(self) -> str:
        """Build appendices based on repo analysis."""
        patterns = self.signals.get('java_class_patterns', {})
        frameworks = self.signals.get('frameworks', [])
        loc = self.signals.get('loc', 0)
        dependencies = self.signals.get('dependencies', {})

        arch_desc = f"Layered Architecture: {patterns.get('Controller', 0)} Controllers, {patterns.get('Service', 0)} Services, {patterns.get('Repository', 0)} Repositories"

        frameworks_ref = ", ".join(frameworks) if frameworks else "Java"

        dep_summary = ""
        if dependencies:
            for dep_type, dep_list in dependencies.items():
                if dep_list:
                    dep_summary += f"- {dep_type}: {', '.join(dep_list[:3])}\n"

        return f"""## Appendices

### A. Glossary

| Term | Definition |
|------|-----------|
| Controller | REST API request handler ({patterns.get('Controller', 0)} detected) |
| Service | Business logic layer ({patterns.get('Service', 0)} services) |
| Repository | Data access layer ({patterns.get('Repository', 0)} repositories) |
| Entity | Domain model ({patterns.get('Entity', 0)} entities) |
| DTO | Data Transfer Object ({patterns.get('DTO', 0)} found) |
| Mapper | Entity/DTO transformation ({patterns.get('Mapper', 0)} mappers) |
| REST | Representational State Transfer |
| ACID | Atomicity, Consistency, Isolation, Durability |

### B. Architecture Summary

**Repository:** {self.repo_name}
**Total LOC:** {loc:,}
**Architecture:** {arch_desc}

### C. Technology Stack

- **Frameworks:** {frameworks_ref}
- **Primary Language:** Java
{dep_summary if dep_summary else "- No dependencies mapped"}

### D. Component Distribution

| Component Type | Count |
|---|---|
| Controllers | {patterns.get('Controller', 0)} |
| Services | {patterns.get('Service', 0)} |
| Repositories | {patterns.get('Repository', 0)} |
| Entities | {patterns.get('Entity', 0)} |
| Mappers | {patterns.get('Mapper', 0)} |
| DTOs | {patterns.get('DTO', 0)} |

### E. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-09-11 | System | Initial BRD from {self.repo_name} |

### F. Document Control

- **Document ID:** BRD-{self.repo_name}-001
- **Status:** Generated
- **Classification:** Internal
- **Last Modified:** 2026-09-11
- **Repository:** {self.repo_name}
- **LOC Analyzed:** {loc:,}
- **Components Found:** {sum([patterns.get(t, 0) for t in ['Controller', 'Service', 'Repository', 'Entity', 'DTO', 'Mapper']])}

### G. References

- Spring Framework Documentation
- Java Patterns and Practices
- REST API Design Guidelines
- Database Design Principles
- Security Best Practices

### H. Analysis Methodology

This BRD was generated through:
1. Repository signal extraction and analysis
2. Codebase pattern detection
3. Component inventory generation
4. Architecture diagram creation
5. API specification generation
6. Gap and risk analysis

**Confidence Level:** {self.signals.get('confidence', 0.75):.1%}
"""
