"""
Anthropic Claude API Adapter
Supports: claude-3-opus, claude-3-sonnet, claude-3-haiku
"""

import os
from typing import Optional


class AnthropicClient:
    """Anthropic Claude API client."""
    
    def __init__(self):
        self.provider = "anthropic"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Anthropic client."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic>=0.40.0")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion with Claude."""
        if not self.client:
            return ""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self.client.messages.create(
                model="claude-3-opus-20250219",
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful BRD analysis expert.",
                messages=messages,
                temperature=temperature
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic error: {e}")
            return ""
    
    def has_api(self) -> bool:
        """Check if API is available."""
        return self.client is not None
