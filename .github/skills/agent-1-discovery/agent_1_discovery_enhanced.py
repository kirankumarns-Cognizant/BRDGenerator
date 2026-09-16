"""
Agent 1 Discovery Enhanced Script
Standalone execution wrapper for Agent 1 discovery and scoping
"""

import sys
import argparse
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.agent_1_discovery import Agent1Discovery
from config_loader.config_loader import ConfigLoader
from orchestrator.state import PipelineState
import json


def main():
    parser = argparse.ArgumentParser(description="Agent 1: Discovery & Scoping")
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--output", help="Output directory (overrides config)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Load configuration
    print("Loading configuration...")
    config = ConfigLoader(args.config)
    
    # Override repository path
    config.config['resources']['repo']['path'] = args.repo
    
    # Initialize state
    state = PipelineState()
    state["repo_path"] = args.repo
    
    # Initialize agent
    print("\nInitializing Agent 1: Discovery & Scoping...")
    agent = Agent1Discovery(config=config)
    
    # Execute agent
    print("\nExecuting discovery and scoping...")
    result = agent.execute(state)
    
    # Determine output path
    if args.output:
        output_dir = Path(args.output)
    else:
        kb_root = config.get_kb_output_root()
        repo_name = Path(args.repo).name
        output_dir = Path(kb_root) / repo_name / "agent_1"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write outputs
    print(f"\nWriting outputs to: {output_dir}")
    
    outputs = {
        "scope_definition.json": result.get("scope_definition"),
        "artifact_catalog.json": result.get("artifact_catalog"),
        "dependency_map.json": result.get("dependency_map")
    }
    
    for filename, data in outputs.items():
        if data:
            output_path = output_dir / filename
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ {filename}")
        else:
            print(f"  ⚠ {filename} (not generated)")
    
    # Print summary
    confidence = result.get("overall_confidence", 0.0)
    print(f"\n{'='*50}")
    print(f"Agent 1 Execution Complete")
    print(f"{'='*50}")
    print(f"Overall Confidence: {confidence:.2f}")
    
    if confidence < 0.6:
        print("⚠ WARNING: Low confidence score - review outputs carefully")
    
    print(f"\nOutputs available at: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
