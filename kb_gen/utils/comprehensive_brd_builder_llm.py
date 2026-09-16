"""
Comprehensive BRD Builder (LLM-POWERED VERSION)
Generates complete, repo-specific markdown BRD with actual API endpoints,
domain-specific diagrams, and business context from repository analysis.
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

from kb_gen.utils.agent_llm import AgentLLM


class ComprehensiveBRDBuilderLLM:
    """Builds comprehensive, repo-specific BRD using Claude."""

    def __init__(self, repo_name: str, repo_path: str, signals: Dict[str, Any], api_key: Optional[str] = None, kb_path: Optional[Path] = None):
        self.repo_name = repo_name
        self.repo_path = Path(repo_path)
        self.kb_path = Path(kb_path) if kb_path else None
        self.signals = signals
        self.agent_llm = AgentLLM(repo_path, api_key)
        self.domain = self._infer_domain()
        self._api_endpoints_cache = None
        self._entity_models_cache = None
        self._data_flow_cache = None
        self._loaded_artifacts = {}

    def _extract_api_endpoints(self) -> List[Dict[str, Any]]:
        """Extract actual Spring Boot API endpoints from controller files."""
        if self._api_endpoints_cache is not None:
            return self._api_endpoints_cache

        endpoints = []
        try:
            for fpath in self.repo_path.rglob("*Controller.java"):
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")

                    # Extract class-level mapping
                    class_mapping = re.search(r'@RequestMapping\("([^"]+)"\)', content)
                    base_path = class_mapping.group(1) if class_mapping else ""

                    # Extract method-level mappings
                    methods = re.findall(
                        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*"([^"]*)"[^)]*\)|@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*value\s*=\s*"([^"]*)"',
                        content
                    )

                    for match in methods:
                        http_method = match[0] or match[2]
                        path = match[1] or match[3]

                        # Convert mapping type to HTTP method
                        method_map = {
                            'GetMapping': 'GET',
                            'PostMapping': 'POST',
                            'PutMapping': 'PUT',
                            'DeleteMapping': 'DELETE',
                            'PatchMapping': 'PATCH',
                            'RequestMapping': 'GET'
                        }

                        full_path = f"{base_path}{path}".replace('""', '')
                        if full_path:
                            endpoints.append({
                                'path': full_path,
                                'method': method_map.get(http_method, 'GET'),
                                'controller': fpath.stem
                            })
                except Exception:
                    pass
        except Exception:
            pass

        self._api_endpoints_cache = endpoints
        return endpoints

    def _extract_entity_models(self) -> List[Dict[str, Any]]:
        """Extract actual entity and DTO models from code."""
        if self._entity_models_cache is not None:
            return self._entity_models_cache

        models = []
        try:
            # Extract entity files
            for fpath in self.repo_path.rglob("*.java"):
                if any(x in fpath.name for x in ['Entity', 'DTO', 'Model', 'Request', 'Response']):
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        class_match = re.search(r'(?:@Entity|@Data|@Getter|@Setter)[\s\S]*?public\s+class\s+(\w+)', content)
                        if class_match:
                            class_name = class_match.group(1)
                            # Extract fields
                            fields = re.findall(r'private\s+(\w+)\s+(\w+);', content)
                            models.append({
                                'name': class_name,
                                'file': fpath.stem,
                                'fields': [{'type': f[0], 'name': f[1]} for f in fields[:5]]
                            })
                    except Exception:
                        pass
        except Exception:
            pass

        self._entity_models_cache = models
        return models

    def _extract_data_flow(self) -> str:
        """Analyze and describe actual data flow in the repository."""
        if self._data_flow_cache is not None:
            return self._data_flow_cache

        flow_desc = []
        try:
            # Count components
            controllers = self.signals.get('java_class_patterns', {}).get('Controller', 0)
            services = self.signals.get('java_class_patterns', {}).get('Service', 0)
            repositories = self.signals.get('java_class_patterns', {}).get('Repository', 0)
            entities = self.signals.get('java_class_patterns', {}).get('Entity', 0)
            dtos = self.signals.get('java_class_patterns', {}).get('DTO', 0)

            if controllers > 0:
                flow_desc.append(f"- {controllers} API controller(s) handling HTTP requests")
            if services > 0:
                flow_desc.append(f"- {services} service(s) implementing business logic")
            if repositories > 0:
                flow_desc.append(f"- {repositories} repository/DAO(s) for data persistence")
            if entities > 0:
                flow_desc.append(f"- {entities} entity model(s) mapping to database")
            if dtos > 0:
                flow_desc.append(f"- {dtos} DTO(s) for request/response payloads")

            # Detect major frameworks
            imports = self.signals.get('top_imports', [])
            frameworks_used = []
            if any('spring' in str(imp[0]).lower() for imp in imports):
                frameworks_used.append("Spring Framework")
            if any('hibernate' in str(imp[0]).lower() for imp in imports):
                frameworks_used.append("Hibernate ORM")
            if any('mybatis' in str(imp[0]).lower() for imp in imports):
                frameworks_used.append("MyBatis")

            if frameworks_used:
                flow_desc.append(f"- Technology: {', '.join(frameworks_used)}")
        except Exception:
            pass

        result = "\n".join(flow_desc) if flow_desc else "Multi-tier architecture with controllers, services, and persistence layer"
        self._data_flow_cache = result
        return result

    def _load_artifact(self, artifact_name: str) -> Dict[str, Any]:
        """Load an artifact from the KB directory."""
        if artifact_name in self._loaded_artifacts:
            return self._loaded_artifacts[artifact_name]

        if not self.kb_path:
            return {}

        artifact_path = self.kb_path / f"{artifact_name}.json"
        if artifact_path.exists():
            try:
                data = json.loads(artifact_path.read_text(encoding="utf-8", errors="ignore"))
                self._loaded_artifacts[artifact_name] = data
                return data
            except Exception:
                pass

        return {}

    def _infer_domain(self) -> str:
        """Infer business domain from package names."""
        domain_keywords = {
            'banking': ['bank', 'finance', 'transaction', 'transfer', 'payment', 'account', 'lending'],
            'ecommerce': ['store', 'shop', 'product', 'cart', 'order', 'purchase', 'catalog', 'seller'],
            'healthcare': ['patient', 'doctor', 'appointment', 'medical', 'health', 'clinic', 'prescription'],
            'library': ['book', 'library', 'member', 'lending', 'catalog', 'isbn'],
            'inventory': ['inventory', 'stock', 'warehouse', 'product', 'sku', 'supplier'],
            'project': ['project', 'task', 'sprint', 'team', 'milestone'],
        }

        package_text = ' '.join(self.signals.get('main_packages', [])).lower()

        for domain, keywords in domain_keywords.items():
            if any(kw in package_text for kw in keywords):
                return domain

        return 'general-application'

    def build(self) -> str:
        """Build complete repo-specific comprehensive BRD."""
        sections = []

        sections.append(self._build_title())
        sections.append(self._build_executive_summary())
        sections.append(self._build_system_overview())
        sections.append(self._build_architecture_diagram())
        sections.append(self._build_technology_stack())
        sections.append(self._build_component_inventory())
        sections.append(self._build_api_endpoints())
        sections.append(self._build_data_flow_diagram())
        sections.append(self._build_sequence_diagrams())
        sections.append(self._build_request_response_diagrams())
        sections.append(self._build_functional_requirements())
        sections.append(self._build_business_rules())
        sections.append(self._build_user_journeys())
        sections.append(self._build_non_functional_requirements())
        sections.append(self._build_acceptance_criteria())
        sections.append(self._build_risk_assessment())
        sections.append(self._build_gap_analysis())
        sections.append(self._build_recommendations())

        return "\n\n".join(filter(None, sections))

    def _build_title(self) -> str:
        """Build title section."""
        return f"""# {self.repo_name} - Comprehensive Business Requirements Document

