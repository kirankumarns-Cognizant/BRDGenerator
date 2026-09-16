"""
BRD Confidence Calculator — calculates overall confidence after pipeline execution.
Analyzes all artifacts and agent outputs to compute final BRD confidence score.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple


class BRDConfidenceCalculator:
    """Calculates overall BRD confidence based on artifact completeness and quality."""

    # Expected artifacts per agent
    AGENT_ARTIFACTS = {
        "Agent 1": ["scope_definition.json", "artifact_catalog.json", "dependency_map.json",
                   "business_rules.json", "actors.json", "journey_map.json",
                   "test_journey_coverage.json", "brd_executive_summary.md", "brd_final.json"],
        "Agent 2": ["journey_map.json", "journey_conflicts.json", "test_journey_coverage.json"],
        "Agent 3": ["business_rules.json", "orphaned_rules.json", "rule_test_coverage.json"],
        "Agent 4": ["gap_analysis.json", "gap_register.json", "brd_gap_summary.json", "brd_test_gap_analysis.json"],
        "Agent 5": ["synthesis_decisions.json", "COMPREHENSIVE_RULES_BRD.md"],
        "Agent 6": ["acceptance_criteria_gherkin.json", "test_case_analysis.json", "acceptance_criteria.feature"],
        "Agent 7": ["risk_register.json", "dependency_register.json", "regulatory_flags.json",
                   "regulatory_unresolved.json", "test_gap_risk_register.json", "prioritized_gap_closure_tests.json"],
        "Agent 8": ["brd_executive_summary.md", "COMPREHENSIVE_BRD_*.md", "regression_gap_report.json",
                   "new_test_suggestions.json", "coverage_summary.json", "openapi_spec.json"],
        "Agent 9": ["brd_final.json"]
    }

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.metrics = {}

    def calculate_overall_confidence(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate overall BRD confidence score (0-1)."""
        report = {
            "repository": self.repo_path.name,
            "timestamp": str(Path(self.repo_path / "brd_final.json").stat().st_mtime) if (self.repo_path / "brd_final.json").exists() else "N/A",
            "agent_scores": {},
            "artifact_metrics": {},
            "data_quality_metrics": {},
            "overall_confidence": 0.0,
            "confidence_grade": "N/A"
        }

        # Calculate individual agent confidence
        total_confidence = 0.0
        agent_count = 0

        for agent_name, expected_artifacts in self.AGENT_ARTIFACTS.items():
            agent_confidence = self._calculate_agent_confidence(expected_artifacts)
            report["agent_scores"][agent_name] = agent_confidence
            total_confidence += agent_confidence
            agent_count += 1

        # Calculate artifact metrics
        report["artifact_metrics"] = self._calculate_artifact_metrics()

        # Calculate data quality
        report["data_quality_metrics"] = self._calculate_data_quality()

        # Overall confidence
        overall = (total_confidence / agent_count) * 0.6 + report["artifact_metrics"]["completeness"] * 0.25 + report["data_quality_metrics"]["population_score"] * 0.15

        report["overall_confidence"] = round(overall, 3)
        report["confidence_grade"] = self._grade_confidence(overall)
        report["confidence_percentage"] = round(overall * 100, 1)

        return overall, report

    def _calculate_agent_confidence(self, expected_artifacts: list) -> float:
        """Calculate confidence for a specific agent based on artifact presence."""
        found = 0
        for artifact_pattern in expected_artifacts:
            if "*" in artifact_pattern:
                # Wildcard pattern
                pattern = artifact_pattern.replace("*.md", "")
                if any(self.repo_path.glob(f"{pattern}*.md")):
                    found += 1
            else:
                if (self.repo_path / artifact_pattern).exists():
                    found += 1

        return found / len(expected_artifacts) if expected_artifacts else 0.0

    def _calculate_artifact_metrics(self) -> Dict[str, float]:
        """Calculate metrics about artifacts."""
        json_files = list(self.repo_path.glob("*.json"))
        md_files = list(self.repo_path.glob("*.md"))
        feature_files = list(self.repo_path.glob("*.feature"))
        total_files = len(json_files) + len(md_files) + len(feature_files)

        expected_total = 31
        completeness = min(total_files / expected_total, 1.0)

        return {
            "json_files": len(json_files),
            "markdown_files": len(md_files),
            "feature_files": len(feature_files),
            "total_artifacts": total_files,
            "expected_total": expected_total,
            "completeness": completeness
        }

    def _calculate_data_quality(self) -> Dict[str, Any]:
        """Calculate data quality by checking file sizes and content."""
        metrics = {
            "non_empty_jsons": 0,
            "populated_jsons": 0,
            "empty_jsons": 0,
            "avg_json_size": 0,
            "population_score": 0.0
        }

        json_files = list(self.repo_path.glob("*.json"))
        sizes = []

        for json_file in json_files:
            try:
                with open(json_file, encoding='utf-8') as f:
                    data = json.load(f)
                    size = json_file.stat().st_size

                if size > 100:  # Not empty
                    metrics["non_empty_jsons"] += 1
                    sizes.append(size)

                # Check if populated with data
                if self._is_populated(data):
                    metrics["populated_jsons"] += 1
                else:
                    metrics["empty_jsons"] += 1

            except Exception:
                pass

        if sizes:
            metrics["avg_json_size"] = round(sum(sizes) / len(sizes), 0)

        if json_files:
            metrics["population_score"] = metrics["populated_jsons"] / len(json_files)

        return metrics

    @staticmethod
    def _is_populated(data: Dict) -> bool:
        """Check if JSON data is actually populated (not empty template)."""
        if not isinstance(data, dict):
            return False

        # Check for key indicators of populated data
        has_data = False
        for key, value in data.items():
            if key in ["artifacts", "dependencies", "rules", "risks", "gaps", "journeys"]:
                if isinstance(value, (list, dict)) and len(value) > 0:
                    has_data = True
                    break
            elif key in ["total_artifacts", "dependency_count", "total_risks"]:
                if value > 0:
                    has_data = True
                    break

        return has_data

    @staticmethod
    def _grade_confidence(confidence: float) -> str:
        """Convert confidence score to letter grade."""
        if confidence >= 0.95:
            return "A+ (Excellent)"
        elif confidence >= 0.90:
            return "A (Excellent)"
        elif confidence >= 0.85:
            return "B+ (Very Good)"
        elif confidence >= 0.80:
            return "B (Very Good)"
        elif confidence >= 0.75:
            return "C+ (Good)"
        elif confidence >= 0.70:
            return "C (Good)"
        elif confidence >= 0.60:
            return "D (Fair)"
        else:
            return "F (Incomplete)"

    def generate_report(self) -> str:
        """Generate formatted confidence report."""
        overall, metrics = self.calculate_overall_confidence()

        report_lines = [
            "",
            "=" * 70,
            "BRD CONFIDENCE REPORT",
            "=" * 70,
            f"Repository: {self.repo_path.name}",
            "",
            f"Overall BRD Confidence: {metrics['confidence_percentage']:.1f}%",
            f"Confidence Grade: {metrics['confidence_grade']}",
            "",
            "Agent Completion Scores:",
            "-" * 70,
        ]

        for agent, score in metrics["agent_scores"].items():
            percentage = score * 100
            bar = "[" + "=" * int(percentage / 5) + " " * (20 - int(percentage / 5)) + "]"
            report_lines.append(f"  {agent:20} {percentage:6.1f}% {bar}")

        report_lines.extend([
            "",
            "Artifact Completeness:",
            "-" * 70,
            f"  JSON Files: {metrics['artifact_metrics']['json_files']}/{metrics['artifact_metrics']['expected_total']}",
            f"  Markdown Files: {metrics['artifact_metrics']['markdown_files']}",
            f"  Feature Files: {metrics['artifact_metrics']['feature_files']}",
            f"  Total Artifacts: {metrics['artifact_metrics']['total_artifacts']}/{metrics['artifact_metrics']['expected_total']}",
            f"  Completeness: {metrics['artifact_metrics']['completeness']:.1%}",
            "",
            "Data Quality Metrics:",
            "-" * 70,
            f"  Non-Empty JSONs: {metrics['data_quality_metrics']['non_empty_jsons']}",
            f"  Populated JSONs: {metrics['data_quality_metrics']['populated_jsons']}",
            f"  Empty JSONs: {metrics['data_quality_metrics']['empty_jsons']}",
            f"  Average JSON Size: {metrics['data_quality_metrics']['avg_json_size']} bytes",
            f"  Data Population Score: {metrics['data_quality_metrics']['population_score']:.1%}",
            "",
            "=" * 70,
        ])

        return "\n".join(report_lines)
