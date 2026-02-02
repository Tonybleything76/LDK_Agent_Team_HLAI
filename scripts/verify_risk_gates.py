
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Ensure we can import orchestrator
sys.path.append(os.getcwd())

from orchestrator import root_agent

class TestRiskGates(unittest.TestCase):
    
    def setUp(self):
        self.mock_config = {
            "mode": "cli",
            "provider": "openai",
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [3, 6, 9],
                "risk_gate_escalation": {
                    "enabled": False,
                    "open_questions_threshold": 8,
                    "force_gate_on_qa_critical": True
                }
            },
            "validation": { "min_deliverable_chars": 10 },
            "agents": [
                {"name": "agent_1", "prompt_path": "mock_prompt", "gate": False},
                {"name": "agent_2", "prompt_path": "mock_prompt", "gate": False},
                {"name": "qa_agent", "prompt_path": "mock_prompt", "gate": False}
            ]
        }

    @patch('os.path.exists')
    @patch('orchestrator.root_agent.compute_inputs_hash')
    @patch('orchestrator.root_agent.compute_config_hash')
    @patch('orchestrator.root_agent.get_initial_state')
    @patch('orchestrator.root_agent.load_config')
    @patch('orchestrator.root_agent.load_text')
    @patch('orchestrator.root_agent.get_provider')
    @patch('orchestrator.root_agent.approval_gate')
    @patch('orchestrator.root_agent.write_ledger')
    @patch('orchestrator.root_agent.write_manifest')
    @patch('orchestrator.root_agent.write_checkpoint')
    @patch('orchestrator.root_agent.ensure_run_dirs')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_risk_escalation_disabled(self, mock_open, mock_makedirs, mock_ensure, mock_ckpt, mock_manifest, mock_ledger, mock_gate, mock_provider, mock_load_text, mock_load_config, mock_get_state, mock_hash_cfg, mock_hash_inp, mock_exists):
        # Setup
        mock_exists.return_value = True
        mock_hash_cfg.return_value = "mock_hash"
        mock_hash_inp.return_value = "mock_hash"
        mock_get_state.return_value = {}
        mock_load_config.return_value = self.mock_config
        mock_load_text.return_value = "Mock Prompt"
        mock_ensure.return_value = "mock_dir"
        
        # Mock Provider Responses
        # Agent 1 (Step 1): High open questions (10), but escalation DISABLED
        response_1 = json.dumps({
            "deliverable_markdown": "content content content",
            "updated_state": {},
            "open_questions": ["q"] * 10
        })
        
        mock_instance = MagicMock()
        mock_instance.run.return_value = response_1
        mock_provider.return_value = mock_instance
        
        # Run Pipeline just for step 1
        with patch('orchestrator.root_agent.INPUTS_DIR', 'mock_inputs'):
             root_agent.run_pipeline(start_step=1) 
        
        # Verify approval_gate NOT called for step 1
        calls = [c for c in mock_gate.mock_calls if c.args[0] == 1]
        self.assertEqual(len(calls), 0, "Gate should NOT be called for step 1 when disabled")

    @patch('os.path.exists')
    @patch('orchestrator.root_agent.compute_inputs_hash')
    @patch('orchestrator.root_agent.compute_config_hash')
    @patch('orchestrator.root_agent.get_initial_state')
    @patch('orchestrator.root_agent.load_config')
    @patch('orchestrator.root_agent.load_text')
    @patch('orchestrator.root_agent.get_provider')
    @patch('orchestrator.root_agent.approval_gate')
    @patch('orchestrator.root_agent.write_ledger')
    @patch('orchestrator.root_agent.write_manifest')
    @patch('orchestrator.root_agent.write_checkpoint')
    @patch('orchestrator.root_agent.ensure_run_dirs')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_risk_escalation_threshold(self, mock_open, mock_makedirs, mock_ensure, mock_ckpt, mock_manifest, mock_ledger, mock_gate, mock_provider, mock_load_text, mock_load_config, mock_get_state, mock_hash_cfg, mock_hash_inp, mock_exists):
        # Setup Config: Enabled = True, Threshold = 5
        mock_exists.return_value = True
        mock_hash_cfg.return_value = "mock_hash"
        mock_hash_inp.return_value = "mock_hash"
        mock_get_state.return_value = {}
        config = self.mock_config.copy()
        config['approval']['risk_gate_escalation']['enabled'] = True
        config['approval']['risk_gate_escalation']['open_questions_threshold'] = 5
        mock_load_config.return_value = config
        mock_load_text.return_value = "Mock Prompt"
        mock_ensure.return_value = "mock_dir"

        # Mock Provider 
        # Agent 1 (Step 1): 6 open questions -> ESCALATE
        response_1 = json.dumps({
            "deliverable_markdown": "content content content",
            "updated_state": {},
            "open_questions": ["q"] * 6
        })
        
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [response_1, response_1, response_1] 
        mock_provider.return_value = mock_instance
        
        with patch('orchestrator.root_agent.INPUTS_DIR', 'mock_inputs'):
             root_agent.run_pipeline()
        
        # Verify gate called for step 1
        calls = [c for c in mock_gate.mock_calls if c.args[0] == 1]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].kwargs['gate_type'], 'risk_gate')
        self.assertIn('open_questions_threshold', calls[0].kwargs['gate_reason'])

    @patch('os.path.exists')
    @patch('orchestrator.root_agent.compute_inputs_hash')
    @patch('orchestrator.root_agent.compute_config_hash')
    @patch('orchestrator.root_agent.get_initial_state')
    @patch('orchestrator.root_agent.load_config')
    @patch('orchestrator.root_agent.load_text')
    @patch('orchestrator.root_agent.get_provider')
    @patch('orchestrator.root_agent.approval_gate')
    @patch('orchestrator.root_agent.write_ledger')
    @patch('orchestrator.root_agent.write_manifest')
    @patch('orchestrator.root_agent.write_checkpoint')
    @patch('orchestrator.root_agent.ensure_run_dirs')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_risk_escalation_qa_critical(self, mock_open, mock_makedirs, mock_ensure, mock_ckpt, mock_manifest, mock_ledger, mock_gate, mock_provider, mock_load_text, mock_load_config, mock_get_state, mock_hash_cfg, mock_hash_inp, mock_exists):
        # Setup: Enabled = True
        mock_exists.return_value = True
        mock_hash_cfg.return_value = "mock_hash"
        mock_hash_inp.return_value = "mock_hash"
        mock_get_state.return_value = {}
        config = self.mock_config.copy()
        config['approval']['risk_gate_escalation']['enabled'] = True
        mock_load_config.return_value = config
        mock_load_text.return_value = "Mock Prompt"
        mock_ensure.return_value = "mock_dir"

        # Mock Provider
        # Step 1: Normal
        # Step 2: Normal
        # Step 3 (QA): Critical Error
        
        normal_resp = json.dumps({
            "deliverable_markdown": "content content content",
            "updated_state": {},
            "open_questions": []
        })
        
        qa_resp = json.dumps({
            "deliverable_markdown": "qa report content content",
            "updated_state": {
                "qa": {
                    "critical_errors": ["MAJOR FAIL"],
                    "suggestions": []
                }
            },
            "open_questions": []
        })
        
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [normal_resp, normal_resp, qa_resp]
        mock_provider.return_value = mock_instance
        
        with patch('orchestrator.root_agent.INPUTS_DIR', 'mock_inputs'):
             root_agent.run_pipeline()
        
        # Verify gate called for step 3
        calls = [c for c in mock_gate.mock_calls if c.args[0] == 3]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].kwargs['gate_type'], 'risk_gate')
        self.assertIn('qa_critical_errors', calls[0].kwargs['gate_reason'])

if __name__ == '__main__':
    unittest.main()