**Generated**: {self.signals.get('timestamp', 'N/A')}
**Domain**: {self.domain.title()}
**Confidence**: {self.signals.get('confidence', 0.85):.0%}
**Repository Path**: {self.repo_path}"""

    def _build_executive_summary(self) -> str:
        """Build LLM-generated executive summary."""
        if not self.agent_llm.has_api():
            return self._fallback_executive_summary()

        prompt = f"""
Generate a professional executive summary for this {self.domain} application.

Repository: {self.repo_name}
Domain: {self.domain}
Technology Stack: {', '.join(self.signals.get('frameworks', []))}
Components: {self.signals['java_class_patterns'].get('Controller', 0)} controllers,
            {self.signals['java_class_patterns'].get('Service', 0)} services,
            {self.signals['java_class_patterns'].get('Repository', 0)} repositories
LOC: {self.signals.get('loc', 0):,}
Main Packages: {', '.join(self.signals.get('main_packages', [])[:3])}

Generate a 4-5 paragraph executive summary that:
1. Describes what this application does (based on domain)
2. Explains key business objectives
3. Lists main features/capabilities
4. Mentions technology approach
5. States business value

Return ONLY the summary text, no markdown formatting."""

        result = self.agent_llm.call_claude(prompt)
        return f"## Executive Summary\n\n{result}" if result else self._fallback_executive_summary()

    def _fallback_executive_summary(self) -> str:
        """Fallback executive summary."""
        return f"""## Executive Summary

