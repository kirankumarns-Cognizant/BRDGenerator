"""
OpenAI API Adapter
Supports: GPT-4, GPT-3.5-turbo
"""

import os
from typing import Optional


class OpenAIClient:
    """OpenAI API client."""
    
    def __init__(self):
        self.provider = "openai"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai>=1.0.0")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion with GPT."""
        if not self.client:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt or "You are a helpful BRD analysis expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI error: {e}")
            # Fallback to gpt-3.5-turbo if gpt-4 not available
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful BRD analysis expert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e2:
                print(f"OpenAI fallback error: {e2}")
                return ""
    
    def has_api(self) -> bool:
        """Check if API is available."""
        return self.client is not None
