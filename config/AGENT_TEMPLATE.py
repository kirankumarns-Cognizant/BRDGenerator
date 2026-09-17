"""
AGENT TEMPLATE - How to use LLM Model Selector in your agents

Copy this pattern to each agent file (.github/skills/agent-X-*/agent_X_*.py)
to enable smart model selection based on task complexity.
"""

import json
import sys
from pathlib import Path

# Import LLM selection utilities
from config.llm_selector import LLMSelector
from config.llm_client import LLMClient


def create_llm_client(agent_number: int):
    """
    Create LLM client with model selected based on agent task complexity.
    
    Args:
        agent_number: Which agent (1-8)
        
    Returns:
        LLM client configured with appropriate model
    """
    # Get model configuration for this agent
    model_config = LLMSelector.get_model_for_agent(agent_number)
    
    print(f"\n🤖 Agent {agent_number}: Model Selection")
    print(f"   Complexity: {model_config['complexity']}")
    print(f"   Model: {model_config['model']}")
    print(f"   Task: {model_config['task']}")
    print(f"   Max Tokens: {model_config['max_tokens']}")
    print(f"   Temperature: {model_config['temperature']}\n")
    
    # Create client with selected model
    llm = LLMClient(
        provider=model_config["provider"],
        model=model_config["model"],
        temperature=model_config["temperature"],
        max_tokens=model_config["max_tokens"]
    )
    
    return llm, model_config


# ============================================================================
# EXAMPLE 1: Agent 2 (LOW complexity - uses claude-3-haiku)
# ============================================================================

def agent_2_example(repo_path, output_dir):
    """Example Agent 2 implementation with smart model selection."""
    
    llm, model_config = create_llm_client(agent_number=2)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load previous agent's output
    scope = json.loads((output_dir / "scope_definition.json").read_text())
    
    # Scan Java controllers (no LLM needed)
    controllers = [
        "CatalogController",
        "CartController", 
        "OrderController",
        "AccountController"
    ]
    
    # CALL LLM with selected model (haiku for low complexity)
    prompt = f"""
    Given this Java pet store with controllers:
    - {', '.join(controllers)}
    
    And this scope:
    - Project: {scope['project_name']}
    - Tech: {', '.join(scope.get('technology_stack', []))}
    
    Map the main user journeys. Return JSON with:
    {{
        "journeys": [
            {{
                "actor": "customer",
                "journey_name": "Browse and Purchase",
                "steps": [
                    "1. Open home page",
                    "2. Search for pet",
                    "..."
                ],
                "confidence": 0.88
            }}
        ]
    }}
    """
    
    # Call with selected model (fast & cheap haiku for simple task)
    response = llm.call_json(prompt)
    
    # Save outputs
    with open(output_dir / "user_journeys.json", "w") as f:
        json.dump(response.get("journeys", []), f, indent=2)
    
    print("✅ Agent 2 completed with claude-3-haiku (cost-optimized)")
    return response


# ============================================================================
# EXAMPLE 2: Agent 5 (HIGH complexity - uses claude-3-opus)
# ============================================================================