**Project**: {self.repo_name}
**Domain**: {self.domain.title()}
**Primary Language**: Java
**Build System**: {'Gradle' if 'Gradle' in self.signals.get('frameworks', []) else 'Maven'}

The {self.repo_name} system is a {self.domain}-focused application implementing core business operations.
This document provides complete specifications of system requirements, architecture, and implementation details."""

    def _build_system_overview(self) -> str:
        """Build system overview."""
        packages = self.signals.get('main_packages', [])
        frameworks = self.signals.get('frameworks', [])

        overview = f"""## System Overview

### Purpose
{self.repo_name} provides comprehensive {self.domain} capabilities including:
- Core {self.domain} process management
- Data persistence and retrieval
- System integration capabilities
- User and transaction management

### Architecture Components
- **Web Layer**: {self.signals['java_class_patterns'].get('Controller', 0)} Controllers
- **Business Logic**: {self.signals['java_class_patterns'].get('Service', 0)} Services
- **Data Access**: {self.signals['java_class_patterns'].get('Repository', 0)} Repositories
- **Domain Entities**: {self.signals['java_class_patterns'].get('Entity', 0)} Entities

### Technology Stack
- **Frameworks**: {', '.join(frameworks) if frameworks else 'Spring Framework'}
- **Build System**: Maven/Gradle
- **Total LOC**: {self.signals.get('loc', 0):,}
- **Main Packages**: {', '.join(packages[:5])}"""

        return overview

    def _build_architecture_diagram(self) -> str:
        """Build repo-specific architecture diagram with actual component details."""
        if not self.agent_llm.has_api():
            return self._fallback_architecture_diagram()

        patterns = self.signals['java_class_patterns']

        # Extract actual components from repository
        controllers = [f.stem for f in self.repo_path.rglob("*Controller.java")][:3]
        services = [f.stem for f in self.repo_path.rglob("*Service.java")][:3]
        repositories = [f.stem for f in self.repo_path.rglob("*Repository.java")][:3]

        components_desc = f"""
DETECTED COMPONENTS:
- Controllers ({patterns.get('Controller', 0)}): {', '.join(controllers) if controllers else 'Multiple API controllers'}
- Services ({patterns.get('Service', 0)}): {', '.join(services) if services else 'Multiple business services'}
- Repositories ({patterns.get('Repository', 0)}): {', '.join(repositories) if repositories else 'Multiple data access objects'}
- Entities ({patterns.get('Entity', 0)})
- DTOs ({patterns.get('DTO', 0)})
"""

        prompt = f"""
Create a DETAILED, REPOSITORY-SPECIFIC PlantUML architecture diagram for this {self.domain} application.

{components_desc}

Technology Stack: {', '.join(self.signals.get('frameworks', []))}
Main Packages: {', '.join(self.signals.get('main_packages', [])[:3])}

REQUIREMENTS:
1. Generate a COMPLETE PlantUML diagram (@startuml...@enduml)
2. Use the ACTUAL component names detected above (not generic 'Controller', 'Service')
3. Show all 4 layers clearly: API/Presentation → Business Logic → Data Access → Database
4. Use packages to group related components by their actual domain
5. Show realistic inter-component dependencies
6. Include external systems/databases as applicable to {self.domain}
7. Add component roles/descriptions in comments
8. Make the diagram specific to this {self.domain} system's actual architecture

For a {self.domain} application, show realistic layer interactions specific to the detected components."""

        diagram = self.agent_llm.call_claude(prompt, max_tokens=2000)
        if diagram and "@startuml" in diagram:
            return f"""## Architecture Diagram

```plantuml
{diagram}
```"""
        return self._fallback_architecture_diagram()

    def _fallback_architecture_diagram(self) -> str:
        """Fallback architecture diagram."""
        patterns = self.signals['java_class_patterns']
        return f"""## Architecture Diagram

```plantuml
@startuml
package "{self.repo_name}" {{
  package "Presentation Layer" {{
    component [Controller] as controller
  }}
  package "Business Logic Layer" {{
    component [Service] as service
  }}
  package "Data Access Layer" {{
    component [Repository] as repo
  }}
  package "Domain Layer" {{
    component [Entity] as entity
  }}
}}

controller --> service
service --> repo
repo --> entity
@enduml
```"""

    def _build_technology_stack(self) -> str:
        """Build technology stack section."""
        frameworks = self.signals.get('frameworks', [])
        return f"""## Technology Stack

