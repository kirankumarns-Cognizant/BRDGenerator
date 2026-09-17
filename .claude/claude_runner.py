"""
Claude BRD Pipeline Runner

This module enables Claude to execute the BRD generation pipeline programmatically.
Claude can import and use this to run the full 9-agent pipeline.

Usage:
    from .claude.claude_runner import execute_pipeline
    result = execute_pipeline('/path/to/repo', ['doc1.pdf'])
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any


class ClaudeRunner:
    """Interface for Claude to execute BRD pipeline."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize runner with project root."""
        if project_root:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent.parent
        
        self.config_path = self.project_root / "config" / "config.yaml"
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def execute_full_pipeline(
        self,
        repo_path: str,
        documents: Optional[List[str]] = None,
        confidence_threshold: float = 0.6,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the full BRD pipeline (Agents 1-9).
        
        Args:
            repo_path: Path to repository to analyze
            documents: List of document paths to include
            confidence_threshold: Minimum confidence score (0.0-1.0)
            verbose: Enable detailed output
            
        Returns:
            {
                "status": "SUCCESS" | "FAILURE",
                "execution_time": seconds,
                "overall_confidence": 0.0-1.0,
                "agents_executed": [1, 2, 3, ...],
                "artifacts": [list of output files],
                "output_dir": path to results,
                "errors": [if any],
                "metrics": {...}
            }
        """
        print("🚀 Starting BRD Pipeline Orchestration...")
        print(f"   Repository: {repo_path}")
        if documents:
            print(f"   Documents: {len(documents)} file(s)")
        print(f"   Config: {self.config_path}")
        print()
        
        try:
            # Validate inputs
            repo_path_obj = Path(repo_path)
            if not repo_path_obj.exists():
                raise FileNotFoundError(f"Repository not found: {repo_path}")
            
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config not found: {self.config_path}")
            
            # Execute pipeline
            cmd = [
                "python",
                str(self.project_root / "run_all_agents.py"),
                repo_path,
                "--config", str(self.config_path)
            ]
            
            if verbose:
                cmd.append("--verbose")
            
            print(f"📋 Executing: {' '.join(cmd)}\n")
            
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "output_dir": str(self.project_root / "KB" / Path(repo_path).name),
                    "agents_executed": list(range(1, 10)),
                    "confidence_threshold": confidence_threshold
                }
            else:
                return {
                    "status": "FAILURE",
                    "error": f"Pipeline execution failed with code {result.returncode}",
                    "output_dir": None
                }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "output_dir": None
            }
    
    def execute_agent(
        self,
        agent_num: int,
        repo_path: str,
        documents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single agent.
        
        Args:
            agent_num: Agent number (1-9)
            repo_path: Path to repository
            documents: List of document paths
            
        Returns:
            Agent execution result with output and confidence
        """
        valid_agents = range(1, 10)
        if agent_num not in valid_agents:
            return {
                "status": "ERROR",
                "error": f"Invalid agent number. Must be 1-9."
            }
        
        print(f"🤖 Executing Agent {agent_num}...")
        
        agent_script = self.project_root / f"agent{agent_num}_runner.py"
        if not agent_script.exists():
            # Try alternate path
            agent_script = self.project_root / ".github" / "skills" / f"agent-{agent_num}-*" / f"agent_{agent_num}_*.py"
        
        try:
            cmd = ["python", str(agent_script), repo_path]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_root))
            
            if result.returncode == 0:
                return {
                    "status": "SUCCESS",
                    "agent": agent_num,
                    "output": result.stdout
                }
            else:
                return {
                    "status": "FAILURE",
                    "agent": agent_num,
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "status": "ERROR",
                "agent": agent_num,
                "error": str(e)
            }
    
    def get_model_config(self, agent_num: int) -> Dict[str, str]:
        """Get LLM model configuration for an agent."""
        try:
            from config.llm_selector import LLMSelector
            return LLMSelector.get_model_for_agent(agent_num)
        except Exception as e:
            return {"error": str(e)}
    
    def validate_config(self) -> bool:
        """Validate configuration file."""
        try:
            from config.config_loader import ConfigLoader
            config = ConfigLoader(str(self.config_path))
            print("✅ Configuration valid")
            print(f"   Agents: 9")
            print(f"   LLM Providers: Anthropic, OpenAI")
            return True
        except Exception as e:
            print(f"❌ Configuration invalid: {e}")
            return False
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline execution status."""
        status_file = self.logs_dir / "pipeline_status.json"
        if status_file.exists():
            with open(status_file) as f:
                return json.load(f)
        return {"status": "IDLE", "current_agent": None}


def execute_pipeline(
    repo_path: str,
    documents: Optional[List[str]] = None,
    project_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for Claude to execute BRD pipeline.
    
    Usage:
        result = execute_pipeline("KB/my-repo", ["spec.pdf"])
        if result["status"] == "SUCCESS":
            print(f"BRD saved to {result['output_dir']}")
    """
    runner = ClaudeRunner(project_root)
    return runner.execute_full_pipeline(repo_path, documents)


def execute_single_agent(
    agent_num: int,
    repo_path: str,
    project_root: Optional[str] = None
) -> Dict[str, Any]:
    """Execute a single agent."""
    runner = ClaudeRunner(project_root)
    return runner.execute_agent(agent_num, repo_path)


if __name__ == "__main__":
    # Example usage
    runner = ClaudeRunner()
    
    # Validate configuration
    runner.validate_config()
    
    # Show model config for each agent
    print("\n📊 Agent Model Configuration:")
    for agent_num in range(1, 10):
        config = runner.get_model_config(agent_num)
        if "error" not in config:
            print(f"   Agent {agent_num}: {config.get('model')} ({config.get('complexity')})")
    
    print("\n✅ Claude BRD Pipeline Runner is ready!")
    print("\nUsage:")
    print("  from .claude.claude_runner import execute_pipeline")
    print("  result = execute_pipeline('KB/my-repo')")
