
import json
import os
import shutil
import pytest
from pathlib import Path
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch
from orchestrator.media_spec import validate_media_spec
from services.delivery_packager import DeliveryPackager
from scripts.bundle_export import collect_run_files
from scripts.run_report import generate_report_data

@patch('scripts.bundle_export.run_subprocess')
def test_offline_media_delivery_integration(mock_subprocess, tmp_path):
    """
    Offline integration test for Phase 4 Media Delivery Layer.
    Verifies:
    1. Media Spec Validation
    2. Delivery Packaging (Slides/SCORM)
    3. Bundle Export (including dist/)
    4. Run Report (deployables section)
    """
    mock_subprocess.return_value = "{}"
    
    # --------------------------------------------------------------------------
    # 1. Setup Run Context
    # --------------------------------------------------------------------------
    run_id = "20260206_OFFLINE_TEST"
    run_dir = tmp_path / "outputs" / run_id
    run_dir.mkdir(parents=True)
    
    # Copy fixture for CA (simulating Pass 1 output)
    fixtures_dir = Path(__file__).parent / "fixtures"
    ca_fixture = fixtures_dir / "course_architecture_minimal.json"
    
    # Ensure fixture exists or create a minimal one if running in environment where it's missing
    if ca_fixture.exists():
        shutil.copy(ca_fixture, run_dir / "course_architecture.json")
    else:
        # Fallback minimal CA
        ca_data = {
            "course_id": "TEST_COURSE_001", 
            "modules": [],
            "learning_objects": []
        }
        with open(run_dir / "course_architecture.json", "w") as f:
            json.dump(ca_data, f)

    # initialize manifest and audit summary
    (run_dir / "run_manifest.json").write_text('{"system_version": "0.6.0-test", "status": "completed"}')
    (run_dir / "audit_summary.json").write_text('{"run_metadata": {}, "gate_summary": {}, "open_questions_summary": {}}')

    from orchestrator.course_architecture import stable_hash
    
    # Calculate hash of the CA we just saved
    with open(run_dir / "course_architecture.json", "r") as f:
        ca_loaded = json.load(f)
    ca_hash = stable_hash(ca_loaded)

    # --------------------------------------------------------------------------
    # 2. Simulate Media Spec (Media Producer Agent Output)
    # --------------------------------------------------------------------------
    media_spec = {
        "course_id": "TEST_COURSE_001",
        "generated_at_utc": "2026-02-06T12:00:00Z",
        "architecture_hash": ca_hash,
        "media_assets": [
            {
                "learning_object_id": "lo_01",
                "slides": [
                    {
                        "order": 1,
                        "title": "Welcome",
                        "layout": "title",
                        "bullets": ["Point 1", "Point 2"],
                        "narration": "Welcome to the course."
                    }
                ]
            }
        ]
    }
    
    # Validate Media Spec
    validate_media_spec(media_spec)
    
    # Save as if agent produced it
    (run_dir / "08_media_producer_agent_state.json").write_text(json.dumps({
        "updated_state": {"media_spec": media_spec},
        "deliverable_markdown": "# Media Spec",
        "open_questions": []
    }))

    # --------------------------------------------------------------------------
    # 3. Delivery Packaging
    # --------------------------------------------------------------------------
    packager = DeliveryPackager(run_dir)
    results = packager.process(media_spec)
    
    # Assertions on Packager
    assert (run_dir / "dist" / "TEST_COURSE_001_presentation.html").exists()
    assert (run_dir / "dist" / "TEST_COURSE_001_scorm_package.zip").exists()
    assert results["slides_html"].endswith(".html")

    # --------------------------------------------------------------------------
    # 4. Bundle Export Integration
    # --------------------------------------------------------------------------
    bundle_files = collect_run_files(run_id, run_dir, include_state=True)
    bundle_arcnames = [f['arcname'] for f in bundle_files]
    
    # Verify dist is included
    assert "dist/TEST_COURSE_001_presentation.html" in bundle_arcnames
    assert "dist/TEST_COURSE_001_scorm_package.zip" in bundle_arcnames
    assert "08_media_producer_agent_state.json" in bundle_arcnames # State included

    # --------------------------------------------------------------------------
    # 5. Run Report Integration
    # --------------------------------------------------------------------------
    # Simulate loading json files
    audit_summary = json.loads((run_dir / "audit_summary.json").read_text())
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    
    report_data = generate_report_data(run_dir, audit_summary, manifest)
    
    # Verify Deployables section in data
    assert "deployables" in report_data
    deployables = report_data["deployables"]
    assert "dist/TEST_COURSE_001_presentation.html" in deployables
    assert "dist/TEST_COURSE_001_scorm_package.zip" in deployables

    print("\n✅ Verification Complete: All components integrated successfully offline.")
