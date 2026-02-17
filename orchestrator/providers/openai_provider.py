import os
import json
import urllib.request
import urllib.error
from typing import Any, Dict
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI API provider using Chat Completions endpoint.
    
    Requires:
        - OPENAI_API_KEY environment variable
        - Optional: OPENAI_MODEL (default: gpt-4o-mini)
        - Optional: OPENAI_TEMPERATURE (default: 0.2)
    """
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for OpenAI provider. "
                "Set it before running: export OPENAI_API_KEY='your-key-here'"
            )
        
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
        
        # Parse temperature (default 0.2 for deterministic JSON)
        try:
            self.temperature = float(os.environ.get("OPENAI_TEMPERATURE", "0.2"))
        except ValueError:
            self.temperature = 0.2

        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def run(self, prompt: str) -> str:
        """
        Execute prompt using OpenAI Chat Completions API.
        Enforces JSON mode if supported, with fallback.
        
        Args:
            prompt: Full prompt text to send to the model
            
        Returns:
            Raw text response from the model (should be valid JSON per agent contract)
            
        Raises:
            Exception: If API call fails or returns error
        """
        # Strong system instruction for JSON enforcement
        system_message = {
            "role": "system", 
            "content": "Return ONLY valid JSON that matches the requested schema. No markdown. No prose."
        }
        
        payload = {
            "model": self.model,
            "messages": [
                system_message,
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }
        
        try:
            return self._execute_request(payload)
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            
            # Check if error is related to response_format (e.g. model doesn't support it)
            if e.code == 400 and ("response_format" in error_body or "type" in error_body):
                # Fallback: Retry without response_format but with stronger prompt
                print(f"Warning: Model {self.model} rejected JSON mode. Retrying with strong system prompt.")
                
                # Remove response_format
                retry_payload = payload.copy()
                retry_payload.pop("response_format", None)
                
                # Strengthen system message
                new_messages = [m.copy() for m in retry_payload["messages"]]
                for m in new_messages:
                    if m["role"] == "system":
                        m["content"] += " JSON ONLY."
                retry_payload["messages"] = new_messages
                
                try:
                    return self._execute_request(retry_payload)
                    
                except urllib.error.HTTPError as retry_e:
                    retry_error_body = retry_e.read().decode("utf-8")
                    raise Exception(
                        f"OpenAI API retry failed with status {retry_e.code}: {retry_error_body}"
                    )
            else:
                # Re-raise other HTTP errors with body
                raise Exception(
                    f"OpenAI API request failed with status {e.code}: {error_body}"
                )
                
        except Exception as e:
            raise Exception(f"OpenAI API request failed: {str(e)}")

    def _execute_request(self, payload: Dict[str, Any]) -> str:
        """Helper to execute the actual HTTP request"""
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
        
        with urllib.request.urlopen(request, timeout=120) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            
            if "choices" not in response_data or len(response_data["choices"]) == 0:
                raise ValueError(f"Unexpected OpenAI API response format: {response_data}")
            
            content = response_data["choices"][0]["message"]["content"]
            
            # ------------------------------------------------------------------
            # JSON Integrity Check & Auto-Repair
            # ------------------------------------------------------------------
            try:
                # Try to parse to verify it is valid JSON
                json.loads(content)
                return content.strip()
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON Parse Error in OpenAI response. Attempting repair...")
                
                # RECURSION GUARD: Check if we are already in a retry loop
                # If the last message was our repair prompt, do not retry again
                if len(payload.get("messages", [])) > 0:
                     last_msg = payload["messages"][-1]
                     if last_msg.get("role") == "user" and "Previous response object failed to parse" in last_msg.get("content", ""):
                         print("⚠️  JSON repair failed (recursion detected). Aborting.")
                         raise e

                # Construct repair payload
                # We simply append a user message asking to fix it
                repair_payload = payload.copy()
                new_messages = [m.copy() for m in repair_payload["messages"]]
                
                # Append the failure context
                new_messages.append({
                    "role": "user",
                    "content": (
                        f"Previous response object failed to parse as JSON: {str(e)}\n\n"
                        f"Here is your JSON:\n{content}\n\n"
                        f"Please FIX this and return ONLY valid JSON."
                    )
                })
                
                repair_payload["messages"] = new_messages
                
                # We can keep response_format={"type": "json_object"} if model supports it
                # or rely on the prompt. Let's keep it if original had it.
                
                try:
                    return self._execute_request(repair_payload)
                except Exception as repair_error:
                     # If repair fails (HTTP or otherwise), we raise the ORIGINAL parse error 
                     # or the new error? 
                     # If we return the raw string here, the Agent validation will fail later 
                     # and dump the error file, which is robust.
                     # BUT the requirement says "returns ONLY corrected JSON".
                     # If we fail here, we should probably let the downstream validator handle it.
                     # However, to satisfy the test "verify retry success", we must return new content.
                     raise repair_error