### Frameworks & Libraries
{chr(10).join(f"- {fw}" for fw in frameworks) if frameworks else "- Spring Framework"}

### Build Tools
- Maven or Gradle
- JUnit 5 for testing

### Database
- Relational Database (MySQL, PostgreSQL, H2)
- ORM: Spring Data JPA/Hibernate

### Key Dependencies
{json.dumps({k: v[:3] for k, v in self.signals.get('dependencies', {}).items()}, indent=2)}"""

    def _build_component_inventory(self) -> str:
        """Build component inventory."""
        patterns = self.signals['java_class_patterns']
        return f"""## Component Inventory

| Type | Count | Purpose |
|------|-------|---------|
| Controllers | {patterns.get('Controller', 0)} | API endpoints and request handling |
| Services | {patterns.get('Service', 0)} | Business logic implementation |
| Repositories | {patterns.get('Repository', 0)} | Data persistence |
| Entities | {patterns.get('Entity', 0)} | Domain models |
| Mappers | {patterns.get('Mapper', 0)} | Data transformation |

### Main Packages
{chr(10).join(f"- {pkg}" for pkg in self.signals.get('main_packages', [])[:10])}"""

    def _build_api_endpoints(self) -> str:
        """Build ACTUAL API endpoints detected from repository."""
        # Extract actual endpoints from repository
        detected_endpoints = self._extract_api_endpoints()

        if detected_endpoints and self.agent_llm.has_api():
            # Build table from actual detected endpoints
            endpoints_table = "| Endpoint | Method | Controller | Description |\n"
            endpoints_table += "|----------|--------|-----------|-------------|\n"

            # Get descriptions from Claude for each endpoint
            patterns = self.signals['java_class_patterns']

            # Use detected endpoints or generate descriptions if available
            for endpoint in detected_endpoints[:10]:
                path = endpoint['path']
                method = endpoint['method']
                controller = endpoint['controller']
                # Infer description from path
                if 'Get' in method or 'get' in path.lower():
                    desc = f"Retrieve {path.split('/')[-1]} from {self.domain}"
                elif 'Post' in method or 'post' in path.lower():
                    desc = f"Create new {path.split('/')[-1]} in {self.domain}"
                elif 'Put' in method or 'put' in path.lower():
                    desc = f"Update {path.split('/')[-1]} in {self.domain}"
                elif 'Delete' in method or 'delete' in path.lower():
                    desc = f"Delete {path.split('/')[-1]} from {self.domain}"
                else:
                    desc = f"Operate on {path.split('/')[-1]} in {self.domain}"

                endpoints_table += f"| {path} | {method} | {controller} | {desc} |\n"

            return f"""## API Endpoints

### Detected REST Endpoints
{endpoints_table}"""

        # Fallback to LLM generation if no endpoints detected
        if not self.agent_llm.has_api():
            return self._fallback_api_endpoints()

        patterns = self.signals['java_class_patterns']
        prompt = f"""
Generate realistic API endpoints specification for a {self.domain} application with {patterns.get('Controller', 0)} controllers.

Domain: {self.domain}
Controllers: {patterns.get('Controller', 0)}
Services: {patterns.get('Service', 0)}

Generate a realistic REST API specification with:
1. 8-12 endpoints specific to {self.domain}
2. Each endpoint with: path, method (GET/POST/PUT/DELETE), description, request/response models
3. Include authentication/authorization headers
4. Domain-specific operations

For example if {self.domain}:
- Banking: /api/transfers, /api/accounts, /api/transactions, etc.
- E-commerce: /api/products, /api/orders, /api/cart, etc.
- Healthcare: /api/patients, /api/appointments, /api/prescriptions, etc.

Format as a markdown table with columns: Endpoint, Method, Description, Auth Required"""

        result = self.agent_llm.call_claude(prompt, max_tokens=2000)
        if result:
            return f"""## API Endpoints

### Overview
REST API endpoints for {self.domain} operations:

{result}"""
        return self._fallback_api_endpoints()

    def _fallback_api_endpoints(self) -> str:
        """Fallback API endpoints."""
        if self.domain == 'banking':
            endpoints = """
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/accounts | GET | List user accounts |
| /api/transfers | POST | Create fund transfer |
| /api/transactions | GET | Transaction history |
| /api/payments | POST | Process payment |"""
        elif self.domain == 'ecommerce':
            endpoints = """
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/products | GET | List products |
| /api/orders | POST | Create order |
| /api/cart | GET/POST | Manage shopping cart |
| /api/reviews | GET/POST | Product reviews |"""
        else:
            endpoints = """
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/resources | GET | List resources |
| /api/operations | POST | Create operation |
| /api/status | GET | System status |"""

        return f"""## API Endpoints

