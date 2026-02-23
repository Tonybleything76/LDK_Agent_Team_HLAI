#!/usr/bin/env python3
"""
Quality Review Agent Runner

Executes the Quality Review Agent against the final storyboard output to evaluate
pedagogical rigor and intellectual depth.

Usage:
    python3 scripts/run_quality_review.py --course-slug <slug> --inputs-dir <dir> ...
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
EXPORTS_DIR = PROJECT_ROOT / "exports"

from orchestrator.agents.quality_review_agent import run_quality_review

def main():
    parser = argparse.ArgumentParser(description="Run Quality Review Agent")
    parser.add_argument("--course-slug", required=True)
    parser.add_argument("--inputs-dir", type=Path, default=None)
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--premium-threshold", type=int, default=9)
    parser.add_argument("--min-quality", type=int, default=7)

    args = parser.parse_args()

    # Find the state files
    # Depending on how it's called, inputs_dir might point directly to a run dir
    # or we might need to find the latest run in outputs/
    
    la_file = None
    sb_file = None
    
    if args.inputs_dir and (args.inputs_dir / "03_learning_architect_agent_state.json").exists():
        la_file = args.inputs_dir / "03_learning_architect_agent_state.json"
        sb_file = args.inputs_dir / "06_storyboard_agent_state.json"
    else:
        # Fallback to the latest run in outputs/
        outputs_dir = PROJECT_ROOT / "outputs"
        all_runs = sorted(
            [d for d in outputs_dir.iterdir() if d.is_dir() and d.name.startswith("20")],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        for run_dir in all_runs:
            if (run_dir / "03_learning_architect_agent_state.json").exists() and (run_dir / "06_storyboard_agent_state.json").exists():
                la_file = run_dir / "03_learning_architect_agent_state.json"
                sb_file = run_dir / "06_storyboard_agent_state.json"
                break

    if not la_file or not sb_file or not la_file.exists() or not sb_file.exists():
        print("ERROR: Could not find required state files (03_learning_architect_agent_state.json, 06_storyboard_agent_state.json)")
        sys.exit(1)

    with open(la_file, "r") as f:
        la_state = json.load(f)
    
    with open(sb_file, "r") as f:
        sb_state = json.load(f)

    print(f"Running Quality Review for '{args.course_slug}'...")
    try:
        report = run_quality_review(
            storyboard_state=sb_state,
            la_state=la_state,
            provider_name=args.provider,
            model=args.model
        )
    except Exception as e:
        print(f"ERROR: Quality review failed: {e}")
        sys.exit(1)

    # Check schema rules
    score = report.get("quality_score", 0)
    # Check if premium flag meets logic
    if score >= args.premium_threshold:
        report["premium_flag"] = True
    else:
        report["premium_flag"] = False

    # write output
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = EXPORTS_DIR / f"quality_review_report_{args.course_slug}.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Quality Review Report saved to {report_path}")
    print("=" * 40)
    print(f"Quality Score: {score}/10")
    print(f"Premium Flag : {report.get('premium_flag')}")
    print("Domain Scores:")
    for domain, val in report.get("domain_scores", {}).items():
        print(f"  - {domain}: {val}/2")
    
    if score < args.min_quality:
        print(f"\n❌ FAIL: Score {score} is below minimum quality threshold {args.min_quality}.")
        sys.exit(1)
    else:
        print(f"\n✅ PASS: Quality bar met.")
        sys.exit(0)

if __name__ == "__main__":
    main()
