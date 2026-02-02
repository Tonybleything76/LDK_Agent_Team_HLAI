from typing import Any, Dict


class BaseProvider:
    """
    Base interface for all providers.

    Any provider must implement:
        run(prompt: str) -> str
        
    The returned string should be valid JSON matching the agent output contract.
    """

    def run(self, prompt: str) -> str:
        raise NotImplementedError("BaseProvider.run(prompt) must be implemented")