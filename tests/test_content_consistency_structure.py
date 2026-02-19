import json
import pytest
import shutil
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import scripts.run_content_consistency as run_consistency

@pytest.fixture
def dummy_run_data(tmp_path):
    # Create a dummy run directory with a learning architect state
    run_path = tmp_path / "run_data"
    run_path.mkdir()
    
    la_state = {
        "updated_state": {
            "curriculum": {
                "modules": [
                    {
                        "module_id": "M1",
                        "title": "Module 1",
                        "key_concepts": ["C1", "C2", "C3", "C4", "C5"],
                        "activities": ["A1", "A2"],
                        "checks": ["Q1", "Q2"]
                    },
                    {
                        "module_id": "M2",
                        "title": "Module 2",
                        "key_concepts": ["C1", "C2", "C3", "C4"],
                        "activities": ["A1", "A2"],
                        "checks": ["Q1", "Q2"]
                    }
                ]
            }
        }
    }
    
    with open(run_path / "03_learning_architect_agent_state.json", "w") as f:
        json.dump(la_state, f)
        
    return {"path": run_path}

def test_analyze_structure_extractor(dummy_run_data):
    metrics = run_consistency.analyze_structure(dummy_run_data)
    
    assert metrics["modules_count"] == 2
    assert metrics["module_ids"] == ["M1", "M2"]
    assert metrics["per_module_counts"]["M1"]["key_concepts"] == 5
    assert metrics["per_module_counts"]["M1"]["activities"] == 2
    assert metrics["per_module_counts"]["M1"]["checks"] == 2
    assert metrics["schema_validity"]["learning_architect"] is True

def test_stability_score_perfect():
    # 6 modules, stable counts within ranges (kc: 4-8, act: 2-4, chk: 2-3)
    reports = [
        {
            "structure": {
                "modules_count": 6,
                "module_ids": ["M1", "M2", "M3", "M4", "M5", "M6"],
                "per_module_counts": {
                    f"M{i}": {"key_concepts": 5, "activities": 3, "checks": 2} for i in range(1, 7)
                }
            }
        }
    ] * 3
    
    score = run_consistency.calculate_stability_score(reports)
    assert score == 100

def test_stability_score_module_count_drift():
    # One run has 6 modules, another has 5. Max score should be 50.
    reports = [
        {
            "structure": {
                "modules_count": 6,
                "module_ids": ["M1", "M2", "M3", "M4", "M5", "M6"],
                "per_module_counts": {
                    f"M{i}": {"key_concepts": 5, "activities": 3, "checks": 2} for i in range(1, 7)
                }
            }
        },
        {
            "structure": {
                "modules_count": 5,
                "module_ids": ["M1", "M2", "M3", "M4", "M5"],
                "per_module_counts": {
                    f"M{i}": {"key_concepts": 5, "activities": 3, "checks": 2} for i in range(1, 6)
                }
            }
        }
    ]
    
    score = run_consistency.calculate_stability_score(reports)
    assert score <= 50

def test_stability_score_id_order_drift():
    # 6 modules, but order reversed in second run
    reports = [
        {
            "structure": {
                "modules_count": 6,
                "module_ids": ["M1", "M2", "M3", "M4", "M5", "M6"],
                "per_module_counts": {
                    f"M{i}": {"key_concepts": 5, "activities": 3, "checks": 2} for i in range(1, 7)
                }
            }
        },
        {
            "structure": {
                "modules_count": 6,
                "module_ids": ["M6", "M5", "M4", "M3", "M2", "M1"],
                "per_module_counts": {
                    f"M{i}": {"key_concepts": 5, "activities": 3, "checks": 2} for i in range(1, 7)
                }
            }
        }
    ]
    
    score = run_consistency.calculate_stability_score(reports)
    assert score <= 70

@patch("scripts.run_content_consistency.run_pipeline")
def test_main_creates_structure_overview_in_zip(mock_run_pipeline, tmp_path, monkeypatch):
    """Test that main() correctly packages structure_overview.md in the output zip."""
    
    # Mock exports and tmp dirs to test isolation
    exports_dir = tmp_path / "exports"
    temp_dir = tmp_path / "tmp_harness"
    monkeypatch.setattr(run_consistency, "EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(run_consistency, "TEMP_DIR", temp_dir)
    
    # Setup inputs
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    
    # Provide fake args
    test_args = ["run_content_consistency.py", "--inputs-dir", str(inputs_dir), "--runs", "1"]
    monkeypatch.setattr("sys.argv", test_args)
    
    # Mock run_pipeline to return a fake run directory
    fake_run_dir = tmp_path / "fake_run"
    fake_run_dir.mkdir()
    
    # Write empty required artifacts to fake run
    for fn in run_consistency.REQUIRED_ARTIFACTS:
        (fake_run_dir / fn).touch()
        
    mock_run_pipeline.return_value = fake_run_dir
    
    # Run main
    run_consistency.main()
    
    # Verify ZIP contents
    zip_path = exports_dir / "content_consistency_pack.zip"
    assert zip_path.exists()
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "diff_overview.md" in namelist
        assert "structure_overview.md" in namelist