def agent_5_example(repo_path, output_dir):
    """Example Agent 5 implementation with smart model selection."""
    
    llm, model_config = create_llm_client(agent_number=5)
    
    output_dir = Path(output_dir)
    
    # Load all previous outputs
    scope = json.loads((output_dir / "scope_definition.json").read_text())
    journeys = json.loads((output_dir / "user_journeys.json").read_text())
    rules = json.loads((output_dir / "business_rules.json").read_text())
    gaps = json.loads((output_dir / "gap_analysis.json").read_text())
    
    # CALL LLM with selected model (opus for high complexity)
    prompt = f"""
    Synthesize all BRD information and generate requirements:
    
    Scope: {json.dumps(scope, indent=2)}
    Journeys: {json.dumps(journeys, indent=2)}
    Rules: {json.dumps(rules, indent=2)}
    Gaps: {json.dumps(gaps, indent=2)}
    
    Generate 45+ functional requirements + non-functional requirements.
    Return JSON with:
    {{
        "functional_requirements": [
            {{
                "req_id": "FR_001",
                "title": "Browse Catalog",
                "description": "...",
                "priority": "high"
            }}
        ],
        "non_functional_requirements": [...]
    }}
    """
    
    # Call with selected model (powerful opus for complex synthesis)
    response = llm.call_json(prompt)
    
    # Save outputs
    with open(output_dir / "functional_requirements.json", "w") as f:
        json.dump(response.get("functional_requirements", []), f, indent=2)
    
    with open(output_dir / "non_functional_requirements.json", "w") as f:
        json.dump(response.get("non_functional_requirements", []), f, indent=2)
    
    print("✅ Agent 5 completed with claude-3-opus (high-quality reasoning)")
    return response


# ============================================================================
# EXAMPLE 3: Agent 7 (MEDIUM complexity - uses claude-3-sonnet)
# ============================================================================

def agent_7_example(repo_path, output_dir):
    """Example Agent 7 implementation with smart model selection."""
    
    llm, model_config = create_llm_client(agent_number=7)
    
    output_dir = Path(output_dir)
    
    # Load relevant outputs
    dependencies = json.loads((output_dir / "dependency_map.json").read_text())
    requirements = json.loads((output_dir / "functional_requirements.json").read_text())
    
    # CALL LLM with selected model (sonnet for medium complexity)
    prompt = f"""
    Analyze risks and dependencies:
    
    Dependencies: {json.dumps(dependencies, indent=2)}
    Requirements: {json.dumps(requirements, indent=2)}
    
    Identify:
    1. Technology risks (outdated libs, security)
    2. Dependency risks
    3. Architectural risks
    
    Return JSON with risks array containing: risk_id, title, severity, impact, mitigation
    """
    
    # Call with selected model (balanced sonnet for strategic analysis)
    response = llm.call_json(prompt)
    
    # Save outputs
    with open(output_dir / "risk_assessment.json", "w") as f:
        json.dump(response.get("risks", []), f, indent=2)
    
    print("✅ Agent 7 completed with claude-3-sonnet (balanced reasoning)")
    return response


# ============================================================================
# HOW TO USE IN YOUR ACTUAL AGENTS
# ============================================================================

"""
STEP 1: Add these imports to each agent file:
    from config.llm_selector import LLMSelector
    from config.llm_client import LLMClient

STEP 2: In your main() function, create the LLM client:
    def main(repo_path, output_dir):
        llm, model_config = create_llm_client(agent_number=2)
        
        # Your code here...
        response = llm.call_json(your_prompt)

STEP 3: Update config/config.yaml with LLM settings (already done!)

STEP 4: Set ANTHROPIC_API_KEY environment variable:
    export ANTHROPIC_API_KEY="your-api-key-here"

STEP 5: Test that it works:
    python config/llm_selector.py  # Should show model mappings
"""

if __name__ == "__main__":
    print("\n" + "="*70)
    print("📚 AGENT TEMPLATE - Smart LLM Model Selection")
    print("="*70)
    
    # Show all agent-to-model mappings
    LLMSelector.print_agent_models()
    
    print("\n" + "="*70)
    print("💡 INTEGRATION STEPS:")
    print("="*70)
    print("""
1. Copy this template to each agent:
   .github/skills/agent-X-*/agent_X_*.py

2. Import at the top:
   from config.llm_selector import LLMSelector
   from config.llm_client import LLMClient

3. In main() function:
   llm, config = create_llm_client(agent_number=X)
   response = llm.call_json(prompt)

4. Set API key:
   export ANTHROPIC_API_KEY="sk-ant-..."

5. Test:
   streamlit run app.py
   
✅ Each agent will now use the optimal model for its task!
    """)
    print("="*70)
