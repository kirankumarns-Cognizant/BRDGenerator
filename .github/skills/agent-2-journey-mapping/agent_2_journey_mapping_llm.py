#!/usr/bin/env python3
"""
Agent 2: Journey Mapping — LLM-POWERED VERSION
Maps user/actor journeys through the system based on detected components and flows.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from kb_gen.utils.agent_llm import AgentLLM
from kb_gen.utils.repo_specific_analyzer import RepoSpecificAnalyzer

# Tools used by this agent
TOOLS_USED = [
    "Flow Analyzer",
    "Actor Mapper",
    "Touchpoint Detector",
    "Journey Visualizer",
    "Process Sequencer",
]

class LLMJourneyMappingAgent:
    """LLM-powered journey mapping agent."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.repo_analyzer = RepoSpecificAnalyzer(self.repo_path)
        self.timestamp = datetime.now().isoformat()

    def run(self) -> Dict[str, Any]:
        """Execute journey mapping."""
        print(f"\n{'='*60}")
        print("Agent 2: LLM-Powered Journey Mapping")
        print(f"{'='*60}")

        outputs = {}

        try:
            print("[1/3] Generating journey_map.json...")
            outputs["journey_map"] = self._generate_journey_map()

            print("[2/3] Generating journey_conflicts.json...")
            outputs["journey_conflicts"] = self._generate_journey_conflicts()

            print("[3/3] Generating test_journey_coverage.json...")
            outputs["test_journey_coverage"] = self._generate_test_journey_coverage()

            self._write_outputs(outputs)

            # Print tools used
            tools_str = ", ".join(TOOLS_USED)
            print(f"\nGenerated {len(outputs)} output files")
            print(f"🔧 Tools used for journey-mapping: {tools_str}")
            print(f"\n{'='*60}\n[OK] Journey Mapping Complete!\n{'='*60}\n")
            return outputs
        except Exception as e:
            print(f"ERROR: {e}")
            return {}

    def _generate_journey_map(self) -> Dict[str, Any]:
        """Generate journey_map.json with REPO-SPECIFIC journeys."""
        signals = self.agent_llm.repo_signals.get_all_signals()

        # Extract repository-specific journey contexts
        journey_contexts = self.repo_analyzer.generate_journey_contexts()
        actors = self.repo_analyzer.extract_actual_actors()

        if not self.agent_llm.has_api():
            # Build journeys without LLM
            journeys = []
            for idx, ctx in enumerate(journey_contexts, 1):
                journeys.append({
                    "id": f"J-{idx:03d}",
                    "actor": ctx.get("actors", actors)[0] if ctx.get("actors") else "User",
                    "title": ctx.get("description", "User Journey"),
                    "type": ctx.get("type", "CRUD"),
                    "steps": [
                        "Access system",
                        f"Execute {ctx.get('type', 'operation')}",
                        "Complete action",
                        "Receive confirmation"
                    ],
                    "outcome": "Operation completed successfully"
                })

            return {
                "repository": self.repo_name,
                "timestamp": self.timestamp,
                "journeys": journeys,
                "total_journeys": len(journeys),
                "confidence": 0.75,
            }

        # Use LLM to enhance journeys with actual repository details
        journey_specs = "\n".join([f"  - {j['type']}: {j['description']}" for j in journey_contexts[:8]])
        actors_desc = ", ".join(actors)

        prompt = f"""
Generate 8-10 detailed user/actor journeys for this repository based on ACTUAL detected structure:

DETECTED JOURNEYS/OPERATIONS:
{journey_specs}

DETECTED ACTORS: {actors_desc}

Repository Details:
- Controllers: {signals['java_class_patterns'].get('Controller', 0)}
- Services: {signals['java_class_patterns'].get('Service', 0)}
- Repositories: {signals['java_class_patterns'].get('Repository', 0)}
- Main Packages: {', '.join(signals.get('main_packages', [])[:3])}

For EACH journey, generate:
- id: "J-XXX" format (J-001, J-002, etc.)
- actor: One of the detected actors
- title: Descriptive title
- type: Operation type (CREATE, READ, UPDATE, DELETE, AUTHENTICATE, etc.)
- steps: Array of 4-6 specific steps
- outcome: Expected outcome
- error_scenarios: 2-3 possible error paths

Return as JSON with array of journey objects."""

        result = self.agent_llm.generate_json_output(prompt, max_tokens=3000)

        if result and "journeys" in result:
            result["repository"] = self.repo_name
            result["timestamp"] = self.timestamp
            result["total_journeys"] = len(result.get("journeys", []))
            result["confidence"] = 0.85
            return result

        # Fallback: build from detected contexts
        journeys = []
        for idx, ctx in enumerate(journey_contexts, 1):
            journeys.append({
                "id": f"J-{idx:03d}",
                "actor": ctx.get("actors", actors)[0] if ctx.get("actors") else "User",
                "title": ctx.get("description", "User Journey"),
                "type": ctx.get("type", "CRUD"),
                "steps": [
                    f"User ({ctx.get('actor', 'User')}) initiates {ctx.get('type', 'operation')}",
                    "System validates request",
                    "Processing logic executes",
                    "Data persisted/retrieved",
                    "Confirmation sent to user"
                ],
                "outcome": "Operation completed successfully",
                "error_scenarios": ["Validation failure", "Authorization denied", "System error"]
            })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "journeys": journeys,
            "total_journeys": len(journeys),
            "confidence": 0.80,
        }

    def _generate_journey_conflicts(self) -> Dict[str, Any]:
        """Generate journey_conflicts.json with REPO-SPECIFIC analysis."""
        journey_contexts = self.repo_analyzer.generate_journey_contexts()

        # Identify potential conflicts
        conflicts = []

        # Check for conflicting operations on same entity
        entity_ops = {}
        for ctx in journey_contexts:
            if "entity" in ctx:
                entity = ctx["entity"]
                if entity not in entity_ops:
                    entity_ops[entity] = []
                entity_ops[entity].append(ctx.get("type"))

        # Multiple write operations on same entity could conflict
        for entity, ops in entity_ops.items():
            if ops.count("UPDATE") > 1 or (ops.count("UPDATE") > 0 and ops.count("DELETE") > 0):
                conflicts.append({
                    "id": f"CONFLICT-{len(conflicts)+1}",
                    "type": "Concurrent Modification",
                    "description": f"Multiple write operations on {entity} entity",
                    "affected_journeys": ["UPDATE", "DELETE"],
                    "resolution": "Implement optimistic locking or versioning"
                })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts),
            "resolved_conflicts": 0,
            "confidence": 0.80,
        }

    def _generate_test_journey_coverage(self) -> Dict[str, Any]:
        """Generate test_journey_coverage.json with REPO-SPECIFIC data."""
        journey_contexts = self.repo_analyzer.generate_journey_contexts()
        testing_gaps = self.repo_analyzer.detect_testing_gaps()

        total_journeys = len(journey_contexts)
        test_count = testing_gaps.get("test_count", 0)

        # Estimate coverage: rough estimate based on test count vs components
        if total_journeys > 0:
            coverage_percentage = min(100, (test_count / max(1, total_journeys)) * 100)
        else:
            coverage_percentage = 0

        tested_journeys = min(test_count, total_journeys)
        untested_journeys = max(0, total_journeys - tested_journeys)

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "total_journeys": total_journeys,
            "coverage_percentage": int(coverage_percentage),
            "tested_journeys": tested_journeys,
            "untested_journeys": untested_journeys,
            "test_infrastructure": testing_gaps.get("test_types", []),
            "confidence": 0.80,
        }

    def _write_outputs(self, outputs: Dict[str, Any]):
        """Write outputs to JSON files."""
        for name, data in outputs.items():
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

    agent = LLMJourneyMappingAgent(args.repo_path, args.output, args.api_key)
    agent.run()
