#!/usr/bin/env python3
"""
Agent 6: Acceptance Criteria — LLM-POWERED VERSION
Generates acceptance criteria for system features.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kb_gen.utils.agent_llm import AgentLLM

# Tools used by this agent
TOOLS_USED = [
    "Criteria Generator",
    "Gherkin Converter",
    "Test Case Builder",
    "Scenario Mapper",
    "Validator",
]

class LLMAcceptanceCriteriaAgent:
    """LLM-powered acceptance criteria agent."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.timestamp = datetime.now().isoformat()

    def run(self) -> Dict[str, Any]:
        """Execute acceptance criteria generation."""
        print(f"\n{'='*60}")
        print("Agent 6: LLM-Powered Acceptance Criteria")
        print(f"{'='*60}")

        outputs = {}

        try:
            print("[1/4] Generating acceptance_criteria.json...")
            outputs["acceptance_criteria"] = self._generate_acceptance_criteria()

            print("[2/4] Generating acceptance_criteria_gherkin.json...")
            outputs["acceptance_criteria_gherkin"] = self._generate_gherkin_criteria()

            print("[3/4] Generating test_case_analysis.json...")
            outputs["test_case_analysis"] = self._generate_test_case_analysis()

            print("[4/4] Generating acceptance_criteria.feature...")
            outputs["acceptance_criteria_feature"] = self._generate_feature_file()

            self._write_outputs(outputs)
            
            # Print tools used
            tools_str = ", ".join(TOOLS_USED)
            print(f"\nGenerated {len(outputs)} output files")
            print(f"🔧 Tools used for acceptance-criteria: {tools_str}")
            print(f"\n{'='*60}\n[OK] Acceptance Criteria Complete!\n{'='*60}\n")
            return outputs
        except Exception as e:
            print(f"ERROR: {e}")
            return {}

    def _generate_acceptance_criteria(self) -> Dict[str, Any]:
        """Generate acceptance_criteria.json using LLM with repo-specific domain context."""
        signals = self.agent_llm.repo_signals.get_all_signals()

        if not self.agent_llm.has_api():
            return self._fallback_acceptance_criteria(signals)

        prompt = f"""
You are a QA expert. Based on this repository's architecture and business domain,
generate SPECIFIC acceptance criteria that reflect REAL business scenarios.

REPOSITORY DOMAIN ANALYSIS:
- Repository Name: {self.repo_name}
- Frameworks: {', '.join(signals['frameworks']) if signals['frameworks'] else 'Not detected'}
- Architecture: Analyze packages to infer domain
- Main Packages: {', '.join(signals['main_packages'][:5])}

COMPONENT STRUCTURE:
- Controllers: {signals['java_class_patterns'].get('Controller', 0)}
- Services: {signals['java_class_patterns'].get('Service', 0)}
- Repositories: {signals['java_class_patterns'].get('Repository', 0)}
- Entities: {signals['java_class_patterns'].get('Entity', 0)}

DETECTED FRAMEWORKS & TECHNOLOGIES:
{self._format_tech_stack(signals)}

Based on the domain (inferred from package names: {self._infer_domain(signals['main_packages'])}),
generate 5-8 domain-specific acceptance criteria (NOT generic ones).

For each criterion include:
- id: AC00X
- title: Specific to domain (e.g., if banking: "Fund Transfer Authorization")
- description: Clear, business-focused description
- given/when/then: Gherkin format with real business scenarios
- acceptance_criteria: 4-5 specific acceptance checks relevant to the business domain
- priority: high/medium/low
- component: Affected component

Return VALID JSON with "criteria" array. Make each criterion unique to this repository's business purpose.
"""

        result = self.agent_llm.generate_json_output(prompt)

        if not result or not result.get('criteria'):
            return self._fallback_acceptance_criteria(signals)

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "total_criteria": len(result.get('criteria', [])),
            "criteria": result.get('criteria', []),
            "detected_components": {
                "controllers": signals['java_class_patterns'].get('Controller', 0),
                "services": signals['java_class_patterns'].get('Service', 0),
                "repositories": signals['java_class_patterns'].get('Repository', 0),
                "entities": signals['java_class_patterns'].get('Entity', 0),
                "mappers": signals['java_class_patterns'].get('Mapper', 0),
            },
            "confidence": 0.9 if result else 0.6,
            "inferred_domain": self._infer_domain(signals['main_packages']),
        }

    def _infer_domain(self, packages: list) -> str:
        """Infer business domain from package names."""
        domain_keywords = {
            'banking': ['bank', 'finance', 'transaction', 'transfer', 'payment', 'account'],
            'ecommerce': ['store', 'shop', 'product', 'cart', 'order', 'purchase', 'catalog'],
            'healthcare': ['patient', 'doctor', 'appointment', 'medical', 'health', 'clinic'],
            'library': ['book', 'library', 'member', 'lending', 'catalog'],
            'inventory': ['inventory', 'stock', 'warehouse', 'product', 'sku'],
            'user_management': ['user', 'profile', 'account', 'auth', 'permission'],
        }

        package_text = ' '.join(packages).lower()

        for domain, keywords in domain_keywords.items():
            if any(kw in package_text for kw in keywords):
                return domain

        return 'general-application'

    def _format_tech_stack(self, signals) -> str:
        """Format technology stack info for prompt."""
        frameworks = signals.get('frameworks', [])
        if not frameworks:
            return "- No specific frameworks detected"
        return "\n".join([f"- {fw}" for fw in frameworks])

    def _fallback_acceptance_criteria(self, signals: Dict) -> Dict[str, Any]:
        """Fallback: Generate minimum viable criteria based on pattern analysis."""
        patterns = signals['java_class_patterns']
        domain = self._infer_domain(signals['main_packages'])

        criteria = []

        if patterns.get('Controller', 0) > 0:
            criteria.append({
                "id": "AC001",
                "title": f"{domain.title()} API Request Handling",
                "description": f"System with {patterns['Controller']} controller(s) handles requests",
                "given": f"System with {patterns['Controller']} endpoint(s) operational",
                "when": "Valid request received",
                "then": "Request processed correctly",
                "acceptance_criteria": [
                    "✓ Request validated",
                    "✓ Response status 2xx",
                    "✓ Response body correct",
                    "✓ Response time < 500ms"
                ],
                "priority": "high",
                "component": "Controller"
            })

        if patterns.get('Service', 0) > 0:
            criteria.append({
                "id": "AC002",
                "title": f"{domain.title()} Business Logic",
                "description": f"System with {patterns['Service']} service(s) executes correctly",
                "given": f"System with {patterns['Service']} service(s) configured",
                "when": "Business operation invoked",
                "then": "Service executes with correct results",
                "acceptance_criteria": [
                    "✓ Services execute without errors",
                    "✓ Business rules enforced",
                    "✓ Data consistent",
                    "✓ Transactions handled correctly"
                ],
                "priority": "high",
                "component": "Service"
            })

        if patterns.get('Repository', 0) > 0:
            criteria.append({
                "id": "AC003",
                "title": f"{domain.title()} Data Persistence",
                "description": f"System with {patterns['Repository']} repository(ies) persists data",
                "given": f"System with {patterns['Repository']} repository(ies)",
                "when": "Save/Update/Delete triggered",
                "then": "Data persisted correctly",
                "acceptance_criteria": [
                    f"✓ {patterns['Repository']} repository(ies) successful",
                    "✓ Data written correctly",
                    "✓ Constraints maintained",
                    "✓ Transactions committed"
                ],
                "priority": "high",
                "component": "Repository"
            })

        if patterns.get('Entity', 0) > 0:
            criteria.append({
                "id": "AC004",
                "title": f"{domain.title()} Entity Management",
                "description": f"System with {patterns['Entity']} entity/entities manages domain objects",
                "given": f"System with {patterns['Entity']} domain entity/entities",
                "when": "Entity state is modified or created",
                "then": "Entity maintains valid state and enforces invariants",
                "acceptance_criteria": [
                    f"✓ {patterns['Entity']} entity/entities created successfully",
                    "✓ All required fields are present",
                    "✓ Field values are within valid ranges",
                    "✓ Entity relationships are maintained"
                ],
                "priority": "high",
                "component": "Entity"
            })

        # AC005: Data Transformation
        if patterns.get('Mapper', 0) > 0:
            criteria.append({
                "id": "AC005",
                "title": f"{domain.title()} Data Transformation",
                "description": f"System with {patterns['Mapper']} mapper(s) transforms data between layers",
                "given": f"System with {patterns['Mapper']} mapper(s) for data transformation",
                "when": "Entity is mapped to DTO or vice versa",
                "then": "All fields are mapped correctly with no data loss",
                "acceptance_criteria": [
                    f"✓ {patterns['Mapper']} mapper(s) transform data correctly",
                    "✓ All fields are mapped to destination object",
                    "✓ Type conversions are correct",
                    "✓ Null values are handled appropriately"
                ],
                "priority": "medium",
                "component": "Mapper"
            })

        # AC006: Authentication & Authorization
        criteria.append({
            "id": "AC006",
            "title": "Authentication & Authorization",
            "description": "System verifies user identity and permissions",
            "given": "System is running with security enabled",
            "when": "User attempts to access protected resource",
            "then": "System validates authentication and authorization",
            "acceptance_criteria": [
                "✓ Valid credentials are accepted",
                "✓ Invalid credentials are rejected",
                "✓ Unauthorized access returns 403 Forbidden",
                "✓ Unauthenticated access returns 401 Unauthorized",
                "✓ Role-based access control works"
            ],
            "priority": "high",
            "component": "Security"
        })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "total_criteria": len(criteria),
            "criteria": criteria,
            "detected_components": {
                "controllers": controllers,
                "services": services,
                "repositories": repos,
                "entities": entities,
                "mappers": mappers
            },
            "confidence": 0.85 if len(criteria) > 3 else 0.75
        }

    def _generate_gherkin_criteria(self) -> Dict[str, Any]:
        """Generate acceptance_criteria_gherkin.json using LLM with domain context."""
        signals = self.agent_llm.repo_signals.get_all_signals()
        patterns = signals['java_class_patterns']
        domain = self._infer_domain(signals['main_packages'])

        if not self.agent_llm.has_api():
            return self._fallback_gherkin_scenarios(patterns, domain)

        prompt = f"""
Generate GHERKIN-FORMATTED scenarios (BDD format) specific to this {domain} system.
Do NOT generate generic scenarios - make them business-relevant.

DOMAIN: {domain}
COMPONENTS:
- Controllers: {patterns.get('Controller', 0)}
- Services: {patterns.get('Service', 0)}
- Repositories: {patterns.get('Repository', 0)}
- Entities: {patterns.get('Entity', 0)}

Generate 4-6 realistic business scenarios in Gherkin format.
Each scenario should include: Feature, Scenario name, Given/When/Then steps.

Return valid JSON with "scenarios" array containing objects with:
- id: SC001, SC002, etc
- feature: Feature name
- scenario: Scenario title
- given: Given condition
- when: Action
- then: Expected result
- context: Business context explanation

Make scenarios specific to {domain} domain (e.g., if banking, use fund transfer scenarios).
"""

        result = self.agent_llm.generate_json_output(prompt)

        if not result or not result.get('scenarios'):
            return self._fallback_gherkin_scenarios(patterns, domain)

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "domain": domain,
            "detected_components": {
                "controllers": patterns.get('Controller', 0),
                "services": patterns.get('Service', 0),
                "repositories": patterns.get('Repository', 0),
            },
            "scenarios": result.get('scenarios', []),
            "total_scenarios": len(result.get('scenarios', [])),
            "confidence": 0.9 if result else 0.75,
        }

    def _fallback_gherkin_scenarios(self, patterns: Dict, domain: str) -> Dict[str, Any]:
        """Fallback Gherkin scenarios based on pattern analysis."""
        scenarios = []

        if patterns.get('Controller', 0) > 0:
            scenarios.append({
                "id": "SC001",
                "feature": f"{domain.title()} API",
                "scenario": "Valid API request",
                "given": f"System with {patterns['Controller']} controller(s) running",
                "when": "Valid HTTP request received",
                "then": "Request processed successfully",
                "context": "User interacts with system API"
            })

        if patterns.get('Service', 0) > 0:
            scenarios.append({
                "id": "SC002",
                "feature": f"{domain.title()} Business Logic",
                "scenario": "Execute business operation",
                "given": f"System with {patterns['Service']} service(s) configured",
                "when": f"Business operation invoked",
                "then": "Operation completes with correct result",
                "context": "Service layer applies business rules"
            })

        if patterns.get('Repository', 0) > 0:
            scenarios.append({
                "id": "SC003",
                "feature": f"{domain.title()} Data Management",
                "scenario": "Persist data to database",
                "given": f"System with {patterns['Repository']} repository(ies)",
                "when": "Save/Update operation triggered",
                "then": "Data persisted and retrievable",
                "context": "Repository layer handles data persistence"
            })

        if not scenarios:
            scenarios = [{
                "id": "SC001",
                "feature": "System Operation",
                "scenario": "Basic operation",
                "given": "System is initialized",
                "when": "User interacts with system",
                "then": "System responds appropriately",
                "context": "Basic user interaction"
            }]

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "domain": domain,
            "scenarios": scenarios,
            "total_scenarios": len(scenarios),
            "confidence": 0.75,
        }

    def _generate_test_case_analysis(self) -> Dict[str, Any]:
        """Generate test_case_analysis.json using LLM."""
        signals = self.agent_llm.repo_signals.get_all_signals()
        patterns = signals['java_class_patterns']
        java_files = signals.get('java_files', [])
        test_files = [f for f in java_files if 'Test' in f]
        domain = self._infer_domain(signals['main_packages'])

        if not self.agent_llm.has_api():
            return self._fallback_test_case_analysis(patterns, test_files, domain)

        prompt = f"""
Analyze this {domain} system architecture and recommend test strategy.

ARCHITECTURE:
- Controllers: {patterns.get('Controller', 0)}
- Services: {patterns.get('Service', 0)}
- Repositories: {patterns.get('Repository', 0)}
- Existing test files: {len(test_files)}

Generate a JSON response with:
- test_cases array with: type (unit/integration/e2e), layer (controller/service/repository), count, description
- coverage_gaps: Missing test areas
- recommended_tests: Specific tests for this {domain} domain
- total_layers_tested: Number of layers that need testing

Be specific to {domain} domain when suggesting tests.
"""

        result = self.agent_llm.generate_json_output(prompt)

        if not result or not result.get('test_cases'):
            return self._fallback_test_case_analysis(patterns, test_files, domain)

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "domain": domain,
            "test_files_found": len(test_files),
            "test_cases": result.get('test_cases', []),
            "coverage_gaps": result.get('coverage_gaps', []),
            "recommended_tests": result.get('recommended_tests', []),
            "total_layers_tested": len(result.get('test_cases', [])),
            "coverage": min(0.5 + (len(test_files) * 0.1), 0.95),
            "confidence": 0.9 if result else 0.75,
        }

    def _fallback_test_case_analysis(self, patterns: Dict, test_files: list, domain: str) -> Dict[str, Any]:
        """Fallback test case analysis."""
        test_cases = []

        if patterns.get('Controller', 0) > 0:
            test_cases.append({
                "type": "integration",
                "layer": "controller",
                "count": patterns.get('Controller', 0),
                "description": f"Integration tests for {patterns.get('Controller', 0)} controllers"
            })

        if patterns.get('Service', 0) > 0:
            test_cases.append({
                "type": "unit",
                "layer": "service",
                "count": patterns.get('Service', 0),
                "description": f"Unit tests for {patterns.get('Service', 0)} {domain} services"
            })

        if patterns.get('Repository', 0) > 0:
            test_cases.append({
                "type": "integration",
                "layer": "repository",
                "count": patterns.get('Repository', 0),
                "description": f"Repository tests for {patterns.get('Repository', 0)} data access components"
            })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "domain": domain,
            "test_files_found": len(test_files),
            "test_cases": test_cases,
            "coverage": min(0.5 + (len(test_files) * 0.1), 0.95),
            "total_layers_tested": len(test_cases),
            "confidence": 0.7 if test_cases else 0.5,
        }

    def _generate_feature_file(self) -> str:
        """Generate acceptance_criteria.feature file with repo-specific scenarios."""
        signals = self.agent_llm.repo_signals.get_all_signals()
        patterns = signals['java_class_patterns']
        controllers = patterns.get('Controller', 0)
        services = patterns.get('Service', 0)
        repos = patterns.get('Repository', 0)

        features = []

        if controllers > 0:
            features.append(f"""  Feature: REST API Operations
    Background:
      Given the API server is running
      And {controllers} API endpoints are available

    Scenario: Successful API request
      When a valid HTTP request is sent to an endpoint
      Then the server responds with status 200
      And the response contains expected data""")

        if services > 0:
            features.append(f"""  Feature: Service Layer Processing
    Background:
      Given {services} business services are configured

    Scenario: Business logic execution
      When a service operation is invoked
      Then business rules are applied
      And the operation completes successfully""")

        if repos > 0:
            features.append(f"""  Feature: Data Management
    Background:
      Given {repos} data repositories are configured

    Scenario: Data persistence
      When data is submitted for storage
      Then data is persisted to database
      And data can be retrieved correctly""")

        if not features:
            features = [f"""  Scenario: Basic system operation
    Given the system is initialized
    When a request is made
    Then the system responds"""]

        return f"""Feature: {self.repo_name} Acceptance Criteria

{chr(10).join(features)}
"""

    def _write_outputs(self, outputs: Dict[str, Any]):
        """Write outputs to files."""
        for name, data in outputs.items():
            if isinstance(data, str):
                if "feature" in name:
                    filepath = self.output_path / f"acceptance_criteria.feature"
                else:
                    filepath = self.output_path / f"{name}.md"
                filepath.write_text(data)
            else:
                filepath = self.output_path / f"{name}.json"
                filepath.write_text(json.dumps(data, indent=2))
            print(f"  [OK] Wrote {filepath.name}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    parser.add_argument("--output", default=None)
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    agent = LLMAcceptanceCriteriaAgent(args.repo_path, args.output, args.api_key)
    agent.run()
