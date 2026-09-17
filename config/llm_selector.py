"""
LLM Model Selector - Smart model selection based on task complexity

Selects appropriate LLM model for each agent:
- HIGH complexity → claude-3-opus (best reasoning)
- MEDIUM complexity → claude-3-sonnet (good balance)
- LOW complexity → claude-3-haiku (fast & cost-effective)
"""

import os
from typing import Dict, Tuple
from pathlib import Path

try:
    from .config_loader import ConfigLoader
except ImportError:
    from config_loader import ConfigLoader

# Initialize config loader
_config_path = Path(__file__).parent / "config.yaml"
try:
    _config = ConfigLoader(str(_config_path))
except Exception as e:
    print(f"Warning: Could not load config.yaml: {e}")
    _config = None


class LLMSelector:
    """Select appropriate LLM model based on agent task complexity."""
    
    # Agent complexity mapping
    AGENT_COMPLEXITY = {
        1: "HIGH",      # Discovery - complex scope analysis
        2: "LOW",       # Journey mapping - pattern matching
        3: "LOW",       # Rules extraction - simple analysis
        4: "LOW",       # Gap identification - checklist comparison
        5: "HIGH",      # Synthesis - complex reasoning
        6: "LOW",       # Acceptance criteria - template filling
        7: "MEDIUM",    # Risk analysis - strategic thinking
        8: "HIGH",      # BRD writing - complex synthesis
        9: "NONE"       # KB Store - no LLM needed (vector DB only)
    }
    
    @staticmethod
    def get_model_for_agent(agent_number: int) -> Dict:
        """
        Get LLM configuration for specific agent.
        
        Args:
            agent_number: Agent 1-9
            
        Returns:
            Dict with: model, temperature, max_tokens, complexity, task
        """
        if agent_number == 9:
            return {
                "model": None,
                "temperature": None,
                "max_tokens": None,
                "complexity": "NONE",
                "task": "Vector database (no LLM needed)",
                "provider": None
            }
        
        agent_key = f"agent{agent_number}"
        
        # Get from config.yaml
        try:
            if _config is None:
                return LLMSelector._get_default_config(agent_number)
            
            model_config = _config.get(f"llm.models.agent{agent_number}")
            
            if not model_config:
                # Fallback to defaults
                return LLMSelector._get_default_config(agent_number)
            
            return {
                "model": model_config.get("model"),
                "temperature": model_config.get("temperature", 0.7),
                "max_tokens": model_config.get("max_tokens", 4096),
                "complexity": LLMSelector.AGENT_COMPLEXITY.get(agent_number, "UNKNOWN"),
                "task": model_config.get("task", "Unknown task"),
                "provider": model_config.get("provider", _config.get("llm.default_provider", "anthropic") if _config else "anthropic"),
                "name": model_config.get("name", f"Agent {agent_number}")
            }
        except Exception as e:
            print(f"⚠️  Warning: Could not load config for agent{agent_number}: {e}")
            return LLMSelector._get_default_config(agent_number)
    
    @staticmethod
    def _get_default_config(agent_number: int) -> Dict:
        """Get default model config if config.yaml not available."""
        defaults = {
            1: {
                "model": "claude-3-opus",
                "temperature": 0.7,
                "max_tokens": 4096,
                "complexity": "HIGH",
                "task": "Complex scope analysis"
            },
            2: {
                "model": "claude-3-haiku",
                "temperature": 0.5,
                "max_tokens": 2048,
                "complexity": "LOW",
                "task": "Pattern matching on journeys"
            },
            3: {
                "model": "claude-3-haiku",
                "temperature": 0.3,
                "max_tokens": 2048,
                "complexity": "LOW",
                "task": "Rule extraction"
            },
            4: {
                "model": "claude-3-haiku",
                "temperature": 0.5,
                "max_tokens": 2048,
                "complexity": "LOW",
                "task": "Gap identification"
            },
            5: {
                "model": "claude-3-opus",
                "temperature": 0.7,
                "max_tokens": 4096,
                "complexity": "HIGH",
                "task": "Requirement synthesis"
            },
            6: {
                "model": "claude-3-haiku",
                "temperature": 0.3,
                "max_tokens": 1024,
                "complexity": "LOW",
                "task": "Acceptance criteria template"
            },
            7: {
                "model": "claude-3-sonnet",
                "temperature": 0.6,
                "max_tokens": 3000,
                "complexity": "MEDIUM",
                "task": "Risk and dependency analysis"
            },
            8: {
                "model": "claude-3-opus",
                "temperature": 0.7,
                "max_tokens": 8192,
                "complexity": "HIGH",
                "task": "BRD document synthesis"
            }
        }
        
        default = defaults.get(agent_number, {
            "model": "claude-3-opus",
            "temperature": 0.7,
            "max_tokens": 4096,
            "complexity": "UNKNOWN"
        })
        
        default["provider"] = os.getenv("LLM_PROVIDER", "anthropic")
        return default
    
    @staticmethod
    def get_complexity(agent_number: int) -> str:
        """Get task complexity for agent."""
        return LLMSelector.AGENT_COMPLEXITY.get(agent_number, "UNKNOWN")
    
    @staticmethod
    def get_model_name(agent_number: int) -> str:
        """Get just the model name."""
        config_dict = LLMSelector.get_model_for_agent(agent_number)
        return config_dict.get("model", "unknown")
    
    @staticmethod
    def get_api_key() -> str:
        """Get LLM API key from environment."""
        api_key_env = config.get("llm.api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(
                f"LLM API key not found. "
                f"Please set environment variable: {api_key_env}"
            )
        return api_key
    
    @staticmethod
    def print_agent_models():
        """Print all agent-to-model mappings (for debugging/logging)."""
        print("\n" + "="*70)
        print("🤖 AGENT → LLM MODEL MAPPING")
        print("="*70)
        
        total_cost_high = 0
        total_cost_optimized = 0
        
        for agent_num in range(1, 10):
            config_dict = LLMSelector.get_model_for_agent(agent_num)
            complexity = config_dict.get("complexity")
            model = config_dict.get("model")
            task = config_dict.get("task")
            
            if complexity == "NONE":
                print(f"\nAgent {agent_num}: {task}")
                print(f"  Model: N/A (Vector Database)")
                continue
            
            # Estimated costs (rough, per request)
            model_costs = {
                "claude-3-opus": 0.05,
                "claude-3-sonnet": 0.03,
                "claude-3-haiku": 0.008
            }
            
            cost = model_costs.get(model, 0.05)
            total_cost_optimized += cost
            
            # If all used opus (non-optimized)
            total_cost_high += model_costs["claude-3-opus"]
            
            complexity_emoji = {
                "HIGH": "🔴",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(complexity, "⚪")
            
            print(f"\nAgent {agent_num}: {task}")
            print(f"  {complexity_emoji} Complexity: {complexity}")
            print(f"  Model: {model}")
            print(f"  Est. Cost/BRD: ${cost:.3f}")
        
        print("\n" + "="*70)
        print(f"📊 COST ANALYSIS:")
        print(f"  If all agents used claude-3-opus: ${total_cost_high:.2f} per BRD")
        print(f"  Optimized (smart selection):      ${total_cost_optimized:.2f} per BRD")
        print(f"  Cost Reduction: {((total_cost_high - total_cost_optimized) / total_cost_high * 100):.1f}%")
        print("="*70 + "\n")
    
    @staticmethod
    def validate_config() -> Tuple[bool, str]:
        """
        Validate that LLM configuration is properly set up.
        
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        errors = []
        
        # Check API key
        try:
            api_key = LLMSelector.get_api_key()
            if not api_key:
                errors.append("LLM API key is empty")
        except ValueError as e:
            errors.append(str(e))
        
        # Check config has all agents
        for agent_num in range(1, 9):
            config_dict = LLMSelector.get_model_for_agent(agent_num)
            if not config_dict.get("model"):
                errors.append(f"Agent {agent_num} has no model configured")
        
        if errors:
            return False, "\n".join(f"  ❌ {e}" for e in errors)
        
        return True, "✅ LLM configuration is valid"


# Initialize and print on import (for debugging)
if __name__ == "__main__":
    # Print all mappings when run as script
    is_valid, message = LLMSelector.validate_config()
    print(message)
    
    if is_valid:
        LLMSelector.print_agent_models()
    else:
        print("\n⚠️  Configuration Issues:")
        print(message)
