#!/usr/bin/env python3
"""
Content Consistency Harness

Executes multiple "content-only" pilot runs for the same inputs and produces a
deterministic evaluation report and a zipped evidence pack.

Usage:
    python3 scripts/run_content_consistency.py --inputs-dir <dir>

Arguments:
    --inputs-dir <dir>          Directory containing input files (required)
    --provider <provider>       Provider to use (default: openai)
    --runs <n>                  Number of runs to execute (default: 3)
    --governance_profile <prof> Governance profile (default: content_only)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
EXPORTS_DIR = PROJECT_ROOT / "exports"
TEMP_DIR = PROJECT_ROOT / "tmp" / "consistency_harness"

REQUIRED_ARTIFACTS = [
    "01_strategy_lead_agent_state.json",
    "03_learning_architect_agent_state.json",
    "04_instructional_designer_agent_state.json",
    "05_assessment_designer_agent_state.json",
    "06_storyboard_agent_state.json",
    "07_qa_agent_state.json",
    "08_change_management_agent_state.json",
    "09_operations_librarian_agent_state.json",
    "audit_summary.json",
    "run_manifest.json",
]

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_pipeline(
    inputs_dir: Path,
    provider: str,
    governance_profile: str,
    auto_approve: bool,
    model: str
) -> Path:
    """Executes a single pipeline run and returns the run directory."""
    
    # Construct command
    cmd = [
        "python3", "scripts/run_pipeline.py",
        "--inputs-dir", str(inputs_dir.resolve().relative_to(PROJECT_ROOT.resolve())),
        "--governance_profile", governance_profile,
        "--yes", # Skip cost confirmation
    ]
    if auto_approve:
        cmd.append("--auto_approve")

    
    if provider == "dry_run":
        cmd.append("--dry_run")
    elif provider:
        cmd.extend(["--mode", provider])

    # Environment variables
    env = os.environ.copy()
    env["PROVIDER"] = provider
    if provider == "openai" and model:
        env["OPENAI_MODEL"] = model
    
    # We need to capture the output to find the run_id directory
    # run_pipeline prints "Run ID: <timestamp>" or similar, but
    # it is most reliable to check the newest directory in outputs/ after run.
    # However, to be robust against parallel runs (unlikely here but good practice),
    # we can parse stdout. run_pipeline logic:
    # "Audit summary generated: outputs/<run_id>/audit_summary.json"
    
    log(f"Executing pipeline (provider={provider}, profile={governance_profile})...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=env
    )
    
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise RuntimeError(f"Pipeline execution failed with code {result.returncode}")

    # Parse run_dir from stdout
    run_dir = None
    for line in result.stdout.splitlines():
        if "Audit summary generated:" in line:
            # Format: "Audit summary generated: outputs/20231027_123456/audit_summary.json"
            path_str = line.split("generated:")[1].strip()
            run_dir = (PROJECT_ROOT / path_str).parent
            break
            
    if not run_dir or not run_dir.exists():
        # Fallback: get the most recent directory in outputs
        # This is slightly risky but acceptable if we are single-threaded
        all_runs = sorted(
            [d for d in OUTPUTS_DIR.iterdir() if d.is_dir() and d.name.startswith("20")],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        if all_runs:
            run_dir = all_runs[0]
            
    if not run_dir:
        raise RuntimeError("Could not determine run directory from pipeline output")
        
    log(f"Run completed: {run_dir.name}")
    return run_dir

def collect_artifacts(run_dir: Path, dest_dir: Path):
    """Copies required artifacts from run_dir to dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for filename in REQUIRED_ARTIFACTS:
        src = run_dir / filename
        if src.exists():
            shutil.copy2(src, dest_dir / filename)
        else:
            log(f"Warning: Artifact {filename} missing in {run_dir.name}")

