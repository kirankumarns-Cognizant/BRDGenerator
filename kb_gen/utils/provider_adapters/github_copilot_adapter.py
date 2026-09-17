"""
GitHub Copilot Chat Extension Adapter
Detects GitHub Copilot Chat (paid subscription) VS Code extension
No CLI required - works via VS Code extension
"""

import os
from pathlib import Path
from typing import Optional


class GitHubCopilotClient:
    """GitHub Copilot Chat extension client (VS Code)."""
    
    def __init__(self):
        self.provider = "github_copilot_chat"
        self.available = self._check_availability()
        self.extension_name = None
    
    def _check_availability(self) -> bool:
        """Check if GitHub Copilot Chat extension is installed in VS Code."""
        try:
            # Check VS Code extensions directory directly (no window opening!)
            vscode_extensions_dir = Path(os.path.expanduser("~")) / ".vscode" / "extensions"
            
            if not vscode_extensions_dir.exists():
                return False
            
            # Look for GitHub Copilot Chat extension folder
            for ext_dir in vscode_extensions_dir.iterdir():
                if ext_dir.is_dir():
                    dir_name = ext_dir.name.lower()
                    # Check for different GitHub Copilot Chat naming patterns
                    if "github" in dir_name and "copilot" in dir_name and "chat" in dir_name:
                        self.extension_name = "github.copilot-chat"
                        return True
                    elif "copilot-chat" in dir_name:
                        self.extension_name = "github.copilot-chat"
                        return True
            
            return False
        
        except Exception as e:
            return False
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Get completion from GitHub Copilot Chat extension."""
        if not self.available:
            return ""
        
        try:
            # GitHub Copilot Chat is primarily interactive in VS Code
            # For automated use, we would need VS Code Server or Extension API
            # For now, return empty as it requires VS Code interactivity
            # In production, this could integrate with VS Code's Extension API
            return ""
        
        except Exception as e:
            print(f"GitHub Copilot Chat error: {e}")
            return ""
    
    def has_api(self) -> bool:
        """Check if GitHub Copilot Chat extension is available."""
        return self.available
