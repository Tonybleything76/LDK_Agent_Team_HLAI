import os
from .base import BaseProvider
from .manual_provider import ManualProvider
from .claude_cli_provider import ClaudeCliProvider
from .openai_provider import OpenAIProvider
from .perplexity_provider import PerplexityProvider
from .dry_run_provider import DryRunProvider

__all__ = [
    "BaseProvider", 
    "ManualProvider", 
    "ClaudeCliProvider", 
    "OpenAIProvider",
    "PerplexityProvider",
    "DryRunProvider",
    "get_provider"
]


def get_provider(provider_name: str = None) -> BaseProvider:
    """
    Factory function to create provider instances.
    
    Args:
        provider_name: Name of provider to create. If None, reads from PROVIDER env var.
                      Supported values: 'manual', 'claude_cli', 'openai', 'openai_api', 
                                       'perplexity', 'dry_run'
    
    Returns:
        BaseProvider instance
    
    Raises:
        ValueError: If provider_name is unsupported or not specified
    """
    if provider_name is None:
        provider_name = os.environ.get("PROVIDER", "").strip().lower()
    
    provider_name = provider_name.strip().lower()
    
    if provider_name == "manual":
        return ManualProvider()
    elif provider_name in ("claude_cli", "claude"):
        return ClaudeCliProvider()
    elif provider_name in ("openai", "openai_api"):
        return OpenAIProvider()
    elif provider_name == "perplexity":
        return PerplexityProvider()
    elif provider_name == "dry_run":
        return DryRunProvider()
    else:
        raise ValueError(
            f"Unknown provider: '{provider_name}'. "
            f"Supported providers: 'manual', 'claude_cli', 'openai', 'perplexity', 'dry_run'. "
            f"Set PROVIDER environment variable or pass provider_name parameter."
        )
