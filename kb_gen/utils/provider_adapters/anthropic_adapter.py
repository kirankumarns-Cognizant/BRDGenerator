"""
Anthropic Claude API Adapter
"""

import os
from typing import Optional

# Default model. Sonnet 5 is ~2x faster than Opus 5 at similar quality for the
# JSON-formatting workloads the BRD agents do. Callers can override per call
# via the `model` argument to `complete()`.
DEFAULT_MODEL = "claude-sonnet-5"

# Legacy inverted names → real current-generation Anthropic model IDs.
# The API uses `claude-<tier>-<gen>` (e.g. `claude-opus-5`). Old configs
# used `claude-<gen>-<tier>` (e.g. `claude-5-opus`); this map rescues them
# so a partially-updated config doesn't 404. Legacy tiers with no direct
# equivalent (Claude 3, 3.5, Claude 4-bare, Haiku 5) are mapped to the
# closest current-gen model rather than to invalid IDs.
_MODEL_ALIASES = {
    # Correct-format Claude 5
    "claude-5-opus": "claude-opus-5",
    "claude-5-sonnet": "claude-sonnet-5",
    "claude-5-haiku": "claude-haiku-4-5",     # no Haiku 5 exists; current Haiku is 4.5
    # Claude 4 family — bare "4" is not a real ID; route to the latest dot-version.
    "claude-4-opus": "claude-opus-4-8",
    "claude-4-sonnet": "claude-sonnet-4-6",
    # Legacy pre-current-gen: silently upgrade to current-gen equivalents.
    "claude-3.5-sonnet": "claude-sonnet-5",
    "claude-3.5-haiku": "claude-haiku-4-5",
    "claude-3-opus": "claude-opus-5",
    "claude-3-sonnet": "claude-sonnet-5",
    "claude-3-haiku": "claude-haiku-4-5",
}


def _resolve_model(name: Optional[str]) -> str:
    if not name:
        return DEFAULT_MODEL
    return _MODEL_ALIASES.get(name, name)


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
        temperature: float = 0.7,
        model: Optional[str] = None,
    ) -> str:
        """Generate completion with Claude.

        `temperature` is accepted so every provider adapter shares one signature,
        but it is not forwarded: current Claude models removed the sampling
        parameters, and the SDK rejects the keyword outright.

        `model` accepts either a real Anthropic model ID or a config alias
        (e.g. "claude-5-sonnet"). When omitted, DEFAULT_MODEL is used.
        """
        if not self.client:
            return ""

        resolved = _resolve_model(model)
        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.messages.create(
                model=resolved,
                max_tokens=max_tokens,
                system=system_prompt or "You are a helpful BRD analysis expert.",
                messages=messages,
            )

            return next((b.text for b in response.content if b.type == "text"), "")
        except Exception as e:
            print(f"Anthropic error ({resolved}): {e}")
            return ""
    
    def has_api(self) -> bool:
        """Check if API is available."""
        return self.client is not None