### Available Operations
{endpoints}"""

    def _build_data_flow_diagram(self) -> str:
        """Build repo-specific data flow diagram with actual component details."""
        if not self.agent_llm.has_api():
            return self._fallback_data_flow()

        # Extract actual repository components
        endpoints = self._extract_api_endpoints()[:3]  # Top 3 endpoints
        endpoints_desc = "\n".join([f"  - {e['method']} {e['path']} ({e['controller']})" for e in endpoints])

        # Get actual data flow description
        data_flow_info = self._extract_data_flow()

        # Extract entity models
        models = self._extract_entity_models()[:3]
        models_desc = "\n".join([f"  - {m['name']}: {', '.join(f['name'] for f in m['fields'])}" for m in models])

        prompt = f"""
Create a detailed, repository-specific PlantUML sequence diagram showing actual data flow for this {self.domain} application.

ACTUAL REPOSITORY STRUCTURE:
{data_flow_info}

SAMPLE API ENDPOINTS:
{endpoints_desc if endpoints_desc else "  - Multiple REST endpoints"}

ENTITY MODELS:
{models_desc if models_desc else "  - Domain entities for {self.domain}"}

REQUIREMENTS:
1. Generate a COMPLETE PlantUML sequence diagram (@startuml...@enduml)
2. Show realistic request flow: Client → Controller → Service → Repository → Database
3. Include actual entity/DTO names from models above
4. Show typical data transformation between layers
5. Include at least one error/exception handling path
6. Make it specific to detected {self.domain} domain with realistic business operations

Example: For a {self.domain} system, show the actual workflow for main operation (create, read, update, delete)"""

        diagram = self.agent_llm.call_claude(prompt, max_tokens=2000)
        if diagram and "@startuml" in diagram:
            return f"""## Data Flow Diagram

```plantuml
{diagram}
```"""
        return self._fallback_data_flow()

    def _fallback_data_flow(self) -> str:
        """Fallback data flow diagram."""
        return f"""## Data Flow Diagram

```plantuml
@startuml
actor User
participant Controller
participant Service
participant Repository
database Database

User -> Controller: Request
Controller -> Service: Business Logic
Service -> Repository: Query/Persist
Repository -> Database: SQL
Database --> Repository: Result
Repository --> Service: Data
Service --> Controller: Response
Controller --> User: HTTP Response
@enduml
```"""

    def _build_sequence_diagrams(self) -> str:
        """Build repo-specific sequence diagrams for main workflows."""
        if not self.agent_llm.has_api():
            return self._fallback_sequence_diagrams()

        # Extract actual endpoints and components
        endpoints = self._extract_api_endpoints()[:3]
        models = self._extract_entity_models()[:3]

        endpoints_desc = "\n".join([f"  - {e['method']} {e['path']}" for e in endpoints]) if endpoints else "  - Multiple REST endpoints"
        models_desc = "\n".join([f"  - {m['name']}" for m in models]) if models else "  - Domain entities"

        data_flow = self._extract_data_flow()

        prompt = f"""
Generate 2-3 REPOSITORY-SPECIFIC PlantUML sequence diagrams showing realistic business workflows for this {self.domain} application.

ACTUAL DETECTED ENDPOINTS:
{endpoints_desc}

DETECTED ENTITY MODELS:
{models_desc}

ARCHITECTURE:
{data_flow}

REQUIREMENTS:
1. Generate MULTIPLE COMPLETE PlantUML sequence diagrams (@startuml...@enduml)
2. Each diagram shows a realistic {self.domain} workflow:
   - Workflow 1: Main CRUD operation (create/read using detected endpoints)
   - Workflow 2: Complex business operation (e.g., fund transfer, order checkout)
   - Workflow 3: Error/exception handling scenario
3. Use ACTUAL component names from detected models and endpoints
4. Show interactions between: Client → Controller → Service → Repository → Database
5. Include data transformations (request DTO → entity → response DTO)
6. Show realistic business validations and checks specific to {self.domain}

Make each diagram specific to the actual operations your {self.domain} system performs."""

        result = self.agent_llm.call_claude(prompt, max_tokens=3000)
        if result:
            return f"""## Sequence Diagrams

### Key Workflows

{result}"""
        return self._fallback_sequence_diagrams()

    def _fallback_sequence_diagrams(self) -> str:
        """Fallback sequence diagrams."""
        return f"""## Sequence Diagrams

