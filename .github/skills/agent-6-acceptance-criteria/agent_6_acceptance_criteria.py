"""
Agent 6: Acceptance Criteria Generation
Generates acceptance criteria from journeys and business rules.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config_loader import ConfigLoader

class Agent6AcceptanceCriteria:
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
            ("journey_map.json", "journey_map"),
            ("business_rules.json", "business_rules"),
            ("gap_analysis.json", "gap_analysis")
        ]
        
        for filename, attr_name in files_to_load:
            file_path = self.kb_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    setattr(self, attr_name, json.load(f))
            else:
                setattr(self, attr_name, {})
        
        print(f"   ✓ Loaded data from previous agents")
    
    def generate_acceptance_criteria(self):
        """Generate acceptance criteria for each journey"""
        print("✅ Generating acceptance criteria...")
        
        all_criteria = []
        journeys = self.journey_map.get("journeys", [])
        
        for journey in journeys:
            criteria_set = {
                "journey_id": journey.get("journey_id"),
                "journey_name": journey.get("name"),
                "criteria": self._create_criteria_for_journey(journey),
                "gherkin_scenarios": self._create_gherkin(journey)
            }
            all_criteria.append(criteria_set)
        
        self.state["acceptance_criteria"] = {
            "all_criteria": all_criteria,
            "total_journey_criteria": len(all_criteria),
            "total_individual_criteria": sum(len(c["criteria"]) for c in all_criteria)
        }
        
        print(f"   ✓ Generated criteria for {len(all_criteria)} journeys")
    
    def _create_criteria_for_journey(self, journey):
        """Create acceptance criteria for a specific journey"""
        criteria = []
        
        # Given-When-Then format
        criteria.append({
            "id": f"AC_{journey.get('journey_id')}_001",
            "type": "FUNCTIONAL",
            "description": f"GIVEN a user initiates {journey.get('name')}, WHEN the request is valid, THEN the system processes it successfully",
            "priority": "HIGH"
        })
        
        criteria.append({
            "id": f"AC_{journey.get('journey_id')}_002",
            "type": "VALIDATION",
            "description": f"GIVEN invalid input data, WHEN the request is submitted, THEN the system returns appropriate error messages",
            "priority": "HIGH"
        })
        
        criteria.append({
            "id": f"AC_{journey.get('journey_id')}_003",
            "type": "PERFORMANCE",
            "description": f"GIVEN normal load conditions, WHEN the journey executes, THEN response time is less than 2 seconds",
            "priority": "MEDIUM"
        })
        
        criteria.append({
            "id": f"AC_{journey.get('journey_id')}_004",
            "type": "SECURITY",
            "description": f"GIVEN an unauthenticated user, WHEN attempting access, THEN the system denies access with 401 status",
            "priority": "HIGH"
        })
        
        return criteria
    
    def _create_gherkin(self, journey):
        """Create Gherkin scenarios for journey"""
        scenario_name = journey.get("name", "Unknown Journey").replace("User Journey: ", "")
        
        gherkin = f"""Feature: {scenario_name}
  As a user
  I want to {scenario_name.lower()}
  So that I can achieve my business goal

  Scenario: Successful {scenario_name}
    Given the user is authenticated
    And the system is available
    When the user initiates {scenario_name.lower()}
    And provides valid input data
    Then the system processes the request successfully
    And returns a success response
    And updates the system state accordingly

  Scenario: Invalid Input Handling
    Given the user is authenticated
    When the user provides invalid input data
    Then the system validates the input
    And returns an error message
    And the system state remains unchanged

  Scenario: Unauthorized Access
    Given the user is not authenticated
    When the user attempts to access {scenario_name.lower()}
    Then the system denies access
    And returns a 401 Unauthorized response
