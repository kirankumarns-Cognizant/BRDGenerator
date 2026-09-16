#!/usr/bin/env python3
"""
Agent 2: Journey Mapping - ENHANCED
Extracts user journeys, actors, and interaction flows from Java web applications.
Properly handles Stripes ActionBeans, Spring Controllers, and session management.
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


class EnhancedJourneyMappingAgent:
    """Enhanced journey mapping that extracts real user flows from source code."""
    
    # HTTP method annotations/patterns
    HTTP_PATTERNS = {
        "@HandlesEvent": "Stripes Event Handler",
        "@DefaultHandler": "Stripes Default Handler",
        "@GetMapping": "HTTP GET",
        "@PostMapping": "HTTP POST", 
        "@PutMapping": "HTTP PUT",
        "@DeleteMapping": "HTTP DELETE",
        "@RequestMapping": "HTTP Request",
        "Resolution": "Stripes Resolution",
    }
    
    # Session and state patterns
    SESSION_PATTERNS = [
        "@SessionScope",
        "@SessionAttributes",
        "HttpSession",
        "session.getAttribute",
        "session.setAttribute",
    ]
    
    # Navigation patterns
    NAVIGATION_PATTERNS = {
        "ForwardResolution": "Forward to JSP",
        "RedirectResolution": "Redirect",
        "StreamingResolution": "Stream Response",
        "ErrorResolution": "Error Page",
        "redirect:": "Spring Redirect",
        "forward:": "Spring Forward",
    }
    
    def __init__(self, repo_path: str, config_path: str = None, output_path: str = None):
        self.repo_path = Path(repo_path)
        self.repo_name = self.repo_path.name
        self.config = ConfigLoader(config_path) if config_path else ConfigLoader()
        self.output_path = Path(output_path) if output_path else Path("KB") / self.repo_name
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Load discovery outputs
        self.system_overview = self._load_json("system_overview.json")
        self.artifact_catalog = self._load_json("artifact_catalog.json")
        self.scope_definition = self._load_json("scope_definition.json")
        
        # Journey accumulation
        self.actors: List[Dict] = []
        self.journeys: List[Dict] = []
        self.interactions: List[Dict] = []
        self.conflicts: List[Dict] = []
        self.confidence = 1.0
    
    def run(self) -> Dict[str, Any]:
        """Execute the enhanced journey mapping agent."""
        print(f"\n{'='*60}")
        print("Agent 2: Enhanced Journey Mapping")
        print(f"{'='*60}")
        print(f"Repository: {self.repo_path}")
        
        try:
            # Phase 1: Extract actors from the system
            print("\n[Phase 1] Identifying actors...")
            self._extract_actors()
            
            # Phase 2: Analyze controllers/actionbeans for user flows
            print("\n[Phase 2] Analyzing user interaction points...")
            self._analyze_interaction_points()
            
            # Phase 3: Build journey maps
            print("\n[Phase 3] Constructing journey maps...")
            self._build_journey_maps()
            
            # Phase 4: Detect conflicts and issues
            print("\n[Phase 4] Detecting journey conflicts...")
            self._detect_conflicts()
            
            # Phase 5: Generate outputs
            print("\n[Phase 5] Generating journey outputs...")
            outputs = self._generate_outputs()
            
            print(f"\n{'='*60}")
            print("Journey Mapping Complete!")
            print(f"  - Actors identified: {len(self.actors)}")
            print(f"  - Journeys mapped: {len(self.journeys)}")
            print(f"  - Interactions found: {len(self.interactions)}")
            print(f"  - Conflicts detected: {len(self.conflicts)}")
            print(f"{'='*60}\n")
            
            return outputs
            
        except Exception as e:
            print(f"ERROR: Journey mapping failed - {e}")
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
    
    def _extract_actors(self):
        """Extract actors from the system based on domain entities and authentication."""
        # Default actors for web applications
        self.actors = [
            {
                "id": "guest",
                "name": "Guest User",
                "type": "human",
                "description": "Unauthenticated visitor browsing the application",
                "permissions": ["view_catalog", "view_products"],
                "source": "inferred"
            },
            {
                "id": "registered_user",
                "name": "Registered User", 
                "type": "human",
                "description": "Authenticated user with account access",
                "permissions": ["view_catalog", "add_to_cart", "checkout", "manage_account"],
                "source": "inferred"
            }
        ]
        
        # Check for Account/User entities
        artifacts = self.artifact_catalog.get("artifacts", [])
        
        for artifact in artifacts:
            name = artifact.get("name", "")
            
            # Look for admin-related classes
            if "Admin" in name:
                self.actors.append({
                    "id": "admin",
                    "name": "Administrator",
                    "type": "human",
                    "description": "System administrator with full access",
                    "permissions": ["all"],
                    "source": artifact["file_path"]
                })
            
            # Look for system integrations
            if "Service" in name and artifact.get("type") == "SERVICE_LAYER":
                # Services might indicate system actors
                pass
        
        # Add system actor
        self.actors.append({
            "id": "system",
            "name": "System",
            "type": "system",
            "description": "Automated system processes and scheduled tasks",
            "permissions": ["internal_operations"],
            "source": "inferred"
        })
        
        print(f"  Identified {len(self.actors)} actors")
    
    def _analyze_interaction_points(self):
        """Analyze ActionBeans and Controllers for user interaction points."""
        artifacts = self.artifact_catalog.get("artifacts", [])
        
        controllers = [a for a in artifacts if a.get("type") in ["WEB_CONTROLLER", "REST_CONTROLLER"]]
        
        for controller in controllers:
            file_path = self.repo_path / controller["file_path"]
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Extract all handler methods
                handlers = self._extract_handlers(content, controller)
                self.interactions.extend(handlers)
                
            except Exception as e:
                print(f"  Warning: Could not analyze {controller['name']}: {e}")
                self.confidence *= 0.98
        
        print(f"  Found {len(self.interactions)} interaction points")
    
    def _extract_handlers(self, content: str, controller: Dict) -> List[Dict]:
        """Extract handler methods from controller/actionbean."""
        handlers = []
        controller_name = controller.get("name", "Unknown")
        
        # Extract class-level annotations
        is_session_scoped = "@SessionScope" in content
        
        # Pattern for Stripes @HandlesEvent
        event_pattern = r'@HandlesEvent\s*\(\s*["\'](\w+)["\']\s*\)'
        for match in re.finditer(event_pattern, content):
            event_name = match.group(1)
            
            # Find the method after this annotation
            method_match = re.search(
                rf'@HandlesEvent\s*\(\s*["\'{event_name}["\']\s*\)[^{{]*?public\s+\w+\s+(\w+)\s*\(',
                content, re.DOTALL
            )
            
            method_name = method_match.group(1) if method_match else event_name
            
            handlers.append({
                "controller": controller_name,
                "event": event_name,
                "method": method_name,
                "type": "stripes_event",
                "session_scoped": is_session_scoped,
                "http_method": "POST" if event_name in ["save", "add", "update", "delete", "submit"] else "GET",
                "navigation": self._extract_navigation(content, method_name)
            })
        
        # Pattern for @DefaultHandler
        if "@DefaultHandler" in content:
            default_match = re.search(r'@DefaultHandler[^{{]*?public\s+\w+\s+(\w+)\s*\(', content, re.DOTALL)
            if default_match:
                handlers.append({
                    "controller": controller_name,
                    "event": "default",
                    "method": default_match.group(1),
                    "type": "stripes_default",
                    "session_scoped": is_session_scoped,
                    "http_method": "GET",
                    "navigation": self._extract_navigation(content, default_match.group(1))
                })
        
        # Pattern for public Resolution methods (Stripes)
        resolution_pattern = r'public\s+Resolution\s+(\w+)\s*\([^)]*\)\s*(?:throws[^{]*)?\{'
        for match in re.finditer(resolution_pattern, content):
            method_name = match.group(1)
            
            # Skip if already captured by event handler
            if any(h["method"] == method_name for h in handlers):
                continue
            
            handlers.append({
                "controller": controller_name,
                "event": method_name,
                "method": method_name,
                "type": "stripes_resolution",
                "session_scoped": is_session_scoped,
                "http_method": "GET" if method_name.startswith(("view", "show", "get", "list")) else "POST",
                "navigation": self._extract_navigation(content, method_name)
            })
        
        # Spring MVC patterns
        for annotation in ["@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping", "@RequestMapping"]:
            if annotation in content:
                mapping_pattern = rf'{annotation}\s*\([^)]*\)[^{{]*?public\s+\w+\s+(\w+)\s*\('
                for match in re.finditer(mapping_pattern, content, re.DOTALL):
                    method_name = match.group(1)
                    handlers.append({
                        "controller": controller_name,
                        "event": method_name,
                        "method": method_name,
                        "type": "spring_mvc",
                        "http_method": annotation.replace("@", "").replace("Mapping", "").upper() or "GET",
                        "navigation": self._extract_navigation(content, method_name)
                    })
        
        return handlers
    
    def _extract_navigation(self, content: str, method_name: str) -> Dict:
        """Extract navigation target from method."""
        # Find method body
        method_pattern = rf'(?:public|protected)\s+\w+\s+{method_name}\s*\([^)]*\)[^{{]*\{{([^}}]+)\}}'
        method_match = re.search(method_pattern, content, re.DOTALL)
        
        if not method_match:
            return {"type": "unknown", "target": "unknown"}
        
        method_body = method_match.group(1)
        
        # Check for ForwardResolution
        forward_match = re.search(r'ForwardResolution\s*\(\s*["\']([^"\']+)["\']', method_body)
        if forward_match:
            return {"type": "forward", "target": forward_match.group(1)}
        
        # Check for RedirectResolution
        redirect_match = re.search(r'RedirectResolution\s*\(\s*(\w+)\.class', method_body)
        if redirect_match:
            return {"type": "redirect", "target": redirect_match.group(1)}
        
        # Check for StreamingResolution
        if "StreamingResolution" in method_body:
            return {"type": "stream", "target": "response"}
        
        return {"type": "resolution", "target": "dynamic"}
    
    def _build_journey_maps(self):
        """Build comprehensive journey maps from interactions."""
        
        # Group interactions by controller
        by_controller = {}
        for interaction in self.interactions:
            ctrl = interaction["controller"]
            if ctrl not in by_controller:
                by_controller[ctrl] = []
            by_controller[ctrl].append(interaction)
        
        # Build journeys per controller/feature area
        for controller, interactions in by_controller.items():
            feature_name = controller.replace("ActionBean", "").replace("Controller", "")
            
            # Determine journey based on controller name
            journey = self._create_journey_for_feature(feature_name, interactions)
            if journey:
                self.journeys.append(journey)
        
        print(f"  Built {len(self.journeys)} user journeys")
    
    def _create_journey_for_feature(self, feature_name: str, interactions: List[Dict]) -> Optional[Dict]:
        """Create a user journey for a feature area."""
        if not interactions:
            return None
        
        # Determine primary actor
        primary_actor = "registered_user"
        if feature_name.lower() in ["catalog", "product", "category"]:
            primary_actor = "guest"
        elif feature_name.lower() in ["account", "order", "cart"]:
            primary_actor = "registered_user"
        
        # Build steps from interactions
        steps = []
        for idx, interaction in enumerate(interactions):
            steps.append({
                "step_number": idx + 1,
                "action": f"{interaction['http_method']} {interaction['event']}",
                "description": self._describe_action(interaction),
                "handler": f"{interaction['controller']}.{interaction['method']}",
                "navigation": interaction.get("navigation", {}),
                "requires_auth": interaction.get("session_scoped", False)
            })
        
        return {
            "id": f"journey_{feature_name.lower()}",
            "name": f"{feature_name} Journey",
            "description": f"User journey for {feature_name} functionality",
            "primary_actor": primary_actor,
            "preconditions": self._get_preconditions(feature_name, interactions),
            "steps": steps,
            "postconditions": self._get_postconditions(feature_name),
            "alternative_flows": self._get_alternative_flows(feature_name),
            "exception_flows": self._get_exception_flows(feature_name),
            "confidence": 0.85
        }
    
    def _describe_action(self, interaction: Dict) -> str:
        """Generate human-readable description of an action."""
        event = interaction.get("event", "action")
        method = interaction.get("method", event)
        
        descriptions = {
            "view": f"View {event.replace('view', '')} page",
            "show": f"Display {event.replace('show', '')} details",
            "list": f"List all {event.replace('list', '')} items",
            "add": f"Add new {event.replace('add', '')}",
            "save": f"Save {event.replace('save', '')} data",
            "update": f"Update {event.replace('update', '')} information",
            "delete": f"Delete {event.replace('delete', '')} item",
            "search": f"Search for {event.replace('search', '')}",
            "submit": f"Submit {event.replace('submit', '')} form",
        }
        
        for prefix, desc in descriptions.items():
            if event.lower().startswith(prefix):
                return desc
        
        return f"Execute {event} action"
    
    def _get_preconditions(self, feature_name: str, interactions: List[Dict]) -> List[str]:
        """Get preconditions for a journey."""
        preconditions = []
        
        if any(i.get("session_scoped") for i in interactions):
            preconditions.append("User must be authenticated")
        
        feature_preconditions = {
            "Order": ["User has items in cart", "User is logged in"],
            "Cart": ["User is browsing catalog"],
            "Account": ["User has registered account"],
            "Checkout": ["Cart is not empty", "User is logged in"],
        }
        
        preconditions.extend(feature_preconditions.get(feature_name, []))
        
        return preconditions if preconditions else ["None"]
    
    def _get_postconditions(self, feature_name: str) -> List[str]:
        """Get postconditions for a journey."""
        postconditions = {
            "Order": ["Order is placed", "Cart is cleared", "Confirmation shown"],
            "Cart": ["Cart is updated", "Item count reflected"],
            "Account": ["Account information updated", "Session refreshed"],
            "Catalog": ["Products displayed", "Categories shown"],
        }
        
        return postconditions.get(feature_name, [f"{feature_name} action completed"])
    
    def _get_alternative_flows(self, feature_name: str) -> List[Dict]:
        """Get alternative flows for a journey."""
        alt_flows = {
            "Order": [
                {"name": "Update Quantity", "trigger": "User changes item quantity", "steps": ["Update quantity", "Recalculate total"]},
                {"name": "Apply Coupon", "trigger": "User enters coupon code", "steps": ["Validate coupon", "Apply discount"]}
            ],
            "Cart": [
                {"name": "Remove Item", "trigger": "User clicks remove", "steps": ["Remove from cart", "Update display"]},
                {"name": "Save for Later", "trigger": "User saves item", "steps": ["Move to wishlist", "Remove from cart"]}
            ],
            "Account": [
                {"name": "Forgot Password", "trigger": "User forgot password", "steps": ["Send reset email", "Show confirmation"]},
                {"name": "Update Profile", "trigger": "User edits profile", "steps": ["Validate input", "Save changes"]}
            ]
        }
        
        return alt_flows.get(feature_name, [])
    
    def _get_exception_flows(self, feature_name: str) -> List[Dict]:
        """Get exception flows for a journey."""
        exception_flows = {
            "Order": [
                {"name": "Payment Failed", "trigger": "Payment processing error", "recovery": "Show error and retry options"},
                {"name": "Out of Stock", "trigger": "Item unavailable", "recovery": "Notify user and suggest alternatives"}
            ],
            "Account": [
                {"name": "Invalid Credentials", "trigger": "Wrong username/password", "recovery": "Show error message"},
                {"name": "Account Locked", "trigger": "Too many attempts", "recovery": "Show lockout message"}
            ]
        }
        
        return exception_flows.get(feature_name, [])
    
    def _detect_conflicts(self):
        """Detect potential conflicts in journeys."""
        
        # Check for missing authentication
        for journey in self.journeys:
            has_auth_steps = any(step.get("requires_auth") for step in journey.get("steps", []))
            
            if journey["primary_actor"] == "registered_user" and not has_auth_steps:
                self.conflicts.append({
                    "type": "authentication_gap",
                    "journey": journey["name"],
                    "description": "Journey requires registered user but no authentication check found",
                    "severity": "medium",
                    "recommendation": "Add authentication verification step"
                })
        
        # Check for dead ends (no navigation)
        for interaction in self.interactions:
            nav = interaction.get("navigation", {})
            if nav.get("type") == "unknown":
                self.conflicts.append({
                    "type": "unclear_navigation",
                    "handler": f"{interaction['controller']}.{interaction['method']}",
                    "description": "Handler has unclear navigation/response",
                    "severity": "low",
                    "recommendation": "Review handler return type and navigation"
                })
        
        print(f"  Detected {len(self.conflicts)} potential conflicts")
    
    def _generate_outputs(self) -> Dict[str, Any]:
        """Generate all journey mapping outputs."""
        
        # 1. Actors JSON
        actors_output = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "actors": self.actors,
            "actor_count": len(self.actors)
        }
        self._write_json("actors.json", actors_output)
        
        # 2. Journey Map JSON
        journey_map = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_journeys": len(self.journeys),
                "total_interactions": len(self.interactions),
                "controllers_analyzed": len(set(i["controller"] for i in self.interactions))
            },
            "journeys": self.journeys,
            "interactions": self.interactions
        }
        self._write_json("journey_map.json", journey_map)
        
        # 3. Journey Conflicts JSON
        conflicts_output = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "conflicts": self.conflicts,
            "conflict_count": len(self.conflicts),
            "by_severity": {
                "high": len([c for c in self.conflicts if c["severity"] == "high"]),
                "medium": len([c for c in self.conflicts if c["severity"] == "medium"]),
                "low": len([c for c in self.conflicts if c["severity"] == "low"])
            }
        }
        self._write_json("journey_conflicts.json", conflicts_output)
        
        # 4. Test Journey Coverage JSON (CONSOLIDATED - includes gap analysis)
        test_coverage = {
            "repository": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "agent": "Agent 2: Journey Mapping",
            "confidence": self.confidence,
            "journeys": [
                {
                    "id": j.get("id", f"UJ-{idx+1:03d}"),
                    "name": j.get("name", "Unknown Journey"),
                    "test_coverage_percentage": 0,  # TODO: Calculate from test analysis
                    "has_gap": True,  # Default to true until test mapping is implemented
                    "covered_scenarios": [],
                    "missing_scenarios": j.get("steps", []),
                    "tests": []
                }
                for idx, j in enumerate(self.journeys)
            ],
            "summary": {
                "total_journeys": len(self.journeys),
                "journeys_with_gaps": len(self.journeys),  # All have gaps initially
                "average_coverage": 0.0,
                "critical_gaps": [
                    {
                        "journey_id": j.get("id", f"UJ-{idx+1:03d}"),
                        "gap": "No test coverage found",
                        "risk": "medium"
                    }
                    for idx, j in enumerate(self.journeys[:5])  # First 5 as critical
                ]
            }
        }
        self._write_json("test_journey_coverage.json", test_coverage)
        
        return {
            "status": "success",
            "actors_found": len(self.actors),
            "journeys_mapped": len(self.journeys),
            "interactions_found": len(self.interactions),
            "conflicts_detected": len(self.conflicts),
            "confidence": self.confidence,
            "outputs": ["actors.json", "journey_map.json", "journey_conflicts.json", "test_journey_coverage.json"]
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
            "timestamp": datetime.now().isoformat()
        }
        
        self._write_json("actors.json", {"actors": [], "error": error})
        self._write_json("journey_map.json", {"journeys": [], "error": error})
        self._write_json("journey_conflicts.json", {"conflicts": [], "error": error})
        self._write_json("test_journey_coverage.json", {"journeys": [], "summary": {}, "error": error})
        
        return {"status": "error", "error": error, "confidence": self.confidence}


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 2: Enhanced Journey Mapping")
    parser.add_argument("repo_path", nargs="?", help="Path to repository")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Output directory path")
    
    args = parser.parse_args()
    
    repo_path = args.repo_path
    if not repo_path:
        config = ConfigLoader(args.config)
        repo_path = config.get("repository.path", ".")
    
    agent = EnhancedJourneyMappingAgent(
        repo_path=repo_path,
        config_path=args.config,
        output_path=args.output
    )
    
    result = agent.run()
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
