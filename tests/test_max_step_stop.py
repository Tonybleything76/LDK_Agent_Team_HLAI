
import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.run_pipeline import main as run_pipeline_main
from orchestrator.root_agent import run_pipeline

# We need to mock input validation and config loading to avoid real file dependencies if possible
# Or we can just use the existing files if they are available in the env.
# The user's repo seems to have inputs/ and config/, so we can rely on them or mock them.
# Let's mock them to be safe and isolated.

class TestMaxStepStop:
    @pytest.fixture
    def mock_inputs(self, tmp_path):
        """Setup mock inputs and config for the test"""
        # Create temp inputs dir
        inputs_dir = tmp_path / "inputs"
        inputs_dir.mkdir()
        (inputs_dir / "business_brief.md").write_text("Mock brief " * 100)
        (inputs_dir / "sme_notes.md").write_text("Mock notes " * 100)
        
        # Create temp config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_content = {
            "agents": [
                {"name": "agent1", "prompt_path": str(tmp_path / "agent1.txt"), "provider": "dry_run"},
                {"name": "agent2", "prompt_path": str(tmp_path / "agent2.txt"), "provider": "dry_run"},
            ],
            "approval": {
                "gate_strategy": "per_phase",
                "phase_gates": []
            },
            "validation": {
                "min_deliverable_chars": 10
            }
        }
        config_path = config_dir / "run_config.json"
        config_path.write_text(json.dumps(config_content))
        
        # Create dummy prompt files
        (tmp_path / "agent1.txt").write_text("Prompt 1")
        (tmp_path / "agent2.txt").write_text("Prompt 2")
        
        return {
            "root": tmp_path,
            "config_path": str(config_path),
            "inputs_dir": str(inputs_dir)
        }

    @patch("scripts.run_pipeline.INPUTS_DIR")
    @patch("scripts.run_pipeline.BUSINESS_BRIEF_PATH")
    @patch("scripts.run_pipeline.SME_NOTES_PATH")
    @patch("scripts.run_pipeline.PROJECT_ROOT")
    def test_max_step_cli(self, mock_root, mock_brief_path, mock_sme_path, mock_inputs_dir_path, mock_inputs):
        """Test the full CLI flow with --max-step 1"""
        
        # Setup mocks
        root = mock_inputs["root"]
        mock_root.return_value = root
        
        # We need to patch CONFIG_PATH with a real Path object because open() is used on it
        real_config_path = Path(mock_inputs["config_path"])
        
        mock_inputs_dir_path.__str__.return_value = mock_inputs["inputs_dir"]
        
        mock_brief_path.exists.return_value = True
        mock_brief_path.stat.return_value.st_size = 1000
        
        mock_sme_path.exists.return_value = True
        mock_sme_path.stat.return_value.st_size = 1000
        
        # Mock sys.argv
        with patch("sys.argv", ["run_pipeline.py", "--dry_run", "--max-step", "1", "--yes", "--skip_preflight", "--allow-dirty-worktree", "--governance_profile", "dev"]), \
             patch("scripts.run_pipeline.CONFIG_PATH", real_config_path), \
             patch("orchestrator.root_agent.CONFIG_PATH", real_config_path), \
             patch("orchestrator.root_agent.INPUTS_DIR", mock_inputs["inputs_dir"]), \
             patch("orchestrator.root_agent.OUTPUTS_DIR", str(root / "outputs")), \
             patch("orchestrator.root_agent.LEDGER_PATH", str(root / "governance/run_ledger.jsonl")):
                 
            # Force run
            try:
                run_pipeline_main()
            except SystemExit as e:
                assert e.code == 0
            
            # Verify outputs
            outputs_dir = root / "outputs"
            assert outputs_dir.exists()
            
            # Find the run dir (should be one)
            run_dirs = list(outputs_dir.iterdir())
            assert len(run_dirs) == 1
            run_dir = run_dirs[0]
            
            # Verify Manifest
            manifest_path = run_dir / "run_manifest.json"
            assert manifest_path.exists()
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            assert manifest["status"] == "completed"
            assert manifest["current_step_completed"] == 1
            
            # Verify Ledger
            ledger_path = root / "governance/run_ledger.jsonl"
            assert ledger_path.exists()
            
            events = []
            with open(ledger_path) as f:
                for line in f:
                    events.append(json.loads(line))
            
            # Find run_stopped_early event
            stop_events = [e for e in events if e.get("event") == "run_stopped_early"]
            assert len(stop_events) == 1
            assert stop_events[0]["max_step"] == 1
            assert stop_events[0]["last_step_completed"] == 1

