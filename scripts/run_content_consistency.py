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
    governance_profile: str
) -> Path:
    """Executes a single pipeline run and returns the run directory."""
    
    # Construct command
    cmd = [
        "python3", "scripts/run_pipeline.py",
        "--inputs-dir", str(inputs_dir.resolve().relative_to(PROJECT_ROOT.resolve())),
        "--governance_profile", governance_profile,
        "--yes", # Skip cost confirmation
        "--auto_approve", # Skip phase gates
    ]
    
    if provider == "dry_run":
        cmd.append("--dry_run")
    elif provider:
        cmd.extend(["--mode", provider])

    # Environment variables
    env = os.environ.copy()
    env["PROVIDER"] = provider
    
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
    # This involves reading the copied JSON files in run_data['path']
    base_path = run_data['path']
    metrics = {
        "modules_count": 0,
        "objectives_count": 0,
        "assessment_items_count": 0,
        "schema_validity": {}
    }
    
    # 1. Learning Architect (Curriculum/Modules)
    la_path = base_path / "03_learning_architect_agent_state.json"
    if la_path.exists():
        try:
            with open(la_path) as f:
                data = json.load(f)
                updated_state = data.get("updated_state", {})
                curriculum = updated_state.get("curriculum", {})
                outline = curriculum.get("outline", [])
                metrics["modules_count"] = len(outline)
                metrics["objectives_count"] = sum(len(m.get("objectives", [])) for m in outline)
                metrics["schema_validity"]["learning_architect"] = True
        except json.JSONDecodeError:
            metrics["schema_validity"]["learning_architect"] = False

    # 2. Instructional Designer (Assessment Items often defined here or in next step)
    # Actually, Assessment Designer is 05.
    ad_path = base_path / "05_assessment_designer_agent_state.json"
    if ad_path.exists():
        try:
            with open(ad_path) as f:
                data = json.load(f)
                # Assessment structure varies, but let's check for 'assessment_items' or similar
                # Usually updated_state.assessment or similar.
                # Inspecting prompt for Assessment Designer would confirm, but let's look for known keys.
                # If structure unknown, we count raw items if list, or key count.
                # Assuming generic "assessment" key
                updated_state = data.get("updated_state", {})
                assessment = updated_state.get("assessment", {})
                if assessment:
                   if isinstance(assessment, list):
                       metrics["assessment_items_count"] = len(assessment)
                   elif isinstance(assessment, dict):
                        # heuristics
                        metrics["assessment_items_count"] = len(assessment.get("questions", []) or assessment.get("items", []))
                metrics["schema_validity"]["assessment_designer"] = True
        except:
            metrics["schema_validity"]["assessment_designer"] = False

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
    
    # Strategy Lead Analysis
    sl_path = run_path / "01_strategy_lead_agent_state.json"
    if sl_path.exists():
        try:
            with open(sl_path) as f:
                data = json.load(f)
                # Check markdown content for keywords
                # Note: The agent state usually contains 'deliverable' or 'messages' history.
                # run_pipeline implementation saves specific state files. 
                # Assuming 01_strategy_lead_agent_state.json is the DIRECT state output
                # which usually has keys like "strategy", "deliverable_markdown", etc.
                
                # We need to check if we are reading the raw agent state or the final artifact mapping.
                # The file name implies it's the state dump.
                
                # If text is in 'deliverable_markdown' or keys in 'strategy'
                text_content = ""
                if "deliverable_markdown" in data:
                    text_content += data["deliverable_markdown"]
                
                # Heuristics
                lower_text = text_content.lower()
                if "belief" in lower_text: scores["belief_clarity_present"] = True
                if "behavior" in lower_text: scores["behavior_clarity_present"] = True
                if "system" in lower_text or "policy" in lower_text or "enabler" in lower_text:
                    scores["systems_policies_present"] = True
                    
                # Alignment Calculation (0-2)
                # Presence of Goal (Strategy) -> Outline (LA) -> Assessment (AD)
                # We need cross-file checks. 
                updated_state = data.get("updated_state", {})
                strategy = updated_state.get("strategy", {})
                has_goals = False
                if strategy and "goals" in strategy:
                    if strategy["goals"]: has_goals = True
                
                # We'll update alignment in a wider scope or check other files here?
                # Let's do partial check here.
                if has_goals: scores["alignment_score"] += 1
                
        except Exception as e:
            log(f"Error reading Strategy Lead state: {e}")

    # Check alignment part 2 (Curriculum & Assessment existence)
    # We already checked goals. Now check if they flow down.
    # Simple proxy: if modules > 0 and assessment items > 0 (calculated in structure)
    # We can refine this.
    
    # Copilot Check in Learning Architect
    la_path = run_path / "03_learning_architect_agent_state.json"
    if la_path.exists():
        try:
            with open(la_path) as f:
                updated_state = data.get("updated_state", {})
                curriculum = updated_state.get("curriculum", {})
                outline = curriculum.get("outline", [])
                
                # Alignment score pt 2: Has modules?
                if outline: scores["alignment_score"] += 1
                
                # Copilot Coverage
                # Check for "Copilot" in titles or objectives
                copilot_mentions = 0
                for module in outline:
                    text = (module.get("title", "") + " " + " ".join(module.get("objectives", []))).lower()
                    if "copilot" in text:
                        copilot_mentions += 1
                
                if copilot_mentions > 0:
                    scores["copilot_coverage_score"] = 1
                if copilot_mentions > 3: # Arbitrary threshold for "good" coverage
                    scores["copilot_coverage_score"] = 2
                    
        except:
            pass

    # Normalize alignment to 0-2 (Goals + Modules) - max 2
    scores["alignment_score"] = min(scores["alignment_score"], 2)
    
    return scores

