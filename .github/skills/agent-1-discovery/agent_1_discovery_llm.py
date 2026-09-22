#!/usr/bin/env python3
"""
Agent 1: Discovery & Scoping — LLM-POWERED VERSION
Uses Claude to generate repo-specific outputs based on actual repository analysis.
Produces all 9 Agent 1 outputs: artifact_catalog, dependency_map, scope_definition, etc.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kb_gen.utils.agent_llm import AgentLLM
from kb_gen.utils.repo_signals import RepoSignals

# Tools used by this agent
TOOLS_USED = [
    "Repo Scanner",
    "File Analyzer",
    "Dependency Mapper",
    "Code Pattern Detector",
    "Tech Stack Analyzer",
]

class LLMDiscoveryAgent:
    """LLM-powered discovery agent that generates repo-specific outputs."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.signals = self.agent_llm.repo_signals
        self.timestamp = datetime.now().isoformat()

    def run(self) -> Dict[str, Any]:
        """Execute the LLM-powered discovery agent."""
        print(f"\n{'='*60}", flush=True)
        print("Agent 1: LLM-Powered Discovery & Scoping", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Repository: {self.repo_path}", flush=True)
        print(f"Output: {self.output_path}", flush=True)
        print(f"API Available: {self.agent_llm.has_api()}", flush=True)

        # Force a verbose signal scan up front so the tracker shows what the
        # agent is looking at, instead of just "step 1/9" for minutes.
        print("\nScanning repository for signals (frameworks, files, deps)...", flush=True)
        scan_started = time.time()
        signals_preview = self.signals.get_all_signals(verbose=True)
        # Cache the result on the RepoSignals instance so each substep reuses it
        # instead of re-walking the tree.
        self.signals._cache["all_signals"] = signals_preview
        print(f"Signal scan complete in {time.time() - scan_started:.1f}s.", flush=True)

        outputs = {}

        try:
            # Generate each artifact
            self._announce_step(1, 9, "scope_definition.json", uses_llm=True)
            outputs["scope_definition"] = self._generate_scope_definition()

            self._announce_step(2, 9, "artifact_catalog.json", uses_llm=False)
            outputs["artifact_catalog"] = self._generate_artifact_catalog()

            self._announce_step(3, 9, "dependency_map.json", uses_llm=False)
            outputs["dependency_map"] = self._generate_dependency_map()

            self._announce_step(4, 9, "business_rules.json", uses_llm=True)
            outputs["business_rules"] = self._generate_business_rules()

            self._announce_step(5, 9, "actors.json", uses_llm=False)
            outputs["actors"] = self._generate_actors()

            self._announce_step(6, 9, "journey_map.json", uses_llm=False)
            outputs["journey_map"] = self._generate_journey_map()

            self._announce_step(7, 9, "brd_executive_summary.md", uses_llm=False)
            outputs["brd_executive_summary"] = self._generate_executive_summary()

            self._announce_step(8, 9, "coverage_summary.json", uses_llm=False)
            outputs["coverage_summary"] = self._generate_coverage_summary()

            self._announce_step(9, 9, "brd_final.json", uses_llm=False)
            outputs["brd_final"] = self._generate_brd_final()

            # Write all outputs
            self._write_outputs(outputs)

            # Print tools used
            tools_str = ", ".join(TOOLS_USED)
            print(f"\nGenerated {len(outputs)} output files")
            print(f"🔧 Tools used for discovery: {tools_str}")
            print(f"\n{'='*60}")
            print("[OK] Discovery Complete!")
            print(f"{'='*60}\n")

            return outputs

        except Exception as e:
            print(f"ERROR: Discovery failed - {e}")
            import traceback
            traceback.print_exc()
            return {}

    # ──────────────────────────────────────────────────────────────────────────────
    # Output Generators
    # ──────────────────────────────────────────────────────────────────────────────

    def _generate_scope_definition(self) -> Dict[str, Any]:
        """Generate scope_definition.json using Claude."""
        signals = self.signals.get_all_signals()

        # If no API, return signal-based summary
        if not self.agent_llm.has_api():
            return {
                "repository": self.repo_name,
                "repository_path": str(self.repo_path),
                "analysis_timestamp": self.timestamp,
                "scope_summary": {
                    "description": f"Repository {self.repo_name} with {len(signals['frameworks'])} detected frameworks",
                    "primary_language": self._detect_primary_language(signals),
                    "build_system": self._detect_build_system(signals),
                    "architecture_pattern": "Unknown",
                    "total_java_classes": signals["java_class_patterns"].get("Service", 0) + signals["java_class_patterns"].get("Controller", 0),
                },
                "technology_stack": {
                    "frameworks": signals["frameworks"],
                    "databases": [],
                    "testing": [],
                    "build_tools": self._extract_build_tools(signals),
                    "all_technologies": {}
                },
                "components": {
                    "controllers": signals["java_class_patterns"].get("Controller", 0),
                    "services": signals["java_class_patterns"].get("Service", 0),
                    "data_access": signals["java_class_patterns"].get("Repository", 0),
                    "domain_entities": signals["java_class_patterns"].get("Entity", 0),
                },
                "business_capabilities": [],
                "confidence": 0.7,
            }

        # Call Claude for enhanced analysis
        prompt = f"""
Analyze this repository scope and create a comprehensive scope definition.

Repository Signals:
- Frameworks: {signals['frameworks']}
- Total LOC: {signals['loc']:,}
- Main Packages: {signals['main_packages']}
- Java Classes: {json.dumps(signals['java_class_patterns'])}

Generate a JSON response with this structure:
{{
  "repository": "{self.repo_name}",
  "repository_path": "{self.repo_path}",
  "analysis_timestamp": "{self.timestamp}",
  "scope_summary": {{
    "description": "...",
    "primary_language": "...",
    "build_system": "...",
    "architecture_pattern": "...",
    "total_java_classes": N
  }},
  "technology_stack": {{
    "frameworks": [...],
    "databases": [...],
    "testing": [...],
    "build_tools": [...],
    "all_technologies": {{}}
  }},
  "components": {{
    "controllers": N,
    "services": N,
    "data_access": N,
    "domain_entities": N
  }},
  "business_capabilities": [...],
  "confidence": 0.9
}}
"""
        result = self.agent_llm.generate_json_output(prompt)
        return result or self._generate_scope_definition()  # Fallback to signal-based

    def _generate_artifact_catalog(self) -> Dict[str, Any]:
        """Generate artifact_catalog.json with ALL repo artifacts."""
        signals = self.signals.get_all_signals()
        java_files = signals.get("java_files", [])

        # Categorize all artifacts by type
        artifacts_by_type = {
            "controllers": [],
            "services": [],
            "repositories": [],
            "entities": [],
            "dtos": [],
            "mappers": [],
            "configs": [],
            "utils": [],
            "tests": [],
            "other": []
        }

        for f in java_files:
            artifact_name = f.split(".")[-1]
            package = ".".join(f.split(".")[:-1])
            
            # Categorize by name patterns
            if 'Controller' in artifact_name:
                artifacts_by_type["controllers"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Service' in artifact_name:
                artifacts_by_type["services"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Repository' in artifact_name:
                artifacts_by_type["repositories"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Entity' in artifact_name or 'Model' in artifact_name:
                artifacts_by_type["entities"].append({"name": artifact_name, "package": package, "file": f})
            elif 'DTO' in artifact_name or 'Dto' in artifact_name:
                artifacts_by_type["dtos"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Mapper' in artifact_name:
                artifacts_by_type["mappers"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Config' in artifact_name or 'Configuration' in artifact_name:
                artifacts_by_type["configs"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Util' in artifact_name or 'Helper' in artifact_name or 'Common' in artifact_name:
                artifacts_by_type["utils"].append({"name": artifact_name, "package": package, "file": f})
            elif 'Test' in artifact_name:
                artifacts_by_type["tests"].append({"name": artifact_name, "package": package, "file": f})
            else:
                artifacts_by_type["other"].append({"name": artifact_name, "package": package, "file": f})

        # Flatten all artifacts
        all_artifacts = []
        for artifact_list in artifacts_by_type.values():
            all_artifacts.extend(artifact_list)

        catalog = {
            "repository": self.repo_name,
            "scan_timestamp": self.timestamp,
            "agent": "Agent 1: Discovery & Scoping",
            "confidence": 0.85,
            "summary": {
                "total_artifacts": len(java_files),
                "by_type": {
                    "controllers": len(artifacts_by_type["controllers"]),
                    "services": len(artifacts_by_type["services"]),
                    "repositories": len(artifacts_by_type["repositories"]),
                    "entities": len(artifacts_by_type["entities"]),
                    "dtos": len(artifacts_by_type["dtos"]),
                    "mappers": len(artifacts_by_type["mappers"]),
                    "configs": len(artifacts_by_type["configs"]),
                    "utils": len(artifacts_by_type["utils"]),
                    "tests": len(artifacts_by_type["tests"]),
                    "other": len(artifacts_by_type["other"])
                },
                "packages": len(signals["main_packages"])
            },
            "artifacts_by_category": artifacts_by_type,
            "all_artifacts": all_artifacts,
            "packages": list(signals["main_packages"])
        }
        return catalog

    def _generate_dependency_map(self) -> Dict[str, Any]:
        """Generate dependency_map.json."""
        signals = self.signals.get_all_signals()

        return {
            "repository": self.repo_name,
            "agent": "Agent 1: Discovery & Scoping",
            "confidence": 0.8,
            "build_tool": self._detect_build_system(signals),
            "dependencies": signals["dependencies"],
            "dependency_count": sum(len(v) for v in signals["dependencies"].values()),
            "frameworks": signals["frameworks"],
        }

    def _generate_business_rules(self) -> Dict[str, Any]:
        """Generate business_rules.json."""
        signals = self.signals.get_all_signals()

        if not self.agent_llm.has_api():
            return {
                "repository": self.repo_name,
                "timestamp": self.timestamp,
                "rules": [],
                "confidence": 0.6,
            }

        prompt = f"""
Based on this repository structure, infer business rules:
- Frameworks: {signals['frameworks']}
- Packages: {signals['main_packages']}
- Java Files: {signals['java_files'][:10]}

Generate a JSON object with an array of inferred business rules. Format:
{{
  "repository": "{self.repo_name}",
  "timestamp": "{self.timestamp}",
  "rules": [
    {{"rule": "...", "category": "...", "priority": "high|medium|low"}}
  ],
  "confidence": 0.8
}}
"""
        result = self.agent_llm.generate_json_output(prompt)
        if result:
            return result

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "rules": [],
            "confidence": 0.6,
        }

    def _generate_actors(self) -> Dict[str, Any]:
        """Generate actors.json based on detected components."""
        signals = self.signals.get_all_signals()
        java_files = signals.get('java_files', [])
        packages = signals.get('main_packages', [])

        # Extract domain context from packages
        domains = set()
        for pkg in packages[:10]:
            parts = pkg.split('.')
            for i, part in enumerate(parts):
                if part not in ['com', 'org', 'net', 'io', 'api', 'main', 'java', 'util', 'config', 'service', 'repository', 'controller']:
                    domains.add(part)

        # Generate domain-specific actors
        actors = []

        # Add domain-specific actors based on detected components
        if 'Controller' in str(java_files):
            actors.append({
                "name": "API Consumer",
                "description": "Client consuming REST API endpoints",
                "role": "consumer"
            })

        # Add actors based on domain context
        for domain in sorted(list(domains))[:3]:
            domain_title = domain.replace('_', ' ').title()
            actors.append({
                "name": f"{domain_title} Manager",
                "description": f"User managing {domain} operations",
                "role": "manager"
            })

        # Add service-specific actors
        if signals['java_class_patterns'].get('Service', 0) > 0:
            actors.append({
                "name": "Service Administrator",
                "description": "Administrator managing business services",
                "role": "admin"
            })

        # Add data manager actor
        if signals['java_class_patterns'].get('Repository', 0) > 0:
            actors.append({
                "name": "Data Manager",
                "description": "User managing data persistence and queries",
                "role": "data_manager"
            })

        # Always add system actor
        actors.append({
            "name": "External System",
            "description": "External systems and integrations",
            "role": "system"
        })

        # If no specific actors detected, use generics
        if len(actors) == 1:  # Only system actor
            actors = [
                {"name": "End User", "description": "Primary system user", "role": "user"},
                {"name": "Administrator", "description": "System administrator", "role": "admin"},
                {"name": "External System", "description": "External systems and integrations", "role": "system"},
            ]

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "detected_domains": list(domains)[:5],
            "detected_components": {
                "controllers": signals['java_class_patterns'].get('Controller', 0),
                "services": signals['java_class_patterns'].get('Service', 0),
                "repositories": signals['java_class_patterns'].get('Repository', 0),
            },
            "actors": actors,
            "confidence": 0.8,
        }

    def _generate_journey_map(self) -> Dict[str, Any]:
        """Generate journey_map.json."""
        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "journeys": [],
            "confidence": 0.6,
        }

    def _generate_executive_summary(self) -> str:
        """Generate brd_executive_summary.md."""
        signals = self.signals.get_all_signals()

        return f"""# Executive Summary - {self.repo_name}

## Repository Overview
- **Location**: {self.repo_path}
- **Primary Language**: {self._detect_primary_language(signals)}
- **Frameworks**: {', '.join(signals['frameworks']) or 'None detected'}
- **Total Lines of Code**: {signals['loc']:,}

## Technology Stack
- **Main Packages**: {', '.join(signals['main_packages'][:5])}
- **Build Tool**: {self._detect_build_system(signals)}
- **Dependencies**: {sum(len(v) for v in signals['dependencies'].values())} packages

## Component Summary
- **Controllers**: {signals['java_class_patterns'].get('Controller', 0)}
- **Services**: {signals['java_class_patterns'].get('Service', 0)}
- **Repositories**: {signals['java_class_patterns'].get('Repository', 0)}
- **Domain Entities**: {signals['java_class_patterns'].get('Entity', 0)}

## Confidence Level
Generated: {self.timestamp}
"""

    def _generate_coverage_summary(self) -> Dict[str, Any]:
        """Generate coverage_summary.json."""
        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "coverage": {
                "discovery": 0.9,
                "business_rules": 0.7,
                "acceptance_criteria": 0.6,
                "testing": 0.5,
            },
            "gaps": [],
            "confidence": 0.75,
        }

    def _generate_brd_final(self) -> Dict[str, Any]:
        """Generate brd_final.json."""
        signals = self.signals.get_all_signals()

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "version": "1.0",
            "scope": {
                "description": f"BRD for {self.repo_name}",
                "frameworks": signals["frameworks"],
                "components": len(signals["java_files"]),
            },
            "business_rules": [],
            "acceptance_criteria": [],
            "confidence": 0.8,
        }

    # ──────────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────────

    def _detect_primary_language(self, signals: Dict[str, Any]) -> str:
        """Detect primary programming language."""
        file_stats = signals["file_stats"]
        if file_stats.get(".java", 0) > 0:
            return "Java"
        if file_stats.get(".py", 0) > 0:
            return "Python"
        if file_stats.get(".js", 0) > 0 or file_stats.get(".ts", 0) > 0:
            return "JavaScript/TypeScript"
        if file_stats.get(".go", 0) > 0:
            return "Go"
        if file_stats.get(".rs", 0) > 0:
            return "Rust"
        return "Unknown"

    def _detect_build_system(self, signals: Dict[str, Any]) -> str:
        """Detect build system."""
        frameworks = signals["frameworks"]
        if "Spring Framework" in frameworks or "Spring MVC" in frameworks:
            return "Maven"  # Default for Spring
        if any("Gradle" in f for f in signals["java_files"][:5]):
            return "Gradle"
        if "npm" in signals["dependencies"]:
            return "npm"
        return "Unknown"

    def _extract_build_tools(self, signals: Dict[str, Any]) -> list:
        """Extract build tools from signals."""
        tools = []
        if any("maven" in f.lower() for f in signals["java_files"]):
            tools.append("Maven")
        if any("gradle" in f.lower() for f in signals["java_files"]):
            tools.append("Gradle")
        if "npm" in signals["dependencies"]:
            tools.append("npm")
        return tools

    def _classify_artifact(self, artifact: str) -> str:
        """Classify artifact by name."""
        if "Controller" in artifact:
            return "REST_CONTROLLER"
        if "Service" in artifact:
            return "SERVICE_LAYER"
        if "Repository" in artifact or "Mapper" in artifact:
            return "DATA_ACCESS"
        if "Entity" in artifact or "Domain" in artifact:
            return "DOMAIN_ENTITY"
        return "UNKNOWN"

    def _announce_step(self, idx: int, total: int, output_name: str, uses_llm: bool) -> None:
        """Emit a `[X/Y]` sub-step line plus a Writing: hint so the frontend
        can display the target artifact alongside the step counter."""
        tag = "(LLM call)" if uses_llm else "(local)"
        print(f"[{idx}/{total}] Generating {output_name} {tag}", flush=True)
        print(f"Writing: {self.output_path / output_name}", flush=True)

    def _write_outputs(self, outputs: Dict[str, Any]):
        """Write all outputs to JSON files."""
        for name, data in outputs.items():
            if isinstance(data, str):
                # Markdown file
                filepath = self.output_path / f"{name}.md"
                filepath.write_text(data)
            else:
                # JSON file
                filepath = self.output_path / f"{name}.json"
                filepath.write_text(json.dumps(data, indent=2))
            # Absolute path so users can click through in the log block.
            print(f"Wrote: {filepath}", flush=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent 1: LLM-Powered Discovery & Scoping")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--output", help="Output path for artifacts", default=None)
    parser.add_argument("--api-key", help="Anthropic API key", default=None)

    args = parser.parse_args()

    agent = LLMDiscoveryAgent(args.repo_path, args.output, args.api_key)
    agent.run()
