"""
Multi-Provider LLM Orchestrator
Supports: Anthropic, OpenAI, Gemini, GitHub Copilot, Claude Code
Fallback chain: Try all available API keys → VS Code extensions → Static Analysis
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from enum import Enum


class LLMProvider(str, Enum):
    """Available LLM providers."""
    CLAUDE_API = "claude_api"
    OPENAI = "openai"
    GEMINI = "gemini"
    GITHUB_COPILOT = "github_copilot"
    CLAUDE_CODE = "claude_code"
    STATIC = "static"


class MultiProviderLLM:
    """Smart multi-provider LLM orchestrator with automatic fallback."""
    
    # Priority chain for provider selection
    # 1. API Keys (Claude, OpenAI, Gemini) - highest priority
    # 2. GitHub Copilot Chat (VS Code extension - paid)
    # 3. Claude Code (VS Code extension - free)
    # 4. Static Analysis (fallback - no LLM)
    PROVIDER_PRIORITY = [
        LLMProvider.CLAUDE_API,      # 1st - Claude API
        LLMProvider.OPENAI,          # 1st - OpenAI API
        LLMProvider.GEMINI,          # 1st - Gemini API
        LLMProvider.GITHUB_COPILOT,  # 2nd - GitHub Copilot Chat (VS Code)
        LLMProvider.CLAUDE_CODE,     # 3rd - Claude Code (VS Code)
        LLMProvider.STATIC,          # 4th - Fallback
    ]
    
    def __init__(self):
        self.active_provider = None
        self.available_providers = {}
        self.clients = {}
        self._detect_all_providers()
        self._select_best_provider()
    
    def _detect_all_providers(self):
        """Detect which providers are available."""
        print("\n🔍 Detecting LLM providers...")
        
        # API-based providers
        self._check_anthropic()
        self._check_openai()
        self._check_gemini()
        
        # VS Code extension providers (no API key needed)
        self._check_github_copilot()
        self._check_claude_code()
        
        # Static analysis always available
        self.available_providers[LLMProvider.STATIC] = {
            "available": True,
            "name": "Static Analysis",
            "mode": "local",
            "requires_key": False
        }
    
    def _check_anthropic(self):
        """Check if Anthropic Claude API is available."""
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        available = len(key) > 0
        
        self.available_providers[LLMProvider.CLAUDE_API] = {
            "available": available,
            "name": "Claude API (Anthropic)",
            "mode": "api",
            "requires_key": True,
            "has_key": available,
            "key_env": "ANTHROPIC_API_KEY"
        }
        
        if available:
            print(f"  ✅ Claude API detected (ANTHROPIC_API_KEY set)")
        else:
            print(f"  ⚪ Claude API not available (ANTHROPIC_API_KEY not set)")
    
    def _check_openai(self):
        """Check if OpenAI API is available."""
        key = os.getenv("OPENAI_API_KEY", "").strip()
        available = len(key) > 0
        
        self.available_providers[LLMProvider.OPENAI] = {
            "available": available,
            "name": "OpenAI (GPT-4, GPT-3.5)",
            "mode": "api",
            "requires_key": True,
            "has_key": available,
            "key_env": "OPENAI_API_KEY"
        }
        
        if available:
            print(f"  ✅ OpenAI API detected (OPENAI_API_KEY set)")
        else:
            print(f"  ⚪ OpenAI API not available (OPENAI_API_KEY not set)")
    
    def _check_gemini(self):
        """Check if Google Gemini API is available."""
        key = os.getenv("GOOGLE_API_KEY", "").strip()
        available = len(key) > 0
        
        self.available_providers[LLMProvider.GEMINI] = {
            "available": available,
            "name": "Google Gemini",
            "mode": "api",
            "requires_key": True,
            "has_key": available,
            "key_env": "GOOGLE_API_KEY"
        }
        
        if available:
            print(f"  ✅ Google Gemini API detected (GOOGLE_API_KEY set)")
        else:
            print(f"  ⚪ Google Gemini API not available (GOOGLE_API_KEY not set)")
    
    def _check_github_copilot(self):
        """Check if GitHub Copilot Chat extension is installed in VS Code."""
        try:
            from pathlib import Path
            
            # Check VS Code extensions directory directly (no window opening!)
            vscode_extensions_dir = Path(os.path.expanduser("~")) / ".vscode" / "extensions"
            
            if not vscode_extensions_dir.exists():
                self.available_providers[LLMProvider.GITHUB_COPILOT] = {
                    "available": False,
                    "name": "GitHub Copilot Chat (VS Code Extension)",
                    "mode": "vscode_extension",
                    "requires_key": False,
                    "has_key": True
                }
                print(f"  ⚪ GitHub Copilot Chat not available (.vscode not found)")
                return
            
            # Look for GitHub Copilot Chat extension folder
            has_copilot_chat = False
            for ext_dir in vscode_extensions_dir.iterdir():
                if ext_dir.is_dir():
                    dir_name = ext_dir.name.lower()
                    # Check for GitHub Copilot Chat naming patterns
                    if "github" in dir_name and "copilot" in dir_name and "chat" in dir_name:
                        has_copilot_chat = True
                        break
                    elif "copilot-chat" in dir_name:
                        has_copilot_chat = True
                        break
            
            self.available_providers[LLMProvider.GITHUB_COPILOT] = {
                "available": has_copilot_chat,
                "name": "GitHub Copilot Chat (VS Code Extension)",
                "mode": "vscode_extension",
                "requires_key": False,
                "has_key": True
            }
            
            if has_copilot_chat:
                print(f"  ✅ GitHub Copilot Chat extension detected in VS Code")
            else:
                print(f"  ⚪ GitHub Copilot Chat extension not found (requires paid subscription)")
            
            return
        
        except Exception as e:
            pass
        
        # Default to unavailable
        self.available_providers[LLMProvider.GITHUB_COPILOT] = {
            "available": False,
            "name": "GitHub Copilot Chat (VS Code Extension)",
            "mode": "vscode_extension",
            "requires_key": False,
            "has_key": True
        }
        print(f"  ⚪ GitHub Copilot Chat extension not available")
    
    def _check_claude_code(self):
        """Check if Claude Code extension is active in VS Code by checking filesystem."""
        try:
            from pathlib import Path
            import os
            
            # Check VS Code extensions directory directly (no window opening!)
            vscode_extensions_dir = Path(os.path.expanduser("~")) / ".vscode" / "extensions"
            
            if not vscode_extensions_dir.exists():
                self.available_providers[LLMProvider.CLAUDE_CODE] = {
                    "available": False,
                    "name": "Claude Code (VS Code Extension)",
                    "mode": "vscode_extension",
                    "requires_key": False,
                    "has_key": True
                }
                print(f"  ⚪ Claude Code extension not available (.vscode not found)")
                return
            
            # Look for Claude Code extension folder
            has_claude_code = False
            for ext_dir in vscode_extensions_dir.iterdir():
                if ext_dir.is_dir():
                    dir_name = ext_dir.name.lower()
                    if "anthropic" in dir_name and "claude" in dir_name:
                        has_claude_code = True
                        break
                    elif "claude-code" in dir_name:
                        has_claude_code = True
                        break
            
            self.available_providers[LLMProvider.CLAUDE_CODE] = {
                "available": has_claude_code,
                "name": "Claude Code (VS Code Extension)",
                "mode": "vscode_extension",
                "requires_key": False,
                "has_key": True
            }
            
            if has_claude_code:
                print(f"  ✅ Claude Code extension detected in VS Code")
            else:
                print(f"  ⚪ Claude Code extension not found (install from VS Code extensions)")
            
            return
        
        except Exception as e:
            pass
        
        # Default to unavailable
        self.available_providers[LLMProvider.CLAUDE_CODE] = {
            "available": False,
            "name": "Claude Code (VS Code Extension)",
            "mode": "vscode_extension",
            "requires_key": False,
            "has_key": True
        }
        print(f"  ⚪ Claude Code extension not available")
    
    def _select_best_provider(self):
        """Select the best available provider based on priority."""
        for provider in self.PROVIDER_PRIORITY:
            if self.available_providers.get(provider, {}).get("available"):
                self.active_provider = provider
                info = self.available_providers[provider]
                
                if info["mode"] == "api":
                    print(f"\n🚀 Using: {info['name']}")
                else:
                    print(f"\n🚀 Using: {info['name']} (No API key required)")
                
                return
        
        # Fallback to static analysis
        self.active_provider = LLMProvider.STATIC
        print(f"\n⚠️  Fallback to: Static Analysis (Code pattern detection)")
    
    def get_client(self):
        """Get initialized client for active provider."""
        if self.active_provider in self.clients:
            return self.clients[self.active_provider]
        
        client = None
        
        if self.active_provider == LLMProvider.CLAUDE_API:
            from .provider_adapters.anthropic_adapter import AnthropicClient
            client = AnthropicClient()
        
        elif self.active_provider == LLMProvider.OPENAI:
            from .provider_adapters.openai_adapter import OpenAIClient
            client = OpenAIClient()
        
        elif self.active_provider == LLMProvider.GEMINI:
            from .provider_adapters.gemini_adapter import GeminiClient
            client = GeminiClient()
        
        elif self.active_provider == LLMProvider.GITHUB_COPILOT:
            from .provider_adapters.github_copilot_adapter import GitHubCopilotClient
            client = GitHubCopilotClient()
        
        elif self.active_provider == LLMProvider.CLAUDE_CODE:
            from .provider_adapters.claude_code_adapter import ClaudeCodeClient
            client = ClaudeCodeClient()
        
        if client:
            self.clients[self.active_provider] = client
        
        return client
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> str:
        """Generate completion using active provider.

        `model` is forwarded to adapters that support per-call model
        selection (currently the Anthropic adapter). Non-supporting
        adapters ignore it silently."""
        client = self.get_client()

        if client is None:
            return ""

        try:
            # Try passing model first; fall back to signature without model
            # for adapters that don't accept it yet.
            try:
                return client.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model,
                )
            except TypeError:
                return client.complete(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
        except Exception as e:
            print(f"⚠️  Provider error: {e}")
            return ""
    
    def generate_json_output(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate JSON output from provider."""
        client = self.get_client()
        
        if client is None:
            return {}
        
        try:
            response = client.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=4096
            )
            
            # Extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError, Exception):
            return {}
    
    def has_api(self) -> bool:
        """Check if active provider has API/connection."""
        return self.active_provider != LLMProvider.STATIC
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about active provider."""
        provider = self.available_providers.get(self.active_provider, {})
        return {
            "name": provider.get("name", "Unknown"),
            "provider": self.active_provider.value if self.active_provider else "none",
            "mode": provider.get("mode", "unknown"),
            "requires_api_key": provider.get("requires_key", False),
            "available": provider.get("available", False)
        }
    
    def list_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """List all available providers."""
        return self.available_providers
    
    def switch_provider(self, provider: LLMProvider) -> bool:
        """Manually switch to a different provider."""
        if self.available_providers.get(provider, {}).get("available"):
            self.active_provider = provider
            print(f"✅ Switched to: {self.available_providers[provider]['name']}")
            return True
        else:
            print(f"❌ Provider not available: {provider.value}")
            return False


# Global instance
_llm = None


def get_multi_provider_llm() -> MultiProviderLLM:
    """Get or create global LLM instance."""
    global _llm
    if _llm is None:
        _llm = MultiProviderLLM()
    return _llm


def get_active_provider() -> str:
    """Get active provider name."""
    llm = get_multi_provider_llm()
    info = llm.get_provider_info()
    return info["name"]


def get_llm_client():
    """Get active LLM client."""
    llm = get_multi_provider_llm()
    return llm.get_client()
