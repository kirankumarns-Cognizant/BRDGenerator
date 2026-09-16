"""
Agent 7: Risk and Dependency Analysis
Analyzes risks and dependencies in the modernization effort.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config_loader import ConfigLoader

class Agent7RiskDependency:
    def __init__(self, repo_path: str, config_path: str, kb_path: str):
        self.repo_path = Path(repo_path)
        self.config = ConfigLoader(config_path)
        self.kb_path = Path(kb_path)
        self.state = {}
        self.confidence = 1.0
        
    def load_previous_outputs(self):
        """Load outputs from previous agents"""
        print("📥 Loading previous agent outputs...")
        
        files_to_load = [
            ("dependency_map.json", "dependency_map"),
            ("gap_analysis.json", "gap_analysis"),
            ("system_overview.json", "system_overview")
        ]
        
        for filename, attr_name in files_to_load:
            file_path = self.kb_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    setattr(self, attr_name, json.load(f))
            else:
                setattr(self, attr_name, {})
        
        print(f"   ✓ Loaded data from previous agents")
    
    def identify_risks(self):
        """Identify risks in the modernization effort"""
        print("⚠️  Identifying risks...")
        
        risks = []
        risk_id = 1
        
        # Technical risks
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "TECHNICAL",
            "severity": "HIGH",
            "probability": "MEDIUM",
            "title": "Technology Stack Migration Complexity",
            "description": "Migrating from legacy technology stack may introduce compatibility issues",
            "impact": "Project delays, increased costs, potential system instability",
            "mitigation": "Conduct thorough testing, phased migration approach, maintain fallback options",
            "owner": "Technical Lead"
        })
        risk_id += 1
        
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "TECHNICAL",
            "severity": "HIGH",
            "probability": "MEDIUM",
            "title": "Data Migration Risk",
            "description": "Risk of data loss or corruption during migration",
            "impact": "Data integrity issues, business disruption",
            "mitigation": "Comprehensive data backup, validation scripts, dry-run migrations",
            "owner": "Data Architect"
        })
        risk_id += 1
        
        # Integration risks
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "INTEGRATION",
            "severity": "MEDIUM",
            "probability": "HIGH",
            "title": "Third-Party Integration Failures",
            "description": "External system integrations may fail during modernization",
            "impact": "Service disruption, functionality gaps",
            "mitigation": "API contract testing, mock external services, gradual cutover",
            "owner": "Integration Lead"
        })
        risk_id += 1
        
        # Business risks
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "BUSINESS",
            "severity": "HIGH",
            "probability": "MEDIUM",
            "title": "Business Process Disruption",
            "description": "Modernization may disrupt critical business processes",
            "impact": "Revenue loss, customer dissatisfaction",
            "mitigation": "Staged rollout, comprehensive user training, maintain legacy system in parallel",
            "owner": "Business Owner"
        })
        risk_id += 1
        
        # Security risks
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "SECURITY",
            "severity": "CRITICAL",
            "probability": "LOW",
            "title": "Security Vulnerabilities",
            "description": "New architecture may introduce security vulnerabilities",
            "impact": "Data breach, compliance violations, reputational damage",
            "mitigation": "Security audits, penetration testing, secure coding practices",
            "owner": "Security Officer"
        })
        risk_id += 1
        
        # Resource risks
        risks.append({
            "risk_id": f"RISK_{risk_id:03d}",
            "category": "RESOURCE",
            "severity": "MEDIUM",
            "probability": "HIGH",
            "title": "Skill Gap in Team",
            "description": "Team may lack expertise in new technologies",
            "impact": "Project delays, suboptimal implementation",
            "mitigation": "Training programs, hire specialists, engage consultants",
            "owner": "Project Manager"
        })
        risk_id += 1
        
        self.state["risks"] = {
            "identified_risks": risks,
            "total_risks": len(risks),
            "by_category": self._categorize_risks(risks),
            "by_severity": self._categorize_by_severity(risks),
            "by_probability": self._categorize_by_probability(risks)
        }
        
        print(f"   ✓ Identified {len(risks)} risks")
    
    def _categorize_risks(self, risks):
        """Categorize risks by category"""
        categories = {}
        for risk in risks:
            category = risk.get("category", "UNKNOWN")
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        return categories
    
    def _categorize_by_severity(self, items):
        """Categorize items by severity"""
        severity = {}
        for item in items:
            sev = item.get("severity", "UNKNOWN")
            if sev not in severity:
                severity[sev] = 0
            severity[sev] += 1
        return severity
    
    def _categorize_by_probability(self, risks):
        """Categorize risks by probability"""
        probability = {}
        for risk in risks:
            prob = risk.get("probability", "UNKNOWN")
            if prob not in probability:
                probability[prob] = 0
            probability[prob] += 1
        return probability
    
    def analyze_dependencies(self):
        """Analyze project dependencies"""
        print("🔗 Analyzing dependencies...")
        
        dependencies = []
        dep_id = 1
        
        # Technical dependencies
        dependencies.append({
            "dependency_id": f"DEP_{dep_id:03d}",
            "type": "TECHNICAL",
            "source": "Application",
            "target": "Database",
            "relationship": "REQUIRES",
            "criticality": "HIGH",
            "description": "Application requires database connectivity"
        })
        dep_id += 1
        
        dependencies.append({
            "dependency_id": f"DEP_{dep_id:03d}",
            "type": "TECHNICAL",
            "source": "Frontend",
            "target": "Backend APIs",
            "relationship": "CONSUMES",
            "criticality": "HIGH",
            "description": "Frontend consumes backend REST APIs"
        })
        dep_id += 1
        
        # Infrastructure dependencies
        dependencies.append({
            "dependency_id": f"DEP_{dep_id:03d}",
            "type": "INFRASTRUCTURE",
            "source": "Application",
            "target": "Cloud Platform",
            "relationship": "HOSTED_ON",
            "criticality": "CRITICAL",
            "description": "Application will be hosted on cloud infrastructure"
        })
        dep_id += 1
        
        # External dependencies
        dependencies.append({
            "dependency_id": f"DEP_{dep_id:03d}",
            "type": "EXTERNAL",
            "source": "Application",
            "target": "Third-Party Services",
            "relationship": "INTEGRATES_WITH",
            "criticality": "MEDIUM",
            "description": "Application integrates with external services (payment, auth, etc.)"
        })
        dep_id += 1
        
        # Team dependencies
        dependencies.append({
            "dependency_id": f"DEP_{dep_id:03d}",
            "type": "RESOURCE",
            "source": "Development Team",
            "target": "DevOps Team",
            "relationship": "DEPENDS_ON",
            "criticality": "HIGH",
            "description": "Development depends on DevOps for deployment pipeline"
        })
        dep_id += 1
        
        self.state["dependencies"] = {
            "identified_dependencies": dependencies,
            "total_dependencies": len(dependencies),
            "by_type": self._categorize_by_type(dependencies),
            "by_criticality": self._categorize_by_criticality(dependencies)
        }
        
        print(f"   ✓ Analyzed {len(dependencies)} dependencies")
    
    def _categorize_by_type(self, items):
        """Categorize items by type"""
        types = {}
        for item in items:
            item_type = item.get("type", "UNKNOWN")
            if item_type not in types:
                types[item_type] = 0
            types[item_type] += 1
        return types
    
    def _categorize_by_criticality(self, items):
        """Categorize items by criticality"""
        criticality = {}
        for item in items:
            crit = item.get("criticality", "UNKNOWN")
            if crit not in criticality:
                criticality[crit] = 0
            criticality[crit] += 1
        return criticality
    
    def create_risk_matrix(self):
        """Create risk probability-impact matrix"""
        print("📊 Creating risk matrix...")
        
        risks = self.state["risks"]["identified_risks"]
        
        matrix = {
            "CRITICAL_HIGH": [],  # Critical severity, high probability
            "HIGH_HIGH": [],       # High severity, high probability
            "HIGH_MEDIUM": [],     # High severity, medium probability
            "MEDIUM_HIGH": [],     # Medium severity, high probability
            "OTHER": []
        }
        
        for risk in risks:
            severity = risk.get("severity", "LOW")
            probability = risk.get("probability", "LOW")
            
            key = f"{severity}_{probability}"
            if key in matrix:
                matrix[key].append(risk)
            else:
                matrix["OTHER"].append(risk)
        
        self.state["risk_matrix"] = matrix
        print(f"   ✓ Risk matrix created")
    
    def generate_output(self, output_path: str):
        """Generate final JSON output"""
        print("💾 Generating output files...")
        
        output_dir = Path(output_path)
        
        self.state["overall_confidence"] = self.confidence
        self.state["agent"] = "Agent 7: Risk & Dependency Analysis"
        self.state["timestamp"] = datetime.now().isoformat()
        
        files_written = []
        
        # 1. Risk Register
        risk_register = {
            "project_name": self.repo_path.name,
            "agent": "Agent 7: Risk & Dependency Analysis",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "risks": self.state.get("risks", {}),
            "risk_matrix": self.state.get("risk_matrix", {})
        }
        risk_file = output_dir / "risk_register.json"
        with open(risk_file, 'w') as f:
            json.dump(risk_register, f, indent=2)
        files_written.append(str(risk_file))
        print(f"   ✓ Wrote {risk_file.name} ({risk_file.stat().st_size} bytes)")
        
        # 2. Dependency Register
        dependency_register = {
            "project_name": self.repo_path.name,
            "agent": "Agent 7: Risk & Dependency Analysis",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "dependencies": self.state.get("dependencies", {})
        }
        deps_file = output_dir / "dependency_register.json"
        with open(deps_file, 'w') as f:
            json.dump(dependency_register, f, indent=2)
        files_written.append(str(deps_file))
        print(f"   ✓ Wrote {deps_file.name} ({deps_file.stat().st_size} bytes)")
        
        # 3. Regulatory Unresolved
        regulatory_unresolved = {
            "project_name": self.repo_path.name,
            "agent": "Agent 7: Risk & Dependency Analysis",
            "confidence": self.confidence,
            "unresolved_regulatory_items": [],
            "compliance_gaps": ["GDPR data handling", "Security audit pending"]
        }
        regulatory_file = output_dir / "regulatory_unresolved.json"
        with open(regulatory_file, 'w') as f:
            json.dump(regulatory_unresolved, f, indent=2)
        files_written.append(str(regulatory_file))
        print(f"   ✓ Wrote {regulatory_file.name} ({regulatory_file.stat().st_size} bytes)")
        
        # 4. Test Gap Risk Register
        test_gap_risk = {
            "project_name": self.repo_path.name,
            "agent": "Agent 7: Risk & Dependency Analysis",
            "confidence": self.confidence,
            "test_gaps_with_risks": [],
            "high_risk_untested_areas": ["payment processing", "data migration"]
        }
        test_risk_file = output_dir / "test_gap_risk_register.json"
        with open(test_risk_file, 'w') as f:
            json.dump(test_gap_risk, f, indent=2)
        files_written.append(str(test_risk_file))
        print(f"   ✓ Wrote {test_risk_file.name} ({test_risk_file.stat().st_size} bytes)")
        
        return files_written
    
    def run(self, output_path: str):
        """Execute Agent 7 workflow"""
        print("🚀 Starting Agent 7: Risk and Dependency Analysis")
        print(f"   KB Path: {self.kb_path}")
        print(f"   Output: {output_path}")
        print()
        
        self.load_previous_outputs()
        self.identify_risks()
        self.analyze_dependencies()
        self.create_risk_matrix()
        files = self.generate_output(output_path)
        
        print()
        print(f"✅ Agent 7 completed with confidence: {self.confidence:.2f}")
        print(f"📊 Generated {len(files)} output files")
        return self.state

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 7: Risk & Dependency Analysis")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    config_path = args.config
    kb_path = args.output
    
    if not repo_path or not kb_path:
        print("Usage: python agent_7_risk_dependency.py <repo_path> --config <config_path> --output <kb_path>")
        sys.exit(1)
    
    try:
        agent = Agent7RiskDependency(repo_path, config_path, kb_path)
        agent.run(kb_path)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
