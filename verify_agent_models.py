#!/usr/bin/env python3
"""
Verify which actual model each agent is configured to use.
Shows real configuration from config.yaml, not display text.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.config_loader import ConfigLoader
from config.llm_selector import LLMSelector

def verify_agent_models():
    """Display actual model configuration for all 9 agents."""
    
    try:
        config_path = Path(__file__).parent / "config" / "config.yaml"
        config = ConfigLoader(str(config_path))
        llm_config = config.get("llm", {})
        
        print("\n" + "="*80)
        print("AGENT MODEL CONFIGURATION VERIFICATION")
        print("="*80)
        print("\nThis shows the ACTUAL models configured in config.yaml")
        print("(Not display text - real configuration)\n")
        
        models_section = llm_config.get("models", {})
        
        # Display each agent
        for agent_num in range(1, 10):
            agent_key = f"agent{agent_num}"
            agent_config = models_section.get(agent_key, {})
            
            if not agent_config:
                continue
            
            name = agent_config.get("name", "Unknown")
            model = agent_config.get("model", "N/A")
            provider = agent_config.get("provider", "N/A").upper()
            complexity = agent_config.get("complexity", "N/A")
            task = agent_config.get("task", "")
            temperature = agent_config.get("temperature", "N/A")
            max_tokens = agent_config.get("max_tokens", "N/A")
            
            # Color codes
            complexity_emoji = {
                "HIGH": "🔴",
                "MEDIUM": "🟡", 
                "LOW": "🟢"
            }.get(complexity, "⚪")
            
            print(f"Agent {agent_num}: {name}")
            print(f"  {'─' * 76}")
            print(f"  Model:      {model}")
            print(f"  Provider:   {provider}")
            print(f"  Complexity: {complexity_emoji} {complexity}")
            print(f"  Task:       {task}")
            print(f"  Temperature: {temperature}")
            print(f"  Max Tokens:  {max_tokens}")
            print()
        
        # Display provider details
        print("\n" + "="*80)
        print("PROVIDER DETAILS")
        print("="*80 + "\n")
        
        providers = llm_config.get("providers", {})
        
        for provider_name, provider_data in providers.items():
            models_list = provider_data.get("available_models", [])
            print(f"\n{provider_name.upper()} ({len(models_list)} models available):")
            print("─" * 80)
            for model_info in models_list:
                model_id = model_info.get("id")
                display = model_info.get("display")
                input_cost = model_info.get("input_cost_per_mtok", 0)
                output_cost = model_info.get("output_cost_per_mtok", 0)
                
                print(f"  • {model_id}")
                print(f"    Display: {display}")
                print(f"    Cost: ${input_cost:.5f}/MTok input, ${output_cost:.5f}/MTok output")
        
        print("\n" + "="*80)
        print("✅ VERIFICATION COMPLETE")
        print("="*80)
        print("\nThese are the REAL models each agent will use.")
        print("This configuration is loaded from config/config.yaml at runtime.")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_agent_models()