### Main Workflow
```plantuml
@startuml
participant Client
participant API
participant Business
participant Data

Client -> API: Request
API -> Business: Process
Business -> Data: Query
Data --> Business: Result
Business --> API: Response
API --> Client: HTTP 200
@enduml
```"""

    def _build_request_response_diagrams(self) -> str:
        """Build repo-specific request/response payload diagrams."""
        if not self.agent_llm.has_api():
            return self._fallback_request_response_diagrams()

        # Extract actual endpoints and models
        endpoints = self._extract_api_endpoints()[:2]
        models = self._extract_entity_models()[:3]

        endpoints_desc = "\n".join([f"  - {e['method']} {e['path']}: from {e['controller']}" for e in endpoints]) if endpoints else "  - Multiple REST endpoints"

        models_desc = ""
        for m in models[:2]:
            fields = ", ".join([f"{f['name']}: {f['type']}" for f in m['fields']])
            models_desc += f"  - {m['name']}: {{{fields}}}\n"

        if not models_desc:
            models_desc = "  - Domain entities and DTOs"

        prompt = f"""
Generate REPOSITORY-SPECIFIC request/response payload examples for this {self.domain} application.

DETECTED API ENDPOINTS:
{endpoints_desc}

DETECTED DATA MODELS:
{models_desc}

Domain: {self.domain}

REQUIREMENTS:
1. Create detailed JSON schema diagrams or request/response examples for the actual endpoints above
2. Show realistic payload structures based on detected models
3. Include 2-3 different endpoint examples:
   - GET endpoint request/response
   - POST/CREATE endpoint with full payload
   - Error response example
4. Use actual entity and field names from your models
5. Make payloads realistic for a {self.domain} system
6. Include HTTP status codes and response headers where relevant
7. Add comments explaining key fields

Format as code blocks with actual JSON examples, not diagrams. Be specific to the detected models and endpoints."""

        result = self.agent_llm.call_claude(prompt, max_tokens=2500)
        if result:
            return f"""## Request/Response Examples

### API Payload Structures

{result}"""
        return self._fallback_request_response_diagrams()

    def _fallback_request_response_diagrams(self) -> str:
        """Fallback request/response diagrams."""
        return f"""## Request/Response Examples

### Create {self.domain} Entity
```json
POST /api/resources
Content-Type: application/json

{{
  "id": "RES-001",
  "name": "Resource Name",
  "description": "Resource Description",
  "status": "ACTIVE",
  "createdAt": "2024-01-01T00:00:00Z"
}}

HTTP/1.1 201 Created
{{
  "id": "RES-001",
  "name": "Resource Name",
  "status": "ACTIVE",
  "links": {{
    "self": "/api/resources/RES-001"
  }}
}}
```

### Retrieve {self.domain} Entity
```json
GET /api/resources/RES-001

HTTP/1.1 200 OK
{{
  "id": "RES-001",
  "name": "Resource Name",
  "description": "Resource Description",
  "status": "ACTIVE",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-02T00:00:00Z"
}}
```

### Error Response
```json
HTTP/1.1 400 Bad Request
{{
  "error": "VALIDATION_ERROR",
  "message": "Invalid request payload",
  "details": [
    {{
      "field": "name",
      "error": "Name is required"
    }}
  ]
}}
```"""

    def _build_functional_requirements(self) -> str:
        """Build functional requirements."""
        if not self.agent_llm.has_api():
            return self._fallback_functional_requirements()

        prompt = f"""
List 8-10 functional requirements for a {self.domain} application.

Each requirement should:
1. Start with FR### (FR001, FR002, etc.)
2. Have a clear title
3. Include brief description
4. Be specific to {self.domain}

Format as markdown bullet points."""

        result = self.agent_llm.call_claude(prompt, max_tokens=1500)
        if result:
            return f"""## Functional Requirements

{result}"""
        return self._fallback_functional_requirements()

    def _fallback_functional_requirements(self) -> str:
        """Fallback functional requirements."""
        if self.domain == 'banking':
            reqs = """
- FR001: Users can create and manage accounts
- FR002: Fund transfers between accounts with validation
- FR003: Transaction history and reporting
- FR004: Payment processing and confirmation
- FR005: Account balance inquiry"""
        elif self.domain == 'ecommerce':
            reqs = """
- FR001: Product catalog management
- FR002: Shopping cart functionality
- FR003: Order creation and tracking
- FR004: Payment processing
- FR005: Product reviews and ratings"""
        else:
            reqs = """
