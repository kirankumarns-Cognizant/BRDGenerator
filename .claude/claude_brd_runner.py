#!/usr/bin/env python3
"""
Claude BRD Runner - Simplified CLI for BRD generation via .claude
Calls the proven .github framework directly to generate comprehensive 30+ file outputs.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run BRD pipeline via .github framework."""
    if len(sys.argv) < 2:
        print("Usage: python claude_brd_runner.py <repo_path> [--output OUTPUT_DIR] [--all]")
        print("\nExample:")
        print("  python claude_brd_runner.py Sample_Repos/Springy-Store-Microservices --output KB/brd_output")
        print("  python claude_brd_runner.py Sample_Repos/Library-Management-System-JAVA-master --output KB/lib --all")
        print("\nOptions:")
        print("  --output DIR   Output directory (default: KB)")
        print("  --all          Run on all sub-repos (default: main repo only)")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    # Parse output directory if provided
    output_dir = "KB"
    run_all_repos = False
    
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
    
    if "--all" in sys.argv:
        run_all_repos = True
    
    # Verify repo path exists
    if not Path(repo_path).exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("CLAUDE BRD RUNNER - Comprehensive Business Requirements Document Generation")
    print("="*80)
    print(f"Repository:    {repo_path}")
    print(f"Output:        {output_dir}")
    print(f"Process Mode:  {'All sub-repos' if run_all_repos else 'Main repo only (fastest)'}")
    print("Framework:     .github (LLM-powered agents)")
    print("Expected:      30+ comprehensive analysis files")
    print("="*80 + "\n")
    
    # Call run_all_agents.py with UTF-8 encoding for Windows compatibility
    try:
        cmd = [sys.executable, "run_all_agents.py", repo_path, "--output", output_dir]
        if run_all_repos:
            cmd.append("--all")
        
        # Set environment for UTF-8 support on Windows
        import os
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running BRD pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
