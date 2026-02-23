import subprocess
import sys
from pathlib import Path

def test_run_quality_review_imports():
    """
    Ensure scripts/run_quality_review.py is import-safe and runnable 
    from the repo root without requiring PYTHONPATH or editable install.
    """
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_quality_review.py"
    
    # Run the script with --help using the current Python executable
    # We clear PYTHONPATH from env to ensure we rely solely on internal bootstrap
    import os
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
        
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    assert "--course-slug" in result.stdout, "Expected --course-slug in help output"