- FR001: User authentication and authorization
- FR002: Resource creation and management
- FR003: Data persistence and retrieval
- FR004: System operations execution
- FR005: Audit logging"""

        return f"""## Functional Requirements

{reqs}"""

    def _build_business_rules(self) -> str:
        """Build business rules section with ACTUAL repo-specific rules."""
        # Try to load from artifact
        business_rules_artifact = self._load_artifact("business_rules")

        if business_rules_artifact and "rules" in business_rules_artifact:
            rules = business_rules_artifact.get("rules", [])
            if rules:
                content = f"""## Business Rules

Total Rules Identified: {len(rules)}

### Rule Categories
"""
                # Organize rules by category
                categories = {}
                for rule in rules:
                    cat = rule.get("category", "other")
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(rule)

                for cat, cat_rules in sorted(categories.items()):
                    content += f"\n### {cat.title()} ({len(cat_rules)} rules)\n"
                    for rule in cat_rules[:3]:  # Show first 3 of each category
                        content += f"\n**{rule.get('id', 'N/A')}: {rule.get('title', 'N/A')}**\n"
                        content += f"- Description: {rule.get('description', 'N/A')}\n"
                        content += f"- Applies to: {rule.get('applies_to', 'N/A')}\n"
                        content += f"- Priority: {rule.get('priority', 'N/A')}\n"

                return content

        # Fallback to generic if no artifact found
        return f"""## Business Rules

Business rules are defined in `business_rules.json` artifact.
Key rule categories:
- Validation Rules
- Constraint Rules
- Workflow Rules
- Security Rules
- Performance Rules"""

    def _build_user_journeys(self) -> str:
        """Build user journeys section."""
        return f"""## User Journeys

User journeys for this {self.domain} system are defined in `journey_map.json` artifact.
Main actors identified:
- End Users
- Administrators
- System Integrations"""

    def _build_non_functional_requirements(self) -> str:
        """Build non-functional requirements."""
        return f"""## Non-Functional Requirements

### Performance
- Response Time: < 500ms for API endpoints
- Throughput: Support 1000+ concurrent users
- Availability: 99.9% uptime

### Security
- Authentication: OAuth2/JWT
- Authorization: Role-based access control (RBAC)
- Data Encryption: TLS for transit, AES for storage
- Audit Logging: All transactions logged

### Scalability
- Horizontal scaling support
- Load balancing ready
- Database optimization indexed

### Maintainability
- Code documentation
- Unit test coverage > 80%
- CI/CD pipeline integration"""

    def _build_acceptance_criteria(self) -> str:
        """Build acceptance criteria section with ACTUAL repo-specific criteria."""
        # Try to load from artifact
        ac_artifact = self._load_artifact("acceptance_criteria")

        if ac_artifact and "acceptance_criteria" in ac_artifact:
            criteria = ac_artifact.get("acceptance_criteria", [])
            total_criteria = len(criteria)

            if total_criteria > 0:
                # Organize by type
                positive = [c for c in criteria if c.get("type") == "positive"]
                negative = [c for c in criteria if c.get("type") == "negative"]
                boundary = [c for c in criteria if c.get("type") == "boundary"]

                content = f"""## Acceptance Criteria

Total Test Scenarios: {total_criteria}
- Positive Cases: {len(positive)}
- Negative Cases: {len(negative)}
- Boundary Cases: {len(boundary)}

### Sample Test Scenarios
"""
                # Show a few scenarios from each type
                for test_type, tests in [("Positive", positive), ("Negative", negative), ("Boundary", boundary)]:
                    if tests:
                        content += f"\n#### {test_type} Test Cases\n"
                        for test in tests[:2]:
                            content += f"\n**{test.get('id', 'N/A')}: {test.get('scenario', 'N/A')}**\n"
                            content += f"- Given: {test.get('given', 'N/A')}\n"
                            content += f"- When: {test.get('when', 'N/A')}\n"
                            content += f"- Then: {test.get('then', 'N/A')}\n"
                            if test.get('coverage'):
                                content += f"- Coverage: {test.get('coverage', 'N/A')}\n"

                return content

        # Fallback to generic if no artifact found
        return f"""## Acceptance Criteria

Detailed acceptance criteria are in `acceptance_criteria.json` artifact.
Key areas tested:
- API endpoint functionality
- Business logic correctness
- Data persistence integrity
- Security controls
- Performance benchmarks"""

    def _build_risk_assessment(self) -> str:
        """Build risk assessment section with ACTUAL repo-specific risks."""
        # Try to load from artifact
        risk_register_artifact = self._load_artifact("risk_register")

        if risk_register_artifact and "risks" in risk_register_artifact:
            risks = risk_register_artifact.get("risks", [])
            risk_summary = risk_register_artifact.get("risk_summary", {})

            if risks:
                content = f"""## Risk Assessment

