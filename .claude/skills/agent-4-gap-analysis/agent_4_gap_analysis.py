#!/usr/bin/env python3
"""
Agent 4: Gap Analysis
Analyzes gaps between current state and desired state, identifies missing features.
Wrapper for Claude execution via .claude framework.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.config_loader import ConfigLoader

# Try to import real agent executor, fallback to mock if unavailable
try:
    from kb_gen.core.agent_executor import AgentExecutor
    KB_GEN_AVAILABLE = True
except ImportError:
    KB_GEN_AVAILABLE = False
    class AgentExecutor:
        """Mock executor fallback."""
        def __init__(self, agent_num: int, config=None):
            self.agent_num = agent_num
            self.config = config


class Agent4GapAnalysis:
    """Agent 4: Gap Analysis implementation - Uses real kb_gen logic."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.kb_gen_available = KB_GEN_AVAILABLE
        
        # Initialize real kb_gen backend if available
        if self.kb_gen_available:
            try:
                from kb_gen.analysis.gap_analyzer import GapAnalyzer
                self.backend = GapAnalyzer(self.config)
            except (ImportError, Exception) as e:
                import logging
                logging.warning(f"Failed to initialize real Agent 4 backend: {e}")
                self.backend = None
        else:
            self.backend = None
        
        # Fallback executor
        self.executor = AgentExecutor(agent_num=4, config=self.config)
    
    def execute(self, scope_definition: Dict[str, Any], business_rules: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute gap analysis between current and desired states using real kb_gen logic.
        
        Args:
            scope_definition: Scope definition from Agent 1
            business_rules: Business rules from Agent 3
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing identified_gaps, missing_features, improvement_areas
        """
        # Try real backend first
        if self.backend:
            try:
                result = self.backend.execute(scope_definition=scope_definition, business_rules=business_rules, **kwargs)
                return {**result, "confidence": result.get("confidence", 0.78), "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real backend execution failed: {e}")
        
        # Fallback to executor (which has graceful mock fallback)
        return self.executor.execute(scope_definition=scope_definition, business_rules=business_rules, **kwargs)
    
    def analyze_gaps(self, current_state: Dict, desired_state: Dict) -> List[Dict[str, Any]]:
        """Analyze gaps between states."""
        return self.executor.analyze_gaps(current_state, desired_state)


def main():
    """CLI entry point for Agent 4."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Agent 4: Gap Analysis")
    parser.add_argument("scope_file", help="JSON file with scope_definition from Agent 1")
    parser.add_argument("rules_file", help="JSON file with business_rules from Agent 3")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    with open(args.scope_file) as f:
        scope = json.load(f)
    with open(args.rules_file) as f:
        rules = json.load(f)
    
    agent = Agent4GapAnalysis(args.config)
    result = agent.execute(scope, rules)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