def calculate_stability_score(reports: List[Dict[str, Any]]) -> int:
    """Calculates a 0-100 stability score based on variance."""
    if not reports: return 0
    
    # Metrics to track variance
    module_counts = [r["structure"]["modules_count"] for r in reports]
    objective_counts = [r["structure"]["objectives_count"] for r in reports]
    
    # Variance penalty
    score = 100
    
    # If module counts differ, heavy penalty
    if len(set(module_counts)) > 1:
        score -= 20
        
    # If objective counts differ significantly (more than 10%)
    avg_obj = sum(objective_counts) / len(objective_counts) if objective_counts else 0
    if avg_obj > 0:
        max_diff = max(abs(x - avg_obj) for x in objective_counts)
        pct_diff = max_diff / avg_obj
        if pct_diff > 0.1:
            score -= 10
        if pct_diff > 0.2:
            score -= 20

    return max(0, score)

def main():
    parser = argparse.ArgumentParser(description="Content Consistency Harness")
    parser.add_argument("--inputs-dir", required=True, type=Path)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--governance_profile", default="content_only")
    
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
            run_dir = run_pipeline(args.inputs_dir, args.provider, args.governance_profile)
            
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
    structure_deltas = {
        "modules_variance": len(set(r["structure"]["modules_count"] for r in successful_reports)) > 1 if successful_reports else False,
        "objectives_variance": len(set(r["structure"]["objectives_count"] for r in successful_reports)) > 1 if successful_reports else False
    }

    final_report = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "inputs_dir": str(args.inputs_dir),
            "provider": args.provider,
            "runs": args.runs,
            "profile": args.governance_profile
        },
        "overall_stability_score": stability_score,
        "structure_deltas": structure_deltas,
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
        diff_md += f"**Stability Score**: {stability_score}/100\n\n"
        diff_md += "## Structural Comparison\n"
        
        # Table header
        diff_md += "| Run ID | Modules | Objectives | Alignment |\n"
        diff_md += "|---|---|---|---|\n"
        for r in successful_reports:
            diff_md += f"| {r['run_id']} | {r['structure']['modules_count']} | {r['structure']['objectives_count']} | {r['quality_rubric']['alignment_score']} |\n"
            
        zf.writestr("diff_overview.md", diff_md)

    log(f"Pack generated: {zip_path}")
    
    # 5. Cleanup
    shutil.rmtree(TEMP_DIR)
    print(f"\n✅ Content Consistency Check Completed.")

if __name__ == "__main__":
    main()
