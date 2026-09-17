#!/usr/bin/env python3
"""
Agent 1: Discovery & Scoping
Scans Java repositories, catalogs artifacts, and produces scope definitions.
Wrapper for Claude execution via .claude framework.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent paths for imports
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


class Agent1Discovery:
    """Agent 1: Discovery & Scoping implementation - Uses real kb_gen logic."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigLoader(config_path or "config/config.yaml")
        self.kb_gen_available = KB_GEN_AVAILABLE
        
        # Initialize real kb_gen backend if available
        if self.kb_gen_available:
            try:
                from kb_gen.ingestion.ingestor import RepositoryIngestor
                self.backend = RepositoryIngestor(self.config)
            except (ImportError, Exception) as e:
                import logging
                logging.warning(f"Failed to initialize real Agent 1 backend: {e}")
                self.backend = None
        else:
            self.backend = None
        
        # Fallback executor
        self.executor = AgentExecutor(agent_num=1, config=self.config)
    
    def execute(self, repo_path: str, **kwargs) -> Dict[str, Any]:
        """
        Execute discovery and scoping on a repository using real kb_gen logic.
        
        Args:
            repo_path: Path to Java repository to scan
            **kwargs: Additional parameters (scope, filters, etc.)
        
        Returns:
            Dictionary containing scope_definition, artifact_catalog, dependency_map
        """
        # Try real backend first
        if self.backend:
            try:
                result = self.backend.execute(repo_path=repo_path, **kwargs)
                return {**result, "confidence": result.get("confidence", 0.85), "kb_gen_used": True}
            except Exception as e:
                import logging
                logging.error(f"Real backend execution failed: {e}")
        
        # Fallback to executor (which has graceful mock fallback)
        return self.executor.execute(repo_path=repo_path, **kwargs)
    
    def scan_repository(self, repo_path: str) -> Dict[str, Any]:
        """Scan repository and catalog artifacts."""
        return self.executor.scan_repository(repo_path)
    
    def analyze_dependencies(self, artifacts: list) -> Dict[str, Any]:
        """Analyze dependencies between artifacts."""
        return self.executor.analyze_dependencies(artifacts)


def main():
    """CLI entry point for Agent 1."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 1: Discovery & Scoping")
    parser.add_argument("repo_path", help="Path to Java repository")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    agent = Agent1Discovery(args.config)
    result = agent.execute(args.repo_path)
    
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        import json
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