"""
        
        return gherkin
    
    def create_test_scenarios(self):
        """Create detailed test scenarios"""
        print("🧪 Creating test scenarios...")
        
        test_scenarios = []
        
        for criteria_set in self.state["acceptance_criteria"]["all_criteria"]:
            for criterion in criteria_set["criteria"]:
                scenario = {
                    "scenario_id": criterion["id"].replace("AC_", "TS_"),
                    "journey_id": criteria_set["journey_id"],
                    "type": criterion["type"],
                    "test_case": criterion["description"],
                    "priority": criterion["priority"],
                    "test_data": self._generate_test_data(criterion["type"]),
                    "expected_result": self._generate_expected_result(criterion["type"])
                }
                test_scenarios.append(scenario)
        
        self.state["test_scenarios"] = {
            "scenarios": test_scenarios,
            "total_scenarios": len(test_scenarios),
            "by_type": self._categorize_by_type(test_scenarios)
        }
        
        print(f"   ✓ Created {len(test_scenarios)} test scenarios")
    
    def _generate_test_data(self, test_type):
        """Generate sample test data based on type"""
        test_data_map = {
            "FUNCTIONAL": {"input": "valid_request_payload", "auth": "valid_token"},
            "VALIDATION": {"input": "invalid_request_payload", "auth": "valid_token"},
            "PERFORMANCE": {"input": "valid_request_payload", "load": "normal"},
            "SECURITY": {"input": "valid_request_payload", "auth": "no_token"}
        }
        return test_data_map.get(test_type, {})
    
    def _generate_expected_result(self, test_type):
        """Generate expected result based on type"""
        result_map = {
            "FUNCTIONAL": "HTTP 200, valid response payload",
            "VALIDATION": "HTTP 400, error message describing validation failure",
            "PERFORMANCE": "Response time < 2 seconds",
            "SECURITY": "HTTP 401, access denied message"
        }
        return result_map.get(test_type, "Success")
    
    def _categorize_by_type(self, items):
        """Categorize items by type"""
        categories = {}
        for item in items:
            item_type = item.get("type", "UNKNOWN")
            if item_type not in categories:
                categories[item_type] = 0
            categories[item_type] += 1
        return categories
    
    def generate_output(self, output_path: str):
        """Generate final JSON output"""
        print("💾 Generating output files...")
        
        output_dir = Path(output_path)
        
        self.state["overall_confidence"] = self.confidence
        self.state["agent"] = "Agent 6: Acceptance Criteria"
        self.state["timestamp"] = datetime.now().isoformat()
        
        files_written = []
        
        # 1. Acceptance Criteria (Gherkin format .feature file)
        gherkin_file = output_dir / "acceptance_criteria.feature"
        with open(gherkin_file, 'w') as f:
            for criteria_set in self.state.get("acceptance_criteria", {}).get("all_criteria", []):
                f.write(criteria_set.get("gherkin_scenarios", ""))
                f.write("\n\n")
        files_written.append(str(gherkin_file))
        print(f"   ✓ Wrote {gherkin_file.name} ({gherkin_file.stat().st_size} bytes)")
        
        # 2. Acceptance Criteria Gherkin (JSON version)
        gherkin_json = {
            "project_name": self.repo_path.name,
            "agent": "Agent 6: Acceptance Criteria",
            "confidence": self.confidence,
            "timestamp": datetime.now().isoformat(),
            "criteria": self.state.get("acceptance_criteria", {})
        }
        gherkin_json_file = output_dir / "acceptance_criteria_gherkin.json"
        with open(gherkin_json_file, 'w') as f:
            json.dump(gherkin_json, f, indent=2)
        files_written.append(str(gherkin_json_file))
        print(f"   ✓ Wrote {gherkin_json_file.name} ({gherkin_json_file.stat().st_size} bytes)")
        
        # 3. Regression Gap Report
        regression_gap_report = {
            "project_name": self.repo_path.name,
            "agent": "Agent 6: Acceptance Criteria",
            "confidence": self.confidence,
            "regression_gaps": [],
            "missing_regression_tests": ["payment flow", "user registration"]
        }
        regression_file = output_dir / "regression_gap_report.json"
        with open(regression_file, 'w') as f:
            json.dump(regression_gap_report, f, indent=2)
        files_written.append(str(regression_file))
        print(f"   ✓ Wrote {regression_file.name} ({regression_file.stat().st_size} bytes)")
        
        # 4. New Test Suggestions
        new_test_suggestions = {
            "project_name": self.repo_path.name,
            "agent": "Agent 6: Acceptance Criteria",
            "confidence": self.confidence,
            "suggested_tests": self.state.get("test_scenarios", {}).get("scenarios", [])[:10]
        }
        suggestions_file = output_dir / "new_test_suggestions.json"
        with open(suggestions_file, 'w') as f:
            json.dump(new_test_suggestions, f, indent=2)
        files_written.append(str(suggestions_file))
        print(f"   ✓ Wrote {suggestions_file.name} ({suggestions_file.stat().st_size} bytes)")
        
        # 5. Prioritized Gap Closure Tests
        prioritized_tests = {
            "project_name": self.repo_path.name,
            "agent": "Agent 6: Acceptance Criteria",
            "confidence": self.confidence,
            "prioritized_tests": [
                {"priority": 1, "test": "Critical security tests"},
                {"priority": 2, "test": "Core functionality E2E tests"}
            ]
        }
        prioritized_file = output_dir / "prioritized_gap_closure_tests.json"
        with open(prioritized_file, 'w') as f:
            json.dump(prioritized_tests, f, indent=2)
        files_written.append(str(prioritized_file))
        print(f"   ✓ Wrote {prioritized_file.name} ({prioritized_file.stat().st_size} bytes)")
        
        return files_written
    
    def run(self, output_path: str):
        """Execute Agent 6 workflow"""
        print("🚀 Starting Agent 6: Acceptance Criteria Generation")
        print(f"   KB Path: {self.kb_path}")
        print(f"   Output: {output_path}")
        print()
        
        self.load_previous_outputs()
        self.generate_acceptance_criteria()
        self.create_test_scenarios()
        files = self.generate_output(output_path)
        
        print()
        print(f"✅ Agent 6 completed with confidence: {self.confidence:.2f}")
        print(f"📊 Generated {len(files)} output files")
        return self.state

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 6: Acceptance Criteria")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    config_path = args.config
    kb_path = args.output
    
    if not repo_path or not kb_path:
        print("Usage: python agent_6_acceptance_criteria.py <repo_path> --config <config_path> --output <kb_path>")
        sys.exit(1)
    
    try:
        agent = Agent6AcceptanceCriteria(repo_path, config_path, kb_path)
        agent.run(kb_path)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
