"""
Microservices Analyzer
Detects microservices architecture and extracts individual service information.
Generates service-specific BRDs instead of treating entire repo as monolith.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class MicroservicesAnalyzer:
    """Analyzes microservices architecture and identifies individual services."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.is_microservices = False
        self.services: Dict[str, Dict[str, Any]] = {}

    def analyze(self) -> Dict[str, Any]:
        """Analyze repository for microservices architecture."""
        print(f"\n[Microservices Analyzer] Analyzing {self.repo_name}...")

        # Check for microservices patterns
        self._detect_microservices_patterns()

        if self.is_microservices:
            print(f"  ✓ Microservices architecture detected!")
            self._extract_services()
            print(f"  ✓ Identified {len(self.services)} services")

            for service_name, info in self.services.items():
                print(f"    - {service_name}")
                print(f"      Controllers: {info.get('controllers', 0)}")
                print(f"      Services: {info.get('services', 0)}")
                print(f"      Repositories: {info.get('repositories', 0)}")
                print(f"      Entities: {info.get('entities', 0)}")

        return {
            "is_microservices": self.is_microservices,
            "services": self.services,
            "service_count": len(self.services),
        }

    def _detect_microservices_patterns(self):
        """Detect microservices architecture patterns."""
        patterns_found = []

        # Pattern 1: Multi-module Maven (pom.xml with <modules>)
        if self._has_multi_module_maven():
            patterns_found.append("multi-module-maven")
            self.is_microservices = True

        # Pattern 2: Service-named directories
        if self._has_service_directories():
            patterns_found.append("service-directories")
            self.is_microservices = True

        # Pattern 3: Multiple Spring Boot applications
        if self._has_multiple_boot_apps():
            patterns_found.append("multiple-boot-apps")
            self.is_microservices = True

        # Pattern 4: Docker Compose or Kubernetes files
        if self._has_orchestration_files():
            patterns_found.append("orchestration-files")
            self.is_microservices = True

        print(f"  Microservices patterns detected: {patterns_found}")

    def _has_multi_module_maven(self) -> bool:
        """Check for multi-module Maven setup."""
        pom_path = self.repo_path / "pom.xml"
        if pom_path.exists():
            content = pom_path.read_text(errors="ignore")
            if "<modules>" in content and "<module>" in content:
                return True
        return False

    def _has_service_directories(self) -> bool:
        """Check for service-named directories."""
        service_keywords = [
            "-service", "_service", "-api", "_api", "-ms", "_ms",
            "service-", "service_", "api-", "api_",
        ]

        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                item_lower = item.name.lower()
                if any(kw in item_lower for kw in service_keywords):
                    return True
        return False

    def _has_multiple_boot_apps(self) -> bool:
        """Check for multiple Spring Boot applications."""
        boot_app_count = 0
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["target", "build"]]
            if "pom.xml" in files:
                pom_content = Path(root).joinpath("pom.xml").read_text(errors="ignore")
                if "spring-boot-starter" in pom_content:
                    boot_app_count += 1
        return boot_app_count > 1

    def _has_orchestration_files(self) -> bool:
        """Check for Docker Compose or Kubernetes files."""
        orchestration_files = ["docker-compose.yml", "docker-compose.yaml", "k8s.yaml", "kubernetes.yaml"]
        for root, dirs, files in os.walk(self.repo_path):
            for orch_file in orchestration_files:
                if orch_file in files:
                    return True
        return False

    def _extract_services(self):
        """Extract individual microservices."""
        service_dirs = self._find_service_directories()

        for service_path in service_dirs:
            service_name = service_path.name
            service_info = self._analyze_service(service_path)
            if service_info["has_code"]:
                self.services[service_name] = service_info

    def _find_service_directories(self) -> List[Path]:
        """Find directories that represent individual services."""
        service_dirs = []
        service_keywords = [
            "-service", "_service", "-api", "_api", "service-", "service_"
        ]

        # Search in common locations
        common_locations = ["store-services", "services", "microservices", "modules"]

        for location in common_locations:
            location_path = self.repo_path / location
            if location_path.exists():
                for item in location_path.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        item_lower = item.name.lower()
                        if any(kw in item_lower for kw in service_keywords):
                            service_dirs.append(item)

        # Also search at root level
        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                item_lower = item.name.lower()
                if any(kw in item_lower for kw in service_keywords) and item not in service_dirs:
                    # Verify it has code
                    if (item / "src").exists() or self._count_java_files(item) > 0:
                        service_dirs.append(item)

        return sorted(service_dirs)

    def _analyze_service(self, service_path: Path) -> Dict[str, Any]:
        """Analyze individual service."""
        service_name = service_path.name
        info = {
            "name": service_name,
            "path": str(service_path),
            "has_code": False,
            "controllers": 0,
            "services": 0,
            "repositories": 0,
            "entities": 0,
            "java_files": [],
            "purpose": self._infer_service_purpose(service_name),
        }

        # Count Java classes
        java_files = self._find_java_files(service_path)
        info["java_files"] = java_files
        info["has_code"] = len(java_files) > 0

        if info["has_code"]:
            info["controllers"] = sum(1 for f in java_files if "Controller" in f)
            info["services"] = sum(1 for f in java_files if "Service" in f)
            info["repositories"] = sum(1 for f in java_files if "Repository" in f)
            info["entities"] = sum(1 for f in java_files if "Entity" in f or "Domain" in f)

        # Extract actual class names for actors
        info["actors"] = self._extract_actors_from_service(service_path, service_name)

        return info

    def _find_java_files(self, path: Path, limit: int = 1000) -> List[str]:
        """Find Java files in a directory."""
        java_files = []
        count = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["target", "build"]]
            for file in files:
                if file.endswith(".java") and count < limit:
                    rel_path = os.path.relpath(os.path.join(root, file), path)
                    java_files.append(rel_path.replace("\\", "/"))
                    count += 1
        return java_files

    def _count_java_files(self, path: Path) -> int:
        """Count Java files in directory."""
        count = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["target", "build"]]
            for file in files:
                if file.endswith(".java"):
                    count += 1
        return count

    def _infer_service_purpose(self, service_name: str) -> str:
        """Infer service purpose from its name."""
        service_lower = service_name.lower()

        purposes = {
            "product": "Manages product catalog, details, and inventory",
            "recommendation": "Provides product recommendations to users",
            "review": "Handles product reviews and ratings",
            "order": "Manages order creation and processing",
            "cart": "Manages shopping cart operations",
            "payment": "Processes payments and transactions",
            "user": "Manages user accounts and profiles",
            "auth": "Handles authentication and authorization",
            "notification": "Sends notifications to users",
            "inventory": "Manages inventory and stock levels",
            "shipping": "Manages shipping and logistics",
            "report": "Generates reports and analytics",
        }

        for keyword, purpose in purposes.items():
            if keyword in service_lower:
                return purpose

        return f"Provides {service_name.replace('-', ' ').title()} functionality"

    def _extract_actors_from_service(self, service_path: Path, service_name: str) -> List[Dict[str, str]]:
        """Extract realistic actors based on service name and content."""
        actors = []
        service_lower = service_name.lower()

        # Service-specific actors
        if "product" in service_lower:
            actors.extend([
                {"name": "Product Manager", "role": "manager", "description": "Manages product catalog"},
                {"name": "Product Viewer", "role": "user", "description": "Browses products"},
            ])
        elif "review" in service_lower:
            actors.extend([
                {"name": "Reviewer", "role": "user", "description": "Posts product reviews"},
                {"name": "Review Moderator", "role": "admin", "description": "Moderates reviews"},
            ])
        elif "recommendation" in service_lower:
            actors.extend([
                {"name": "Shopper", "role": "user", "description": "Receives recommendations"},
                {"name": "Analytics Engine", "role": "system", "description": "Generates recommendations"},
            ])
        elif "order" in service_lower:
            actors.extend([
                {"name": "Customer", "role": "user", "description": "Places orders"},
                {"name": "Order Fulfiller", "role": "admin", "description": "Processes orders"},
            ])
        elif "payment" in service_lower:
            actors.extend([
                {"name": "Payer", "role": "user", "description": "Initiates payments"},
                {"name": "Payment Processor", "role": "system", "description": "Processes transactions"},
            ])
        elif "user" in service_lower or "auth" in service_lower:
            actors.extend([
                {"name": "User", "role": "user", "description": "System user"},
                {"name": "Account Manager", "role": "admin", "description": "Manages user accounts"},
            ])
        else:
            # Generic actors for unknown services
            actors.extend([
                {"name": f"{service_name.title()} User", "role": "user", "description": f"Uses {service_name}"},
                {"name": f"{service_name.title()} Admin", "role": "admin", "description": f"Administers {service_name}"},
            ])

        # Add API consumer (always applicable in microservices)
        actors.append({
            "name": "API Consumer",
            "role": "system",
            "description": f"External service consuming {service_name} API"
        })

        return actors

    def get_service_specific_scope(self, service_name: str) -> Dict[str, Any]:
        """Get scope definition for a specific service."""
        if service_name not in self.services:
            return {}

        service = self.services[service_name]

        return {
            "repository": self.repo_name,
            "service": service_name,
            "service_purpose": service["purpose"],
            "scope_summary": {
                "description": service["purpose"],
                "architecture_pattern": "Microservice in Spring Cloud ecosystem",
                "total_java_classes": len(service["java_files"]),
            },
            "components": {
                "controllers": service["controllers"],
                "services": service["services"],
                "repositories": service["repositories"],
                "entities": service["entities"],
            },
            "actors": service["actors"],
        }

    def get_service_specific_gaps(self, service_name: str) -> Dict[str, Any]:
        """Generate service-specific gaps."""
        if service_name not in self.services:
            return {}

        service = self.services[service_name]
        gaps = []

        # Identify gaps based on service components
        if service["controllers"] > 0 and service["services"] == 0:
            gaps.append({
                "id": "GAP001",
                "title": f"{service_name} - Missing Service Layer",
                "description": "Controllers exist but service layer is missing",
                "severity": "high",
            })

        if service["services"] > 0 and service["repositories"] == 0:
            gaps.append({
                "id": "GAP002",
                "title": f"{service_name} - Missing Data Access Layer",
                "description": "Services exist but repository layer is missing",
                "severity": "high",
            })

        if service["repositories"] == 0 and service["entities"] == 0:
            gaps.append({
                "id": "GAP003",
                "title": f"{service_name} - Missing Data Model",
                "description": "No entities or repositories detected",
                "severity": "medium",
            })

        # Service-specific gaps
        if "product" in service_name.lower():
            gaps.extend([
                {
                    "id": "GAP101",
                    "title": f"{service_name} - Inventory Management",
                    "description": "Need to track product inventory levels",
                    "severity": "high",
                },
                {
                    "id": "GAP102",
                    "title": f"{service_name} - Product Catalog",
                    "description": "Need comprehensive product categorization",
                    "severity": "medium",
                },
            ])

        elif "order" in service_name.lower():
            gaps.extend([
                {
                    "id": "GAP201",
                    "title": f"{service_name} - Order Status Tracking",
                    "description": "Need detailed order lifecycle tracking",
                    "severity": "high",
                },
                {
                    "id": "GAP202",
                    "title": f"{service_name} - Order Fulfillment",
                    "description": "Need integration with fulfillment system",
                    "severity": "high",
                },
            ])

        elif "review" in service_name.lower():
            gaps.extend([
                {
                    "id": "GAP301",
                    "title": f"{service_name} - Review Moderation",
                    "description": "Need review moderation workflow",
                    "severity": "medium",
                },
                {
                    "id": "GAP302",
                    "title": f"{service_name} - Rating Aggregation",
                    "description": "Need to aggregate ratings across reviews",
                    "severity": "low",
                },
            ])

        return {
            "repository": self.repo_name,
            "service": service_name,
            "total_gaps": len(gaps),
            "gaps": gaps,
        }

    def get_service_specific_actors(self, service_name: str) -> Dict[str, Any]:
        """Get realistic actors for a specific service."""
        if service_name not in self.services:
            return {}

        service = self.services[service_name]

        return {
            "repository": self.repo_name,
            "service": service_name,
            "actors": service["actors"],
            "total_actors": len(service["actors"]),
        }
