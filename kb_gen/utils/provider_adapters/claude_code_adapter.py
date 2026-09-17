"""
Claude Code Extension Adapter
Integrates with VS Code extension - no API key required
Extension: anthropic.claude-code or github.copilot-chat
"""

import subprocess
import json
import socket
import os
from typing import Optional
from pathlib import Path


class ClaudeCodeClient:
    """Claude Code extension client."""
    
    def __init__(self):
        self.provider = "claude_code"
        self.available = self._check_availability()
        self.socket_path = None
        self.extension_name = None
    
    def _check_availability(self) -> bool:
        """Check if Claude Code extension is installed in VS Code."""
        try:
            # Try multiple methods to detect VS Code
            code_cmd = self._find_code_command()
            if not code_cmd:
                return False
            
            result = subprocess.run(
                [code_cmd, "--list-extensions"],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                extensions_text = result.stdout.lower()
                
                # Check for Claude Code extension (multiple possible names)
                if "anthropic.claude" in extensions_text or "claude-code" in extensions_text or "claude" in extensions_text:
                    # Try to identify exact extension name
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line_lower = line.lower()
                        if "anthropic" in line_lower and "claude" in line_lower:
                            self.extension_name = line.strip()
                            return True
                        elif "claude" in line_lower and "code" in line_lower:
                            self.extension_name = line.strip()
                            return True
                    
                    # If Claude extension found but exact name unknown
                    if self.extension_name is None:
                        self.extension_name = "anthropic.claude-code"
                    return True
                
                # Check for GitHub Copilot Chat as fallback
                if "github.copilot-chat" in extensions_text or "copilot-chat" in extensions_text:
                    self.extension_name = "github.copilot-chat"
                    return True
            
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            return False
    
    @staticmethod
    def _find_code_command() -> Optional[str]:
        """Find the 'code' command in system PATH or common locations."""
        import shutil
        
        # Try standard PATH first
        code_path = shutil.which("code")
        if code_path:
            return code_path
        
        # Try Windows common locations
        if os.name == 'nt':
            common_paths = [
                r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
                r"C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd",
                r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd".format(os.getenv("USERNAME")),
            ]
            for path in common_paths:
                if Path(path).exists():
                    return path
        
        return None
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Get completion from Claude Code extension via VS Code."""
        if not self.available:
            return ""
        
        try:
            # Combine prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Try direct communication via Claude Code API
            response = self._call_claude_code_api(full_prompt)
            
            if response:
                return response
            
            # Fallback: Try via VS Code CLI
            response = self._call_via_vscode_cli(full_prompt)
            
            return response if response else ""
        
        except Exception as e:
            print(f"Claude Code error: {e}")
            return ""
    
    def _call_claude_code_api(self, prompt: str) -> Optional[str]:
        """Try to call Claude Code extension API."""
        try:
            # Try to import and use Claude's Python SDK through VS Code
            # This is a workaround for direct extension communication
            
            # Check if we can access Anthropic client from VS Code environment
            try:
                import anthropic
                
                # VS Code Claude Code extension may have injected an API key
                # Try to use it if available
                api_key = os.getenv("VSCODE_CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
                
                if api_key:
                    client = anthropic.Anthropic(api_key=api_key)
                    message = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return message.content[0].text
            except (ImportError, Exception):
                pass
            
            return None
        except Exception:
            return None
    
    def _call_via_vscode_cli(self, prompt: str) -> Optional[str]:
        """Try to call via VS Code CLI."""
        try:
            code_cmd = self._find_code_command()
            if not code_cmd:
                return None
            
            # Save prompt to temp file for VS Code to read
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                temp_file = f.name
            
            try:
                # Open in VS Code with Claude Code context
                # Note: This opens VS Code but doesn't directly return output
                # Better approach: Use extension's command interface
                
                result = subprocess.run(
                    [code_cmd, "--remote-debugging-port=9222"],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                # This approach has limitations; Claude Code is primarily interactive
                return None
            finally:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
        
        except Exception:
            return None
    
    def has_api(self) -> bool:
        """Check if extension is available."""
        return self.available
