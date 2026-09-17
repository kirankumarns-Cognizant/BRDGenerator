#!/usr/bin/env python3
"""
Streamlit Model Display Test
Shows what will appear in Streamlit UI during pipeline execution
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.llm_selector import LLMSelector

def test_streamlit_display():
    """Show what Streamlit will display for each agent."""
    
    print("\n" + "="*80)
    print("STREAMLIT MODEL DISPLAY TEST")
    print("="*80)
    print("\nWhen running 'python -m streamlit run app.py', during pipeline execution")
    print("you will see the following for each agent:\n")
    
    agents = [
        ("Agent 1: Discovery & Scoping", 1),
        ("Agent 2: Journey Mapping", 2),
        ("Agent 3: Business Rules", 3),
        ("Agent 4: Gap Analysis", 4),
        ("Agent 5: Synthesis", 5),
        ("Agent 6: Acceptance Criteria", 6),
        ("Agent 7: Risk & Dependency", 7),
        ("Agent 8: BRD Summarizer", 8),
    ]
    
    for agent_name, agent_num in agents:
        try:
            model_config = LLMSelector.get_model_for_agent(agent_num)
            model_info = {
                "model": model_config.get("model"),
                "provider": model_config.get("provider").upper(),
                "complexity": model_config.get("complexity"),
            }
            
            # Show the JSON that will be sent through the queue
            status_msg = {
                "__status": "agent_start",
                "name": agent_name,
                "index": agent_num - 1,
                "model_info": model_info
            }
            
            print(f"\n{'─'*80}")
            print(f"Agent: {agent_name}")
            print(f"{'─'*80}")
            print(f"Status Message (sent through pipeline):")
            print(json.dumps(status_msg, indent=2))
            
            print(f"\n✅ Streamlit will display:")
            print(f"   📊 Model Info:")
            print(f"   Model:      {model_info['model']}")
            print(f"   Provider:   {model_info['provider']}")
            print(f"   Complexity: {model_info['complexity']}")
            
        except Exception as e:
            print(f"\n❌ Error processing {agent_name}: {e}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)
    print("\nModel info will appear in a Streamlit container next to current agent.")
    print("Run: python -m streamlit run app.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_streamlit_display()
