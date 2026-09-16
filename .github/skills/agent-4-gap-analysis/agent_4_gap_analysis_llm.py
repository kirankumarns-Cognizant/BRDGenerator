#!/usr/bin/env python3
"""
Agent 4: Gap Analysis — LLM-POWERED VERSION
Identifies gaps between requirements and implementation.
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
    "Gap Identifier",
    "Gap Prioritizer",
    "JSON Parser",
    "State Analyzer",
    "JSON Writer",
    "Target Modeler",
]

class LLMGapAnalysisAgent:
    """LLM-powered gap analysis agent."""

    def __init__(self, repo_path: str, output_path: Optional[str] = None, api_key: Optional[str] = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.agent_llm = AgentLLM(self.repo_path, api_key, kb_path=self.output_path)
        self.repo_analyzer = RepoSpecificAnalyzer(self.repo_path)
        self.timestamp = datetime.now().isoformat()

    def run(self) -> Dict[str, Any]:
        """Execute gap analysis."""
        print(f"\n{'='*60}")
        print("Agent 4: LLM-Powered Gap Analysis")
        print(f"{'='*60}")

        outputs = {}

        try:
            print("[1/4] Generating gap_analysis.json...")
            outputs["gap_analysis"] = self._generate_gap_analysis()

            print("[2/4] Generating gap_register.json...")
            outputs["gap_register"] = self._generate_gap_register()

            print("[3/4] Generating brd_gap_summary.json...")
            outputs["brd_gap_summary"] = self._generate_gap_summary()

            print("[4/4] Generating brd_test_gap_analysis.json...")
            outputs["brd_test_gap_analysis"] = self._generate_test_gap_analysis()

            self._write_outputs(outputs)
            
            # Print tools used
            tools_str = ", ".join(TOOLS_USED)
            print(f"\nGenerated {len(outputs)} output files")
            print(f"🔧 Tools used for gap-analysis: {tools_str}")
            print(f"\n{'='*60}\n[OK] Gap Analysis Complete!\n{'='*60}\n")
            return outputs
        except Exception as e:
            print(f"ERROR: {e}")
            return {}

    def _generate_gap_analysis(self) -> Dict[str, Any]:
        """Generate gap_analysis.json with REPO-SPECIFIC data."""
        signals = self.agent_llm.repo_signals.get_all_signals()

        # Detect ACTUAL gaps from repository
        testing_gaps = self.repo_analyzer.detect_testing_gaps()
        doc_gaps = self.repo_analyzer.detect_documentation_gaps()
        tech_risks = self.repo_analyzer.detect_technology_risks()

        gaps = []
        gap_counter = 1

        # Add testing-related gaps
        if not testing_gaps["has_tests"]:
            for missing_test in testing_gaps["missing_tests"][:3]:
                gaps.append({
                    "id": f"GAP{gap_counter:03d}",
                    "category": "Testing",
                    "description": f"Missing {missing_test}",
                    "severity": "high" if gap_counter == 1 else "medium",
                    "impact": "Reduced code reliability and quality assurance",
                    "status": "open",
                    "effort": "medium"
                })
                gap_counter += 1
        else:
            untested_areas = testing_gaps.get("missing_tests", [])
            if untested_areas:
                for area in untested_areas[:2]:
                    gaps.append({
                        "id": f"GAP{gap_counter:03d}",
                        "category": "Testing",
                        "description": f"Incomplete {area}",
                        "severity": "medium",
                        "impact": "Potential bugs in production",
                        "status": "open",
                        "effort": "medium"
                    })
                    gap_counter += 1

        # Add documentation-related gaps
        for missing_doc in doc_gaps["missing_docs"][:3]:
            gaps.append({
                "id": f"GAP{gap_counter:03d}",
                "category": "Documentation",
                "description": f"Missing {missing_doc}",
                "severity": "high" if "API" in missing_doc else "medium",
                "impact": "Developer onboarding and maintenance challenges",
                "status": "open",
                "effort": "small"
            })
            gap_counter += 1

        # Add technology/architecture gaps
        if len(tech_risks) > 0:
            gaps.append({
                "id": f"GAP{gap_counter:03d}",
                "category": "Technology",
                "description": f"{tech_risks[0].get('title', 'Technology vulnerability detected')}",
                "severity": "high",
                "impact": "Security or compatibility risks",
                "status": "open",
                "effort": "large"
            })
            gap_counter += 1

        # Analyze code complexity
        complexity = self.repo_analyzer.analyze_code_complexity()
        if complexity["large_files"] > 3:
            gaps.append({
                "id": f"GAP{gap_counter:03d}",
                "category": "Code Quality",
                "description": f"Large files detected ({complexity['large_files']} files > 500 lines)",
                "severity": "medium",
                "impact": "Reduced maintainability and testability",
                "status": "open",
                "effort": "large"
            })
            gap_counter += 1

        if complexity["god_classes"]:
            gaps.append({
                "id": f"GAP{gap_counter:03d}",
                "category": "Code Quality",
                "description": f"God classes detected: {', '.join(complexity['god_classes'][:2])}",
                "severity": "medium",
                "impact": "High coupling and reduced modularity",
                "status": "open",
                "effort": "large"
            })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "gaps": gaps,
            "total_gaps": len(gaps),
            "confidence": 0.85,
        }

    def _generate_gap_register(self) -> Dict[str, Any]:
        """Generate gap_register.json with REPO-SPECIFIC data."""
        testing_gaps = self.repo_analyzer.detect_testing_gaps()
        doc_gaps = self.repo_analyzer.detect_documentation_gaps()
        tech_risks = self.repo_analyzer.detect_technology_risks()
        complexity = self.repo_analyzer.analyze_code_complexity()

        gaps_by_category = {
            "Testing": len(testing_gaps.get("missing_tests", [])),
            "Documentation": len(doc_gaps.get("missing_docs", [])),
            "Technology": len(tech_risks),
            "Code Quality": 1 if complexity["large_files"] > 0 else 0,
            "Performance": 0,
            "Security": sum(1 for r in tech_risks if "security" in r.get("severity", "").lower()),
        }

        total = sum(gaps_by_category.values())

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "gaps_by_category": gaps_by_category,
            "total_gaps": total,
            "confidence": 0.85,
        }

    def _generate_gap_summary(self) -> Dict[str, Any]:
        """Generate brd_gap_summary.json with REPO-SPECIFIC data."""
        testing_gaps = self.repo_analyzer.detect_testing_gaps()
        doc_gaps = self.repo_analyzer.detect_documentation_gaps()

        summary_parts = []
        if not testing_gaps["has_tests"]:
            summary_parts.append(f"No test files detected. Repository needs test coverage.")
        elif testing_gaps.get("missing_tests"):
            summary_parts.append(f"Missing {len(testing_gaps['missing_tests'])} types of tests")

        if doc_gaps.get("missing_docs"):
            summary_parts.append(f"Missing {len(doc_gaps['missing_docs'])} documentation types")

        summary = " ".join(summary_parts) if summary_parts else "Repository gaps identified"

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "summary": summary,
            "has_tests": testing_gaps["has_tests"],
            "test_types": testing_gaps.get("test_types", []),
            "documentation_available": len(doc_gaps.get("documentation_files", [])),
            "missing_documentation": len(doc_gaps.get("missing_docs", [])),
            "confidence": 0.85,
        }

    def _generate_test_gap_analysis(self) -> Dict[str, Any]:
        """Generate brd_test_gap_analysis.json with REPO-SPECIFIC data."""
        testing_gaps = self.repo_analyzer.detect_testing_gaps()
        complexity = self.repo_analyzer.analyze_code_complexity()

        testing_gap_list = []
        for gap in testing_gaps.get("missing_tests", []):
            testing_gap_list.append({
                "type": gap,
                "priority": "high",
                "effort": "medium"
            })

        coverage_gaps = []
        if complexity["large_files"] > 0:
            coverage_gaps.append({
                "type": "Large File Coverage",
                "files_affected": complexity["large_files"],
                "priority": "medium"
            })

        if complexity["god_classes"]:
            coverage_gaps.append({
                "type": "Complex Class Coverage",
                "classes_affected": len(complexity["god_classes"]),
                "priority": "high"
            })

        return {
            "repository": self.repo_name,
            "timestamp": self.timestamp,
            "test_infrastructure": testing_gaps.get("test_types", []),
            "testing_gaps": testing_gap_list,
            "coverage_gaps": coverage_gaps,
            "total_test_files": testing_gaps.get("test_count", 0),
            "confidence": 0.85,
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

    agent = LLMGapAnalysisAgent(args.repo_path, args.output, args.api_key)
    agent.run()
