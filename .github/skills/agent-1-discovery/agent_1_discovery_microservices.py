#!/usr/bin/env python3
"""
Agent 1: Discovery & Scoping — MICROSERVICES-AWARE VERSION
Detects microservices architecture and generates service-specific outputs.
For microservices: generates individual scope, actors, gaps per service.
For monoliths: generates single comprehensive scope.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kb_gen.utils.agent_llm import AgentLLM
from kb_gen.utils.microservices_analyzer import MicroservicesAnalyzer
from kb_gen.utils.repo_signals import RepoSignals


class LLMDiscoveryAgentMicroservices:
    """LLM-powered discovery agent with microservices support."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.signals = self.agent_llm.repo_signals.get_all_signals()
        self.timestamp = datetime.now().isoformat()

        # Microservices analysis
        self.ms_analyzer = MicroservicesAnalyzer(str(self.repo_path))
        self.ms_analysis = self.ms_analyzer.analyze()

    def run(self) -> Dict[str, Any]:
        """Execute discovery."""
        print(f"\n{'='*60}")
        print("Agent 1: Discovery & Scoping (Microservices-Aware)")
        print(f"{'='*60}")
        print(f"Repository: {self.repo_name}")
        print(f"Microservices: {self.ms_analysis['is_microservices']}")

        outputs = {}

        try:
            if self.ms_analysis["is_microservices"]:
                print(f"\n[Microservices Mode] Analyzing {len(self.ms_analysis['services'])} services...")
                outputs = self._generate_microservices_outputs()
            else:
                print("\n[Monolith Mode] Analyzing single application...")
                outputs = self._generate_monolith_outputs()

            self._write_outputs(outputs)

            print(f"\n{'='*60}")
            print("[OK] Discovery Complete!")
            print(f"{'='*60}\n")

            return {
                "status": "success",
                "is_microservices": self.ms_analysis["is_microservices"],
                "outputs": len(outputs),
            }

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def _generate_microservices_outputs(self) -> Dict[str, Any]:
        """Generate outputs for microservices architecture."""
        outputs = {}

        # Generate service inventory
        print("[1/5] Generating service_inventory.json...")
        outputs["service_inventory"] = self._generate_service_inventory()

        # Generate service-specific scope definitions
        print("[2/5] Generating service-specific scopes...")
        for service_name in self.ms_analysis["services"]:
            print(f"  - {service_name}")
            scope_key = f"scope_{service_name.replace('-', '_')}"
            outputs[scope_key] = self._generate_service_scope(service_name)

        # Generate service-specific actors
        print("[3/5] Generating service-specific actors...")
        for service_name in self.ms_analysis["services"]:
            actors_key = f"actors_{service_name.replace('-', '_')}"
            outputs[actors_key] = self.ms_analyzer.get_service_specific_actors(service_name)

        # Generate service-specific gaps
        print("[4/5] Generating service-specific gaps...")
        for service_name in self.ms_analysis["services"]:
            gaps_key = f"gaps_{service_name.replace('-', '_')}"
            outputs[gaps_key] = self.ms_analyzer.get_service_specific_gaps(service_name)

        # Generate overall architecture overview
        print("[5/5] Generating architecture_overview.json...")
        outputs["architecture_overview"] = self._generate_architecture_overview()

        return outputs

    def _generate_monolith_outputs(self) -> Dict[str, Any]:
        """Generate outputs for monolithic application."""
        outputs = {}

        print("[1/3] Generating scope_definition.json...")
        outputs["scope_definition"] = self._generate_monolith_scope()

        print("[2/3] Generating actors.json...")
        outputs["actors"] = self._generate_monolith_actors()

        print("[3/3] Generating artifact_catalog.json...")
        outputs["artifact_catalog"] = self._generate_artifact_catalog()

        return outputs

    def _generate_service_inventory(self) -> Dict[str, Any]:
        """Generate inventory of all microservices."""
        services_list = []

        for service_name, service_info in self.ms_analysis["services"].items():
            services_list.append({
                "name": service_name,
                "purpose": service_info["purpose"],
                "components": {
                    "controllers": service_info["controllers"],
                    "services": service_info["services"],
                    "repositories": service_info["repositories"],
                    "entities": service_info["entities"],
                },
                "java_files": len(service_info["java_files"]),
                "actors": len(service_info["actors"]),
            })

        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "is_microservices": True,
            "total_services": len(services_list),
            "services": services_list,
        }

    def _generate_service_scope(self, service_name: str) -> Dict[str, Any]:
        """Generate scope for individual service."""
        service_scope = self.ms_analyzer.get_service_specific_scope(service_name)

        if not self.agent_llm.has_api():
            return service_scope

        # Enhance with Claude
        service_info = self.ms_analysis["services"][service_name]
        prompt = f"""
Generate a detailed scope definition for the {service_name} microservice.

Service Purpose: {service_info['purpose']}
Components:
  - Controllers: {service_info['controllers']}
  - Services: {service_info['services']}
  - Repositories: {service_info['repositories']}
  - Entities: {service_info['entities']}

Generate a JSON scope with:
- description: Detailed service description
- responsibilities: What this service is responsible for
- dependencies: Services it depends on
- apis: REST endpoints it provides
- data_model: Key entities it manages

Make it specific to {service_name}."""

        result = self.agent_llm.generate_json_output(prompt)

        if result:
            service_scope.update(result)
            service_scope["llm_enhanced"] = True

        return service_scope

    def _generate_architecture_overview(self) -> Dict[str, Any]:
        """Generate overall microservices architecture overview."""
        if not self.agent_llm.has_api():
            return self._fallback_architecture_overview()

        services_names = list(self.ms_analysis["services"].keys())
        prompt = f"""
Generate a microservices architecture overview for this system.

Services: {', '.join(services_names)}

Generate JSON with:
- architecture_pattern: How services communicate
- service_mesh: Service-to-service communication style
- api_gateway: How external clients access services
- data_consistency: How data consistency is maintained
- recommended_tools: Recommended monitoring/logging tools

Make it specific to these services."""

        result = self.agent_llm.generate_json_output(prompt)

        return result if result else self._fallback_architecture_overview()

    def _fallback_architecture_overview(self) -> Dict[str, Any]:
        """Fallback architecture overview."""
        services_names = list(self.ms_analysis["services"].keys())
        return {
            "repository": self.repo_name,
            "is_microservices": True,
            "architecture_pattern": "Spring Cloud Microservices",
            "services": services_names,
            "communication": "REST/Reactive via Spring Cloud Gateway",
            "service_discovery": "Eureka (Spring Cloud Netflix)",
            "configuration_management": "Spring Cloud Config Server",
            "api_gateway": "Spring Cloud Gateway",
        }

    def _generate_monolith_scope(self) -> Dict[str, Any]:
        """Generate scope for monolithic application."""
        if not self.agent_llm.has_api():
            return self._fallback_monolith_scope()

        prompt = f"""
Generate comprehensive scope for this monolithic Java application.

Frameworks: {', '.join(self.signals.get('frameworks', []))}
Controllers: {self.signals['java_class_patterns'].get('Controller', 0)}
Services: {self.signals['java_class_patterns'].get('Service', 0)}
LOC: {self.signals.get('loc', 0):,}

Generate scope JSON with:
- description: What the application does
- primary_purpose: Main business purpose
- key_features: Core features
- architecture_layers: How it's organized"""

        result = self.agent_llm.generate_json_output(prompt)

        if result:
            result["repository"] = self.repo_name
            return result

        return self._fallback_monolith_scope()

    def _fallback_monolith_scope(self) -> Dict[str, Any]:
        """Fallback monolith scope."""
        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "is_microservices": False,
            "scope_summary": {
                "description": f"Monolithic {self.repo_name} application",
                "primary_language": "Java",
                "frameworks": self.signals.get('frameworks', []),
                "total_classes": sum(self.signals['java_class_patterns'].values()),
            },
        }

    def _generate_monolith_actors(self) -> Dict[str, Any]:
        """Generate realistic actors for monolithic app."""
        if not self.agent_llm.has_api():
            return self._fallback_monolith_actors()

        prompt = f"""
Generate realistic user/system actors for this Java application.

Domain clues from packages: {', '.join(self.signals.get('main_packages', [])[:5])}

Generate JSON with actors array containing:
- name: Actor name
- role: Actor role (user, admin, system)
- description: What they do

Create 5-7 realistic actors specific to the domain."""

        result = self.agent_llm.generate_json_output(prompt)

        if result:
            result["repository"] = self.repo_name
            return result

        return self._fallback_monolith_actors()

    def _fallback_monolith_actors(self) -> Dict[str, Any]:
        """Fallback monolith actors."""
        return {
            "repository": self.repo_name,
            "actors": [
                {"name": "End User", "role": "user", "description": "Primary system user"},
                {"name": "Administrator", "role": "admin", "description": "System administrator"},
                {"name": "API Consumer", "role": "system", "description": "External systems"},
            ],
        }

    def _generate_artifact_catalog(self) -> Dict[str, Any]:
        """Generate artifact catalog."""
        java_files = self.signals.get("java_files", [])

        return {
            "repository": self.repo_name,
            "generated_at": self.timestamp,
            "total_artifacts": len(java_files),
            "by_type": {
                "controllers": self.signals['java_class_patterns'].get('Controller', 0),
                "services": self.signals['java_class_patterns'].get('Service', 0),
                "repositories": self.signals['java_class_patterns'].get('Repository', 0),
                "entities": self.signals['java_class_patterns'].get('Entity', 0),
            },
            "packages": len(self.signals.get("main_packages", [])),
        }

    def _write_outputs(self, outputs: Dict[str, Any]):
        """Write outputs to JSON files."""
        for name, data in outputs.items():
            filepath = self.output_path / f"{name}.json"
            filepath.write_text(json.dumps(data, indent=2))
            print(f"  [OK] Wrote {filepath.name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent 1: Microservices-Aware Discovery")
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("--output", help="Output path", default=None)
    parser.add_argument("--api-key", help="API key", default=None)

    args = parser.parse_args()

    agent = LLMDiscoveryAgentMicroservices(args.repo_path, args.output, args.api_key)
    result = agent.run()

    sys.exit(0 if result.get("status") == "success" else 1)
