"""
Anthropic client factory with fallback-aware initialization.
Strips credentials from error messages before logging.
"""
import os
import re
from typing import Optional


def get_anthropic_client(api_key: Optional[str] = None):
    """Return an Anthropic client, pulling key from env if not provided."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package not installed. Run: pip install anthropic>=0.40.0")

    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Add it to .env or pass api_key= explicitly."
        )
    return anthropic.Anthropic(api_key=key)


def sanitize_error(msg: str) -> str:
    """Remove API keys or tokens from error messages before logging."""
    # Strip sk-ant-... style keys
    msg = re.sub(r"sk-ant-[A-Za-z0-9\-_]+", "sk-ant-***", msg)
    # Strip Bearer tokens
    msg = re.sub(r"Bearer [A-Za-z0-9\-_.]+", "Bearer ***", msg)
    return msg
