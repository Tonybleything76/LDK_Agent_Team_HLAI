import os
import json
import urllib.request
from typing import Any, Dict
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider using Chat Completions endpoint.
    
    Requires:
        - OPENAI_API_KEY environment variable
        - Optional: OPENAI_MODEL (default: gpt-4o-mini)
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider. "
                "Set it before running: export OPENAI_API_KEY='your-key-here'"
            )
        
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def run(self, prompt: str) -> str:
        """
        Execute prompt using OpenAI Chat Completions API.
        
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
            ],
            "temperature": 0.7
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
                    raise ValueError(f"Unexpected OpenAI API response format: {response_data}")
                
                content = response_data["choices"][0]["message"]["content"]
                return content.strip()
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(
                f"OpenAI API request failed with status {e.code}: {error_body}"
            )
        except Exception as e:
            raise Exception(f"OpenAI API request failed: {str(e)}")
