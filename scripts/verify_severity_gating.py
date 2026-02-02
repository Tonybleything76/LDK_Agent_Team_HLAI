
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
from orchestrator.audit import generate_audit_summary

class TestSeverityGating(unittest.TestCase):
    
    def setUp(self):
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
            
        # Base Config
        self.base_config = {
            "mode": "cli",
            "provider": "openai",
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [],
                "require_approval_token": "APPROVE",
                "risk_gate_escalation": {
                    "enabled": True,
                    "open_questions_threshold": 1, 
                    "force_gate_on_qa_critical": False
                }
            },
            "validation": { "min_deliverable_chars": 10 },
            "agents": [
                {"name": "agent_1", "prompt_path": self.prompt_path, "gate": False},
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
    def mock_environment(self, provider_mock):
        with patch("orchestrator.root_agent.CONFIG_PATH", Path(self.config_path)), \
             patch("orchestrator.root_agent.LEDGER_PATH", self.ledger_path), \
             patch("orchestrator.root_agent.INPUTS_DIR", self.inputs_dir), \
             patch("orchestrator.root_agent.OUTPUTS_DIR", self.test_dir), \
             patch("orchestrator.root_agent.load_text", return_value="Mock Prompt"), \
             patch("orchestrator.root_agent.get_provider", return_value=provider_mock), \
             patch("builtins.input", return_value="APPROVE"):
            yield

    def test_audit_summary_severity_counts(self):
        """Verify audit summary accurately counts severities."""
        # Create dummy run dir
        run_id = "test_run_audit"
        run_dir = os.path.join(self.test_dir, run_id)
        os.makedirs(run_dir)
        
        # Dummy manifest
        with open(os.path.join(run_dir, "run_manifest.json"), "w") as f:
            json.dump({"run_id": run_id, "auto_approve": False}, f)
        
        # Create state file with mixed severities
        state_data = {
            "open_questions": [
                "CRITICAL: Critical issue",
                "BLOCKER: Blocker issue",
                "MAJOR: Major issue",
                "MINOR: Minor issue 1",
                "MINOR: Minor issue 2",
                "Unprefixed issue"
            ]
        }
        with open(os.path.join(run_dir, "01_agent_state.json"), "w") as f:
            json.dump(state_data, f)
            
        # Run Audit Generation
        summary_path = generate_audit_summary(run_id, run_dir, ledger_path=self.ledger_path)
        
        with open(summary_path, "r") as f:
            summary = json.load(f)
            
        counts = summary["open_questions_summary"]["severity_counts"]
        print(f"\nAudit Counts: {counts}")
        
        self.assertEqual(counts["critical"], 1)
        self.assertEqual(counts["blocker"], 1)
        self.assertEqual(counts["major"], 1)
        self.assertEqual(counts["minor"], 2)
        self.assertEqual(counts["unprefixed"], 1)
        self.assertEqual(summary["open_questions_summary"]["total_count"], 6)

    def test_weighted_gating_dev_profile(self):
        """Dev profile validation: MAJOR should trigger gate."""
        # Config: Dev profile uses ["CRITICAL", "BLOCKER", "MAJOR", "UNPREFIXED"]
        # Threshold: 1
        
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["weighted_severities"] = ["CRITICAL", "BLOCKER", "MAJOR", "UNPREFIXED"]
        self.write_config(config)
        
        # Mock Provider returns MAJOR issue
        mock_provider = MagicMock()
        mock_provider.run.return_value = json.dumps({
            "deliverable_markdown": "Deliverable",
            "updated_state": {},
            "open_questions": ["MAJOR: Big problem"]
        })
        
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()
            
        ledger = self.get_ledger_lines()
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 1, "Dev profile should gate on MAJOR")
        self.assertEqual(risk_events[0]["observed_open_questions_count_weighted"], 1)

    def test_weighted_gating_prod_profile(self):
        """Prod profile validation: MAJOR should NOT trigger gate."""
        # Config: Prod profile uses ["CRITICAL", "BLOCKER"]
        # Threshold: 1
        
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["weighted_severities"] = ["CRITICAL", "BLOCKER"]
        self.write_config(config)
        
        # Mock Provider returns MAJOR issue
        mock_provider = MagicMock()
        mock_provider.run.return_value = json.dumps({
            "deliverable_markdown": "Deliverable",
            "updated_state": {},
            "open_questions": ["MAJOR: Big problem"]
        })
        
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()
            
        ledger = self.get_ledger_lines()
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 0, "Prod profile should NOT gate on MAJOR")

    def test_weighted_gating_prod_profile_critical(self):
        """Prod profile validation: CRITICAL should trigger gate."""
        
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["weighted_severities"] = ["CRITICAL", "BLOCKER"]
        self.write_config(config)
        
        # Mock Provider returns CRITICAL issue
        mock_provider = MagicMock()
        mock_provider.run.return_value = json.dumps({
            "deliverable_markdown": "Deliverable",
            "updated_state": {},
            "open_questions": ["CRITICAL: Huge problem"]
        })
        
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()
            
        ledger = self.get_ledger_lines()
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 1, "Prod profile SHOULD gate on CRITICAL")

if __name__ == '__main__':
    unittest.main()
