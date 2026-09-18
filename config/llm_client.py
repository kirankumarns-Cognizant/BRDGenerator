"""
LLM Client - Unified interface for calling Claude/OpenAI APIs

Uses the model selected by LLMSelector based on agent task complexity.
"""

import os
import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    """Base class for LLM clients."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """Call LLM and return response."""
        pass
    
    @abstractmethod
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call LLM and parse JSON response."""
        pass


class AnthropicLLMClient(LLMClientBase):
    """Client for Anthropic Claude models."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096, api_key: str = None):
        super().__init__(model, temperature, max_tokens)
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """Call Claude API and return text response.

        self.temperature is deliberately not forwarded: current Claude models
        removed the sampling parameters and the SDK rejects the keyword.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt or "You are a helpful assistant.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return next((b.text for b in response.content if b.type == "text"), "")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call Claude API and parse JSON response."""
        response_text = self.call(prompt, system_prompt)
        
        # Try to extract JSON from response
        try:
            # Try direct JSON parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # If all else fails, wrap the response
            return {"response": response_text, "error": "Could not parse as JSON"}


class OpenAILLMClient(LLMClientBase):
    """Client for OpenAI models (GPT-4, etc)."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 4096, api_key: str = None):
        super().__init__(model, temperature, max_tokens)
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """Call OpenAI API and return text response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call OpenAI API and parse JSON response."""
        response_text = self.call(prompt, system_prompt)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            return {"response": response_text, "error": "Could not parse as JSON"}


class LLMClient:
    """
    Unified LLM Client Factory
    
    Usage:
        from config.llm_selector import LLMSelector
        from config.llm_client import LLMClient
        
        # Get model config for agent
        config = LLMSelector.get_model_for_agent(2)
        
        # Create client with selected model
        llm = LLMClient(
            provider=config["provider"],
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=config["max_tokens"]
        )
        
        # Call LLM
        response = llm.call("Your prompt here")
    """
    
    def __new__(cls, provider: str = "anthropic", model: str = None, 
                temperature: float = 0.7, max_tokens: int = 4096, api_key: str = None):
        """Factory method to create appropriate LLM client."""
        
        if provider.lower() == "anthropic":
            return AnthropicLLMClient(
                model=model or "claude-3-opus",
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        elif provider.lower() == "openai":
            return OpenAILLMClient(
                model=model or "gpt-4",
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# Example usage in agents:
if __name__ == "__main__":
    from llm_selector import LLMSelector
    
    # Example: Using Agent 2 (LOW complexity - haiku)
    print("\n🤖 Example: Agent 2 (User Journey Mapping)")
    print("="*60)
    
    config = LLMSelector.get_model_for_agent(2)
    print(f"Model: {config['model']}")
    print(f"Complexity: {config['complexity']}")
    print(f"Temperature: {config['temperature']}")
    print(f"Max Tokens: {config['max_tokens']}")
    
    # Create client with selected model
    llm = LLMClient(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"]
    )
    
    print(f"\n✅ Created {config['model']} client for Agent 2")
    print(f"   (Fast & cost-effective for pattern matching)")
