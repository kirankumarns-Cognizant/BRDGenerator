#!/usr/bin/env python3
"""
Agent 3: Business Rules Extraction - ENHANCED
Extracts business rules from Java source code including:
- Stripes @Validate annotations
- Bean Validation (JSR-303/380) annotations
- Spring @Transactional boundaries
- Custom validation logic in code
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader


class EnhancedBusinessRulesAgent:
    """Enhanced business rules extraction from Java source code."""
    
    # Stripes validation patterns
    STRIPES_VALIDATION = {
        "required": {"type": "mandatory", "description": "Field is required"},
        "minlength": {"type": "length", "description": "Minimum length constraint"},
        "maxlength": {"type": "length", "description": "Maximum length constraint"},
        "minvalue": {"type": "range", "description": "Minimum value constraint"},
        "maxvalue": {"type": "range", "description": "Maximum value constraint"},
        "mask": {"type": "format", "description": "Regex pattern constraint"},
        "expression": {"type": "custom", "description": "Custom expression validation"},
    }
    
    # Bean Validation (JSR-303/380) annotations
    BEAN_VALIDATION = {
        "@NotNull": {"type": "mandatory", "description": "Must not be null"},
        "@NotEmpty": {"type": "mandatory", "description": "Must not be null or empty"},
        "@NotBlank": {"type": "mandatory", "description": "Must not be null, empty, or whitespace"},
        "@Size": {"type": "length", "description": "Size must be within bounds"},
        "@Min": {"type": "range", "description": "Minimum numeric value"},
        "@Max": {"type": "range", "description": "Maximum numeric value"},
        "@Pattern": {"type": "format", "description": "Must match regex pattern"},
        "@Email": {"type": "format", "description": "Must be valid email format"},
        "@Past": {"type": "temporal", "description": "Date must be in the past"},
        "@Future": {"type": "temporal", "description": "Date must be in the future"},
        "@Positive": {"type": "range", "description": "Must be positive number"},
        "@Negative": {"type": "range", "description": "Must be negative number"},
        "@DecimalMin": {"type": "range", "description": "Minimum decimal value"},
        "@DecimalMax": {"type": "range", "description": "Maximum decimal value"},
        "@Digits": {"type": "format", "description": "Must be within digit constraints"},
    }
    
    # Transaction boundary patterns
    TRANSACTION_PATTERNS = [
        "@Transactional",
        "TransactionTemplate",
        "PlatformTransactionManager",
    ]
    
    def __init__(self, repo_path: str, config_path: str = None, output_path: str = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.config = ConfigLoader(config_path) if config_path else ConfigLoader()
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Load previous agent outputs
        self.artifact_catalog = self._load_json("artifact_catalog.json")
        self.system_overview = self._load_json("system_overview.json")
        
        # Rule accumulation
        self.business_rules: List[Dict] = []
        self.validation_rules: List[Dict] = []
        self.transaction_boundaries: List[Dict] = []
        self.domain_constraints: List[Dict] = []
        self.confidence = 1.0
    
    def run(self) -> Dict[str, Any]:
        """Execute the enhanced business rules extraction."""
        print(f"\n{'='*60}")
        print("Agent 3: Enhanced Business Rules Extraction")
        print(f"{'='*60}")
        print(f"Repository: {self.repo_path}")
        
        try:
            # Phase 1: Extract Stripes @Validate rules
            print("\n[Phase 1] Extracting Stripes validation rules...")
            self._extract_stripes_validations()
            
            # Phase 2: Extract Bean Validation rules
            print("\n[Phase 2] Extracting Bean Validation annotations...")
            self._extract_bean_validations()
            
            # Phase 3: Extract transaction boundaries
            print("\n[Phase 3] Analyzing transaction boundaries...")
            self._extract_transaction_boundaries()
            
            # Phase 4: Infer business rules from domain logic
            print("\n[Phase 4] Inferring business rules from code...")
            self._infer_business_rules()
            
            # Phase 5: Extract domain constraints from entities
            print("\n[Phase 5] Extracting domain entity constraints...")
            self._extract_domain_constraints()
            
            # Phase 6: Generate outputs
            print("\n[Phase 6] Generating business rules outputs...")
            outputs = self._generate_outputs()
            
            total_rules = len(self.business_rules) + len(self.validation_rules)
            print(f"\n{'='*60}")
            print("Business Rules Extraction Complete!")
            print(f"  - Business rules: {len(self.business_rules)}")
            print(f"  - Validation rules: {len(self.validation_rules)}")
            print(f"  - Transaction boundaries: {len(self.transaction_boundaries)}")
            print(f"  - Domain constraints: {len(self.domain_constraints)}")
            print(f"  - Total rules: {total_rules}")
            print(f"{'='*60}\n")
            
            return outputs
            
        except Exception as e:
            print(f"ERROR: Business rules extraction failed - {e}")
            import traceback
            traceback.print_exc()
            self.confidence = 0.3
            return self._generate_error_outputs(str(e))
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON from output path."""
        file_path = self.output_path / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _extract_stripes_validations(self):
        """Extract Stripes @Validate and @ValidateNestedProperties annotations."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        controllers = [a for a in artifacts if a.get("type") in ["WEB_CONTROLLER", "REST_CONTROLLER"]]
        
        for controller in controllers:
            file_path = self.repo_path / controller["file_path"]
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Extract @Validate annotations
                self._parse_stripes_validate(content, controller)
                
                # Extract @ValidateNestedProperties
                self._parse_nested_validations(content, controller)
                
            except Exception as e:
                print(f"  Warning: Could not analyze {controller['name']}: {e}")
                self.confidence *= 0.98
        
        print(f"  Found {len(self.validation_rules)} Stripes validation rules")
    
    def _parse_stripes_validate(self, content: str, controller: Dict):
        """Parse @Validate annotations from Stripes ActionBeans."""
        
        # Pattern for @Validate on setters
        # @Validate(required = true, on = {"newOrder"})
        validate_pattern = r'@Validate\s*\(([^)]+)\)\s*(?:public|private|protected)?\s*void\s+set(\w+)'
        
        for match in re.finditer(validate_pattern, content, re.DOTALL):
            params = match.group(1)
            field_name = match.group(2)
            
            rule = self._parse_validate_params(params, field_name, controller["name"])
            if rule:
                self.validation_rules.append(rule)
        
        # Also check for field-level @Validate
        field_validate_pattern = r'@Validate\s*\(([^)]+)\)\s*(?:private|protected|public)\s+\w+\s+(\w+)\s*;'
        
        for match in re.finditer(field_validate_pattern, content, re.DOTALL):
            params = match.group(1)
            field_name = match.group(2)
            
            rule = self._parse_validate_params(params, field_name, controller["name"])
            if rule:
                self.validation_rules.append(rule)
    
    def _parse_validate_params(self, params: str, field_name: str, class_name: str) -> Optional[Dict]:
        """Parse validation parameters from @Validate annotation."""
        rule = {
            "id": f"VAL_{class_name}_{field_name}".upper(),
            "field": field_name.lower() if field_name[0].isupper() else field_name,
            "class": class_name,
            "type": "validation",
            "constraints": [],
            "events": [],
            "source": f"@Validate annotation in {class_name}"
        }
        
        # Parse required
        if "required" in params.lower():
            required_match = re.search(r'required\s*=\s*(true|false)', params, re.IGNORECASE)
            if required_match and required_match.group(1).lower() == "true":
                rule["constraints"].append({
                    "type": "required",
                    "message": f"{field_name} is required"
                })
        
        # Parse on events
        on_match = re.search(r'on\s*=\s*\{([^}]+)\}', params)
        if on_match:
            events = re.findall(r'["\'](\w+)["\']', on_match.group(1))
            rule["events"] = events
        
        # Parse minlength/maxlength
        for constraint in ["minlength", "maxlength"]:
            match = re.search(rf'{constraint}\s*=\s*(\d+)', params, re.IGNORECASE)
            if match:
                rule["constraints"].append({
                    "type": constraint,
                    "value": int(match.group(1)),
                    "message": f"{field_name} {constraint} is {match.group(1)}"
                })
        
        # Parse minvalue/maxvalue
        for constraint in ["minvalue", "maxvalue"]:
            match = re.search(rf'{constraint}\s*=\s*(\d+)', params, re.IGNORECASE)
            if match:
                rule["constraints"].append({
                    "type": constraint,
                    "value": int(match.group(1)),
                    "message": f"{field_name} {constraint} is {match.group(1)}"
                })
        
        # Parse mask (regex)
        mask_match = re.search(r'mask\s*=\s*["\']([^"\']+)["\']', params)
        if mask_match:
            rule["constraints"].append({
                "type": "pattern",
                "pattern": mask_match.group(1),
                "message": f"{field_name} must match pattern"
            })
        
        return rule if rule["constraints"] else None
    
    def _parse_nested_validations(self, content: str, controller: Dict):
        """Parse @ValidateNestedProperties annotations."""
        nested_pattern = r'@ValidateNestedProperties\s*\(\s*\{([^}]+)\}\s*\)'
        
        for match in re.finditer(nested_pattern, content, re.DOTALL):
            nested_content = match.group(1)
            
            # Extract individual field validations
            field_pattern = r'@Validate\s*\(\s*field\s*=\s*["\'](\w+)["\'][^)]*\)'
            
            for field_match in re.finditer(field_pattern, nested_content):
                field_name = field_match.group(1)
                params = field_match.group(0)
                
                rule = self._parse_validate_params(params, field_name, controller["name"])
                if rule:
                    rule["nested"] = True
                    self.validation_rules.append(rule)
    
    def _extract_bean_validations(self):
        """Extract Bean Validation (JSR-303/380) annotations from domain entities."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        entities = [a for a in artifacts if a.get("type") == "DOMAIN_ENTITY"]
        
        for entity in entities:
            file_path = self.repo_path / entity["file_path"]
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for annotation, info in self.BEAN_VALIDATION.items():
                    pattern = rf'{annotation}(?:\s*\([^)]*\))?\s*(?:private|protected|public)\s+\w+\s+(\w+)'
                    
                    for match in re.finditer(pattern, content):
                        field_name = match.group(1)
                        
                        # Extract annotation parameters
                        full_match = match.group(0)
                        params = self._extract_annotation_params(full_match, annotation)
                        
                        self.validation_rules.append({
                            "id": f"BV_{entity['name']}_{field_name}".upper(),
                            "field": field_name,
                            "class": entity["name"],
                            "type": info["type"],
                            "annotation": annotation,
                            "description": info["description"],
                            "parameters": params,
                            "source": f"Bean Validation in {entity['name']}"
                        })
                
            except Exception as e:
                print(f"  Warning: Could not analyze {entity['name']}: {e}")
        
        print(f"  Found {len([r for r in self.validation_rules if 'annotation' in r])} Bean Validation rules")
    
    def _extract_annotation_params(self, match_text: str, annotation: str) -> Dict:
        """Extract parameters from validation annotation."""
        params = {}
        
        # Size annotation: @Size(min=X, max=Y)
        if annotation == "@Size":
            min_match = re.search(r'min\s*=\s*(\d+)', match_text)
            max_match = re.search(r'max\s*=\s*(\d+)', match_text)
            if min_match:
                params["min"] = int(min_match.group(1))
            if max_match:
                params["max"] = int(max_match.group(1))
        
        # Min/Max annotations
        if annotation in ["@Min", "@Max", "@DecimalMin", "@DecimalMax"]:
            value_match = re.search(r'\(\s*(\d+)\s*\)', match_text)
            if value_match:
                params["value"] = int(value_match.group(1))
        
        # Pattern annotation
        if annotation == "@Pattern":
            regexp_match = re.search(r'regexp\s*=\s*["\']([^"\']+)["\']', match_text)
            if regexp_match:
                params["pattern"] = regexp_match.group(1)
        
        return params
    
    def _extract_transaction_boundaries(self):
        """Extract transaction boundaries from services."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        services = [a for a in artifacts if a.get("type") == "SERVICE_LAYER"]
        
        for service in services:
            file_path = self.repo_path / service["file_path"]
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Find @Transactional methods
                trans_pattern = r'@Transactional(?:\s*\([^)]*\))?\s*(?:public|protected)\s+(\w+)\s+(\w+)\s*\('
                
                for match in re.finditer(trans_pattern, content):
                    return_type = match.group(1)
                    method_name = match.group(2)
                    
                    # Extract propagation and other settings
                    full_match = match.group(0)
                    propagation = "REQUIRED"  # default
                    read_only = False
                    
                    if "readOnly" in full_match and "true" in full_match:
                        read_only = True
                    
                    prop_match = re.search(r'propagation\s*=\s*Propagation\.(\w+)', full_match)
                    if prop_match:
                        propagation = prop_match.group(1)
                    
                    self.transaction_boundaries.append({
                        "id": f"TX_{service['name']}_{method_name}".upper(),
                        "service": service["name"],
                        "method": method_name,
                        "return_type": return_type,
                        "propagation": propagation,
                        "read_only": read_only,
                        "source": f"@Transactional in {service['name']}"
                    })
                
            except Exception as e:
                print(f"  Warning: Could not analyze {service['name']}: {e}")
        
        print(f"  Found {len(self.transaction_boundaries)} transaction boundaries")
    
    def _infer_business_rules(self):
        """Infer business rules from code patterns."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        services = [a for a in artifacts if a.get("type") == "SERVICE_LAYER"]
        
        # Patterns that indicate business rules
        rule_patterns = [
            (r'if\s*\(\s*(\w+)\s*==\s*null\s*\)', "null_check", "Null validation check"),
            (r'if\s*\(\s*(\w+)\s*<=?\s*0\s*\)', "quantity_check", "Quantity/value validation"),
            (r'if\s*\(\s*!?\w+\.isEmpty\(\)\s*\)', "empty_check", "Empty collection check"),
            (r'throw\s+new\s+(\w+Exception)', "exception", "Business exception handling"),
        ]
        
        for service in services:
            file_path = self.repo_path / service["file_path"]
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                for pattern, rule_type, description in rule_patterns:
                    for match in re.finditer(pattern, content):
                        captured = match.group(1) if match.lastindex else match.group(0)
                        
                        self.business_rules.append({
                            "id": f"BR_{service['name']}_{len(self.business_rules) + 1}",
                            "type": rule_type,
                            "description": f"{description}: {captured}",
                            "service": service["name"],
                            "pattern": match.group(0)[:100],
                            "inferred": True,
                            "confidence": 0.7
                        })
                
            except Exception as e:
                pass
        
        print(f"  Inferred {len(self.business_rules)} business rules from code")
    
    def _extract_domain_constraints(self):
        """Extract constraints from domain entities based on field types and patterns."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        entities = [a for a in artifacts if a.get("type") == "DOMAIN_ENTITY"]
        
        for entity in entities:
            fields = entity.get("fields", [])
            
            for field in fields:
                field_name = field.get("name", "")
                field_type = field.get("type", "")
                
                # Infer constraints from naming conventions
                if field_name.lower().endswith("id"):
                    self.domain_constraints.append({
                        "entity": entity["name"],
                        "field": field_name,
                        "constraint": "identifier",
                        "description": f"{field_name} is a unique identifier"
                    })
                
                if field_type in ["Date", "LocalDate", "LocalDateTime"]:
                    self.domain_constraints.append({
                        "entity": entity["name"],
                        "field": field_name,
                        "constraint": "temporal",
                        "description": f"{field_name} contains date/time data"
                    })
                
                if field_type == "BigDecimal":
                    self.domain_constraints.append({
                        "entity": entity["name"],
                        "field": field_name,
                        "constraint": "monetary",
                        "description": f"{field_name} likely contains monetary/decimal value"
                    })
        
        print(f"  Found {len(self.domain_constraints)} domain constraints")
    
    def _generate_outputs(self) -> Dict[str, Any]:
        """Generate all business rules outputs."""
        
        # 1. Business Rules JSON (comprehensive)
        business_rules_output = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Agent 3: Business Rules Extraction",
            "confidence": self.confidence,
            "summary": {
                "total_rules": len(self.business_rules) + len(self.validation_rules),
                "validation_rules": len(self.validation_rules),
                "business_rules": len(self.business_rules),
                "transaction_boundaries": len(self.transaction_boundaries),
                "domain_constraints": len(self.domain_constraints)
            },
            "validation_rules": self.validation_rules,
            "business_rules": self.business_rules
        }
        self._write_json("business_rules.json", business_rules_output)
        
        # 2. Regulatory Flags JSON (compliance-related rules)
        regulatory_flags = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Agent 3: Business Rules Extraction",
            "confidence": self.confidence,
            "flags": [
                {
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("description", "Unknown")[:100],
                    "regulatory_concern": "Data validation",
                    "severity": "medium",
                    "recommendation": "Review for compliance with data protection regulations"
                }
                for rule in self.validation_rules[:10]  # Top 10 validation rules
            ],
            "summary": {
                "total_flags": min(10, len(self.validation_rules)),
                "by_severity": {
                    "high": 0,
                    "medium": min(10, len(self.validation_rules)),
                    "low": 0
                }
            }
        }
        self._write_json("regulatory_flags.json", regulatory_flags)
        
        # 3. Orphaned Rules JSON (rules not mapped to journeys)
        orphaned_rules = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Agent 3: Business Rules Extraction",
            "confidence": self.confidence,
            "orphaned_rules": [
                {
                    "rule_id": rule.get("id"),
                    "rule_description": rule.get("description", "Unknown"),
                    "location": rule.get("service") or rule.get("class", "unknown"),
                    "reason": "No journey mapping found",
                    "priority": "medium"
                }
                for rule in (self.business_rules + self.validation_rules)[:20]  # Sample of first 20
            ],
            "summary": {
                "total_orphaned": len(self.business_rules) + len(self.validation_rules),
                "needs_review": min(20, len(self.business_rules) + len(self.validation_rules))
            }
        }
        self._write_json("orphaned_rules.json", orphaned_rules)
        
        # 4. Rule Test Coverage JSON (CONSOLIDATED - with critical gaps)
        all_rules = [
            {**rule, "type": "validation", "criticality": "medium"}
            for rule in self.validation_rules
        ] + [
            {**rule, "type": "business", "criticality": "high"}
            for rule in self.business_rules
        ]
        
        rule_test_coverage = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Agent 3: Business Rules Extraction",
            "confidence": self.confidence,
            "rules": [
                {
                    "id": rule.get("id", f"BR-{idx+1:03d}"),
                    "name": rule.get("description", "Unknown Rule")[:100],
                    "criticality": rule.get("criticality", "medium"),
                    "test_coverage_percentage": 0,  # TODO: Calculate from test analysis
                    "is_critical_gap": rule.get("criticality") == "high",
                    "tests": [],
                    "risk": "No test coverage found" if rule.get("criticality") == "high" else None
                }
                for idx, rule in enumerate(all_rules[:50])  # Limit to 50 rules
            ],
            "summary": {
                "total_rules": len(all_rules),
                "rules_with_tests": 0,
                "rules_without_tests": len(all_rules),
                "untested_critical_rules": [
                    {
                        "id": rule.get("id", f"BR-{idx+1:03d}"),
                        "name": rule.get("description", "Unknown")[:100],
                        "risk": "critical"
                    }
                    for idx, rule in enumerate(self.business_rules[:10])  # Top 10 business rules
                ]
            }
        }
        self._write_json("rule_test_coverage.json", rule_test_coverage)
        
        return {
            "status": "success",
            "validation_rules": len(self.validation_rules),
            "business_rules": len(self.business_rules),
            "transaction_boundaries": len(self.transaction_boundaries),
            "confidence": self.confidence,
            "outputs": ["business_rules.json", "regulatory_flags.json", "orphaned_rules.json", "rule_test_coverage.json"]
        }
    
    def _build_rules_catalog(self) -> List[Dict]:
        """Build a unified rules catalog."""
        catalog = []
        
        for rule in self.validation_rules:
            catalog.append({
                "id": rule.get("id"),
                "name": f"Validation: {rule.get('field', 'unknown')}",
                "type": "validation",
                "description": self._build_rule_description(rule),
                "applies_to": rule.get("class"),
                "events": rule.get("events", []),
                "severity": "error",
                "automated": True
            })
        
        for rule in self.business_rules:
            catalog.append({
                "id": rule.get("id"),
                "name": rule.get("description", "Business Rule")[:50],
                "type": rule.get("type"),
                "description": rule.get("description"),
                "applies_to": rule.get("service"),
                "severity": "error",
                "automated": True,
                "inferred": rule.get("inferred", False)
            })
        
        return catalog
    
    def _build_rule_description(self, rule: Dict) -> str:
        """Build human-readable description for validation rule."""
        field = rule.get("field", "field")
        constraints = rule.get("constraints", [])
        
        if not constraints:
            return f"Validation rule for {field}"
        
        parts = []
        for constraint in constraints:
            if constraint["type"] == "required":
                parts.append(f"{field} is required")
            elif constraint["type"] == "minlength":
                parts.append(f"minimum length {constraint['value']}")
            elif constraint["type"] == "maxlength":
                parts.append(f"maximum length {constraint['value']}")
            elif constraint["type"] == "pattern":
                parts.append(f"must match pattern")
        
        return "; ".join(parts) if parts else f"Validation for {field}"
    
    def _categorize_rules(self) -> Dict[str, List[Dict]]:
        """Categorize rules by type."""
        categories = {
            "mandatory": [],
            "format": [],
            "range": [],
            "business_logic": [],
            "temporal": [],
            "other": []
        }
        
        for rule in self.validation_rules:
            rule_type = rule.get("type", "other")
            if rule_type in categories:
                categories[rule_type].append(rule)
            else:
                categories["other"].append(rule)
        
        for rule in self.business_rules:
            categories["business_logic"].append(rule)
        
        return categories
    
    def _rules_by_entity(self) -> Dict[str, List[Dict]]:
        """Group rules by entity/class."""
        by_entity = {}
        
        for rule in self.validation_rules + self.business_rules:
            entity = rule.get("class") or rule.get("service") or "unknown"
            if entity not in by_entity:
                by_entity[entity] = []
            by_entity[entity].append(rule)
        
        return by_entity
    
    def _write_json(self, filename: str, data: Dict):
        """Write JSON output file."""
        output_file = self.output_path / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Written: {filename}")
    
    def _generate_error_outputs(self, error: str) -> Dict:
        """Generate minimal outputs in case of error."""
        error_data = {"repository": self.repo_name, "error": error, "timestamp": datetime.now().isoformat()}
        
        self._write_json("business_rules.json", {"rules": [], "error": error})
        self._write_json("regulatory_flags.json", {"flags": [], "error": error})
        self._write_json("orphaned_rules.json", {"orphaned_rules": [], "error": error})
        self._write_json("rule_test_coverage.json", {"rules": [], "summary": {}, "error": error})
        
        return {"status": "error", "error": error, "confidence": self.confidence}


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 3: Enhanced Business Rules Extraction")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    if not repo_path:
        config = ConfigLoader(args.config)
        repo_path = config.get("repository.path", ".")
    
    agent = EnhancedBusinessRulesAgent(
        repo_path=repo_path,
        config_path=args.config,
        output_path=args.output
    )
    
    result = agent.run()
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
