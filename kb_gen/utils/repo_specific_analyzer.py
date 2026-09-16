"""
Repository-Specific Analyzer
Extracts detailed repo-specific data for gaps, journeys, and risks analysis.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Set


class RepoSpecificAnalyzer:
    """Analyzes repository for specific insights."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)

    def detect_testing_gaps(self) -> Dict[str, Any]:
        """Detect testing gaps by analyzing test files."""
        gaps = {
            "has_tests": False,
            "test_types": [],
            "missing_tests": [],
            "coverage_areas": []
        }

        # Look for test files
        test_files = list(self.repo_path.rglob("*Test.java")) + \
                     list(self.repo_path.rglob("*Tests.java")) + \
                     list(self.repo_path.rglob("*Spec.java")) + \
                     list(self.repo_path.rglob("test*.py")) + \
                     list(self.repo_path.rglob("*_test.py"))

        if test_files:
            gaps["has_tests"] = True
            gaps["test_count"] = len(test_files)

            # Detect test types
            for test_file in test_files:
                content = test_file.read_text(encoding="utf-8", errors="ignore").lower()
                if "junit" in content or "@test" in content:
                    gaps["test_types"].append("Unit Tests")
                if "integration" in content or "@springboottest" in content:
                    gaps["test_types"].append("Integration Tests")
                if "mock" in content or "@mock" in content:
                    gaps["test_types"].append("Mocking/Mock Tests")
                if "mock" not in content and "integration" not in content and "junit" not in content:
                    gaps["test_types"].append("Other Tests")

            gaps["test_types"] = list(set(gaps["test_types"]))
        else:
            gaps["missing_tests"] = ["Unit Tests", "Integration Tests", "End-to-End Tests"]

        # Detect untested components
        service_files = list(self.repo_path.rglob("*Service.java"))
        if service_files and len(test_files) < len(service_files) / 2:
            gaps["missing_tests"].append("Service Layer Coverage")

        if not gaps["has_tests"]:
            gaps["missing_tests"].extend([
                "Unit Test Suite",
                "Integration Test Suite",
                "API Contract Tests",
                "Performance Tests"
            ])

        return gaps

    def detect_documentation_gaps(self) -> Dict[str, Any]:
        """Detect documentation gaps."""
        gaps = {
            "documentation_files": [],
            "missing_docs": [],
            "api_docs_available": False,
            "architecture_docs": False
        }

        # Look for documentation
        doc_patterns = [
            ("README", ["README.md", "readme.md", "README.txt"]),
            ("API Docs", ["API.md", "api.md", "API_DOCUMENTATION.md", "openapi.yaml", "swagger.yaml"]),
            ("Architecture", ["ARCHITECTURE.md", "architecture.md", "DESIGN.md", "design.md"]),
            ("Setup Guide", ["SETUP.md", "setup.md", "INSTALLATION.md", "installation.md"]),
            ("Contributing", ["CONTRIBUTING.md", "contributing.md"]),
            ("Changelog", ["CHANGELOG.md", "changelog.md", "HISTORY.md"])
        ]

        found_docs = set()
        for doc_type, patterns in doc_patterns:
            for pattern in patterns:
                if (self.repo_path / pattern).exists():
                    gaps["documentation_files"].append(doc_type)
                    found_docs.add(doc_type)
                    if "API" in doc_type:
                        gaps["api_docs_available"] = True
                    if "Architecture" in doc_type:
                        gaps["architecture_docs"] = True
                    break

        # Detect missing docs
        all_doc_types = [t[0] for t in doc_patterns]
        gaps["missing_docs"] = [d for d in all_doc_types if d not in found_docs]

        # Check for inline documentation
        java_files = list(self.repo_path.rglob("*.java"))
        if java_files:
            poorly_documented_count = 0
            for java_file in java_files[:10]:  # Check first 10
                content = java_file.read_text(encoding="utf-8", errors="ignore")
                if "/**" not in content and "/*" not in content:
                    poorly_documented_count += 1

            if poorly_documented_count > 5:
                gaps["missing_docs"].append("Code Comments & Javadoc")

        if not gaps["documentation_files"]:
            gaps["missing_docs"] = [
                "README",
                "API Documentation",
                "Architecture Documentation",
                "Setup Guide",
                "Code Comments/Javadoc"
            ]

        return gaps

    def detect_controller_entities(self) -> List[str]:
        """Extract entity names from code."""
        entities = []

        # Look for @Entity annotations
        for java_file in self.repo_path.rglob("*Entity.java"):
            match = re.search(r"class\s+(\w+)", java_file.read_text(encoding="utf-8", errors="ignore"))
            if match:
                entities.append(match.group(1))

        # Also check DTO files
        for java_file in self.repo_path.rglob("*DTO.java"):
            match = re.search(r"class\s+(\w+)", java_file.read_text(encoding="utf-8", errors="ignore"))
            if match:
                entities.append(match.group(1))

        return entities[:5]  # Top 5

    def extract_actual_actors(self) -> List[str]:
        """Extract user/actor roles from code."""
        actors = set()

        # Look for role-related code
        for java_file in self.repo_path.rglob("*.java"):
            try:
                content = java_file.read_text(encoding="utf-8", errors="ignore")
                # Look for role patterns
                roles = re.findall(r'(?:ROLE_|role.*=.*")[A-Z_]+', content, re.IGNORECASE)
                for role in roles:
                    actor = role.replace("ROLE_", "").replace('role.*="', "").replace('"', "").title()
                    if actor and len(actor) > 2:
                        actors.add(actor)

                # Look for user types
                if "admin" in content.lower():
                    actors.add("Administrator")
                if "user" in content.lower():
                    actors.add("End User")
                if "guest" in content.lower():
                    actors.add("Guest")
                if "system" in content.lower():
                    actors.add("System")
            except:
                pass

        return list(actors) if actors else ["End User", "Administrator", "System"]

    def detect_technology_risks(self) -> List[Dict[str, str]]:
        """Detect risks based on technology stack."""
        risks = []

        try:
            # Check for deprecated dependencies
            pom_path = self.repo_path / "pom.xml"
            if pom_path.exists():
                pom_content = pom_path.read_text(encoding="utf-8", errors="ignore")

                # Old Spring versions
                if "<version>1." in pom_content or "<version>2.0" in pom_content:
                    risks.append({
                        "id": "TECH-001",
                        "title": "Outdated Spring Framework Version",
                        "severity": "HIGH",
                        "description": "Repository uses older Spring version with potential security vulnerabilities"
                    })

                # Check for missing security dependencies
                if "spring-security" not in pom_content.lower():
                    risks.append({
                        "id": "TECH-002",
                        "title": "Missing Spring Security",
                        "severity": "CRITICAL",
                        "description": "No Spring Security dependency found. Authentication/Authorization may be missing."
                    })

                # Check for missing validation
                if "validation" not in pom_content.lower():
                    risks.append({
                        "id": "TECH-003",
                        "title": "Missing Validation Framework",
                        "severity": "MEDIUM",
                        "description": "No validation framework detected. Input validation may be incomplete."
                    })

        except Exception:
            pass

        return risks

    def analyze_code_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity issues."""
        analysis = {
            "large_files": 0,
            "complex_methods": 0,
            "god_classes": []
        }

        java_files = list(self.repo_path.rglob("*.java"))[:20]  # Limit to first 20

        for java_file in java_files:
            try:
                content = java_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split('\n')

                if len(lines) > 500:
                    analysis["large_files"] += 1

                # Count methods
                methods = len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\(', content))
                if methods > 15:
                    analysis["god_classes"].append(java_file.stem)

                # Check for long methods (rough estimate)
                method_blocks = re.findall(r'\{[\s\S]{1000,}\}', content)
                if method_blocks:
                    analysis["complex_methods"] += len(method_blocks)
            except:
                pass

        return analysis

    def generate_journey_contexts(self) -> List[Dict[str, str]]:
        """Generate specific journey contexts based on detected code."""
        journeys = []
        entities = self.detect_controller_entities()
        actors = self.extract_actual_actors()

        # Create CRUD journeys for each entity
        if entities:
            for entity in entities[:3]:
                journeys.append({
                    "type": "CREATE",
                    "entity": entity,
                    "actors": actors,
                    "description": f"Create new {entity}"
                })
                journeys.append({
                    "type": "READ",
                    "entity": entity,
                    "actors": actors,
                    "description": f"Retrieve and view {entity}"
                })
                journeys.append({
                    "type": "UPDATE",
                    "entity": entity,
                    "actors": actors,
                    "description": f"Update existing {entity}"
                })
                journeys.append({
                    "type": "DELETE",
                    "entity": entity,
                    "actors": actors,
                    "description": f"Delete {entity}"
                })

        # Add error handling journeys
        journeys.append({
            "type": "ERROR_HANDLING",
            "description": "Handle validation errors and exceptions"
        })

        # Add security journeys if applicable
        pom_path = self.repo_path / "pom.xml"
        if pom_path.exists():
            if "spring-security" in pom_path.read_text(encoding="utf-8", errors="ignore").lower():
                journeys.append({
                    "type": "AUTHENTICATION",
                    "description": "User authentication and login process"
                })
                journeys.append({
                    "type": "AUTHORIZATION",
                    "description": "Role-based access control and authorization"
                })

        return journeys[:10]  # Return top 10
