import os
import zipfile
import json
from pathlib import Path
import pytest
from unittest.mock import patch
from scripts.bundle_export import collect_run_files

@patch('scripts.bundle_export.run_subprocess')
def test_collect_run_files_includes_dist(mock_run_subprocess, tmp_path):
    """
    Verify that collect_run_files includes the dist/ directory and its contents.
    """
    mock_run_subprocess.return_value = "{}"  # Mock return for run_report calls
    
    # Setup mock run directory
    run_dir = tmp_path / "outputs" / "20260206_120000"
    run_dir.mkdir(parents=True)
    
    # Create required artifacts for valid run
    (run_dir / "audit_summary.json").write_text("{}")
    (run_dir / "run_manifest.json").write_text("{}")
    
    # Pre-create reports to avoid subprocess usage logic if checked
    (run_dir / "audit_summary.md").write_text("# Audit Summary")
    
    # Create dist directory with artifacts
    dist_dir = run_dir / "dist"
    dist_dir.mkdir()
    (dist_dir / "course_presentation.html").write_text("<html>Slide Content</html>")
    (dist_dir / "scorm_package.zip").write_text("PK...")
    
    # Run collection
    files = collect_run_files("20260206_120000", run_dir, include_state=False)
    
    # Assertions
    filenames = [f['arcname'] for f in files]
    
    assert "dist/course_presentation.html" in filenames, "dist artifacts must be included in bundle"
    assert "dist/scorm_package.zip" in filenames, "dist artifacts must be included in bundle"
    
    # Check source paths
    html_file = next(f for f in files if f['arcname'] == "dist/course_presentation.html")
    assert html_file['source'] == dist_dir / "course_presentation.html"

@patch('scripts.bundle_export.run_subprocess')
def test_collect_run_files_handles_missing_dist(mock_run_subprocess, tmp_path):
    """
    Verify that collect_run_files works gracefully without dist/ directory.
    """
    mock_run_subprocess.return_value = "{}"

    run_dir = tmp_path / "outputs" / "20260206_120001"
    run_dir.mkdir(parents=True)
    (run_dir / "audit_summary.json").write_text("{}")
    
    # Pre-create reports
    (run_dir / "audit_summary.md").write_text("# Audit Summary")
    
    files = collect_run_files("20260206_120001", run_dir, include_state=False)
    
    filenames = [f['arcname'] for f in files]
    assert not any(f.startswith("dist/") for f in filenames)
