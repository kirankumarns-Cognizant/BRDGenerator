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


def run_all_agents(repo_path: str, output_base: str = "KB"):
    """Run all 9 agents on the given repository."""
    repo_path = Path(repo_path)

    # Check if this is a parent directory with multiple sub-repos
    sub_repos = _find_sub_repos(repo_path)

    if sub_repos and len(sub_repos) > 1:
        print(f"\n{'='*70}")
        print(f"MULTI-REPO DETECTED")
        print(f"{'='*70}")
        print(f"Directory: {repo_path}")
        print(f"Found {len(sub_repos)} sub-repositories:\n")
        for i, sub_repo in enumerate(sub_repos, 1):
            print(f"  {i}. {sub_repo.name}")
        print(f"\nRunning all 9 agents on each repo...\n")

        for sub_repo in sub_repos:
            print(f"\n{'#'*70}")
            print(f"Processing: {sub_repo.name}")
            print(f"{'#'*70}\n")
            _run_single_repo(sub_repo, output_base)
        return

    # Single repository
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
        print(f"\n[{'='*60}]")
        print(f"Running {agent_num}: {agent_name}")
        print(f"[{'='*60}]\n")

        try:
            script_path = Path(agent_script)
            if not script_path.exists():
                print(f"WARNING: Script not found: {script_path}")
                failed_agents.append((agent_num, "Script not found"))
                continue

            cmd = [sys.executable, str(script_path), str(repo_path), "--output", str(output_path)]
            result = subprocess.run(cmd, capture_output=False, text=True, timeout=120)

            if result.returncode == 0:
                print(f"\n[OK] {agent_num} completed successfully\n")
                results.append((agent_num, "SUCCESS"))
            else:
                print(f"\n[FAIL] {agent_num} failed with return code {result.returncode}\n")
                results.append((agent_num, "FAILED"))
                failed_agents.append((agent_num, f"Return code {result.returncode}"))

        except Exception as e:
            print(f"\n[ERROR] {agent_num} exception: {e}\n")
            results.append((agent_num, "ERROR"))
            failed_agents.append((agent_num, str(e)))

    # Generate final report
    print(f"\n{'='*70}")
    print("FINAL REPORT")
    print(f"{'='*70}\n")

    print("Agent Execution Summary:")
    for agent, status in results:
        symbol = "[OK]" if status == "SUCCESS" else "[FAIL]"
        print(f"  {symbol} {agent}: {status}")

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

    args = parser.parse_args()

    run_all_agents(args.repo_path, args.output)
