
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path
from contextlib import contextmanager

# Ensure we can import orchestrator
sys.path.append(os.getcwd())

from orchestrator import root_agent

class TestRiskGatePolicy(unittest.TestCase):
    
    def setUp(self):
        # Create a temp directory for run_ledger and outputs
        self.test_dir = tempfile.mkdtemp()
        self.ledger_path = os.path.join(self.test_dir, "run_ledger.jsonl")
        self.config_path = os.path.join(self.test_dir, "run_config.json")
        self.inputs_dir = os.path.join(self.test_dir, "inputs")
        os.makedirs(self.inputs_dir)
        
        # Create dummy inputs
        with open(os.path.join(self.inputs_dir, "business_brief.md"), "w") as f:
            f.write("Brief content")
        with open(os.path.join(self.inputs_dir, "sme_notes.md"), "w") as f:
            f.write("Notes content")
        
        # Create dummy prompt file
        self.prompt_path = os.path.join(self.test_dir, "prompt.md")
        with open(self.prompt_path, "w") as f:
            f.write("Mock Prompt Content")
            
        # Base Config - Risk Enabled
        self.base_config = {
            "mode": "cli",
            "provider": "openai",
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [], # No phase gates for this test to isolate risk trigger
                "require_approval_token": "APPROVE",
                "risk_gate_escalation": {
                    "enabled": True,
                    "open_questions_threshold": 3,
                    "force_gate_on_qa_critical": True
                }
            },
            "validation": { "min_deliverable_chars": 10 },
            "agents": [
                {"name": "agent_1", "prompt_path": self.prompt_path, "gate": False}
            ]
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def write_config(self, config):
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def get_ledger_lines(self):
        if not os.path.exists(self.ledger_path):
            return []
        with open(self.ledger_path, "r") as f:
            return [json.loads(line) for line in f]

    @contextmanager
    def mock_environment(self, provider_mock, auto_approve="false"):
        """
        Sets up the environment for run_pipeline
        """
        env_vars = {
            "AUTO_APPROVE": auto_approve
        }
        
        with patch("orchestrator.root_agent.CONFIG_PATH", Path(self.config_path)), \
             patch("orchestrator.root_agent.LEDGER_PATH", self.ledger_path), \
             patch("orchestrator.root_agent.INPUTS_DIR", self.inputs_dir), \
             patch("orchestrator.root_agent.OUTPUTS_DIR", self.test_dir), \
             patch("orchestrator.root_agent.load_text", return_value="Mock Prompt"), \
             patch("orchestrator.root_agent.get_provider") as mock_get_provider, \
             patch("builtins.input", return_value="APPROVE") as mock_input, \
             patch.dict(os.environ, env_vars):
            
            mock_get_provider.return_value = provider_mock
            yield mock_input

    def test_auto_approve_risk_override_true(self):
        """
        Test A: auto_approve=True, auto_override=True (Default)
        - Trigger risk gate (high open questions)
        - Expect: NO Pause (mock_input NOT called)
        - Expect: risk_gate_forced logged
        - Expect: step_approved with specific reason
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["auto_override"] = True
        self.write_config(config)

        # Risky Response
        risky_response = json.dumps({
            "deliverable_markdown": "Risky content...",
            "updated_state": {},
            "open_questions": ["q1", "q2", "q3", "q4"] # > threshold 3
        })
        mock_provider = MagicMock()
        mock_provider.run.return_value = risky_response

        print("\n--- Test A: Auto-Approve + Auto-Override=True ---")
        with self.mock_environment(mock_provider, auto_approve="true") as mock_input:
            root_agent.run_pipeline()
            
            # Assert NO Pause
            mock_input.assert_not_called()
        
        ledger = self.get_ledger_lines()
        
        # Verify risk_gate_forced
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 1, "Should log risk_gate_forced")
        
        # Verify step_approved reason
        approvals = [e for e in ledger if e.get("event") == "step_approved"]
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["approval_reason"], "Auto-approve override after risk gate")
        
        print("\n--- EVIDENCE (Auto-Override) ---")
        print(json.dumps(risk_events[0]))
        print(json.dumps(approvals[0]))
        print("--------------------------------\n")
        
        print("✅ Test A Passed")

    def test_auto_approve_risk_override_false(self):
        """
        Test B: auto_approve=True, auto_override=False (Strict)
        - Trigger risk gate
        - Expect: PAUSE (mock_input CALLED)
        - Expect: risk_gate_forced logged
        - Expect: step_approved with mode manual/stdin
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["auto_override"] = False
        self.write_config(config)

        # Risky Response
        risky_response = json.dumps({
            "deliverable_markdown": "Risky content...",
            "updated_state": {},
            "open_questions": ["q1", "q2", "q3", "q4"]
        })
        mock_provider = MagicMock()
        mock_provider.run.return_value = risky_response

        print("\n--- Test B: Auto-Approve + Auto-Override=False ---")
        with self.mock_environment(mock_provider, auto_approve="true") as mock_input:
            root_agent.run_pipeline()
            
            # Assert Pause (Input WAS called)
            mock_input.assert_called_once()
        
        ledger = self.get_ledger_lines()
        
        # Verify risk_gate_forced
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 1)
        
        # Verify step_approved mode is manual (because it paused and took input)
        approvals = [e for e in ledger if e.get("event") == "step_approved"]
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0]["approval_mode"], "manual")
        self.assertEqual(approvals[0]["approval_source"], "stdin")
        
        print("\n--- EVIDENCE (Manual Override) ---")
        print(json.dumps(risk_events[0]))
        print(json.dumps(approvals[0]))
        print("--------------------------------\n")
        
        print("✅ Test B Passed")

if __name__ == '__main__':
    unittest.main()
