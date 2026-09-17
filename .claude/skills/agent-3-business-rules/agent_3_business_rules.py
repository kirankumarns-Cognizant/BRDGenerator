#!/usr/bin/env python3
"""
Agent 3: Business Rules Extraction
Extracts business rules, constraints, and validations from code and artifacts.
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


class Agent3BusinessRules:
    """Agent 3: Business Rules Extraction implementation - Uses real kb_gen logic."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.kb_gen_available = KB_GEN_AVAILABLE
        
        # Initialize real kb_gen backend if available
        if self.kb_gen_available:
            try:
                from kb_gen.analysis.rule_extractor import RuleExtractor
                self.backend = RuleExtractor(self.config)
            except (ImportError, Exception) as e:
                import logging
                logging.warning(f"Failed to initialize real Agent 3 backend: {e}")
                self.backend = None
        else:
            self.backend = None
        
        # Fallback executor
        self.executor = AgentExecutor(agent_num=3, config=self.config)
    
    def execute(self, artifact_catalog: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Extract business rules and constraints using real kb_gen logic.
        
        Args:
            artifact_catalog: Artifact catalog from Agent 1
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing business_rules, constraints, validations
        """
        # Try real backend first
        if self.backend:
            try:
                result = self.backend.execute(artifact_catalog=artifact_catalog, **kwargs)
                return {**result, "confidence": result.get("confidence", 0.80), "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real backend execution failed: {e}")
        
        # Fallback to executor (which has graceful mock fallback)
        return self.executor.execute(artifact_catalog=artifact_catalog, **kwargs)
    
    def extract_rules(self, artifacts: List[Dict]) -> List[Dict[str, Any]]:
        """Extract business rules from artifacts."""
        return self.executor.extract_rules(artifacts)
    
    def identify_constraints(self, rules: List[Dict]) -> List[Dict[str, Any]]:
        """Identify constraints and limitations."""
        return self.executor.identify_constraints(rules)


def main():
    """CLI entry point for Agent 3."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Agent 3: Business Rules Extraction")
    parser.add_argument("catalog_file", help="JSON file with artifact_catalog from Agent 1")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    with open(args.catalog_file) as f:
        artifact_catalog = json.load(f)
    
    agent = Agent3BusinessRules(args.config)
    result = agent.execute(artifact_catalog)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
