
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

class TestRiskGateEscalation(unittest.TestCase):
    
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
            
        # Base Config
        self.base_config = {
            "mode": "cli",
            "provider": "openai",
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [3, 6, 9],
                "require_approval_token": "APPROVE",
                "risk_gate_escalation": {
                    "enabled": False,
                    "open_questions_threshold": 3,
                    "force_gate_on_qa_critical": True
                }
            },
            "validation": { "min_deliverable_chars": 10 },
            "agents": [
                {"name": "agent_1", "prompt_path": self.prompt_path, "gate": False},
                {"name": "agent_2", "prompt_path": self.prompt_path, "gate": False},
                {"name": "qa_agent", "prompt_path": self.prompt_path, "gate": False}
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
        """
        Sets up the environment for run_pipeline:
        - Patches CONFIG_PATH, LEDGER_PATH, INPUTS_DIR
        - Patches load_text to return valid prompt
        - Patches get_provider to return the mock
        - Patches input() to simulate user approval
        """
        with patch("orchestrator.root_agent.CONFIG_PATH", Path(self.config_path)), \
             patch("orchestrator.root_agent.LEDGER_PATH", self.ledger_path), \
             patch("orchestrator.root_agent.INPUTS_DIR", self.inputs_dir), \
             patch("orchestrator.root_agent.OUTPUTS_DIR", self.test_dir), \
             patch("orchestrator.root_agent.load_text", return_value="Mock Prompt"), \
             patch("orchestrator.root_agent.get_provider") as mock_get_provider, \
             patch("builtins.input", return_value="APPROVE"):
            
            mock_get_provider.return_value = provider_mock
            yield

    def test_a_baseline_disabled(self):
        """
        Scenario A: Baseline (escalation disabled or enabled=false)
        Confirm only phase gates occur (step 3). No risk_gate_forced events.
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["enabled"] = False
        self.write_config(config)

        # Mock Provider: Safe responses
        safe_response = json.dumps({
            "deliverable_markdown": "Safe content...",
            "updated_state": {},
            "open_questions": []
        })
        mock_provider = MagicMock()
        mock_provider.run.return_value = safe_response

        print("\n--- Test A: Baseline (Disabled) ---")
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()

        ledger = self.get_ledger_lines()
        
        # Verify NO risk_gate_forced
        risk_events = [e for e in ledger if e["event"] == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 0, "Should have NO risk_gate_forced events")

        # Verify phase gate at step 3 (agent: qa_agent in our config is index 2, wait agent list is 1-indexed)
        # Agents: 1=agent_1, 2=agent_2, 3=qa_agent.
        # Phase gates: [3, 6, 9]. Step 3 should validly gate.
        approvals = [e for e in ledger if e["event"] == "step_approved"]
        self.assertTrue(any(e["step_idx"] == 3 for e in approvals), "Should approve step 3 phase gate")

        print("✅ Baseline Test Passed")

    def test_b_threshold_test(self):
        """
        Scenario B: Threshold-trigger test
        enabled=true, threshold=3 (set in setUp)
        Step 1 produces 4 open questions.
        Expect: risk_gate_forced at step 1.
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["enabled"] = True
        self.write_config(config)

        # Mock Provider
        # Step 1: 5 questions (Trigger)
        # Step 2: 0 questions
        # Step 3: 0 questions
        bad_response = json.dumps({
            "deliverable_markdown": "Risky content...",
            "updated_state": {},
            "open_questions": ["q1", "q2", "q3", "q4", "q5"]
        })
        safe_response = json.dumps({
            "deliverable_markdown": "Safe content...",
            "updated_state": {},
            "open_questions": []
        })
        
        mock_provider = MagicMock()
        mock_provider.run.side_effect = [bad_response, safe_response, safe_response]

        print("\n--- Test B: Threshold Trigger ---")
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()

        ledger = self.get_ledger_lines()
        
        # Verify risk_gate_forced at step 1
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        self.assertEqual(len(risk_events), 1, "Should have 1 risk_gate_forced event")
        event = risk_events[0]
        self.assertEqual(event["step_idx"], 1)
        self.assertEqual(event["gate_reason"], "open_questions_threshold")
        self.assertEqual(event["observed_open_questions_count"], 5)
        
        # Verify CLI output simulation (log snippet)
        print(f"Captured Risk Event: {json.dumps(event)}")

        # Verify Audit Summary
        audit_file = os.path.join(self.test_dir, f"audit_summary.json")
        # In current logic, run_dir is test_dir/outputs/run_id usually...
        # Wait, run_pipeline creates run_id dir inside OUTPUTS_DIR.
        # OUTPUTS_DIR is patched to self.test_dir.
        # So we need to find the run dir inside self.test_dir.
        subdirs = [d for d in os.listdir(self.test_dir) if os.path.isdir(os.path.join(self.test_dir, d)) and d != "inputs"]
        self.assertTrue(len(subdirs) > 0, "Should have created a run directory")
        run_dir = os.path.join(self.test_dir, subdirs[0])
        audit_path = os.path.join(run_dir, "audit_summary.json")
        
        self.assertTrue(os.path.exists(audit_path), "Audit summary should exist")
        with open(audit_path, "r") as f:
            audit = json.load(f)
            
        print(f"Captured Audit Summary Keys: {list(audit.keys())}")
        self.assertIn("gate_summary", audit)
        self.assertIn("risk_gates", audit["gate_summary"])
        self.assertTrue(len(audit["gate_summary"]["risk_gates"]) > 0, "Audit should record risk gates")
        self.assertEqual(audit["end_state"], "run_completed")

        print("✅ Threshold Test Passed")

    def test_c_qa_critical_test(self):
        """
        Scenario C: QA critical-trigger test
        enabled=true, force_gate_on_qa_critical=true
        QA Agent (Step 3) produces critical_errors.
        Expect: risk_gate_forced at step 3.
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["enabled"] = True
        self.write_config(config)

        # Mock Provider
        # Step 1: Safe
        # Step 2: Safe
        # Step 3: QA Critical
        safe_response = json.dumps({
            "deliverable_markdown": "Safe content...",
            "updated_state": {},
            "open_questions": []
        })
        qa_critical_response = json.dumps({
            "deliverable_markdown": "QA Report...",
            "updated_state": {
                "qa": {
                    "suggestions": []
                }
            },
            "open_questions": ["CRITICAL: MAJOR BUG FOUND"]
        })

        mock_provider = MagicMock()
        mock_provider.run.side_effect = [safe_response, safe_response, qa_critical_response]

        print("\n--- Test C: QA Critical Trigger ---")
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline()

        ledger = self.get_ledger_lines()
        
        # Verify risk_gate_forced at step 3
        risk_events = [e for e in ledger if e.get("event") == "risk_gate_forced"]
        # Step 3 is also a Phase Gate (3). 
        # Logic: if should_gate is True, it calls `approval_gate`.
        # If BOTH triggers apply (phase gate AND risk), `should_gate` is True.
        # But `gate_type` and `gate_reason` are variables.
        # In my logic:
        # `gate_type` starts as "phase_gate".
        # If risk trigger 1: matches, `gate_type` becomes "risk_gate".
        # If risk trigger 2: matches, `gate_type` becomes "risk_gate".
        # So "risk_gate" overrides "phase_gate" label if triggered.
        
        self.assertEqual(len(risk_events), 1, "Should have 1 risk_gate_forced event")
        event = risk_events[0]
        self.assertEqual(event["step_idx"], 3)
        self.assertEqual(event["gate_reason"], "qa_critical")
        self.assertEqual(event["qa_critical_error_count"], 1)
        
        print(f"Captured Risk Event: {json.dumps(event)}")

        # Verify Audit Summary
        subdirs = [d for d in os.listdir(self.test_dir) if os.path.isdir(os.path.join(self.test_dir, d)) and d != "inputs"]
        run_dir = os.path.join(self.test_dir, subdirs[0])
        audit_path = os.path.join(run_dir, "audit_summary.json")
        
        self.assertTrue(os.path.exists(audit_path), "Audit summary should exist")
        with open(audit_path, "r") as f:
            audit = json.load(f)
            
        # Check for Critical Question in summary
        # Depending on how I implemented extraction, checking total open questions or top 10
        self.assertIn("open_questions_summary", audit)
        print(f"Captured Top 10 Questions: {audit['open_questions_summary']['top_10']}")
        self.assertTrue(any("CRITICAL" in q for q in audit["open_questions_summary"]["top_10"]), "Critical question should be in summary")

        print("✅ QA Critical Test Passed")

    def test_d_manual_rejection(self):
        """
        Scenario D: Manual Rejection
        User inputs 'REJECT' at gate.
        Expect: end_state = 'run_failed' in audit summary.
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["enabled"] = False 
        self.write_config(config)

        # Mock Provider
        mock_provider = MagicMock()
        mock_provider.run.return_value = json.dumps({"deliverable_markdown": "Safe content passing validation", "updated_state": {}, "open_questions": []})

        print("\n--- Test D: Manual Rejection ---")
        # Patch input to return REJECT
        with patch("orchestrator.root_agent.CONFIG_PATH", Path(self.config_path)), \
             patch("orchestrator.root_agent.LEDGER_PATH", self.ledger_path), \
             patch("orchestrator.root_agent.INPUTS_DIR", self.inputs_dir), \
             patch("orchestrator.root_agent.OUTPUTS_DIR", self.test_dir), \
             patch("orchestrator.root_agent.load_text", return_value="Mock Prompt"), \
             patch("orchestrator.root_agent.get_provider", return_value=mock_provider), \
             patch("builtins.input", return_value="REJECT"):
            
            with self.assertRaises(SystemExit) as cm:
                root_agent.run_pipeline()
            
            self.assertEqual(cm.exception.code, 1)

        # Verify Audit Summary
        subdirs = [d for d in os.listdir(self.test_dir) if os.path.isdir(os.path.join(self.test_dir, d)) and d != "inputs"]
        self.assertTrue(len(subdirs) > 0)
        run_dir = os.path.join(self.test_dir, subdirs[0])
        audit_path = os.path.join(run_dir, "audit_summary.json")
        
        self.assertTrue(os.path.exists(audit_path), "Audit summary should exist despite rejection")
        with open(audit_path, "r") as f:
            audit = json.load(f)
            
        self.assertEqual(audit["end_state"], "run_failed")
        self.assertEqual(audit.get("failure_reason"), "approval_rejected")
        print("✅ Manual Rejection Test Passed")

    def test_e_severity_weighted_threshold(self):
        """
        Scenario E: Severity-Weighted Threshold
        enabled=true, threshold=1
        
        Subtest 1: 3 MINOR questions -> Weighted 0 -> NO Gate
        Subtest 2: 1 MAJOR question -> Weighted 1 -> Gate
        """
        config = self.base_config.copy()
        config["approval"]["risk_gate_escalation"]["enabled"] = True
        config["approval"]["risk_gate_escalation"]["open_questions_threshold"] = 1
        self.write_config(config)

        # Mock Provider
        # Response 1: 3 MINORS (Should Pass)
        # Response 2: 1 MAJOR (Should Gate)
        minor_response = json.dumps({
            "deliverable_markdown": "Passable content...",
            "updated_state": {},
            "open_questions": ["MINOR: nits", "minor: style", "MINOR: typo"]
        })
        major_response = json.dumps({
            "deliverable_markdown": "Risky content...",
            "updated_state": {},
            "open_questions": ["MAJOR: Ambiguous requirement"]
        })
        
        mock_provider = MagicMock()
        mock_provider.run.side_effect = [minor_response, major_response, major_response]

        print("\n--- Test E: Severity Weighted Threshold ---")
        with self.mock_environment(mock_provider):
            root_agent.run_pipeline(start_step=1)

        ledger = self.get_ledger_lines()
        
        # Step 1: 3 MINORs -> Should NOT be gated by risk (unless phase gate matches, but let's check risk gates)
        # We are looking for risk_gate_forced events.
        
        # Step 1 (Index 1): MINORs.
        step1_risk = [e for e in ledger if e.get("event") == "risk_gate_forced" and e.get("step_idx") == 1]
        self.assertEqual(len(step1_risk), 0, "MINOR items should NOT trigger threshold gate (weighted count 0)")

        # Step 2 (Index 2): MAJOR.
        step2_risk = [e for e in ledger if e.get("event") == "risk_gate_forced" and e.get("step_idx") == 2]
        self.assertEqual(len(step2_risk), 1, "MAJOR item SHOULD trigger threshold gate")
        
        event = step2_risk[0]
        self.assertEqual(event["observed_open_questions_count_weighted"], 1)
        self.assertEqual(event["observed_open_questions_count_total"], 1)
        
        print(f"Captured Risk Event: {json.dumps(event)}")
        print("✅ Severity Weighted Test Passed")

if __name__ == '__main__':
    unittest.main()
