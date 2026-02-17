import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_pipeline import load_and_validate_config, apply_profile_transformations

class TestContentOnlyMode(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        # Create a sample config for testing
        self.sample_config = {
            "agents": [
                {"name": "strategy_lead_agent", "gate": False},          # 1
                {"name": "learner_research_agent", "gate": False},       # 2
                {"name": "learning_architect_agent", "gate": False},     # 3
                {"name": "instructional_designer_agent", "gate": False}, # 4
                {"name": "assessment_designer_agent", "gate": False},    # 5
                {"name": "storyboard_agent", "gate": False},             # 6
                {"name": "media_producer_agent", "gate": False},         # 7 (TO BE REMOVED)
                {"name": "qa_agent", "gate": False},                     # 8 -> 7
                {"name": "change_management_agent", "gate": False},      # 9 -> 8
                {"name": "operations_librarian_agent", "gate": False}    # 10 -> 9
            ],
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": [3, 6, 9]
            }
        }

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_content_only_profile_filtering(self):
        """Test that content_only profile filters media_producer_agent and adjusts gates."""
        
        # Apply transformation
        new_config = apply_profile_transformations(self.sample_config, "content_only")
        
        # Check agents
        agent_names = [a["name"] for a in new_config["agents"]]
        self.assertNotIn("media_producer_agent", agent_names)
        self.assertEqual(len(agent_names), 9)
        self.assertEqual(agent_names[6], "qa_agent") # Step 7 should now be QA
        
        # Check gates
        self.assertEqual(new_config["approval"]["phase_gates"], [3, 6, 8])

    def test_other_profile_no_change(self):
        """Test that other profiles do not change the config."""
        new_config = apply_profile_transformations(self.sample_config, "pilot")
        self.assertEqual(len(new_config["agents"]), 10)
        self.assertEqual(new_config["approval"]["phase_gates"], [3, 6, 9])
        
    def test_integration_dry_run_execution(self):
        """
        Run the pipeline script in dry_run mode with content_only profile and verify output.
        We use subprocess to feed stdin to handle gates.
        """
        import subprocess
        
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_pipeline.py"),
            "--governance_profile", "content_only",
            "--dry_run",
            "--max-step", "9",
            "--inputs-dir", "_inputs_demo", # Use demo inputs which exist
            "--allow-dirty-worktree" # Necessary if running in dirty repo
        ]
        
        # Prepare input: APPROVE (gates)
        # We need enough approves for all gates.
        # Gates: Strategy(Risk), LA(Phase), Storyboard(Phase), QA(Risk), ChangeMgmt(Phase).
        # Total 5 gates. Dry run skips cost guardrail.
        input_str = ("APPROVE\n" * 10)
        
        # Run process
        result = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Check return code
        if result.returncode != 0:
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            
        self.assertEqual(result.returncode, 0, f"Script failed with code {result.returncode}")
        
        stdout = result.stdout
        
        # Verify Run Plan
        self.assertIn("Agents (9 steps)", stdout)
        self.assertIn("Updated phase gates to: [3, 6, 8]", stdout)
        
        # Verify Execution
        self.assertIn("STARTING PIPELINE EXECUTION", stdout)
        self.assertIn("Running Step 1: strategy_lead_agent", stdout)
        self.assertIn("Running Step 9: operations_librarian_agent", stdout)
        self.assertIn("✅ RUN COMPLETE", stdout)
        
        # Verify Risk Gate Handling
        self.assertIn("RISK GATE: open_questions_threshold", stdout)
        self.assertIn("OVERRIDE and continue", stdout) # Prompt was shown
        
        # Verify Step 7 is QA (since media producer removed)
        self.assertIn("Running Step 7: qa_agent", stdout)
