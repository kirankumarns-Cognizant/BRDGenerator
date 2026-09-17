#!/usr/bin/env python3
"""
Master Orchestrator — Run all 9 LLM-powered agents on a repository.
Generates all 31 artifacts per repository with repo-specific content.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from kb_gen.utils.brd_confidence_calculator import BRDConfidenceCalculator

# Import model display for pipeline tracking
try:
    from config.llm_selector import LLMSelector
except ImportError:
    LLMSelector = None


def run_all_agents(repo_path: str, output_base: str = "KB", skip_multi_repo: bool = True):
    """Run all 9 agents on the given repository.
    
    Args:
        repo_path: Path to repository
        output_base: Base output directory
        skip_multi_repo: If True (default), run only on main repo (don't process sub-repos)
    """
    repo_path = Path(repo_path)

    # Check if this is a parent directory with multiple sub-repos (unless skipped)
    if not skip_multi_repo:
        sub_repos = _find_sub_repos(repo_path)

        if sub_repos and len(sub_repos) > 1:
            print(f"\n{'='*70}")
            print(f"MULTI-REPO DETECTED")
            print(f"{'='*70}")
            print(f"Directory: {repo_path}")
            print(f"Found {len(sub_repos)} sub-repositories:\n")
            for i, sub_repo in enumerate(sub_repos, 1):
                print(f"  {i}. {sub_repo.name}")
            print(f"\nRunning all 9 agents on each repo...")
            print(f"(Use --single to run only on main repo)\n")

            for sub_repo in sub_repos:
                print(f"\n{'#'*70}")
                print(f"Processing: {sub_repo.name}")
                print(f"{'#'*70}\n")
                _run_single_repo(sub_repo, output_base)
            return

    # Single repository (main repo only) - DEFAULT
    _run_single_repo(repo_path, output_base)


def _find_sub_repos(path: Path) -> list:
    """Find sub-repositories (directories with source code)."""
    sub_repos = []

    if not path.is_dir():
        return sub_repos

    for item in path.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        # Check if this looks like a repo (has source files or build files)
        has_java = any(item.rglob("*.java"))
        has_py = any(item.rglob("*.py"))
        has_js = any(item.rglob("*.js"))
        has_build = any(item.rglob(f) for f in ["pom.xml", "build.gradle", "package.json", "setup.py"])

        if has_java or has_py or has_js or has_build:
            sub_repos.append(item)

    return sorted(sub_repos)


def _run_single_repo(repo_path: Path, output_base: str):
    """Run all 9 agents on a single repository."""
    repo_name = repo_path.name
    output_path = Path(output_base) / repo_name

    print(f"\n{'='*70}")
    print(f"BRD AGENT ORCHESTRATOR - Full Pipeline")
    print(f"{'='*70}")
    print(f"Repository: {repo_path}")
    print(f"Output: {output_path}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    agents = [
        ("Agent 1", ".github/skills/agent-1-discovery/agent_1_discovery_llm.py", "Discovery & Scoping"),
        ("Agent 2", ".github/skills/agent-2-journey-mapping/agent_2_journey_mapping_llm.py", "Journey Mapping"),
        ("Agent 3", ".github/skills/agent-3-business-rules/agent_3_business_rules_llm.py", "Business Rules"),
        ("Agent 4", ".github/skills/agent-4-gap-analysis/agent_4_gap_analysis_llm.py", "Gap Analysis"),
        ("Agent 5", ".github/skills/agent-5-synthesis/agent_5_synthesis_llm.py", "Synthesis"),
        ("Agent 6", ".github/skills/agent-6-acceptance-criteria/agent_6_acceptance_criteria_llm.py", "Acceptance Criteria"),
        ("Agent 7", ".github/skills/agent-7-risk-dependency/agent_7_risk_dependency_llm.py", "Risk & Dependency"),
        ("Agent 8", ".github/skills/agent-8-summarizer/agent_8_summarizer_llm.py", "Summarization"),
        ("Agent 9", ".github/skills/agent-9-kb-store-sync/agent_9_kb_store_sync_llm.py", "KB Store Sync"),
    ]

    results = []
    failed_agents = []

    for agent_num, agent_script, agent_name in agents:
        # Get agent number from string (e.g., "Agent 1" -> 1)
        agent_num_int = int(agent_num.split()[-1])
        
        # Get model configuration for this agent
        model_config = None
        model_display = "N/A"
        provider_display = "N/A"
        complexity_display = "N/A"
        
        if LLMSelector:
            try:
                model_config = LLMSelector.get_model_for_agent(agent_num_int)
                model_display = model_config.get("model", "N/A") or "N/A"
                provider_display = model_config.get("provider", "anthropic").upper() or "N/A"
                complexity_display = model_config.get("complexity", "N/A") or "N/A"
            except Exception as err:
                print(f"Warning: Could not get model config: {err}")
        
        # Display model BEFORE agent runs
        print(f"\n{'#'*70}")
        print(f"🤖 {agent_num}: {agent_name}")
        print(f"{'#'*70}")
        print(f"📊 Model Configuration:")
        print(f"   Model:      {model_display}")
        print(f"   Provider:   {provider_display}")
        print(f"   Complexity: {complexity_display}")
        print(f"{'#'*70}\n")
        sys.stdout.flush()

        print(f"\n[{'='*60}]")
        print(f"Executing {agent_num}: {agent_name}")
        print(f"[{'='*60}]\n")
        sys.stdout.flush()

        try:
            script_path = Path(agent_script)
            if not script_path.exists():
                print(f"WARNING: Script not found: {script_path}")
                failed_agents.append((agent_num, "Script not found"))
                continue

            cmd = [sys.executable, str(script_path), str(repo_path), "--output", str(output_path)]
            # Increased timeout to 15 minutes (900s) for LLM API calls
            result = subprocess.run(cmd, capture_output=False, text=True, timeout=900)
            
            sys.stdout.flush()

            if result.returncode == 0:
                # Display completion with model used
                print(f"\n{'='*70}")
                print(f"✅ {agent_num}: {agent_name} - COMPLETED")
                print(f"{'='*70}")
                print(f"📊 Model Used:")
                print(f"   Model:      {model_display}")
                print(f"   Provider:   {provider_display}")
                print(f"   Complexity: {complexity_display}")
                print(f"{'='*70}\n")
                sys.stdout.flush()
                
                results.append((agent_num, "SUCCESS", model_display, provider_display))
            else:
                print(f"\n{'='*70}")
                print(f"❌ {agent_num}: {agent_name} - FAILED")
                print(f"{'='*70}")
                print(f"Return code: {result.returncode}")
                print(f"{'='*70}\n")
                sys.stdout.flush()
                
                results.append((agent_num, "FAILED", model_display, provider_display))
                failed_agents.append((agent_num, f"Return code {result.returncode}"))

        except subprocess.TimeoutExpired as e:
            print(f"\n{'='*70}")
            print(f"⏱️  {agent_num}: {agent_name} - TIMEOUT")
            print(f"{'='*70}")
            print(f"Agent took longer than 15 minutes (LLM API delay)")
            print(f"Try running again - API calls may be slow")
            print(f"{'='*70}\n")
            sys.stdout.flush()
            
            results.append((agent_num, "TIMEOUT", model_display, provider_display))
            failed_agents.append((agent_num, "Timeout - LLM API delay"))

        except Exception as e:
            print(f"\n{'='*70}")
            print(f"⚠️  {agent_num}: {agent_name} - ERROR")
            print(f"{'='*70}")
            print(f"Exception: {e}")
            print(f"{'='*70}\n")
            sys.stdout.flush()
            
            results.append((agent_num, "ERROR", model_display, provider_display))
            failed_agents.append((agent_num, str(e)))

    # Generate final report
    print(f"\n{'='*70}")
    print("FINAL REPORT - AGENT EXECUTION SUMMARY")
    print(f"{'='*70}\n")

    print("Agent Execution Summary with Models:")
    print(f"{'Agent':<12} {'Status':<10} {'Model':<25} {'Provider':<12}")
    print("-" * 70)
    for result in results:
        agent = result[0]
        status = result[1]
        model = result[2] if len(result) > 2 else "N/A"
        provider = result[3] if len(result) > 3 else "N/A"
        # Handle None values
        model = model or "N/A"
        provider = provider or "N/A"
        symbol = "✅" if status == "SUCCESS" else "❌"
        print(f"{agent:<12} {symbol} {status:<8} {model:<25} {provider:<12}")

    # Count artifacts
    if output_path.exists():
        json_files = list(output_path.glob("*.json"))
        md_files = list(output_path.glob("*.md"))
        total_artifacts = len(json_files) + len(md_files)
        print(f"\nArtifacts Generated:")
        print(f"  JSON files: {len(json_files)}")
        print(f"  Markdown files: {len(md_files)}")
        print(f"  Total: {total_artifacts} / 31 expected")

        if total_artifacts >= 31:
            print(f"\n[OK] ALL 31 ARTIFACTS SUCCESSFULLY GENERATED!")
        else:
            print(f"\n[WARNING] Only {total_artifacts} artifacts generated (expected 31)")

    if failed_agents:
        print(f"\nFailed Agents ({len(failed_agents)}):")
        for agent, reason in failed_agents:
            print(f"  - {agent}: {reason}")
    else:
        print(f"\n[OK] All agents executed successfully!")

    # Generate BRD Confidence Report
    print("\n" + "=" * 70)
    print("Calculating BRD Confidence Score...")
    print("=" * 70)

    try:
        calculator = BRDConfidenceCalculator(output_path)
        confidence_report = calculator.generate_report()
        print(confidence_report)
    except Exception as e:
        print(f"[WARNING] Could not calculate confidence: {e}")

    print(f"\nEnd Time: {datetime.now().isoformat()}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run all 9 LLM-powered BRD agents")
    parser.add_argument("repo_path", help="Path to repository to analyze")
    parser.add_argument("--output", default="KB", help="Base output directory")
    parser.add_argument("--all", action="store_true", help="Run on all sub-repos (default: main repo only)")

    args = parser.parse_args()

    # Default: skip_multi_repo=True (run main repo only)
    # If --all flag: skip_multi_repo=False (run all sub-repos)
    run_all_agents(args.repo_path, args.output, skip_multi_repo=not args.all)
