"""
Google Gemini API Adapter
Supports: gemini-pro, gemini-pro-vision
"""

import os
from typing import Optional


class GeminiClient:
    """Google Gemini API client."""
    
    def __init__(self):
        self.provider = "google"
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Gemini client."""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-pro')
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion with Gemini."""
        if not self.client:
            return ""
        
        try:
            # Combine system prompt with user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return ""
    
    def has_api(self) -> bool:
        """Check if API is available."""
        return self.client is not None
