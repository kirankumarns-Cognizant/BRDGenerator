"""
Agent 5: Synthesis
Synthesizes outputs from all previous agents into unified view.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config_loader import ConfigLoader

class Agent5Synthesis:
    def __init__(self, repo_path: str, config_path: str, kb_path: str):
        self.repo_path = Path(repo_path)
        self.config = ConfigLoader(config_path)
        self.kb_path = Path(kb_path)
        self.state = {}
        self.confidence = 1.0
        self.all_data = {}
        
    def load_all_outputs(self):
        """Load outputs from all previous agents"""
        print("📥 Loading all previous agent outputs...")
        
        files_to_load = [
            "scope_definition.json",
            "artifact_catalog.json",
            "dependency_map.json",
            "journey_map.json",
            "actors.json",
            "business_rules.json",
            "business_rules_catalog.json",
            "gap_analysis.json",
            "as_is_state.json",
            "to_be_state.json"
        ]
        
        loaded_count = 0
        for filename in files_to_load:
            file_path = self.kb_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    key = filename.replace(".json", "")
                    self.all_data[key] = json.load(f)
                    loaded_count += 1
        
        print(f"   ✓ Loaded {loaded_count} data files")
    
    def synthesize_system_overview(self):
        """Create high-level system overview"""
        print("🔄 Synthesizing system overview...")
        
        overview = {
            "repository_name": self.all_data.get("scope_definition", {}).get("repository_name", "Unknown"),
            "scan_timestamp": self.all_data.get("scope_definition", {}).get("scan_timestamp", ""),
            "technology_stack": self.all_data.get("scope_definition", {}).get("technology_stack", []),
            "total_entry_points": self.all_data.get("scope_definition", {}).get("total_entry_points", 0),
            "total_artifacts": self.all_data.get("artifact_catalog", {}).get("total_files", 0),
            "total_journeys": self.all_data.get("journey_map", {}).get("total_journeys", 0),
            "total_business_rules": self.all_data.get("business_rules", {}).get("total_rules", 0),
            "total_gaps": self.all_data.get("gap_analysis", {}).get("total_gaps", 0),
            "actors": self.all_data.get("actors", {}).get("actors", [])
        }
        
        self.state["system_overview"] = overview
        print(f"   ✓ System overview created")
    
    def create_unified_model(self):
        """Create unified data model"""
        print("🗂️  Creating unified data model...")
        
        unified_model = {
            "discovery": {
                "entry_points": self.all_data.get("scope_definition", {}).get("entry_points", []),
                "dependencies": self.all_data.get("dependency_map", {})
            },
            "journeys": {
                "all_journeys": self.all_data.get("journey_map", {}).get("journeys", []),
                "actors": self.all_data.get("actors", {}).get("actors", [])
            },
            "business_rules": {
                "rules": self.all_data.get("business_rules", {}).get("rules", []),
                "categories": self.all_data.get("business_rules", {}).get("categories", {})
            },
            "gaps": {
                "as_is": self.all_data.get("as_is_state", {}),
                "to_be": self.all_data.get("to_be_state", {}),
                "identified_gaps": self.all_data.get("gap_analysis", {}).get("identified_gaps", [])
            }
        }
        
        self.state["unified_model"] = unified_model
        print(f"   ✓ Unified model created")
    
    def generate_insights(self):
        """Generate insights from synthesized data"""
        print("💡 Generating insights...")
        
        insights = []
        
        # Complexity insight
        total_entry_points = self.state["system_overview"]["total_entry_points"]
        if total_entry_points > 20:
            insights.append({
                "type": "COMPLEXITY",
                "severity": "HIGH",
                "title": "High System Complexity",
                "description": f"System has {total_entry_points} entry points, indicating high complexity",
                "recommendation": "Consider breaking into microservices"
            })
        
        # Gap analysis insight
        total_gaps = self.state["system_overview"]["total_gaps"]
        if total_gaps > 10:
            insights.append({
                "type": "GAPS",
                "severity": "HIGH",
                "title": "Significant Gaps Identified",
                "description": f"{total_gaps} gaps identified between current and target state",
                "recommendation": "Prioritize gap remediation in phased approach"
            })
        
        # Business rules insight
        total_rules = self.state["system_overview"]["total_business_rules"]
        insights.append({
            "type": "BUSINESS_RULES",
            "severity": "MEDIUM",
            "title": "Business Rules Documentation",
            "description": f"{total_rules} business rules extracted from codebase",
            "recommendation": "Document and validate rules with business stakeholders"
        })
        
        # Technology stack insight
        tech_stack = self.state["system_overview"]["technology_stack"]
        if tech_stack:
            insights.append({
                "type": "TECHNOLOGY",
                "severity": "INFO",
                "title": "Technology Stack Identified",
                "description": f"Current technologies: {', '.join(tech_stack)}",
                "recommendation": "Assess for security vulnerabilities and EOL status"
            })
        
        self.state["insights"] = {
            "all_insights": insights,
            "total_insights": len(insights),
            "by_severity": self._categorize_by_severity(insights)
        }
        
        print(f"   ✓ Generated {len(insights)} insights")
    
    def _categorize_by_severity(self, items):
        """Categorize items by severity"""
        severity = {}
        for item in items:
            sev = item.get("severity", "INFO")
            if sev not in severity:
                severity[sev] = 0
            severity[sev] += 1
        return severity
    
    def create_recommendations(self):
        """Create actionable recommendations"""
        print("📋 Creating recommendations...")
        
        recommendations = []
        
        # From gaps
        gaps = self.all_data.get("gap_analysis", {}).get("identified_gaps", [])
        high_priority_gaps = [g for g in gaps if g.get("severity") == "HIGH"]
        
        if high_priority_gaps:
            recommendations.append({
                "category": "PRIORITY_GAPS",
                "title": "Address High-Priority Gaps First",
                "description": f"Focus on {len(high_priority_gaps)} high-priority gaps",
                "action_items": [
                    f"Gap {g.get('gap_id')}: {g.get('to_be')}" for g in high_priority_gaps[:5]
                ]
            })
        
        # Architecture recommendation
        recommendations.append({
            "category": "ARCHITECTURE",
            "title": "Modernize Architecture",
            "description": "Transition to cloud-native architecture",
            "action_items": [
                "Adopt microservices pattern",
                "Implement API gateway",
                "Enable containerization",
                "Set up CI/CD pipeline"
            ]
        })
        
        self.state["recommendations"] = {
            "all_recommendations": recommendations,
            "total_recommendations": len(recommendations)
        }
        
        print(f"   ✓ Created {len(recommendations)} recommendations")
    
    def generate_output(self, output_path: str):
        """Generate final JSON output"""
        print("💾 Generating output files...")
        
        output_dir = Path(output_path)
        
        self.state["overall_confidence"] = self.confidence
        self.state["agent"] = "Agent 5: Synthesis"
        self.state["timestamp"] = datetime.now().isoformat()
        
        files_written = []
        
        # 1. Synthesis Decisions
        synthesis_decisions = {
            "project_name": self.repo_path.name,
            "agent": "Agent 5: Synthesis",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "decisions": self.state.get("insights", {}),
            "system_overview": self.state.get("system_overview", {})
        }
        decisions_file = output_dir / "synthesis_decisions.json"
        with open(decisions_file, 'w') as f:
            json.dump(synthesis_decisions, f, indent=2)
        files_written.append(str(decisions_file))
        print(f"   ✓ Wrote {decisions_file.name} ({decisions_file.stat().st_size} bytes)")
        
        # 2. BRD Final (JSON - comprehensive unified model)
        brd_final = {
            "project_name": self.repo_path.name,
            "agent": "Agent 5: Synthesis",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "unified_model": self.state.get("unified_model", {}),
            "all_requirements": self.state.get("recommendations", {})
        }
        brd_file = output_dir / "brd_final.json"
        with open(brd_file, 'w') as f:
            json.dump(brd_final, f, indent=2)
        files_written.append(str(brd_file))
        print(f"   ✓ Wrote {brd_file.name} ({brd_file.stat().st_size} bytes)")
        
        # 3. BRD Gap Summary
        brd_gap_summary = {
            "project_name": self.repo_path.name,
            "agent": "Agent 5: Synthesis",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "critical_gaps": [],
            "gap_recommendations": self.state.get("recommendations", {}).get("all_recommendations", [])[:10]
        }
        gap_summary_file = output_dir / "brd_gap_summary.json"
        with open(gap_summary_file, 'w') as f:
            json.dump(brd_gap_summary, f, indent=2)
        files_written.append(str(gap_summary_file))
        print(f"   ✓ Wrote {gap_summary_file.name} ({gap_summary_file.stat().st_size} bytes)")
        
        return files_written
    
    def run(self, output_path: str):
        """Execute Agent 5 workflow"""
        print("🚀 Starting Agent 5: Synthesis")
        print(f"   KB Path: {self.kb_path}")
        print(f"   Output: {output_path}")
        print()
        
        self.load_all_outputs()
        self.synthesize_system_overview()
        self.create_unified_model()
        self.generate_insights()
        self.create_recommendations()
        files = self.generate_output(output_path)
        
        print()
        print(f"✅ Agent 5 completed with confidence: {self.confidence:.2f}")
        print(f"📊 Generated {len(files)} output files")
        return self.state

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 5: Synthesis")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    config_path = args.config
    kb_path = args.output
    
    if not repo_path or not kb_path:
        print("Usage: python agent_5_synthesis.py <repo_path> --config <config_path> --output <kb_path>")
        sys.exit(1)
    
    try:
        agent = Agent5Synthesis(repo_path, config_path, kb_path)
        agent.run(kb_path)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
