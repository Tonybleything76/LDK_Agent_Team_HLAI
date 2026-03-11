"""
Shared utilities for interacting with the pipeline and run output directories.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

OUTPUTS_DIR = Path("outputs")
INPUTS_DIR = Path("inputs")

AGENT_LABELS = [
    (1, "strategy_lead_agent",          "Strategy Lead"),
    (2, "learner_research_agent",        "Learner Research"),
    (3, "learning_architect_agent",      "Learning Architect"),
    (4, "instructional_designer_agent",  "Instructional Designer"),
    (5, "assessment_designer_agent",     "Assessment Designer"),
    (6, "storyboard_agent",              "Storyboard"),
    (7, "media_producer_agent",          "Media Producer"),
    (8, "qa_agent",                      "QA"),
    (9, "change_management_agent",       "Change Management"),
    (10, "operations_librarian_agent",   "Operations Librarian"),
]

PHASE_GATES = {3: "Pass 1 Complete", 6: "Pass 2 Complete", 9: "Pass 3 Complete"}


def list_runs() -> list[dict]:
    """Return metadata for all completed runs, newest first."""
    runs = []
    if not OUTPUTS_DIR.exists():
        return runs
    for run_dir in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        manifest_path = run_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                manifest["_run_dir"] = str(run_dir)
                runs.append(manifest)
            except Exception:
                runs.append({"run_id": run_dir.name, "_run_dir": str(run_dir)})
        else:
            runs.append({"run_id": run_dir.name, "_run_dir": str(run_dir)})
    return runs


def get_run_outputs(run_dir: str) -> dict[str, str]:
    """
    Return a dict mapping agent_name -> deliverable markdown text
    for all checkpoint files found in the run directory.
    """
    result = {}
    run_path = Path(run_dir)
    for step_num, agent_name, _ in AGENT_LABELS:
        checkpoint = run_path / f"step_{step_num:02d}_{agent_name}.json"
        if checkpoint.exists():
            try:
                data = json.loads(checkpoint.read_text())
                result[agent_name] = data.get("deliverable_markdown", "")
            except Exception:
                pass
    return result


def write_inputs(business_brief: str, sme_notes: str, run_inputs_dir: Path) -> None:
    """Write business_brief.md and sme_notes.md to the given directory."""
    run_inputs_dir.mkdir(parents=True, exist_ok=True)
    (run_inputs_dir / "business_brief.md").write_text(business_brief)
    (run_inputs_dir / "sme_notes.md").write_text(sme_notes)


def start_pipeline(business_brief: str, sme_notes: str) -> subprocess.Popen:
    """
    Write inputs and launch the pipeline subprocess with AUTO_APPROVE=1.
    Returns the Popen handle for streaming output.
    """
    # Write inputs into the standard inputs/ directory
    INPUTS_DIR.mkdir(exist_ok=True)
    (INPUTS_DIR / "business_brief.md").write_text(business_brief)
    (INPUTS_DIR / "sme_notes.md").write_text(sme_notes)

    env = os.environ.copy()
    env["AUTO_APPROVE"] = "1"
    env["AUTO_APPROVE_SOURCE"] = "ui"

    proc = subprocess.Popen(
        [sys.executable, "-m", "cli.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=str(Path.cwd()),
    )
    return proc


def format_run_id(run_id: str) -> str:
    """Convert a run_id like '20260311_143022' into a readable datetime string."""
    try:
        dt = datetime.strptime(run_id, "%Y%m%d_%H%M%S")
        return dt.strftime("%b %d, %Y  %H:%M")
    except Exception:
        return run_id
