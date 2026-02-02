import json
from pathlib import Path
from typing import Any, Dict

from orchestrator.providers.base import BaseProvider

class ManualProvider(BaseProvider):
    def __init__(self, tmp_json_path: Path):
        self.tmp_json_path = tmp_json_path

    def run(self, full_prompt: str) -> Dict[str, Any]:
        print("\n" + "="*80)
        print("MANUAL AGENT STEP")
        print("="*80)
        print(f"Please copy the prompt below and paste it into your LLM web UI.\n")
        print(full_prompt)
        print("\n" + "="*80)
        print(f"Once you have the JSON response, save it to:\n{self.tmp_json_path}")
        print("Ensure the file contains ONLY valid JSON.")
        
        while True:
            resp = input(f"\nPress ENTER when {self.tmp_json_path.name} is ready (or type 'skip' to abort): ").strip()
            if resp.lower() == "skip":
                raise KeyboardInterrupt("Skipped by user.")
            
            if not self.tmp_json_path.exists():
                print(f"File not found: {self.tmp_json_path}")
                continue
                
            try:
                text = self.tmp_json_path.read_text(encoding="utf-8")
                # Attempt to parse
                data = json.loads(text)
                return data
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in {self.tmp_json_path}: {e}")
                print("Please fix the file and try again.")
            except Exception as e:
                print(f"Error reading file: {e}")
