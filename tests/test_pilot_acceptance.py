"""
Tests for the Pilot Acceptance Harness (scripts/run_pilot_acceptance.py).

Uses provider=dry_run for speed. Runs the full script end-to-end via subprocess
and asserts that all expected outputs are produced.

NOTE: inputs_dir must be inside (or resolvable relative to) PROJECT_ROOT because
run_content_consistency.py calls inputs_dir.relative_to(PROJECT_ROOT).
We therefore use tmp subdirectories under PROJECT_ROOT/tmp/.
"""

import json
import sys
import zipfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "run_pilot_acceptance.py"
EXPORTS_DIR = PROJECT_ROOT / "exports"
TEST_TMP = PROJECT_ROOT / "tmp" / "test_pilot_acceptance"

COURSE_SLUG = "test_pilot_accept_harness"


@pytest.fixture(autouse=True)
def cleanup():
    """Set up a clean project-relative tmp dir and remove acceptance artifacts before/after."""
    pack = EXPORTS_DIR / f"pilot_acceptance_pack_{COURSE_SLUG}.zip"
    report = EXPORTS_DIR / "content_consistency_report.json"

    # Remove before test
    pack.unlink(missing_ok=True)
    report.unlink(missing_ok=True)

    # Clean test tmp dir
    import shutil
    if TEST_TMP.exists():
        shutil.rmtree(TEST_TMP)
    TEST_TMP.mkdir(parents=True)

    yield

    # Leave artifacts in place for post-failure inspection.


def _run_script(inputs_dir: Path, extra_args=None):
    """Helper: run run_pilot_acceptance.py as a subprocess."""
    import subprocess
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--course-slug", COURSE_SLUG,
        "--inputs-dir", str(inputs_dir),
        "--provider", "dry_run",
        "--runs", "2",
        "--auto-approve",
        "--min-structure-stability", "0",  # dry_run returns 0; gate would otherwise fail
    ]
    if extra_args:
        cmd.extend(extra_args)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


class TestPilotAcceptanceHarness:

    def test_pack_zip_created(self):
        """The pilot acceptance ZIP must exist after a successful dry_run."""
        inputs_dir = TEST_TMP / "inputs_pack"
        result = _run_script(inputs_dir)
        assert result.returncode == 0, (
            f"Script exited non-zero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        pack = EXPORTS_DIR / f"pilot_acceptance_pack_{COURSE_SLUG}.zip"
        assert pack.exists(), f"Expected {pack} to exist after run."

    def test_summary_markdown_in_zip(self):
        """pilot_acceptance_summary.md must be present inside the ZIP."""
        inputs_dir = TEST_TMP / "inputs_summary"
        result = _run_script(inputs_dir)
        assert result.returncode == 0, (
            f"Script exited non-zero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        pack = EXPORTS_DIR / f"pilot_acceptance_pack_{COURSE_SLUG}.zip"
        assert pack.exists()
        with zipfile.ZipFile(pack) as zf:
            names = zf.namelist()
        assert "pilot_acceptance_summary.md" in names, (
            f"pilot_acceptance_summary.md not in zip. Contents: {names}"
        )

    def test_report_json_in_zip_with_overall_stability_score(self):
        """content_consistency_report.json in ZIP must contain overall_stability_score."""
        inputs_dir = TEST_TMP / "inputs_report"
        result = _run_script(inputs_dir)
        assert result.returncode == 0, (
            f"Script exited non-zero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        pack = EXPORTS_DIR / f"pilot_acceptance_pack_{COURSE_SLUG}.zip"
        assert pack.exists()
        with zipfile.ZipFile(pack) as zf:
            names = zf.namelist()
            assert "content_consistency_report.json" in names, (
                f"content_consistency_report.json not in zip. Contents: {names}"
            )
            with zf.open("content_consistency_report.json") as f:
                report = json.load(f)
        assert "overall_stability_score" in report, (
            f"overall_stability_score not in report. Keys: {list(report.keys())}"
        )

    def test_templates_copied_when_inputs_missing(self):
        """When inputs-dir does not exist, templates must be copied into it."""
        fresh_dir = TEST_TMP / "fresh_inputs"
        assert not fresh_dir.exists()
        result = _run_script(fresh_dir)
        assert result.returncode == 0, (
            f"Script exited non-zero.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert (fresh_dir / "business_brief.md").exists(), "business_brief.md not created"
        assert (fresh_dir / "sme_notes.md").exists(), "sme_notes.md not created"

    def test_stability_threshold_gate_fails_when_too_high(self):
        """min-structure-stability=101 must always fail (score can never exceed 100)."""
        import subprocess
        inputs_dir = TEST_TMP / "inputs_thresh"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--course-slug", COURSE_SLUG,
            "--inputs-dir", str(inputs_dir),
            "--provider", "dry_run",
            "--runs", "2",
            "--auto-approve",
            "--no-require-quality",
            "--min-structure-stability", "101",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)
        assert result.returncode != 0, (
            "Expected non-zero exit with min-structure-stability=101, but script passed."
        )