### Risk Summary
- **CRITICAL Risks**: {risk_summary.get('CRITICAL', 0)}
- **HIGH Risks**: {risk_summary.get('HIGH', 0)}
- **MEDIUM Risks**: {risk_summary.get('MEDIUM', 0)}
- **LOW Risks**: {risk_summary.get('LOW', 0)}

### Critical & High Priority Risks
"""
                # Show critical and high risks
                critical_high = [r for r in risks if r.get("severity") in ["CRITICAL", "HIGH"]]
                for risk in critical_high[:6]:
                    content += f"\n**{risk.get('id', 'N/A')}: {risk.get('title', 'N/A')}**\n"
                    content += f"- Category: {risk.get('category', 'N/A')}\n"
                    content += f"- Severity: {risk.get('severity', 'N/A')}\n"
                    content += f"- Description: {risk.get('description', 'N/A')}\n"
                    content += f"- Mitigation: {risk.get('mitigation', 'N/A')}\n"
                    if risk.get('timeline'):
                        content += f"- Timeline: {risk.get('timeline', 'N/A')}\n"

                return content

        # Fallback to generic if no artifact found
        return f"""## Risk Assessment

### High Priority Risks
- Security: Unauthorized access prevention
- Data: Data consistency and integrity
- Performance: Response time SLAs

### Mitigation Strategies
- Security: Implement RBAC and encryption
- Data: Transaction management and backups
- Performance: Caching and indexing strategies"""

    def _build_gap_analysis(self) -> str:
        """Build gap analysis section with ACTUAL repo-specific gaps."""
        # Try to load from artifact
        gap_analysis_artifact = self._load_artifact("gap_analysis")

        if gap_analysis_artifact and "gaps" in gap_analysis_artifact:
            gaps = gap_analysis_artifact.get("gaps", [])
            total_gaps = len(gaps)

            if total_gaps > 0:
                content = f"""## Gap Analysis

Total Gaps Identified: {total_gaps}

### Gap Summary by Category
"""
                # Organize gaps by category
                categories = {}
                for gap in gaps:
                    cat = gap.get("category", "other")
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(gap)

                for cat, cat_gaps in sorted(categories.items()):
                    content += f"\n#### {cat} ({len(cat_gaps)} gap(s))\n"

                # Show high severity gaps first
                content += "\n### High Priority Gaps\n"
                high_severity = [g for g in gaps if g.get("severity") in ["high", "CRITICAL", "HIGH"]]
                for gap in high_severity[:5]:
                    content += f"\n**{gap.get('id', 'N/A')}: {gap.get('description', 'N/A')}**\n"
                    content += f"- Severity: {gap.get('severity', 'N/A')}\n"
                    content += f"- Impact: {gap.get('impact', 'N/A')}\n"
                    if gap.get('effort'):
                        content += f"- Effort: {gap.get('effort', 'N/A')}\n"

                return content

        # Fallback to generic if no artifact found
        return f"""## Gap Analysis

Gap analysis details are in `gap_analysis.json` artifact.
Areas analyzed:
- Architecture completeness
- Technology stack coverage
- Test coverage gaps
- Documentation gaps
- Security posture gaps"""

    def _build_recommendations(self) -> str:
        """Build recommendations section."""
        if not self.agent_llm.has_api():
            return self._fallback_recommendations()

        prompt = f"""
Generate 5-8 recommendations for improving a {self.domain} application with {self.signals['java_class_patterns'].get('Service', 0)} services.

Recommendations should cover:
1. Architecture improvements
2. Performance optimizations
3. Security enhancements
4. Code quality improvements
5. Testing strategy
6. Operational improvements

Format as numbered list with brief explanation for each."""

        result = self.agent_llm.call_claude(prompt, max_tokens=1500)
        if result:
            return f"""## Recommendations

{result}"""
        return self._fallback_recommendations()

    def _fallback_recommendations(self) -> str:
        """Fallback recommendations."""
        return f"""## Recommendations

1. **Caching Strategy**: Implement Redis caching for frequently accessed data
2. **API Documentation**: Generate OpenAPI/Swagger documentation automatically
3. **Monitoring**: Add distributed tracing and metrics collection
4. **Security**: Implement API rate limiting and request validation
5. **Testing**: Increase test coverage to 85%+
6. **Documentation**: Add architecture decision records (ADRs)
7. **Performance**: Profile and optimize slow query paths"""
