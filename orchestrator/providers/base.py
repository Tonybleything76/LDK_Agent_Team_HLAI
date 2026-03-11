from abc import ABC, abstractmethod
from typing import Any, Dict, Union


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Each provider must implement ``run(prompt)`` which sends a prompt to a
    language model and returns the response.  The response may be:

    - A raw string (raw text / JSON text from the API)
    - A pre-parsed dict (e.g. ``ClaudeCliProvider`` unwraps the CLI wrapper)

    Callers in ``root_agent.run_pipeline`` handle both forms via an
    ``isinstance(response, dict)`` guard before passing to ``parse_json_object``.
    """

    @abstractmethod
    def run(self, prompt: str) -> Union[Dict[str, Any], str]:
        """
        Send ``prompt`` to the model and return its response.

        Args:
            prompt: The full rendered prompt string.

        Returns:
            Either a pre-parsed dict (if the provider handles JSON decoding
            internally) or a raw response string for the caller to parse.

        Raises:
            RuntimeError: If the underlying API/CLI call fails.
        """
