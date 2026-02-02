import os
import json
import urllib.request
from typing import Any, Dict
from .base import BaseProvider


class PerplexityProvider(BaseProvider):
    """
    Perplexity API provider using Chat Completions endpoint.
    
    Requires:
        - PERPLEXITY_API_KEY environment variable
        - Optional: PERPLEXITY_MODEL (default: sonar)
    """
    
    def __init__(self):
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "PERPLEXITY_API_KEY environment variable is required for Perplexity provider. "
                "Set it before running: export PERPLEXITY_API_KEY='your-key-here'"
            )
        
        self.model = os.environ.get("PERPLEXITY_MODEL", "sonar").strip()
        self.api_url = "https://api.perplexity.ai/chat/completions"
    
    def run(self, prompt: str) -> str:
        """
        Execute prompt using Perplexity Chat Completions API.
        
        Args:
            prompt: Full prompt text to send to the model
            
        Returns:
            Raw text response from the model (should be valid JSON per agent contract)
            
        Raises:
            Exception: If API call fails or returns error
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                
                if "choices" not in response_data or len(response_data["choices"]) == 0:
                    raise ValueError(f"Unexpected Perplexity API response format: {response_data}")
                
                content = response_data["choices"][0]["message"]["content"]
                return content.strip()
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(
                f"Perplexity API request failed with status {e.code}: {error_body}"
            )
        except Exception as e:
            raise Exception(f"Perplexity API request failed: {str(e)}")
