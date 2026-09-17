#!/usr/bin/env python3
"""
Test to show what the pipeline output will look like with model display.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.llm_selector import LLMSelector

def preview_pipeline_output():
    """Preview how the pipeline will display models after each agent."""
    
    print("\n" + "="*80)
    print("PIPELINE EXECUTION PREVIEW - Model Display")
    print("="*80)
    print("\nThis is what you will see when running the pipeline:\n")
    
    agents = [
        ("Agent 1", "Discovery & Scoping", 1),
        ("Agent 2", "Journey Mapping", 2),
        ("Agent 3", "Business Rules", 3),
        ("Agent 4", "Gap Analysis", 4),
        ("Agent 5", "Synthesis", 5),
        ("Agent 6", "Acceptance Criteria", 6),
        ("Agent 7", "Risk & Dependency", 7),
        ("Agent 8", "BRD Summarizer", 8),
    ]
    
    for agent_num_str, agent_name, agent_num_int in agents:
        # Get model config
        model_config = LLMSelector.get_model_for_agent(agent_num_int)
        model = model_config.get("model")
        provider = model_config.get("provider").upper()
        complexity = model_config.get("complexity")
        
        # Show BEFORE
        print(f"\n{'#'*70}")
        print(f"🤖 {agent_num_str}: {agent_name}")
        print(f"{'#'*70}")
        print(f"📊 Model Configuration:")
        print(f"   Model:      {model}")
        print(f"   Provider:   {provider}")
        print(f"   Complexity: {complexity}")
        print(f"{'#'*70}")
        
        print(f"\n[{'='*60}]")
        print(f"Executing {agent_num_str}: {agent_name}")
        print(f"[{'='*60}]")
        print("\n[Agent execution output would appear here...]")
        
        # Show AFTER
        print(f"\n{'='*70}")
        print(f"✅ {agent_num_str}: {agent_name} - COMPLETED")
        print(f"{'='*70}")
        print(f"📊 Model Used:")
        print(f"   Model:      {model}")
        print(f"   Provider:   {provider}")
        print(f"   Complexity: {complexity}")
        print(f"{'='*70}\n")
    
    print("\n" + "="*80)
    print("✅ This is the expected output format")
    print("="*80 + "\n")

if __name__ == "__main__":
    preview_pipeline_output()
