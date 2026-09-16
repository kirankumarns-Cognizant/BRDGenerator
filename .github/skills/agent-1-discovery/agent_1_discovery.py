#!/usr/bin/env python3
"""
Agent 1: Discovery & Scoping - ENHANCED
Scans Java repositories, catalogs ALL artifacts (ActionBeans, Services, Mappers, Domain entities),
extracts technology stack from imports, and produces comprehensive scope definitions.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader
from tools.adapters.gitpython_adapter import GitPythonAdapter


class EnhancedDiscoveryAgent:
    """Enhanced discovery agent that properly detects all Java artifact types."""
    
    # Comprehensive Java class patterns for different frameworks
    CLASS_PATTERNS = {
        # Stripes MVC patterns
        "ActionBean": {"type": "WEB_CONTROLLER", "framework": "Stripes MVC"},
        "Action": {"type": "WEB_CONTROLLER", "framework": "Stripes MVC"},
        
        # Spring patterns
        "Controller": {"type": "REST_CONTROLLER", "framework": "Spring MVC"},
        "RestController": {"type": "REST_CONTROLLER", "framework": "Spring MVC"},
        "Service": {"type": "SERVICE_LAYER", "framework": "Spring"},
        "ServiceImpl": {"type": "SERVICE_LAYER", "framework": "Spring"},
        "Repository": {"type": "DATA_ACCESS", "framework": "Spring Data"},
        "Component": {"type": "COMPONENT", "framework": "Spring"},
        
        # MyBatis patterns
        "Mapper": {"type": "DATA_ACCESS", "framework": "MyBatis"},
        "Dao": {"type": "DATA_ACCESS", "framework": "Generic"},
        "DaoImpl": {"type": "DATA_ACCESS", "framework": "Generic"},
    }
    
    # Package-based detection for domain entities
    PACKAGE_PATTERNS = {
        "domain": "DOMAIN_ENTITY",
        "model": "DOMAIN_ENTITY",
        "entity": "DOMAIN_ENTITY",
        "dto": "DATA_TRANSFER_OBJECT",
        "vo": "VALUE_OBJECT",
        "bean": "JAVA_BEAN",
    }
    
    # Import patterns for technology stack detection
    IMPORT_PATTERNS = {
        "net.sourceforge.stripes": {"name": "Stripes MVC", "category": "Web Framework"},
        "org.springframework": {"name": "Spring Framework", "category": "Application Framework"},
        "org.springframework.web": {"name": "Spring MVC", "category": "Web Framework"},
        "org.mybatis": {"name": "MyBatis", "category": "ORM"},
        "org.apache.ibatis": {"name": "MyBatis", "category": "ORM"},
        "javax.persistence": {"name": "JPA", "category": "ORM"},
        "org.hibernate": {"name": "Hibernate", "category": "ORM"},
        "javax.servlet": {"name": "Java Servlets", "category": "Web"},
        "javax.sql": {"name": "JDBC", "category": "Database"},
        "java.sql": {"name": "JDBC", "category": "Database"},
        "org.hsqldb": {"name": "HSQLDB", "category": "Database"},
        "org.h2": {"name": "H2 Database", "category": "Database"},
        "com.mysql": {"name": "MySQL", "category": "Database"},
        "org.postgresql": {"name": "PostgreSQL", "category": "Database"},
        "org.junit": {"name": "JUnit", "category": "Testing"},
        "org.mockito": {"name": "Mockito", "category": "Testing"},
        "org.slf4j": {"name": "SLF4J", "category": "Logging"},
        "org.apache.log4j": {"name": "Log4j", "category": "Logging"},
        "com.fasterxml.jackson": {"name": "Jackson", "category": "JSON Processing"},
        "javax.validation": {"name": "Bean Validation", "category": "Validation"},
    }
    
    # Annotation patterns for business rules
    ANNOTATION_PATTERNS = [
        r'@Validate\s*\([^)]+\)',
        r'@ValidateNestedProperties\s*\([^)]+\)',
        r'@NotNull',
        r'@NotEmpty',
        r'@NotBlank',
        r'@Size\s*\([^)]+\)',
        r'@Min\s*\([^)]+\)',
        r'@Max\s*\([^)]+\)',
        r'@Pattern\s*\([^)]+\)',
        r'@Email',
        r'@Transactional',
        r'@SessionScope',
        r'@SpringBean',
        r'@Autowired',
        r'@Service',
        r'@Repository',
        r'@Controller',
    ]
    
    def __init__(self, repo_path: str, config_path: str = None, output_path: str = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.config = ConfigLoader(config_path) if config_path else ConfigLoader()
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize adapter with config
        self.git_adapter = GitPythonAdapter(self.config.config if hasattr(self.config, 'config') else {})
        
        # State accumulation
        self.artifacts: List[Dict] = []
        self.dependencies: Dict[str, List[str]] = {}
        self.tech_stack: Dict[str, Dict] = {}
        self.packages: Dict[str, List[str]] = {}
        self.annotations_found: Dict[str, List[str]] = {}
        self.confidence = 1.0
        
    def run(self) -> Dict[str, Any]:
        """Execute the enhanced discovery agent."""
        print(f"\n{'='*60}")
        print("Agent 1: Enhanced Discovery & Scoping")
        print(f"{'='*60}")
        print(f"Repository: {self.repo_path}")
        print(f"Output: {self.output_path}")
        
        try:
            # Phase 1: Scan all files
            print("\n[Phase 1] Scanning repository structure...")
            all_files = self._scan_repository()
            
            # Phase 2: Analyze Java files in detail
            print("\n[Phase 2] Analyzing Java source files...")
            java_files = [f for f in all_files if f.endswith('.java')]
            print(f"  Found {len(java_files)} Java files")
            self._analyze_java_files(java_files)
            
            # Phase 3: Analyze build configuration
            print("\n[Phase 3] Analyzing build configuration...")
            self._analyze_build_files()
            
            # Phase 4: Analyze configuration files
            print("\n[Phase 4] Analyzing configuration files...")
            self._analyze_config_files()
            
            # Phase 5: Generate outputs
            print("\n[Phase 5] Generating discovery outputs...")
            outputs = self._generate_outputs()
            
            print(f"\n{'='*60}")
            print("Discovery Complete!")
            print(f"  - Artifacts cataloged: {len(self.artifacts)}")
            print(f"  - Technologies detected: {len(self.tech_stack)}")
            print(f"  - Packages found: {len(self.packages)}")
            print(f"  - Overall confidence: {self.confidence:.2f}")
            print(f"{'='*60}\n")
            
            return outputs
            
        except Exception as e:
            print(f"ERROR: Discovery failed - {e}")
            self.confidence = 0.3
            return self._generate_error_outputs(str(e))
    
    def _scan_repository(self) -> List[str]:
        """Scan repository and return all file paths."""
        all_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'node_modules', '.git']]
            
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                all_files.append(rel_path.replace('\\', '/'))
        
        print(f"  Total files: {len(all_files)}")
        return all_files
    
    def _analyze_java_files(self, java_files: List[str]):
        """Analyze Java files to extract classes, imports, and annotations."""
        for java_file in java_files:
            full_path = self.repo_path / java_file
            
            if not full_path.exists():
                continue
                
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Extract class information
                class_info = self._extract_class_info(java_file, content)
                if class_info:
                    self.artifacts.append(class_info)
                
                # Extract imports for tech stack
                self._extract_imports(content)
                
                # Extract annotations for business rules
                self._extract_annotations(java_file, content)
                
                # Track package
                self._track_package(java_file, class_info)
                
            except Exception as e:
                print(f"  Warning: Could not analyze {java_file}: {e}")
                self.confidence *= 0.99
    
    def _extract_class_info(self, file_path: str, content: str) -> Optional[Dict]:
        """Extract detailed class information from Java file."""
        # Extract class name
        class_match = re.search(r'(?:public\s+)?(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)', content)
        if not class_match:
            return None
        
        class_name = class_match.group(1)
        
        # Determine class type based on patterns
        class_type = "UNKNOWN"
        framework = "Unknown"
        
        # Check naming patterns
        for pattern, info in self.CLASS_PATTERNS.items():
            if class_name.endswith(pattern) or pattern in class_name:
                class_type = info["type"]
                framework = info["framework"]
                break
        
        # Check package path for domain entities
        if class_type == "UNKNOWN":
            for pkg_pattern, pkg_type in self.PACKAGE_PATTERNS.items():
                if f"/{pkg_pattern}/" in file_path.lower() or f"\\{pkg_pattern}\\" in file_path.lower():
                    class_type = pkg_type
                    framework = "Domain Model"
                    break
        
        # Check annotations in content
        annotations = []
        if '@Service' in content:
            class_type = "SERVICE_LAYER"
            framework = "Spring"
            annotations.append("@Service")
        if '@Repository' in content:
            class_type = "DATA_ACCESS"
            framework = "Spring Data"
            annotations.append("@Repository")
        if '@Controller' in content or '@RestController' in content:
            class_type = "REST_CONTROLLER"
            framework = "Spring MVC"
            annotations.append("@Controller")
        if '@SessionScope' in content:
            annotations.append("@SessionScope")
            framework = "Stripes MVC"
        if '@Transactional' in content:
            annotations.append("@Transactional")
        
        # Check if it's an interface (likely Mapper)
        if 'interface ' in content and (class_name.endswith('Mapper') or 'Mapper' in class_name):
            class_type = "DATA_ACCESS"
            framework = "MyBatis"
        
        # Extract methods
        methods = self._extract_methods(content)
        
        # Extract fields for domain entities
        fields = []
        if class_type == "DOMAIN_ENTITY":
            fields = self._extract_fields(content)
        
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        package = package_match.group(1) if package_match else "default"
        
        return {
            "name": class_name,
            "file_path": file_path,
            "package": package,
            "type": class_type,
            "framework": framework,
            "annotations": annotations,
            "methods": methods,
            "fields": fields,
            "line_count": content.count('\n'),
            "confidence": 0.95 if class_type != "UNKNOWN" else 0.6
        }
    
    def _extract_methods(self, content: str) -> List[Dict]:
        """Extract method signatures from Java file."""
        methods = []
        
        # Match public/protected methods
        method_pattern = r'(?:public|protected)\s+(?:static\s+)?(?:synchronized\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3).strip()
            
            # Skip getters/setters for brevity
            if method_name.startswith('get') or method_name.startswith('set') or method_name.startswith('is'):
                continue
            
            methods.append({
                "name": method_name,
                "return_type": return_type,
                "parameters": params if params else "none",
            })
        
        return methods[:20]  # Limit to top 20 methods
    
    def _extract_fields(self, content: str) -> List[Dict]:
        """Extract field definitions from domain entities."""
        fields = []
        
        field_pattern = r'private\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*[;=]'
        
        for match in re.finditer(field_pattern, content):
            field_type = match.group(1)
            field_name = match.group(2)
            
            fields.append({
                "name": field_name,
                "type": field_type
            })
        
        return fields
    
    def _extract_imports(self, content: str):
        """Extract import statements to detect technology stack."""
        import_pattern = r'import\s+([\w.]+);'
        
        for match in re.finditer(import_pattern, content):
            import_stmt = match.group(1)
            
            for pattern, tech_info in self.IMPORT_PATTERNS.items():
                if import_stmt.startswith(pattern):
                    tech_name = tech_info["name"]
                    if tech_name not in self.tech_stack:
                        self.tech_stack[tech_name] = {
                            "category": tech_info["category"],
                            "import_count": 0,
                            "first_seen": import_stmt
                        }
                    self.tech_stack[tech_name]["import_count"] += 1
                    break
    
    def _extract_annotations(self, file_path: str, content: str):
        """Extract validation and business rule annotations."""
        for pattern in self.ANNOTATION_PATTERNS:
            for match in re.finditer(pattern, content):
                annotation = match.group(0)
                if file_path not in self.annotations_found:
                    self.annotations_found[file_path] = []
                self.annotations_found[file_path].append(annotation)
    
    def _track_package(self, file_path: str, class_info: Optional[Dict]):
        """Track packages and their contents."""
        if not class_info:
            return
        
        package = class_info.get("package", "default")
        if package not in self.packages:
            self.packages[package] = []
        self.packages[package].append(class_info["name"])
    
    def _analyze_build_files(self):
        """Analyze Maven/Gradle build files for dependencies."""
        # Check pom.xml
        pom_path = self.repo_path / "pom.xml"
        if pom_path.exists():
            self._analyze_pom(pom_path)
        
        # Check build.gradle
        gradle_path = self.repo_path / "build.gradle"
        if gradle_path.exists():
            self._analyze_gradle(gradle_path)
    
    def _analyze_pom(self, pom_path: Path):
        """Analyze Maven pom.xml for dependencies."""
        try:
            content = pom_path.read_text(encoding='utf-8')
            
            # Add Maven to tech stack
            self.tech_stack["Apache Maven"] = {"category": "Build Tool", "import_count": 1}
            
            # Extract dependencies
            dep_pattern = r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>'
            
            for match in re.finditer(dep_pattern, content, re.DOTALL):
                group_id = match.group(1).strip()
                artifact_id = match.group(2).strip()
                dep_key = f"{group_id}:{artifact_id}"
                
                if group_id not in self.dependencies:
                    self.dependencies[group_id] = []
                self.dependencies[group_id].append(artifact_id)
                
                # Map to tech stack
                self._map_dependency_to_tech(group_id, artifact_id)
            
            print(f"  Analyzed pom.xml - Found {sum(len(v) for v in self.dependencies.values())} dependencies")
            
        except Exception as e:
            print(f"  Warning: Could not parse pom.xml: {e}")
    
    def _analyze_gradle(self, gradle_path: Path):
        """Analyze Gradle build.gradle for dependencies."""
        try:
            content = gradle_path.read_text(encoding='utf-8')
            
            # Add Gradle to tech stack
            self.tech_stack["Gradle"] = {"category": "Build Tool", "import_count": 1}
            
            # Extract dependencies
            dep_pattern = r"(?:implementation|compile|api)\s*['\"]([^'\"]+)['\"]"
            
            for match in re.finditer(dep_pattern, content):
                dep = match.group(1)
                parts = dep.split(':')
                if len(parts) >= 2:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    
                    if group_id not in self.dependencies:
                        self.dependencies[group_id] = []
                    self.dependencies[group_id].append(artifact_id)
                    
                    self._map_dependency_to_tech(group_id, artifact_id)
            
            print(f"  Analyzed build.gradle")
            
        except Exception as e:
            print(f"  Warning: Could not parse build.gradle: {e}")
    
    def _map_dependency_to_tech(self, group_id: str, artifact_id: str):
        """Map Maven/Gradle dependency to technology stack."""
        tech_mappings = {
            "org.mybatis": "MyBatis",
            "net.sourceforge.stripes": "Stripes MVC",
            "org.springframework": "Spring Framework",
            "org.hsqldb": "HSQLDB",
            "log4j": "Log4j",
            "junit": "JUnit",
            "org.mockito": "Mockito",
        }
        
        for pattern, tech_name in tech_mappings.items():
            if pattern in group_id:
                if tech_name not in self.tech_stack:
                    self.tech_stack[tech_name] = {"category": "Dependency", "import_count": 0}
                self.tech_stack[tech_name]["import_count"] += 1
    
    def _analyze_config_files(self):
        """Analyze configuration files for additional insights."""
        config_patterns = ['*.xml', '*.properties', '*.yaml', '*.yml', '*.json']
        
        config_files = []
        for pattern in config_patterns:
            for root, dirs, files in os.walk(self.repo_path / "src"):
                dirs[:] = [d for d in dirs if d not in ['target', '.git']]
                for file in files:
                    if file.endswith(pattern[1:]):  # Remove *
                        config_files.append(os.path.join(root, file))
        
        print(f"  Found {len(config_files)} configuration files")
        
        # Special handling for MyBatis mappers
        for config_file in config_files:
            if 'Mapper.xml' in config_file or 'mybatis' in config_file.lower():
                if "MyBatis" not in self.tech_stack:
                    self.tech_stack["MyBatis"] = {"category": "ORM", "import_count": 0}
                self.tech_stack["MyBatis"]["import_count"] += 1
    
    def _generate_outputs(self) -> Dict[str, Any]:
        """Generate all discovery output files."""
        
        # Categorize artifacts
        categorized = self._categorize_artifacts()
        
        # 1. Artifact Catalog
        artifact_catalog = {
            "repository": self.repo_name,
            "scan_timestamp": datetime.now().isoformat(),
            "agent": "Agent 1: Discovery & Scoping",
            "confidence": self.confidence,
            "summary": {
                "total_artifacts": len(self.artifacts),
                "by_type": {k: len(v) for k, v in categorized.items()},
                "packages": len(self.packages)
            },
            "artifacts": self.artifacts,
            "packages": self.packages
        }
        self._write_json("artifact_catalog.json", artifact_catalog)
        
        # 2. Dependency Map
        dependency_map = {
            "repository": self.repo_name,
            "agent": "Agent 1: Discovery & Scoping",
            "confidence": self.confidence,
            "build_tool": "Maven" if "Apache Maven" in self.tech_stack else "Gradle" if "Gradle" in self.tech_stack else "Unknown",
            "dependencies": self.dependencies,
            "dependency_count": sum(len(v) for v in self.dependencies.values())
        }
        self._write_json("dependency_map.json", dependency_map)
        
        # 3. Scope Definition (comprehensive)
        scope_definition = self._generate_scope_definition(categorized)
        self._write_json("scope_definition.json", scope_definition)
        
        # 4. Test Case Analysis (CONSOLIDATED - replaces 4 separate test files)
        test_case_analysis = self._generate_test_case_analysis(categorized)
        self._write_json("test_case_analysis.json", test_case_analysis)
        
        return {
            "status": "success",
            "artifacts_found": len(self.artifacts),
            "technologies_detected": len(self.tech_stack),
            "confidence": self.confidence,
            "outputs": [
                "scope_definition.json",
                "artifact_catalog.json",
                "dependency_map.json",
                "test_case_analysis.json"
            ]
        }
    
    def _categorize_artifacts(self) -> Dict[str, List[Dict]]:
        """Categorize artifacts by type."""
        categorized = {}
        for artifact in self.artifacts:
            art_type = artifact.get("type", "UNKNOWN")
            if art_type not in categorized:
                categorized[art_type] = []
            categorized[art_type].append(artifact)
        return categorized
    
    def _generate_test_case_analysis(self, categorized: Dict) -> Dict:
        """Generate consolidated test case analysis (replaces 4 separate test files)."""
        test_artifacts = [a for a in self.artifacts if 'test' in a.get('path', '').lower() or 'test' in a.get('name', '').lower()]
        
        # Inventory
        by_type = {}
        for test in test_artifacts:
            test_type = 'unit' if 'unit' in test.get('path', '').lower() else 'integration' if 'integration' in test.get('path', '').lower() else 'e2e' if 'e2e' in test.get('path', '').lower() else 'unknown'
            by_type[test_type] = by_type.get(test_type, 0) + 1
        
        # Presence analysis
        components_with_tests = []
        for comp_type in ['WEB_CONTROLLER', 'REST_CONTROLLER', 'SERVICE_LAYER', 'DATA_ACCESS']:
            if categorized.get(comp_type):
                components_with_tests.append(comp_type)
        
        # Traceability mapping
        test_to_code_map = {}
        for test in test_artifacts[:10]:
            test_name = test.get('name', '')
            potential_target = test_name.replace('Test', '').replace('test_', '')
            matching_artifacts = [a['path'] for a in self.artifacts if potential_target in a.get('name', '')]
            if matching_artifacts:
                test_to_code_map[test.get('path', '')] = matching_artifacts[:3]
        
        # Detailed test cases
        test_case_details = []
        for idx, test in enumerate(test_artifacts[:20], 1):
            test_case_details.append({
                "id": f"TC-{idx:03d}",
                "file": test.get('path', ''),
                "name": test.get('name', ''),
                "type": 'unit' if 'unit' in test.get('path', '').lower() else 'integration',
                "priority": 'high' if 'controller' in test.get('path', '').lower() or 'service' in test.get('path', '').lower() else 'medium'
            })
        
        return {
            "repository": self.repo_name,
            "generated_date": datetime.now().isoformat(),
            "agent": "Agent 1: Discovery & Scoping",
            "confidence": self.confidence,
            "inventory": {
                "total_tests": len(test_artifacts),
                "by_type": by_type
            },
            "presence": {
                "components_with_tests": components_with_tests,
                "coverage_percentage": round(len(test_artifacts) / max(len(self.artifacts), 1) * 100, 2) if self.artifacts else 0
            },
            "traceability": {
                "test_to_code_map": test_to_code_map,
                "mapped_tests": len(test_to_code_map)
            },
            "details": {
                "test_cases": test_case_details
            }
        }
    
    def _generate_scope_definition(self, categorized: Dict) -> Dict:
        """Generate comprehensive scope definition."""
        return {
            "repository": self.repo_name,
            "repository_path": str(self.repo_path),
            "analysis_timestamp": datetime.now().isoformat(),
            "scope_summary": {
                "description": f"Java application using {', '.join(list(self.tech_stack.keys())[:5])}",
                "primary_language": "Java",
                "build_system": "Maven" if "Apache Maven" in self.tech_stack else "Gradle",
                "architecture_pattern": self._detect_architecture_pattern(categorized),
                "total_java_classes": len(self.artifacts),
            },
            "technology_stack": {
                "frameworks": [k for k, v in self.tech_stack.items() if v.get("category") in ["Web Framework", "Application Framework", "ORM"]],
                "databases": [k for k, v in self.tech_stack.items() if v.get("category") == "Database"],
                "testing": [k for k, v in self.tech_stack.items() if v.get("category") == "Testing"],
                "build_tools": [k for k, v in self.tech_stack.items() if v.get("category") == "Build Tool"],
                "all_technologies": self.tech_stack
            },
            "components": {
                "controllers": [a["name"] for a in categorized.get("WEB_CONTROLLER", []) + categorized.get("REST_CONTROLLER", [])],
                "services": [a["name"] for a in categorized.get("SERVICE_LAYER", [])],
                "data_access": [a["name"] for a in categorized.get("DATA_ACCESS", [])],
                "domain_entities": [a["name"] for a in categorized.get("DOMAIN_ENTITY", [])],
            },
            "business_capabilities": self._infer_business_capabilities(categorized),
            "annotations_summary": {
                "total_files_with_annotations": len(self.annotations_found),
                "validation_rules_found": sum(1 for anns in self.annotations_found.values() for a in anns if 'Validate' in a),
                "transactional_methods": sum(1 for anns in self.annotations_found.values() for a in anns if 'Transactional' in a),
            },
            "confidence": self.confidence
        }
    
    def _detect_architecture_pattern(self, categorized: Dict) -> str:
        """Detect the architecture pattern based on artifacts."""
        has_controllers = bool(categorized.get("WEB_CONTROLLER") or categorized.get("REST_CONTROLLER"))
        has_services = bool(categorized.get("SERVICE_LAYER"))
        has_data_access = bool(categorized.get("DATA_ACCESS"))
        has_domain = bool(categorized.get("DOMAIN_ENTITY"))
        
        if has_controllers and has_services and has_data_access:
            if "Stripes MVC" in self.tech_stack:
                return "Stripes MVC with Service Layer"
            return "MVC with Service Layer"
        elif has_controllers and has_services:
            return "MVC Pattern"
        elif has_services and has_data_access:
            return "Service-Repository Pattern"
        else:
            return "Traditional Java Application"
    
    def _infer_business_capabilities(self, categorized: Dict) -> List[Dict]:
        """Infer business capabilities from service and controller names."""
        capabilities = []
        
        # Extract from service names
        services = categorized.get("SERVICE_LAYER", [])
        for svc in services:
            name = svc["name"].replace("Service", "").replace("Impl", "")
            if name:
                capabilities.append({
                    "name": f"{name} Management",
                    "source": svc["name"],
                    "type": "service"
                })
        
        # Extract from controller/actionbean names
        controllers = categorized.get("WEB_CONTROLLER", []) + categorized.get("REST_CONTROLLER", [])
        for ctrl in controllers:
            name = ctrl["name"].replace("ActionBean", "").replace("Controller", "").replace("Action", "")
            if name and not any(c["name"].startswith(name) for c in capabilities):
                capabilities.append({
                    "name": f"{name} Operations",
                    "source": ctrl["name"],
                    "type": "controller"
                })
        
        return capabilities
    
    def _generate_system_overview(self, categorized: Dict) -> Dict:
        """Generate system overview for downstream agents."""
        return {
            "system_name": self.repo_name,
            "description": f"Java web application built with {self._get_primary_framework()}",
            "architecture": {
                "pattern": self._detect_architecture_pattern(categorized),
                "layers": {
                    "presentation": {
                        "framework": self._get_primary_framework(),
                        "components": [a["name"] for a in categorized.get("WEB_CONTROLLER", []) + categorized.get("REST_CONTROLLER", [])]
                    },
                    "business": {
                        "framework": "Spring" if "Spring Framework" in self.tech_stack else "Plain Java",
                        "components": [a["name"] for a in categorized.get("SERVICE_LAYER", [])]
                    },
                    "data": {
                        "framework": "MyBatis" if "MyBatis" in self.tech_stack else "JDBC",
                        "components": [a["name"] for a in categorized.get("DATA_ACCESS", [])]
                    },
                    "domain": {
                        "entities": [a["name"] for a in categorized.get("DOMAIN_ENTITY", [])]
                    }
                }
            },
            "technology_stack": list(self.tech_stack.keys()),
            "packages": list(self.packages.keys()),
            "class_details": {
                artifact["name"]: {
                    "type": artifact["type"],
                    "package": artifact["package"],
                    "methods": artifact.get("methods", []),
                    "fields": artifact.get("fields", [])
                }
                for artifact in self.artifacts
            }
        }
    
    def _get_primary_framework(self) -> str:
        """Get the primary web framework."""
        if "Stripes MVC" in self.tech_stack:
            return "Stripes MVC"
        elif "Spring MVC" in self.tech_stack:
            return "Spring MVC"
        elif "Spring Framework" in self.tech_stack:
            return "Spring"
        return "Java Servlets"
    
    def _get_framework_summary(self) -> Dict:
        """Get a summary of frameworks detected."""
        return {
            "web_framework": self._get_primary_framework(),
            "orm": "MyBatis" if "MyBatis" in self.tech_stack else "JDBC" if "JDBC" in self.tech_stack else "None detected",
            "dependency_injection": "Spring" if "Spring Framework" in self.tech_stack else "None detected",
            "database": next((k for k, v in self.tech_stack.items() if v.get("category") == "Database"), "Unknown")
        }
    
    def _write_json(self, filename: str, data: Dict):
        """Write JSON output file."""
        output_file = self.output_path / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Written: {filename}")
    
    def _generate_error_outputs(self, error: str) -> Dict:
        """Generate minimal outputs in case of error."""
        error_data = {
            "repository": self.repo_name,
            "error": error,
            "confidence": self.confidence,
            "agent": "Agent 1: Discovery & Scoping",
            "timestamp": datetime.now().isoformat()
        }
        
        self._write_json("scope_definition.json", error_data)
        self._write_json("artifact_catalog.json", {"artifacts": [], "error": error, "agent": "Agent 1: Discovery & Scoping"})
        self._write_json("dependency_map.json", {"dependencies": {}, "error": error, "agent": "Agent 1: Discovery & Scoping"})
        self._write_json("test_case_analysis.json", {"inventory": {}, "presence": {}, "traceability": {}, "details": {}, "error": error, "agent": "Agent 1: Discovery & Scoping"})
        
        return {
            "status": "error",
            "error": error,
            "confidence": self.confidence
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 1: Enhanced Discovery & Scoping")
    parser.add_argument("repo_path", nargs="?", help="Path to repository to analyze")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    # Get repo path
    repo_path = args.repo_path
    if not repo_path:
        config = ConfigLoader(args.config)
        repo_path = config.get("repository.path", ".")
    
    # Run agent
    agent = EnhancedDiscoveryAgent(
        repo_path=repo_path,
        config_path=args.config,
        output_path=args.output
    )
    
    result = agent.run()
    
    # Exit with appropriate code
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
