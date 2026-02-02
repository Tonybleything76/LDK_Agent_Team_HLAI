import json
import re
import subprocess
from typing import Any, Dict, List

from orchestrator.providers.base import BaseProvider


class ClaudeCliProvider(BaseProvider):
    """
    Runs Claude Code CLI in non-interactive mode.

    Key detail:
    - Claude Code defaults to an interactive TUI, which can hang with pipes.
    - Using `-p/--print` makes it non-interactive and suitable for automation.
    - `--output-format json` improves parse reliability.

    Command used:
      claude -p --output-format json
    """

    def __init__(self, command: str = "claude", timeout_seconds: int = 900):
        self.command = command
        self.timeout_seconds = timeout_seconds

    def _build_cmd(self) -> List[str]:
        return [self.command, "-p", "--output-format", "json"]

    def _run_subprocess(self, prompt: str) -> str:
        cmd = self._build_cmd()


        # Reinforce JSON-only output to reduce risk of extra text.
        wrapped_prompt = (
            "Please provide a response in valid JSON format. \n"
            "Do not include any other text or markdown formatting.\n\n"
            + prompt
        )

        proc = subprocess.run(
            cmd,
            input=wrapped_prompt,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
        )

        if proc.returncode != 0:
            raise RuntimeError(
                "Claude CLI failed.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Exit code: {proc.returncode}\n"
                f"STDERR:\n{proc.stderr}\n"
                f"STDOUT:\n{proc.stdout}\n"
            )

        return proc.stdout

    def _extract_json_object(self, text: str) -> Dict[str, Any]:
        """
        With --output-format json, we expect JSON, but we still keep
        a fallback extraction in case extra wrapper text appears.
        """
        t = (text or "").strip()

        # 0) Unwrap CLI response if present
        # The Claude CLI with --output-format json returns a wrapper dict:
        # { "type": "result", "result": "...", ... }
        try:
            wrapper = json.loads(t)
            if isinstance(wrapper, dict) and "result" in wrapper:
                # If this looks like the CLI wrapper, extract the inner content
                # Note: valid_json_response will also satisfy this check if it has "result"
                # But typically the CLI wrapper has "type": "result" etc.
                if wrapper.get("type") == "result" or "usage" in wrapper:
                    t = wrapper["result"]
        except Exception:
            # If not valid JSON, it's definitely not the wrapper, proceed with raw text
            pass

        t = (t or "").strip()

        # 1) Try parse whole content as JSON
        try:
            obj = json.loads(t)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # 2) Fallback: find first JSON object inside text
        candidates = re.findall(r"\{.*\}", t, flags=re.DOTALL)
        for c in candidates:
            c = c.strip()
            try:
                obj = json.loads(c)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue

        snippet = t[:1200]
        raise ValueError(
            "Could not extract a valid JSON object from Claude output.\n"
            "First 1200 chars of result content:\n"
            f"{snippet}"
        )

    def run(self, prompt: str) -> Dict[str, Any]:
        stdout = self._run_subprocess(prompt)
        return self._extract_json_object(stdout)