def analyze_structure(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes a single run directory for structural metrics."""
    base_path = run_data['path']
    metrics = {
        "modules_count": 0,
        "objectives_count": 0,
        "assessment_items_count": 0,
        "module_ids": [],
        "per_module_counts": {},
        "schema_validity": {}
    }

    # 1. Learning Architect (Curriculum/Modules)
    la_path = base_path / "03_learning_architect_agent_state.json"
    if la_path.exists():
        try:
            with open(la_path) as f:
                data = json.load(f)

            # Support both top-level curriculum and updated_state.curriculum
            curriculum = data.get("curriculum", {})
            if not curriculum:
                updated_state = data.get("updated_state", {})
                curriculum = updated_state.get("curriculum", {})

            # Support curriculum.modules, curriculum.outline, or curriculum.course_architecture
            modules = (
                curriculum.get("modules")
                or curriculum.get("outline")
                or curriculum.get("course_architecture")
                or []
            )

            total_objectives = 0
            metrics["modules_count"] = len(modules)
            for idx, m in enumerate(modules):
                m_id = m.get("module_id", f"M{idx+1}")
                metrics["module_ids"].append(m_id)
                objs = m.get("objectives", [])
                total_objectives += len(objs)
                metrics["per_module_counts"][m_id] = {
                    "title": m.get("title", ""),
                    "objectives": len(objs),
                    "checks": len(m.get("checks", [])),
                    "activities": len(m.get("activities", [])),
                    "key_concepts": len(m.get("key_concepts", []))
                }
            metrics["objectives_count"] = total_objectives
            metrics["schema_validity"]["learning_architect"] = True
        except json.JSONDecodeError:
            metrics["schema_validity"]["learning_architect"] = False

    # 2. Storyboard
    sb_path = base_path / "06_storyboard_agent_state.json"
    if sb_path.exists():
        try:
            with open(sb_path) as f:
                sb_data = json.load(f)
            updated_state = sb_data.get("updated_state", {})
            storyboards = updated_state.get("storyboards", [])
            metrics["storyboard_modules_count"] = len(storyboards)
        except (json.JSONDecodeError, Exception):
            metrics["storyboard_modules_count"] = 0

    return metrics

def calculate_quality_rubric(run_path: Path) -> Dict[str, Any]:
    """Calculates human-centered quality rubric scores."""
    scores = {
        "belief_clarity_present": False,
        "behavior_clarity_present": False,
        "systems_policies_present": False,
        "alignment_score": 0,
        "copilot_coverage_score": 0
    }

    # --- Strategy Lead Analysis ---
    sl_path = run_path / "01_strategy_lead_agent_state.json"
    if sl_path.exists():
        try:
            with open(sl_path) as f:
                sl_data = json.load(f)

            text_content = ""
            if "deliverable_markdown" in sl_data:
                text_content += sl_data["deliverable_markdown"]

            lower_text = text_content.lower()
            if "belief" in lower_text:
                scores["belief_clarity_present"] = True
            if "behavior" in lower_text:
                scores["behavior_clarity_present"] = True
            if "system" in lower_text or "policy" in lower_text or "enabler" in lower_text:
                scores["systems_policies_present"] = True

            # Alignment pt 1: Strategy has goals
            updated_state = sl_data.get("updated_state", {})
            strategy = sl_data.get("strategy", updated_state.get("strategy", {}))
            if strategy and strategy.get("goals"):
                scores["alignment_score"] += 1

        except Exception as e:
            log(f"Error reading Strategy Lead state: {e}")

    # --- Learning Architect Analysis ---
    la_path = run_path / "03_learning_architect_agent_state.json"
    if la_path.exists():
        try:
            with open(la_path) as f:
                la_data = json.load(f)

            # Support both top-level curriculum and updated_state.curriculum
            curriculum = la_data.get("curriculum", {})
            if not curriculum:
                la_updated = la_data.get("updated_state", {})
                curriculum = la_updated.get("curriculum", {})

            # Support modules, outline, or course_architecture
            outline = (
                curriculum.get("modules")
                or curriculum.get("outline")
                or curriculum.get("course_architecture")
                or []
            )

            # Alignment pt 2: Has modules
            if outline:
                scores["alignment_score"] += 1

            # Copilot Coverage
            copilot_mentions = 0
            for module in outline:
                text = (
                    module.get("title", "") + " "
                    + " ".join(module.get("objectives", []))
                ).lower()
                if "copilot" in text:
                    copilot_mentions += 1

            if copilot_mentions > 0:
                scores["copilot_coverage_score"] = 1
            if copilot_mentions > 3:
                scores["copilot_coverage_score"] = 2

        except Exception as e:
            log(f"Error reading Learning Architect state: {e}")

    # Normalize alignment to 0-2 (Goals + Modules)
    scores["alignment_score"] = min(scores["alignment_score"], 2)

    return scores

def calculate_stability_score(reports: List[Dict[str, Any]]) -> int:
    """Calculates a 0-100 Structure Stability Score based on learning architect invariants.

    Scoring:
    - Starts at 100.
    - -20 if module_count varies across runs (variance-based, not against a constant).
    - -20 if objectives_count varies by more than 10% from average across runs.
    - -30 if module ID sequences differ across runs.
    - -5 per module if per-module sub-counts (checks/activities/key_concepts) drift.
    """
    if not reports:
        return 0

    score = 100

    # --- Module count variance ---
    module_counts = [r["structure"]["modules_count"] for r in reports]
    if len(set(module_counts)) > 1:
        score -= 20

    # --- Objectives count variance (>10% of average -> penalty) ---
    obj_counts = [r["structure"].get("objectives_count", 0) for r in reports]
    if len(obj_counts) > 1:
        avg_obj = sum(obj_counts) / len(obj_counts)
        if avg_obj > 0:
            max_diff = max(abs(c - avg_obj) for c in obj_counts)
            if max_diff / avg_obj > 0.10:
                score -= 20

    # --- Module ID sequence stability ---
    first_ids = reports[0]["structure"].get("module_ids", [])
    for r in reports[1:]:
        if r["structure"].get("module_ids", []) != first_ids:
            score -= 30
            break

    # --- Per-module sub-count drift ---
    if first_ids:
        for m_id in first_ids:
            for key in ["checks", "activities", "key_concepts"]:
                counts = [
                    r["structure"].get("per_module_counts", {}).get(m_id, {}).get(key, 0)
                    for r in reports
                ]
                if len(set(counts)) > 1:
                    score -= 5
                    break  # One penalty per module

    return max(0, min(100, score))

def main():
    parser = argparse.ArgumentParser(description="Content Consistency Harness")
    parser.add_argument("--inputs-dir", required=True, type=Path)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--governance_profile", default="content_only")
    parser.add_argument("--model", default="gpt-4o", help="Model to use if provider is openai")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve phase gates")
    
    args = parser.parse_args()
    
    if not args.inputs_dir.exists():
        print(f"Error: Inputs directory {args.inputs_dir} does not exist.")
        sys.exit(1)

    # Setup export directories
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)
    
    run_records = []
    
    print("="*60)
    print(f"CONTENT CONSISTENCY HARNESS")
    print(f"Inputs: {args.inputs_dir}")
    print(f"Runs: {args.runs}")
    print(f"Provider: {args.provider}")
    print("="*60)

    # 1. Execute Runs
    for i in range(args.runs):
        log(f"Starting Run {i+1}/{args.runs}...")
        try:
            run_dir = run_pipeline(
                args.inputs_dir, 
                args.provider, 
                args.governance_profile,
                args.auto_approve,
                args.model
            )
            
            # Destination for this run's artifacts
            run_dest = TEMP_DIR / f"run_{i+1}_{run_dir.name}"
            collect_artifacts(run_dir, run_dest)
            
            run_records.append({
                "run_index": i + 1,
                "run_id": run_dir.name,
                "path": run_dest
            })
            
        except Exception as e:
            log(f"Run {i+1} failed: {e}")
            # We continue to try other runs? 
            # Requirement implies we want a report. If a run fails, it's a stability issue (0 score).
            run_records.append({
                "run_index": i + 1,
                "run_id": "FAILED",
                "error": str(e),
                "path": None
            })

    # 2. Analyze Artifacts
    run_reports = []
    
    for record in run_records:
        if record["path"]:
            structure = analyze_structure(record)
            rubric = calculate_quality_rubric(record["path"])
            
            run_reports.append({
                "run_id": record["run_id"],
                "structure": structure,
                "quality_rubric": rubric,
                "status": "success"
            })
        else:
             run_reports.append({
                "run_id": record.get("run_id", "UNKNOWN"),
                "status": "failed",
                "error": record.get("error")
            })

    # 3. Aggregate Report
    # Filter successful runs for stability calc
    successful_reports = [r for r in run_reports if r["status"] == "success"]
    stability_score = calculate_stability_score(successful_reports)
    
    # Check for structural deltas
    diffs_summary = []
    first_modules_count = successful_reports[0]["structure"]["modules_count"] if successful_reports else 0
    if any(r["structure"]["modules_count"] != first_modules_count for r in successful_reports[1:]):
         diffs_summary.append({"field": "modules_count", "message": "Module count drifted across runs."})
         
    first_ids = successful_reports[0]["structure"].get("module_ids", []) if successful_reports else []
    if any(r["structure"].get("module_ids", []) != first_ids for r in successful_reports[1:]):
         diffs_summary.append({"field": "module_ids", "message": "Module sequence (IDs) drifted across runs."})
         
    for m_id in first_ids:
         for r in successful_reports:
              m_data = r["structure"].get("per_module_counts", {}).get(m_id)
              if m_data:
                   kc, act, chk = m_data.get("key_concepts", 0), m_data.get("activities", 0), m_data.get("checks", 0)
                   if not (3 <= kc <= 5): diffs_summary.append({"field": "key_concepts_count", "module_id": m_id, "message": f"{m_id} key_concepts out of range (3-5): {kc}"})
                   if act != 2: diffs_summary.append({"field": "activities_count", "module_id": m_id, "message": f"{m_id} activities not exactly 2: {act}"})
                   if chk != 2: diffs_summary.append({"field": "checks_count", "module_id": m_id, "message": f"{m_id} checks not exactly 2: {chk}"})
         
         for key in ["key_concepts", "activities", "checks"]:
             counts = [r["structure"].get("per_module_counts", {}).get(m_id, {}).get(key, 0) for r in successful_reports]
             if len(set(counts)) > 1:
                 diffs_summary.append({"field": f"{key}_count", "module_id": m_id, "runs": counts, "message": f"{m_id} {key} counts drifted across runs: {counts}"})

    # Remove duplicates but keep order
    unique_diffs = []
    seen = set()
    for d in diffs_summary:
        s = json.dumps(d, sort_keys=True)
        if s not in seen:
            seen.add(s)
            unique_diffs.append(d)
    diffs_summary = unique_diffs

    final_report = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "inputs_dir": str(args.inputs_dir),
            "provider": args.provider,
            "runs": args.runs,
            "profile": args.governance_profile
        },
        "overall_stability_score": stability_score,
        "structure_stability_score": stability_score,  # backwards-compat alias
        "modules_per_run": [r["structure"]["modules_count"] for r in successful_reports],
        "objectives_per_run": [r["structure"]["objectives_count"] for r in successful_reports],
        "storyboard_per_run": [r["structure"].get("storyboard_modules_count", 0) for r in successful_reports],
        "structure_invariants_by_run": [r["structure"] for r in successful_reports],
        "structure_diffs_summary": diffs_summary,
        "runs": run_reports
    }
    
    report_path = EXPORTS_DIR / "content_consistency_report.json"
    with open(report_path, "w") as f:
        json.dump(final_report, f, indent=2)
    log(f"Report generated: {report_path}")

    # 4. Create ZIP Pack
    zip_path = EXPORTS_DIR / "content_consistency_pack.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add the report
        zf.write(report_path, arcname="content_consistency_report.json")
        
        # Add artifacts from each run
        for record in run_records:
            if record["path"]:
                # Add folder for run
                base_arc = f"run_{record['run_id']}"
                for file_path in record["path"].iterdir():
                    zf.write(file_path, arcname=f"{base_arc}/{file_path.name}")
        
        # Create Diff Overview Markdown
        diff_md = "# Content Consistency Diff Overview\n\n"
        diff_md += f"**Structure Stability Score**: {stability_score}/100\n\n"
        diff_md += "## Structural Comparison\n"
        
        diff_md += "| Run ID | Modules | Alignment |\n"
        diff_md += "|---|---|---|\n"
        for r in successful_reports:
            diff_md += f"| {r['run_id']} | {r['structure']['modules_count']} | {r['quality_rubric']['alignment_score']} |\n"
            
        zf.writestr("diff_overview.md", diff_md)
        
        # Create Structure Overview Markdown
        struct_md = "# Structure Overview\n\n"
        for r in successful_reports:
            struct_md += f"## Run: {r['run_id']}\n"
            for m_id, m_data in r["structure"].get("per_module_counts", {}).items():
                title = m_data.get("title", "Untitled")
                kc = m_data.get("key_concepts", 0)
                act = m_data.get("activities", 0)
                chk = m_data.get("checks", 0)
                struct_md += f"- **{m_id}**: {title} (Concepts: {kc}, Activities: {act}, Checks: {chk})\n"
            struct_md += "\n"
        zf.writestr("structure_overview.md", struct_md)

    log(f"Pack generated: {zip_path}")
    
    # 5. Cleanup
    shutil.rmtree(TEMP_DIR)
    print(f"\n✅ Content Consistency Check Completed.")

if __name__ == "__main__":
    main()
